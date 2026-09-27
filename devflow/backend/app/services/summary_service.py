"""
Summary service.

Two features:
  1. PR Description generator
     Input:  raw unified diff + repo/branch metadata
     Output: structured PR description (title, summary, changes, risks, etc.)

  2. Return-to-work summary generator
     Input:  recent commits, merged PRs, optional Jira updates
     Output: prioritised briefing for a developer returning from leave

Both features use watsonx.ai via ai_service.
Static analysis findings from the diff may be included as context.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.services import ai_service

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Output types
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PRDescription:
    title:            str
    summary:          str
    changes:          list[str]
    technical_impact: str | None
    testing:          str | None
    risks:            str | None
    dependencies:     str | None
    deployment_notes: str | None
    full_description: str   # markdown-formatted complete description

    def to_dict(self) -> dict:
        return {
            "title":            self.title,
            "summary":          self.summary,
            "changes":          self.changes,
            "technical_impact": self.technical_impact,
            "testing":          self.testing,
            "risks":            self.risks,
            "dependencies":     self.dependencies,
            "deployment_notes": self.deployment_notes,
            "full_description": self.full_description,
        }


@dataclass
class PRSummary:
    title:   str
    summary: str

    def to_dict(self) -> dict:
        return {"title": self.title, "summary": self.summary}


@dataclass
class ReturnSummary:
    period:              str
    important_changes:   list[str]
    merged_prs:          list[PRSummary]
    production_changes:  list[str]
    jira_updates:        list[str]
    recommended_actions: list[str]
    full_summary:        str   # markdown-formatted briefing

    def to_dict(self) -> dict:
        return {
            "period":              self.period,
            "important_changes":   self.important_changes,
            "merged_prs":          [p.to_dict() for p in self.merged_prs],
            "production_changes":  self.production_changes,
            "jira_updates":        self.jira_updates,
            "recommended_actions": self.recommended_actions,
            "full_summary":        self.full_summary,
        }


# ─────────────────────────────────────────────────────────────────────────────
# PR Description
# ─────────────────────────────────────────────────────────────────────────────

def generate_pr_description(
    diff: str,
    repository: str,
    branch: str,
) -> PRDescription:
    """
    Generate a professional pull request description from a unified diff.

    Args:
        diff:       Raw unified diff text.
        repository: Full repository name (e.g. "acme/api").
        branch:     Source branch name.

    Returns:
        :class:`PRDescription` with all structured sections.
    """
    logger.info("generate_pr_description: repo=%s branch=%s diff_len=%d", repository, branch, len(diff))

    try:
        ai_response = ai_service.generate_pr_description(
            diff=diff,
            repository=repository,
            branch=branch,
        )
    except Exception as exc:
        logger.error("PR description generation failed: %s", exc)
        return _fallback_pr_description(repository, branch, exc)

    return PRDescription(
        title=ai_response.get("title", f"Changes on {branch}"),
        summary=ai_response.get("summary", ""),
        changes=ai_response.get("changes", []),
        technical_impact=ai_response.get("technical_impact"),
        testing=ai_response.get("testing"),
        risks=ai_response.get("risks"),
        dependencies=ai_response.get("dependencies"),
        deployment_notes=ai_response.get("deployment_notes"),
        full_description=ai_response.get("full_description", ""),
    )


def _fallback_pr_description(repository: str, branch: str, exc: Exception) -> PRDescription:
    return PRDescription(
        title=f"Changes on {branch}",
        summary=f"AI description generation was unavailable: {exc}",
        changes=["Review the diff for changes."],
        technical_impact=None,
        testing=None,
        risks=None,
        dependencies=None,
        deployment_notes=None,
        full_description=(
            f"## {branch}\n\n"
            f"**Repository:** {repository}\n\n"
            f"AI-generated description unavailable. Please write the description manually.\n\n"
            f"*Error: {exc}*"
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Return-to-work summary
# ─────────────────────────────────────────────────────────────────────────────

def generate_return_summary(
    repository: str,
    commits: list[dict],
    pull_requests: list[dict],
    since_date: datetime | None = None,
    jira_updates: list[str] | None = None,
) -> ReturnSummary:
    """
    Generate a prioritised return-to-work briefing.

    Args:
        repository:    Full repository name.
        commits:       List of recent commit dicts (sha, message, author, date).
        pull_requests: List of recent PR dicts (number, title, state, etc.).
        since_date:    The date the developer was last active (for period label).
        jira_updates:  Optional list of Jira ticket summaries to include.

    Returns:
        :class:`ReturnSummary` covering important changes, merged PRs,
        production impacts, and recommended actions.
    """
    # Build period label
    if since_date:
        period = f"Since {since_date.strftime('%Y-%m-%d')}"
    else:
        period = f"Last {len(commits)} commits"

    logger.info(
        "generate_return_summary: repo=%s commits=%d prs=%d",
        repository, len(commits), len(pull_requests),
    )

    try:
        ai_response = ai_service.generate_return_summary(
            commits=commits,
            pull_requests=pull_requests,
            repository=repository,
            period=period,
        )
    except Exception as exc:
        logger.error("Return summary generation failed: %s", exc)
        return _fallback_return_summary(repository, period, commits, pull_requests, jira_updates or [], exc)

    merged_prs = [
        PRSummary(
            title=pr.get("title", ""),
            summary=pr.get("summary", ""),
        )
        for pr in ai_response.get("prs_merged", [])
    ]

    return ReturnSummary(
        period=ai_response.get("period", period),
        important_changes=ai_response.get("highlights", []),
        merged_prs=merged_prs,
        production_changes=ai_response.get("production_changes", []),
        jira_updates=jira_updates or [],
        recommended_actions=ai_response.get("recommended_actions", []),
        full_summary=ai_response.get("full_summary", ""),
    )


def _fallback_return_summary(
    repository: str,
    period: str,
    commits: list[dict],
    pull_requests: list[dict],
    jira_updates: list[str],
    exc: Exception,
) -> ReturnSummary:
    # Build a basic summary from raw data without AI
    merged = [
        PRSummary(title=pr.get("title", f"PR #{pr.get('number','')}"), summary="")
        for pr in pull_requests
        if pr.get("state") in ("closed", "merged")
    ]

    recent_messages = [
        c.get("message", "")[:80] for c in commits[:5]
    ]

    return ReturnSummary(
        period=period,
        important_changes=recent_messages,
        merged_prs=merged,
        production_changes=[],
        jira_updates=jira_updates,
        recommended_actions=["Review the recent commits and merged PRs listed above."],
        full_summary=(
            f"# Return-to-work summary — {repository}\n\n"
            f"**Period:** {period}\n\n"
            f"AI summary unavailable ({exc}). "
            f"Review the {len(commits)} recent commit(s) and "
            f"{len(merged)} merged PR(s) listed above.\n"
        ),
    )
