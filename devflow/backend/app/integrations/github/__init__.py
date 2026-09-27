"""
Low-level GitHub REST API client.

Handles:
  - Token authentication (never exposed to frontend)
  - Automatic retries on 5xx / network errors
  - Rate-limit detection and back-off (X-RateLimit-Remaining)
  - Pagination via Link header
  - Structured error types
  - Request timeout

All methods return parsed JSON dicts / lists.
Callers (github_service.py) are responsible for mapping to domain objects.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

_BASE_URL         = "https://api.github.com"
_TIMEOUT_SECONDS  = 20
_MAX_RETRIES      = 3
_RETRY_BACKOFF    = 1.5   # seconds between retries (multiplied each time)
_RATE_LIMIT_PAUSE = 60    # seconds to pause when rate limit is hit


# ─────────────────────────────────────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────────────────────────────────────

class GitHubError(Exception):
    """Base class for GitHub client errors."""

class GitHubAuthError(GitHubError):
    """401 / 403 from GitHub."""

class GitHubNotFoundError(GitHubError):
    """404 from GitHub."""

class GitHubRateLimitError(GitHubError):
    """429 or X-RateLimit-Remaining == 0."""

class GitHubServerError(GitHubError):
    """5xx from GitHub."""


# ─────────────────────────────────────────────────────────────────────────────
# Client
# ─────────────────────────────────────────────────────────────────────────────

class GitHubClient:
    """
    Thin wrapper around the GitHub REST v3 API.

    Usage::

        client = GitHubClient()
        repos  = client.get("/user/repos")
    """

    def __init__(self, token: str | None = None) -> None:
        self._token = token or settings.github_token
        if not self._token:
            logger.warning("GitHubClient initialised without a token — only public endpoints will work.")

    # ── Low-level request ────────────────────────────────────────────────────

    def _headers(self) -> dict[str, str]:
        h = {
            "Accept":     "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "DevFlow-CodeLens/0.1",
        }
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: Any = None,
        raw_response: bool = False,
    ) -> Any:
        url = path if path.startswith("http") else f"{_BASE_URL}{path}"
        delay = _RETRY_BACKOFF

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                with httpx.Client(timeout=_TIMEOUT_SECONDS) as client:
                    response = client.request(
                        method,
                        url,
                        headers=self._headers(),
                        params=params,
                        json=json,
                    )
            except httpx.TimeoutException as exc:
                if attempt == _MAX_RETRIES:
                    raise GitHubError(f"Request timed out after {_TIMEOUT_SECONDS}s: {url}") from exc
                logger.warning("GitHub request timed out (attempt %d/%d), retrying…", attempt, _MAX_RETRIES)
                time.sleep(delay)
                delay *= _RETRY_BACKOFF
                continue
            except httpx.RequestError as exc:
                if attempt == _MAX_RETRIES:
                    raise GitHubError(f"Network error: {exc}") from exc
                time.sleep(delay)
                delay *= _RETRY_BACKOFF
                continue

            # Rate limit
            remaining = response.headers.get("X-RateLimit-Remaining")
            if remaining == "0":
                reset_at = int(response.headers.get("X-RateLimit-Reset", time.time() + _RATE_LIMIT_PAUSE))
                wait = max(reset_at - int(time.time()), 1)
                logger.warning("GitHub rate limit hit — waiting %ds", wait)
                time.sleep(wait)
                continue

            if response.status_code == 401:
                raise GitHubAuthError("GitHub authentication failed — check GITHUB_TOKEN.")
            if response.status_code == 403:
                raise GitHubAuthError(f"GitHub returned 403 Forbidden for {url}.")
            if response.status_code == 404:
                raise GitHubNotFoundError(f"GitHub resource not found: {url}")
            if response.status_code == 429:
                if attempt == _MAX_RETRIES:
                    raise GitHubRateLimitError("GitHub rate limit exceeded.")
                time.sleep(delay)
                delay *= _RETRY_BACKOFF
                continue
            if response.status_code >= 500:
                if attempt == _MAX_RETRIES:
                    raise GitHubServerError(f"GitHub server error {response.status_code} for {url}")
                time.sleep(delay)
                delay *= _RETRY_BACKOFF
                continue

            response.raise_for_status()

            if raw_response:
                return response.text

            if not response.content:
                return {}
            return response.json()

        raise GitHubError(f"Exhausted {_MAX_RETRIES} retries for {url}")

    def get(self, path: str, *, params: dict | None = None, raw: bool = False) -> Any:
        return self._request("GET", path, params=params, raw_response=raw)

    def post(self, path: str, *, json: Any = None) -> Any:
        return self._request("POST", path, json=json)

    # ── Pagination helper ─────────────────────────────────────────────────────

    def paginate(self, path: str, *, params: dict | None = None, max_pages: int = 10) -> list[Any]:
        """
        Follow GitHub pagination via Link headers and collect all pages.
        Stops after *max_pages* to avoid unbounded requests.
        """
        results: list[Any] = []
        p = dict(params or {})
        p.setdefault("per_page", 100)
        url: str | None = path if path.startswith("http") else f"{_BASE_URL}{path}"

        for _ in range(max_pages):
            if url is None:
                break
            with httpx.Client(timeout=_TIMEOUT_SECONDS) as client:
                resp = client.get(url, headers=self._headers(), params=p if url == path else None)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                results.extend(data)
            else:
                results.append(data)

            # Parse Link header for next page
            link_header = resp.headers.get("Link", "")
            url = _parse_next_link(link_header)
            p = {}  # params already encoded in the next URL

        return results


# ─────────────────────────────────────────────────────────────────────────────
# Webhook signature verification
# ─────────────────────────────────────────────────────────────────────────────

def verify_webhook_signature(
    payload: bytes,
    signature_header: str,
    secret: str,
) -> bool:
    """
    Verify a GitHub webhook HMAC-SHA256 signature.

    Args:
        payload:          Raw request body bytes.
        signature_header: Value of the X-Hub-Signature-256 header.
        secret:           The webhook secret configured in GitHub.

    Returns:
        True if the signature is valid, False otherwise.
    """
    if not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    received = signature_header[len("sha256="):]
    return hmac.compare_digest(expected, received)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_next_link(link_header: str) -> str | None:
    """Extract the 'next' URL from a GitHub Link header."""
    for part in link_header.split(","):
        parts = [p.strip() for p in part.split(";")]
        if len(parts) == 2 and parts[1] == 'rel="next"':
            return parts[0].strip("<>")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Module-level singleton
# ─────────────────────────────────────────────────────────────────────────────

def get_client() -> GitHubClient:
    """Return a GitHubClient configured from application settings."""
    return GitHubClient(token=settings.github_token)
