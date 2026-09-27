"""
Jira router.

GET  /jira/projects                — list accessible Jira projects
POST /jira/draft                   — AI-generate a ticket draft from a finding
POST /jira/issues                  — create issue (REQUIRES explicit confirmation flag)
GET  /jira/issues/{issue_key}      — fetch live issue data from Jira

Issue creation is NEVER automatic.  The request body must carry
`confirmed: true` to signal the developer has reviewed the draft.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models import Finding, User
from app.services.jira_service import JiraIssueDraft, JiraService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jira", tags=["jira"])

# ─────────────────────────────────────────────────────────────────────────────
# Request / response schemas (local — extends global schemas as needed)
# ─────────────────────────────────────────────────────────────────────────────

class ProjectItem(BaseModel):
    key:  str
    name: str
    id:   str


class ProjectListResponse(BaseModel):
    projects: list[ProjectItem]
    total: int


class DraftRequest(BaseModel):
    finding_id: str = Field(description="DB ID of the Finding to draft a ticket for")
    repository:  str = Field(description="Repository name, e.g. 'acme/api'")


class DraftResponse(BaseModel):
    finding_id:          str
    summary:             str
    description:         str
    priority:            str
    component:           str | None
    labels:              list[str]
    acceptance_criteria: list[str]
    technical_notes:     str


class CreateIssueRequest(BaseModel):
    project_key: str  = Field(description="Jira project key, e.g. 'PROJ'")
    issue_type:  str  = Field(default="Bug", description="Jira issue type")
    confirmed:   bool = Field(
        default=False,
        description="Must be true — indicates developer has reviewed the draft",
    )
    # Draft payload (mirrors DraftResponse)
    finding_id:          str
    summary:             str
    description:         str
    priority:            str
    component:           str | None = None
    labels:              list[str]  = []
    acceptance_criteria: list[str]  = []
    technical_notes:     str        = ""


class CreateIssueResponse(BaseModel):
    key:    str
    id:     str
    url:    str
    status: str


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/projects", response_model=ProjectListResponse)
def list_projects(
    _current_user: User = Depends(get_current_user),
) -> ProjectListResponse:
    """Return all Jira projects accessible with the configured credentials."""
    svc = JiraService()
    projects = svc.list_projects()
    return ProjectListResponse(
        projects=[ProjectItem(**p.to_dict()) for p in projects],
        total=len(projects),
    )


@router.post("/draft", response_model=DraftResponse)
def draft_issue(
    req: DraftRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> DraftResponse:
    """
    Generate an AI-assisted Jira ticket draft from a code finding.

    The draft is returned for developer review; nothing is written to Jira.
    """
    finding = db.get(Finding, req.finding_id)
    if finding is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")

    svc = JiraService()
    draft = svc.draft_issue(finding=finding, repository=req.repository)
    return DraftResponse(**draft.to_dict())


@router.post("/issues", response_model=CreateIssueResponse, status_code=status.HTTP_201_CREATED)
def create_issue(
    req: CreateIssueRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> CreateIssueResponse:
    """
    Create a Jira issue from a developer-approved draft.

    The request **must** include ``confirmed: true`` to confirm
    the developer has reviewed the draft before submission.
    """
    if not req.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Issue creation requires explicit confirmation. Set confirmed=true after reviewing the draft.",
        )

    draft = JiraIssueDraft(
        finding_id=req.finding_id,
        summary=req.summary,
        description=req.description,
        priority=req.priority,
        component=req.component,
        labels=req.labels,
        acceptance_criteria=req.acceptance_criteria,
        technical_notes=req.technical_notes,
    )

    svc = JiraService()
    created = svc.create_issue(
        project_key=req.project_key,
        draft=draft,
        issue_type=req.issue_type,
        db=db,
    )

    logger.info(
        "Jira issue %s created by user %s for finding %s",
        created.key, _current_user.id, req.finding_id,
    )
    return CreateIssueResponse(**created.to_dict())


@router.get("/issues/{issue_key}", response_model=dict)
def get_issue(
    issue_key: str,
    _current_user: User = Depends(get_current_user),
) -> dict:
    """Fetch live issue data from Jira by issue key (e.g. ``PROJ-42``)."""
    svc = JiraService()
    return svc.get_issue(issue_key)
