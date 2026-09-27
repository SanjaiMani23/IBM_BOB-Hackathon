"""
GitHub API router.

Endpoints:
  GET  /github/repositories
  GET  /github/repositories/{owner}/{repo}/branches
  GET  /github/repositories/{owner}/{repo}/commits
  GET  /github/repositories/{owner}/{repo}/pulls
  GET  /github/repositories/{owner}/{repo}/pulls/{number}
  GET  /github/repositories/{owner}/{repo}/pulls/{number}/diff
  GET  /github/repositories/{owner}/{repo}/pulls/{number}/files
  POST /github/webhook

Webhook endpoint verifies HMAC-SHA256 signature before processing.
No GitHub resource is modified without explicit developer action.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, status
from fastapi.responses import PlainTextResponse

from app.config import settings
from app.integrations.github import verify_webhook_signature, GitHubAuthError, GitHubNotFoundError
from app.services.github_service import (
    Branch,
    ChangedFile,
    GitHubService,
    PullRequest,
    Repository,
    get_github_service,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Dependency
# ─────────────────────────────────────────────────────────────────────────────

def _svc() -> GitHubService:
    return get_github_service()


# ─────────────────────────────────────────────────────────────────────────────
# Error translation
# ─────────────────────────────────────────────────────────────────────────────

def _handle_github_errors(exc: Exception) -> None:
    """Re-raise GitHub client errors as appropriate HTTPExceptions."""
    if isinstance(exc, GitHubAuthError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    if isinstance(exc, GitHubNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"GitHub error: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# Response schemas (inline — avoids circular imports with schemas/__init__.py)
# ─────────────────────────────────────────────────────────────────────────────

from pydantic import BaseModel


class RepositoryOut(BaseModel):
    full_name:      str
    description:    str | None
    default_branch: str
    html_url:       str
    private:        bool


class BranchOut(BaseModel):
    name:      str
    sha:       str
    protected: bool


class CommitOut(BaseModel):
    sha:     str
    message: str
    author:  str
    date:    str
    url:     str


class PullRequestOut(BaseModel):
    number:        int
    title:         str
    state:         str
    branch:        str
    base:          str
    author:        str
    created_at:    str
    updated_at:    str
    html_url:      str
    commits:       int
    additions:     int
    deletions:     int
    changed_files: int


class ChangedFileOut(BaseModel):
    filename:  str
    status:    str
    additions: int
    deletions: int
    patch:     str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/repositories", response_model=list[RepositoryOut], summary="List accessible repositories")
def list_repositories(svc: GitHubService = Depends(_svc)):
    try:
        repos = svc.list_repositories()
    except Exception as exc:
        _handle_github_errors(exc)
    return [RepositoryOut(**vars(r)) for r in repos]


@router.get(
    "/repositories/{owner}/{repo}/branches",
    response_model=list[BranchOut],
    summary="List branches for a repository",
)
def list_branches(owner: str, repo: str, svc: GitHubService = Depends(_svc)):
    try:
        branches = svc.list_branches(owner, repo)
    except Exception as exc:
        _handle_github_errors(exc)
    return [BranchOut(**vars(b)) for b in branches]


@router.get(
    "/repositories/{owner}/{repo}/commits",
    response_model=list[CommitOut],
    summary="List recent commits on a branch",
)
def list_commits(
    owner: str,
    repo: str,
    branch: str = "main",
    per_page: int = 20,
    svc: GitHubService = Depends(_svc),
):
    try:
        commits = svc.list_commits(owner, repo, branch=branch, per_page=per_page)
    except Exception as exc:
        _handle_github_errors(exc)
    return [CommitOut(**vars(c)) for c in commits]


@router.get(
    "/repositories/{owner}/{repo}/pulls",
    response_model=list[PullRequestOut],
    summary="List pull requests",
)
def list_pull_requests(
    owner: str,
    repo: str,
    state: str = "open",
    svc: GitHubService = Depends(_svc),
):
    try:
        prs = svc.list_pull_requests(owner, repo, state=state)
    except Exception as exc:
        _handle_github_errors(exc)
    return [PullRequestOut(**vars(pr)) for pr in prs]


@router.get(
    "/repositories/{owner}/{repo}/pulls/{number}",
    response_model=PullRequestOut,
    summary="Get a single pull request",
)
def get_pull_request(
    owner: str,
    repo: str,
    number: int,
    svc: GitHubService = Depends(_svc),
):
    try:
        pr = svc.get_pull_request(owner, repo, number)
    except Exception as exc:
        _handle_github_errors(exc)
    return PullRequestOut(**vars(pr))


@router.get(
    "/repositories/{owner}/{repo}/pulls/{number}/diff",
    response_class=PlainTextResponse,
    summary="Get the raw unified diff for a pull request",
)
def get_pull_request_diff(
    owner: str,
    repo: str,
    number: int,
    svc: GitHubService = Depends(_svc),
):
    try:
        return svc.get_pull_request_diff(owner, repo, number)
    except Exception as exc:
        _handle_github_errors(exc)


@router.get(
    "/repositories/{owner}/{repo}/pulls/{number}/files",
    response_model=list[ChangedFileOut],
    summary="Get changed files in a pull request",
)
def get_pull_request_files(
    owner: str,
    repo: str,
    number: int,
    svc: GitHubService = Depends(_svc),
):
    try:
        files = svc.get_pull_request_files(owner, repo, number)
    except Exception as exc:
        _handle_github_errors(exc)
    return [ChangedFileOut(**vars(f)) for f in files]


# ─────────────────────────────────────────────────────────────────────────────
# Webhook
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/webhook",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Receive GitHub webhook events",
)
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
):
    """
    Receive and validate a GitHub webhook payload.

    Verifies the HMAC-SHA256 signature using the configured webhook secret
    (falls back to SECRET_KEY if a dedicated webhook secret is not set).

    Accepted events:
      - push     → triggers diff fetch + analysis pipeline (Stage 6)
      - pull_request (opened / synchronize) → same pipeline

    All processing runs in the background — webhook returns 202 immediately.
    """
    raw_body = await request.body()

    # ── Signature verification ────────────────────────────────────────────────
    webhook_secret = getattr(settings, "github_webhook_secret", None) or settings.secret_key
    if x_hub_signature_256:
        if not verify_webhook_signature(raw_body, x_hub_signature_256, webhook_secret):
            logger.warning("GitHub webhook signature verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature.",
            )
    else:
        # If no secret is configured in GitHub, skip verification in development
        if settings.is_production:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Webhook signature is required in production.",
            )
        logger.debug("Webhook received without signature (development mode)")

    # ── Dispatch ─────────────────────────────────────────────────────────────
    try:
        payload = await request.json() if not raw_body else __import__("json").loads(raw_body)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload.")

    event = x_github_event or "unknown"
    logger.info("GitHub webhook received: event=%s action=%s", event, payload.get("action"))

    background_tasks.add_task(_process_webhook_event, event, payload)

    return {"status": "accepted", "event": event}


def _process_webhook_event(event: str, payload: dict) -> None:
    """
    Background task to process a GitHub webhook event.

    Pull request analysis pipeline will be wired here in Stage 6.
    For now, logs the event so the webhook flow can be tested end-to-end.
    """
    action = payload.get("action", "")
    repo   = (payload.get("repository") or {}).get("full_name", "unknown")

    if event == "pull_request" and action in ("opened", "synchronize", "reopened"):
        pr_number = (payload.get("pull_request") or {}).get("number")
        logger.info("PR event queued for analysis: repo=%s pr=%s action=%s", repo, pr_number, action)
        # TODO Stage 6: call analysis pipeline here
        #   from app.services.analysis_service import run_analysis
        #   run_analysis(repo, pr_number)

    elif event == "push":
        ref    = payload.get("ref", "")
        branch = ref.replace("refs/heads/", "")
        sha    = payload.get("after", "")
        logger.info("Push event: repo=%s branch=%s sha=%s", repo, branch, sha)
        # TODO Stage 6: trigger branch diff analysis

    else:
        logger.debug("Unhandled webhook event: %s / %s", event, action)
