"""
Jira service — business logic layer.

Responsibilities:
  - Project listing and validation
  - AI-assisted ticket draft generation (via ai_service)
  - Issue creation (explicit developer approval required)
  - Issue lookup and update
  - Severity → Jira priority mapping:
      CRITICAL → Highest
      HIGH     → High
      MEDIUM   → Medium
      LOW      → Low
  - Linking issues to findings in the database

Issue creation is NEVER automatic.
Every create call must originate from an explicit user action.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.integrations.jira import JiraClient, get_client
from app.models import Finding, JiraTicket
from app.services import ai_service

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Priority mapping
# ─────────────────────────────────────────────────────────────────────────────

_SEVERITY_TO_PRIORITY: dict[str, str] = {
    "critical": "Highest",
    "high":     "High",
    "medium":   "Medium",
    "low":      "Low",
}

DEFAULT_ISSUE_TYPE = "Bug"


# ─────────────────────────────────────────────────────────────────────────────
# Domain types
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class JiraProject:
    key:  str
    name: str
    id:   str

    def to_dict(self) -> dict:
        return {"key": self.key, "name": self.name, "id": self.id}


@dataclass
class JiraIssueDraft:
    """
    AI-generated ticket content awaiting developer approval.
    This is NEVER automatically sent to Jira.
    """
    finding_id:          str
    summary:             str
    description:         str
    priority:            str
    component:           str | None
    labels:              list[str]
    acceptance_criteria: list[str]
    technical_notes:     str

    def to_dict(self) -> dict:
        return {
            "finding_id":          self.finding_id,
            "summary":             self.summary,
            "description":         self.description,
            "priority":            self.priority,
            "component":           self.component,
            "labels":              self.labels,
            "acceptance_criteria": self.acceptance_criteria,
            "technical_notes":     self.technical_notes,
        }


@dataclass
class CreatedIssue:
    key:  str
    id:   str
    url:  str
    status: str = "created"

    def to_dict(self) -> dict:
        return {"key": self.key, "id": self.id, "url": self.url, "status": self.status}


# ─────────────────────────────────────────────────────────────────────────────
# Service
# ─────────────────────────────────────────────────────────────────────────────

class JiraService:

    def __init__(self, client: JiraClient | None = None) -> None:
        self._client = client or get_client()

    # ── Projects ──────────────────────────────────────────────────────────────

    def list_projects(self) -> list[JiraProject]:
        """Return all Jira projects accessible with the configured credentials."""
        raw = self._client.list_projects()
        return [
            JiraProject(
                key=p.get("key", ""),
                name=p.get("name", ""),
                id=p.get("id", ""),
            )
            for p in raw
        ]

    def get_project(self, project_key: str) -> JiraProject:
        raw = self._client.get_project(project_key)
        return JiraProject(
            key=raw.get("key", project_key),
            name=raw.get("name", ""),
            id=raw.get("id", ""),
        )

    # ── Draft generation ──────────────────────────────────────────────────────

    def draft_issue(
        self,
        finding: Finding,
        repository: str,
    ) -> JiraIssueDraft:
        """
        Use watsonx.ai to draft a Jira ticket from a code finding.
        Returns a :class:`JiraIssueDraft` for developer review.
        This does NOT create anything in Jira.
        """
        finding_dict = {
            "title":          finding.title,
            "severity":       finding.severity,
            "finding_type":   finding.finding_type,
            "explanation":    finding.explanation or "",
            "recommendation": finding.recommendation or "",
            "file_path":      finding.file_path or "",
            "line_number":    finding.line_number,
        }

        try:
            ai_resp = ai_service.generate_jira_ticket(
                finding=finding_dict,
                repository=repository,
            )
        except Exception as exc:
            logger.warning("AI Jira draft failed for finding %s: %s", finding.id, exc)
            ai_resp = _fallback_draft(finding_dict)

        priority = _SEVERITY_TO_PRIORITY.get(finding.severity, "Medium")

        return JiraIssueDraft(
            finding_id=finding.id,
            summary=ai_resp.get("summary", finding.title)[:80],
            description=ai_resp.get("description", finding.explanation or ""),
            priority=ai_resp.get("priority", priority),
            component=ai_resp.get("component"),
            labels=ai_resp.get("labels", [finding.finding_type]),
            acceptance_criteria=ai_resp.get("acceptance_criteria", []),
            technical_notes=ai_resp.get("technical_notes", finding.recommendation or ""),
        )

    # ── Issue creation (requires explicit developer approval) ─────────────────

    def create_issue(
        self,
        project_key: str,
        draft: JiraIssueDraft,
        issue_type: str = DEFAULT_ISSUE_TYPE,
        db: Session | None = None,
    ) -> CreatedIssue:
        """
        Create a Jira issue from an approved draft.

        This method MUST only be called after the developer has explicitly
        reviewed and confirmed the draft. It is the only write operation
        in this service.

        Args:
            project_key: Target Jira project key (e.g. ``"PROJ"``).
            draft:       Developer-approved :class:`JiraIssueDraft`.
            issue_type:  Jira issue type (default: "Bug").
            db:          Optional DB session — used to persist the
                         :class:`JiraTicket` record if provided.

        Returns:
            :class:`CreatedIssue` with Jira issue key and URL.
        """
        fields: dict = {
            "project":   {"key": project_key},
            "summary":   draft.summary,
            "issuetype": {"name": issue_type},
            "priority":  {"name": draft.priority},
            "description": {
                "type":    "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": draft.description}],
                    }
                ],
            },
        }

        if draft.labels:
            fields["labels"] = draft.labels

        logger.info(
            "Creating Jira issue in project %s for finding %s (developer-approved)",
            project_key, draft.finding_id,
        )

        result = self._client.create_issue(fields)
        issue_key = result.get("key", "")
        issue_id  = result.get("id", "")
        issue_url = f"{self._client._base_url}/browse/{issue_key}"

        # Persist to DB if session provided
        if db and draft.finding_id:
            ticket = JiraTicket(
                finding_id=draft.finding_id,
                jira_issue_key=issue_key,
                jira_issue_url=issue_url,
                status="created",
            )
            db.add(ticket)
            db.commit()

        return CreatedIssue(key=issue_key, id=issue_id, url=issue_url)

    # ── Issue lookup ──────────────────────────────────────────────────────────

    def get_issue(self, issue_key: str) -> dict:
        """Return raw Jira issue data for *issue_key*."""
        raw = self._client.get_issue(issue_key)
        fields = raw.get("fields", {})
        return {
            "key":         raw.get("key", issue_key),
            "id":          raw.get("id", ""),
            "summary":     fields.get("summary", ""),
            "status":      (fields.get("status") or {}).get("name", ""),
            "priority":    (fields.get("priority") or {}).get("name", ""),
            "assignee":    ((fields.get("assignee") or {}).get("displayName")),
            "created":     fields.get("created", ""),
            "updated":     fields.get("updated", ""),
            "url":         f"{self._client._base_url}/browse/{raw.get('key', '')}",
        }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _fallback_draft(finding: dict) -> dict:
    """Construct a minimal draft when AI is unavailable."""
    severity = finding.get("severity", "medium")
    return {
        "summary":             finding.get("title", "Code finding")[:80],
        "description":         finding.get("explanation", ""),
        "priority":            _SEVERITY_TO_PRIORITY.get(severity, "Medium"),
        "component":           None,
        "labels":              [finding.get("finding_type", "tech-debt")],
        "acceptance_criteria": ["Issue is resolved and all related tests pass."],
        "technical_notes":     finding.get("recommendation", ""),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Module-level factory
# ─────────────────────────────────────────────────────────────────────────────

def get_jira_service() -> JiraService:
    return JiraService()
