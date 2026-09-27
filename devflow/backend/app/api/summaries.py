"""
Summaries router.

POST /summaries/pr
  Generate a PR description from a unified diff.

POST /summaries/return
  Generate a return-to-work briefing from recent commits and PRs.
"""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.auth import get_current_user
from app.models import User
from app.services.summary_service import (
    PRDescription,
    ReturnSummary,
    generate_pr_description,
    generate_return_summary,
)
from app.services.github_service import get_github_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Request schemas
# ─────────────────────────────────────────────────────────────────────────────

class PRDescriptionRequest(BaseModel):
    repository:  str   # "owner/repo"
    branch:      str
    base_branch: str = "main"
    pull_request: int | None = None   # if provided, fetch diff from GitHub
    diff:         str | None = None   # raw diff (alternative to PR number)


class ReturnSummaryRequest(BaseModel):
    repository:   str
    branch:       str = "main"
    since_date:   datetime | None = None
    jira_updates: list[str] | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Response schemas
# ─────────────────────────────────────────────────────────────────────────────

class PRDescriptionOut(BaseModel):
    title:            str
    summary:          str
    changes:          list[str]
    technical_impact: str | None
    testing:          str | None
    risks:            str | None
    dependencies:     str | None
    deployment_notes: str | None
    full_description: str


class PRSummaryOut(BaseModel):
    title:   str
    summary: str


class ReturnSummaryOut(BaseModel):
    period:              str
    important_changes:   list[str]
    merged_prs:          list[PRSummaryOut]
    production_changes:  list[str]
    jira_updates:        list[str]
    recommended_actions: list[str]
    full_summary:        str


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/pr",
    response_model=PRDescriptionOut,
    summary="Generate a professional PR description from a diff",
)
def pr_description(
    body: PRDescriptionRequest,
    _current_user: User = Depends(get_current_user),
) -> PRDescriptionOut:
    """
    Produces a structured PR description using watsonx.ai.
    Accepts either a raw diff string or a PR number (which is fetched from GitHub).
    """
    parts = body.repository.split("/")
    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="repository must be in 'owner/repo' format.",
        )
    owner, repo = parts

    # Resolve diff
    raw_diff = body.diff
    if not raw_diff:
        if body.pull_request is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Either diff or pull_request must be provided.",
            )
        try:
            svc = get_github_service()
            raw_diff = svc.get_pull_request_diff(owner, repo, body.pull_request)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Failed to fetch diff: {exc}")

    result: PRDescription = generate_pr_description(
        diff=raw_diff,
        repository=body.repository,
        branch=body.branch,
    )
    return PRDescriptionOut(**result.to_dict())


@router.post(
    "/return",
    response_model=ReturnSummaryOut,
    summary="Generate a return-to-work briefing from recent repo activity",
)
def return_summary(
    body: ReturnSummaryRequest,
    _current_user: User = Depends(get_current_user),
) -> ReturnSummaryOut:
    """
    Fetches recent commits and PRs from GitHub then asks watsonx.ai
    to produce a prioritised return-to-work briefing.
    """
    parts = body.repository.split("/")
    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="repository must be in 'owner/repo' format.",
        )
    owner, repo = parts

    try:
        svc = get_github_service()
        commits = [
            vars(c) for c in svc.list_commits(owner, repo, branch=body.branch, per_page=30)
        ]
        prs = [
            vars(pr) for pr in svc.list_pull_requests(owner, repo, state="closed", per_page=20)
        ]
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch repository activity: {exc}")

    result: ReturnSummary = generate_return_summary(
        repository=body.repository,
        commits=commits,
        pull_requests=prs,
        since_date=body.since_date,
        jira_updates=body.jira_updates,
    )

    # Map to response schema
    out_dict = result.to_dict()
    out_dict["merged_prs"] = [
        PRSummaryOut(**pr) for pr in out_dict.pop("merged_prs")
    ]
    return ReturnSummaryOut(**out_dict)
