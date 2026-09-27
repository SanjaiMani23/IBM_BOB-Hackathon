"""
GitHub service — business logic layer.

Wraps the low-level GitHubClient and returns typed domain objects.
All write operations (PR comments) are explicit and require developer action.
No PR is modified automatically.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.integrations.github import GitHubClient, get_client

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Domain types
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Repository:
    full_name:      str
    description:    str | None
    default_branch: str
    html_url:       str
    private:        bool
    clone_url:      str


@dataclass
class Branch:
    name:      str
    sha:       str
    protected: bool


@dataclass
class Commit:
    sha:     str
    message: str
    author:  str
    date:    str
    url:     str


@dataclass
class PullRequest:
    number:     int
    title:      str
    state:      str       # open | closed | merged
    branch:     str
    base:       str
    author:     str
    created_at: str
    updated_at: str
    html_url:   str
    diff_url:   str
    commits:    int
    additions:  int
    deletions:  int
    changed_files: int


@dataclass
class ChangedFile:
    filename:  str
    status:    str      # added | modified | deleted | renamed
    additions: int
    deletions: int
    patch:     str | None   # raw unified diff for this file


# ─────────────────────────────────────────────────────────────────────────────
# Mappers (raw GitHub JSON → domain objects)
# ─────────────────────────────────────────────────────────────────────────────

def _to_repository(data: dict) -> Repository:
    return Repository(
        full_name=data["full_name"],
        description=data.get("description"),
        default_branch=data.get("default_branch", "main"),
        html_url=data["html_url"],
        private=data.get("private", False),
        clone_url=data.get("clone_url", ""),
    )


def _to_branch(data: dict) -> Branch:
    return Branch(
        name=data["name"],
        sha=data["commit"]["sha"],
        protected=data.get("protected", False),
    )


def _to_commit(data: dict) -> Commit:
    c = data.get("commit", data)
    author = c.get("author") or {}
    return Commit(
        sha=data.get("sha", ""),
        message=(c.get("message") or "")[:200],
        author=author.get("name") or author.get("login", "unknown"),
        date=author.get("date", ""),
        url=data.get("html_url", ""),
    )


def _to_pull_request(data: dict) -> PullRequest:
    head = data.get("head", {})
    base = data.get("base", {})
    user = data.get("user", {})
    return PullRequest(
        number=data["number"],
        title=data.get("title", ""),
        state=data.get("state", "open"),
        branch=head.get("ref", ""),
        base=base.get("ref", "main"),
        author=user.get("login", "unknown"),
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
        html_url=data.get("html_url", ""),
        diff_url=data.get("diff_url", ""),
        commits=data.get("commits", 0),
        additions=data.get("additions", 0),
        deletions=data.get("deletions", 0),
        changed_files=data.get("changed_files", 0),
    )


def _to_changed_file(data: dict) -> ChangedFile:
    return ChangedFile(
        filename=data["filename"],
        status=data.get("status", "modified"),
        additions=data.get("additions", 0),
        deletions=data.get("deletions", 0),
        patch=data.get("patch"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Service
# ─────────────────────────────────────────────────────────────────────────────

class GitHubService:
    """
    Business logic for GitHub interactions.

    All data-fetch methods return typed domain objects.
    Write operations (post_pr_comment) are no-ops until explicitly called.
    """

    def __init__(self, client: GitHubClient | None = None) -> None:
        self._client = client or get_client()

    # ── Repositories ─────────────────────────────────────────────────────────

    def list_repositories(self, per_page: int = 30) -> list[Repository]:
        """List repositories accessible with the configured token."""
        data = self._client.paginate("/user/repos", params={"per_page": per_page, "sort": "updated"})
        return [_to_repository(r) for r in data]

    def get_repository(self, owner: str, repo: str) -> Repository:
        data = self._client.get(f"/repos/{owner}/{repo}")
        return _to_repository(data)

    # ── Branches ─────────────────────────────────────────────────────────────

    def list_branches(self, owner: str, repo: str) -> list[Branch]:
        data = self._client.paginate(f"/repos/{owner}/{repo}/branches")
        return [_to_branch(b) for b in data]

    # ── Commits ──────────────────────────────────────────────────────────────

    def get_commit(self, owner: str, repo: str, sha: str) -> Commit:
        data = self._client.get(f"/repos/{owner}/{repo}/commits/{sha}")
        return _to_commit(data)

    def list_commits(
        self,
        owner: str,
        repo: str,
        branch: str = "main",
        per_page: int = 20,
    ) -> list[Commit]:
        data = self._client.paginate(
            f"/repos/{owner}/{repo}/commits",
            params={"sha": branch, "per_page": per_page},
            max_pages=1,
        )
        return [_to_commit(c) for c in data]

    # ── Pull Requests ─────────────────────────────────────────────────────────

    def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        per_page: int = 30,
    ) -> list[PullRequest]:
        data = self._client.paginate(
            f"/repos/{owner}/{repo}/pulls",
            params={"state": state, "per_page": per_page},
        )
        return [_to_pull_request(pr) for pr in data]

    def get_pull_request(self, owner: str, repo: str, number: int) -> PullRequest:
        data = self._client.get(f"/repos/{owner}/{repo}/pulls/{number}")
        return _to_pull_request(data)

    # ── Diff / changed files ──────────────────────────────────────────────────

    def get_pull_request_diff(self, owner: str, repo: str, number: int) -> str:
        """
        Return the raw unified diff for a pull request.
        Uses the application/vnd.github.diff media type via a direct Accept override.
        """
        url = f"/repos/{owner}/{repo}/pulls/{number}"
        # Temporarily override Accept to get raw diff
        with __import__("httpx").Client(timeout=20) as client:
            from app.integrations.github import _BASE_URL
            resp = client.get(
                f"{_BASE_URL}{url}",
                headers={
                    **self._client._headers(),
                    "Accept": "application/vnd.github.diff",
                },
            )
            resp.raise_for_status()
            return resp.text

    def get_pull_request_files(self, owner: str, repo: str, number: int) -> list[ChangedFile]:
        """Return list of changed files in a pull request (with patches)."""
        data = self._client.paginate(f"/repos/{owner}/{repo}/pulls/{number}/files")
        return [_to_changed_file(f) for f in data]

    def get_compare_diff(
        self,
        owner: str,
        repo: str,
        base: str,
        head: str,
    ) -> str:
        """
        Return the raw unified diff between *base* and *head* refs.
        Used when analysing a branch without an open PR.
        """
        from app.integrations.github import _BASE_URL
        with __import__("httpx").Client(timeout=20) as client:
            resp = client.get(
                f"{_BASE_URL}/repos/{owner}/{repo}/compare/{base}...{head}",
                headers={
                    **self._client._headers(),
                    "Accept": "application/vnd.github.diff",
                },
            )
            resp.raise_for_status()
            return resp.text

    # ── Write operations (explicit developer action required) ─────────────────

    def post_pr_comment(
        self,
        owner: str,
        repo: str,
        number: int,
        body: str,
    ) -> dict:
        """
        Post a comment on a pull request.

        This is the ONLY write operation in this service.
        It must only be called after explicit developer approval.
        """
        logger.info("Posting PR comment to %s/%s#%d (approved by developer)", owner, repo, number)
        return self._client.post(
            f"/repos/{owner}/{repo}/issues/{number}/comments",
            json={"body": body},
        )


# ─────────────────────────────────────────────────────────────────────────────
# Module-level singleton factory
# ─────────────────────────────────────────────────────────────────────────────

def get_github_service() -> GitHubService:
    return GitHubService()
