"""
Low-level Jira REST API client.

Handles:
  - Basic auth (email + API token — never exposed to frontend)
  - Request wrapper with timeout and retries
  - Rate-limit handling
  - Structured error types for all failure modes
  - Project lookup, issue creation, retrieval, and update

Authentication uses Atlassian API token (not account password).
All credentials are sourced from environment variables only.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

_API_VERSION     = "rest/api/3"
_TIMEOUT_SECONDS = 20
_MAX_RETRIES     = 3
_RETRY_BACKOFF   = 1.5


# ─────────────────────────────────────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────────────────────────────────────

class JiraError(Exception):
    """Base class for all Jira client errors."""

class JiraAuthError(JiraError):
    """401 / 403 — invalid credentials or insufficient permissions."""

class JiraNotFoundError(JiraError):
    """404 — project or issue does not exist."""

class JiraPermissionError(JiraError):
    """403 — authenticated but not authorised for this action."""

class JiraValidationError(JiraError):
    """400 — invalid project key, issue type, or field values."""

class JiraRateLimitError(JiraError):
    """429 — too many requests."""

class JiraServerError(JiraError):
    """5xx — Jira server error."""


# ─────────────────────────────────────────────────────────────────────────────
# Client
# ─────────────────────────────────────────────────────────────────────────────

class JiraClient:
    """
    Thin wrapper around the Jira REST API v3.

    Uses HTTP Basic auth with Atlassian API token.
    Token is read from ``settings.jira_token`` — never hardcoded.
    """

    def __init__(
        self,
        base_url: str | None = None,
        email: str | None = None,
        token: str | None = None,
    ) -> None:
        self._base_url = (base_url or settings.jira_url).rstrip("/")
        self._email    = email or settings.jira_email
        self._token    = token or settings.jira_token

        if not all([self._base_url, self._email, self._token]):
            logger.warning(
                "JiraClient: one or more credentials are missing "
                "(JIRA_URL, JIRA_EMAIL, JIRA_TOKEN). Jira calls will fail."
            )

    # ── Auth ──────────────────────────────────────────────────────────────────

    def _auth(self) -> tuple[str, str]:
        return (self._email, self._token)

    def _url(self, path: str) -> str:
        return f"{self._base_url}/{_API_VERSION}/{path.lstrip('/')}"

    # ── Request wrapper ───────────────────────────────────────────────────────

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: Any = None,
    ) -> Any:
        url   = self._url(path)
        delay = _RETRY_BACKOFF

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                with httpx.Client(timeout=_TIMEOUT_SECONDS) as client:
                    resp = client.request(
                        method,
                        url,
                        auth=self._auth(),
                        headers={"Accept": "application/json", "Content-Type": "application/json"},
                        params=params,
                        json=json,
                    )
            except httpx.TimeoutException as exc:
                if attempt == _MAX_RETRIES:
                    raise JiraError(f"Jira request timed out: {url}") from exc
                logger.warning("Jira timeout (attempt %d/%d), retrying…", attempt, _MAX_RETRIES)
                time.sleep(delay); delay *= _RETRY_BACKOFF
                continue
            except httpx.RequestError as exc:
                if attempt == _MAX_RETRIES:
                    raise JiraError(f"Jira network error: {exc}") from exc
                time.sleep(delay); delay *= _RETRY_BACKOFF
                continue

            # ── Status handling ───────────────────────────────────────────────
            if resp.status_code == 400:
                body = _safe_json(resp)
                raise JiraValidationError(
                    f"Jira validation error: {body.get('errorMessages', body)}"
                )
            if resp.status_code == 401:
                raise JiraAuthError(
                    "Jira authentication failed — check JIRA_EMAIL and JIRA_TOKEN."
                )
            if resp.status_code == 403:
                raise JiraPermissionError(
                    f"Jira permission denied for {method} {url}."
                )
            if resp.status_code == 404:
                raise JiraNotFoundError(f"Jira resource not found: {url}")
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", delay))
                logger.warning("Jira rate limit — waiting %ds", retry_after)
                time.sleep(retry_after)
                continue
            if resp.status_code >= 500:
                if attempt == _MAX_RETRIES:
                    raise JiraServerError(f"Jira server error {resp.status_code} for {url}")
                time.sleep(delay); delay *= _RETRY_BACKOFF
                continue

            resp.raise_for_status()
            return _safe_json(resp)

        raise JiraError(f"Exhausted {_MAX_RETRIES} retries for {url}")

    def get(self, path: str, *, params: dict | None = None) -> Any:
        return self._request("GET", path, params=params)

    def post(self, path: str, *, json: Any = None) -> Any:
        return self._request("POST", path, json=json)

    def put(self, path: str, *, json: Any = None) -> Any:
        return self._request("PUT", path, json=json)

    # ── Project operations ────────────────────────────────────────────────────

    def list_projects(self) -> list[dict]:
        """Return all projects accessible with the configured credentials."""
        result = self.get("project/search", params={"maxResults": 50, "orderBy": "name"})
        return result.get("values", [])

    def get_project(self, project_key: str) -> dict:
        """Return project metadata for *project_key* (e.g. ``"PROJ"``)."""
        return self.get(f"project/{project_key}")

    # ── Issue operations ──────────────────────────────────────────────────────

    def create_issue(self, fields: dict) -> dict:
        """
        Create a new Jira issue.

        Args:
            fields: Jira fields dict as per the REST API ``fields`` key.

        Returns:
            Dict containing ``id``, ``key``, and ``self`` (URL) of the new issue.
        """
        return self.post("issue", json={"fields": fields})

    def get_issue(self, issue_key: str) -> dict:
        """Return full issue data for *issue_key* (e.g. ``"PROJ-42"``)."""
        return self.get(f"issue/{issue_key}")

    def update_issue(self, issue_key: str, fields: dict) -> None:
        """Update fields on an existing issue. Returns None on success."""
        self.put(f"issue/{issue_key}", json={"fields": fields})

    def add_comment(self, issue_key: str, body_text: str) -> dict:
        """Add a plain-text comment to an issue."""
        return self.post(
            f"issue/{issue_key}/comment",
            json={
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": body_text}],
                        }
                    ],
                }
            },
        )

    def get_issue_types(self, project_key: str) -> list[dict]:
        """Return available issue types for *project_key*."""
        result = self.get(f"project/{project_key}/statuses")
        return result if isinstance(result, list) else []


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _safe_json(resp: httpx.Response) -> Any:
    """Return parsed JSON or empty dict if the body is empty."""
    if not resp.content:
        return {}
    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text}


# ─────────────────────────────────────────────────────────────────────────────
# Module-level factory
# ─────────────────────────────────────────────────────────────────────────────

def get_client() -> JiraClient:
    """Return a JiraClient configured from application settings."""
    return JiraClient()
