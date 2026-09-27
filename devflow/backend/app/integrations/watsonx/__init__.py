"""
Low-level IBM watsonx.ai client.

Responsibilities:
  - IAM token authentication (refreshed automatically before expiry)
  - Model initialisation via ibm-watsonx-ai SDK (with httpx fallback)
  - Text generation requests with configurable parameters
  - Structured response parsing
  - Timeout, rate-limit, and error handling
  - Logging of metadata — never secrets

All provider-specific logic stays in this module.
ai_service.py calls this abstraction and must not make direct HTTP calls.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

_IAM_TOKEN_URL    = "https://iam.cloud.ibm.com/identity/token"
_GENERATION_PATH  = "/ml/v1/text/generation"
_API_VERSION      = "2023-05-29"
_TIMEOUT_SECONDS  = 60
_MAX_RETRIES      = 3
_RETRY_BACKOFF    = 2.0
# Refresh IAM token 5 minutes before expiry
_TOKEN_REFRESH_BUFFER = 300


# ─────────────────────────────────────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────────────────────────────────────

class WatsonxError(Exception):
    """Base error for all watsonx client failures."""

class WatsonxAuthError(WatsonxError):
    """IAM authentication failure."""

class WatsonxRateLimitError(WatsonxError):
    """429 — too many requests."""

class WatsonxTimeoutError(WatsonxError):
    """Request timed out."""

class WatsonxResponseError(WatsonxError):
    """Malformed or unexpected response from the API."""


# ─────────────────────────────────────────────────────────────────────────────
# Response type
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class GenerationResult:
    text:             str
    model_id:         str
    input_token_count:  int = 0
    generated_token_count: int = 0
    stop_reason:      str = ""
    raw:              dict = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# IAM token cache
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class _IamToken:
    access_token: str
    expires_at:   float   # unix timestamp


_token_cache: _IamToken | None = None


def _get_iam_token() -> str:
    """
    Fetch (or return cached) an IBM Cloud IAM access token.
    Token is refreshed automatically 5 minutes before expiry.
    """
    global _token_cache

    now = time.time()
    if _token_cache and now < (_token_cache.expires_at - _TOKEN_REFRESH_BUFFER):
        return _token_cache.access_token

    import httpx

    if not settings.watsonx_api_key:
        raise WatsonxAuthError("WATSONX_API_KEY is not configured.")

    logger.debug("Refreshing IBM Cloud IAM token")
    try:
        resp = httpx.post(
            _IAM_TOKEN_URL,
            data={
                "grant_type":    "urn:ibm:params:oauth:grant-type:apikey",
                "apikey":        settings.watsonx_api_key,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise WatsonxAuthError(f"IAM token request failed: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise WatsonxAuthError(f"IAM token request network error: {exc}") from exc

    data = resp.json()
    token       = data["access_token"]
    expires_in  = int(data.get("expires_in", 3600))

    _token_cache = _IamToken(
        access_token=token,
        expires_at=now + expires_in,
    )
    logger.debug("IAM token refreshed — expires in %ds", expires_in)
    return token


# ─────────────────────────────────────────────────────────────────────────────
# SDK-based client (preferred when ibm-watsonx-ai is installed)
# ─────────────────────────────────────────────────────────────────────────────

def _generate_via_sdk(
    prompt: str,
    model_id: str,
    params: dict,
) -> GenerationResult:
    """Use ibm-watsonx-ai SDK if available."""
    try:
        from ibm_watsonx_ai import APIClient, Credentials              # type: ignore
        from ibm_watsonx_ai.foundation_models import ModelInference    # type: ignore
        from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as gp  # type: ignore
    except ImportError as exc:
        raise ImportError("ibm-watsonx-ai not installed") from exc

    creds = Credentials(
        url=settings.watsonx_url,
        api_key=settings.watsonx_api_key,
    )
    model = ModelInference(
        model_id=model_id,
        credentials=creds,
        project_id=settings.watsonx_project_id,
        params={
            gp.MAX_NEW_TOKENS: params.get("max_new_tokens", 1024),
            gp.TEMPERATURE:    params.get("temperature", 0.2),
            gp.TOP_P:          params.get("top_p", 0.9),
            gp.STOP_SEQUENCES: params.get("stop_sequences", []),
        },
    )

    response = model.generate_text(prompt=prompt, guardrails=False)

    # SDK may return str or dict depending on version
    if isinstance(response, str):
        return GenerationResult(text=response, model_id=model_id)

    results = response.get("results", [{}])
    first   = results[0] if results else {}
    return GenerationResult(
        text=first.get("generated_text", ""),
        model_id=model_id,
        input_token_count=response.get("usage", {}).get("input_tokens", 0),
        generated_token_count=response.get("usage", {}).get("generated_tokens", 0),
        stop_reason=first.get("stop_reason", ""),
        raw=response,
    )


# ─────────────────────────────────────────────────────────────────────────────
# HTTP fallback (plain httpx — no SDK dependency)
# ─────────────────────────────────────────────────────────────────────────────

def _generate_via_http(
    prompt: str,
    model_id: str,
    params: dict,
) -> GenerationResult:
    """Direct HTTP call to the watsonx.ai inference endpoint."""
    import httpx

    token = _get_iam_token()
    url   = (
        f"{settings.watsonx_url.rstrip('/')}{_GENERATION_PATH}"
        f"?version={_API_VERSION}"
    )
    body  = {
        "model_id":   model_id,
        "project_id": settings.watsonx_project_id,
        "input":      prompt,
        "parameters": {
            "max_new_tokens": params.get("max_new_tokens", 1024),
            "temperature":    params.get("temperature", 0.2),
            "top_p":          params.get("top_p", 0.9),
            "stop_sequences": params.get("stop_sequences", []),
        },
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }

    delay = _RETRY_BACKOFF
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            resp = httpx.post(url, json=body, headers=headers, timeout=_TIMEOUT_SECONDS)
        except httpx.TimeoutException as exc:
            if attempt == _MAX_RETRIES:
                raise WatsonxTimeoutError(f"watsonx.ai request timed out after {_TIMEOUT_SECONDS}s") from exc
            logger.warning("watsonx timeout (attempt %d/%d), retrying…", attempt, _MAX_RETRIES)
            time.sleep(delay)
            delay *= _RETRY_BACKOFF
            continue
        except httpx.RequestError as exc:
            if attempt == _MAX_RETRIES:
                raise WatsonxError(f"watsonx network error: {exc}") from exc
            time.sleep(delay)
            delay *= _RETRY_BACKOFF
            continue

        if resp.status_code == 401:
            # Token may have expired mid-flight — flush cache and retry once
            global _token_cache
            _token_cache = None
            if attempt < _MAX_RETRIES:
                token = _get_iam_token()
                headers["Authorization"] = f"Bearer {token}"
                continue
            raise WatsonxAuthError("watsonx.ai authentication failed after token refresh.")

        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", delay))
            logger.warning("watsonx rate limit — waiting %ds", retry_after)
            time.sleep(retry_after)
            continue

        if resp.status_code >= 500:
            if attempt == _MAX_RETRIES:
                raise WatsonxError(f"watsonx server error {resp.status_code}")
            time.sleep(delay)
            delay *= _RETRY_BACKOFF
            continue

        try:
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            raise WatsonxResponseError(f"Failed to parse watsonx response: {exc}") from exc

        results = data.get("results", [{}])
        first   = results[0] if results else {}
        return GenerationResult(
            text=first.get("generated_text", ""),
            model_id=model_id,
            input_token_count=data.get("usage", {}).get("input_tokens", 0),
            generated_token_count=data.get("usage", {}).get("generated_tokens", 0),
            stop_reason=first.get("stop_reason", ""),
            raw=data,
        )

    raise WatsonxError(f"Exhausted {_MAX_RETRIES} retries calling watsonx.ai")


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate(
    prompt: str,
    *,
    model_id: str | None = None,
    max_new_tokens: int = 1024,
    temperature: float = 0.2,
    top_p: float = 0.9,
    stop_sequences: list[str] | None = None,
) -> GenerationResult:
    """
    Send a text-generation request to IBM watsonx.ai.

    Tries the ibm-watsonx-ai SDK first; falls back to plain HTTP if the
    SDK is not installed. Either way the same :class:`GenerationResult`
    is returned.

    Args:
        prompt:         Full prompt string (system + user combined).
        model_id:       Override the default model from settings.
        max_new_tokens: Maximum tokens to generate.
        temperature:    Sampling temperature (lower = more deterministic).
        top_p:          Nucleus sampling probability.
        stop_sequences: List of sequences that terminate generation.

    Returns:
        :class:`GenerationResult` with the generated text and metadata.

    Raises:
        WatsonxAuthError:     Invalid or missing API key / project ID.
        WatsonxTimeoutError:  Request exceeded timeout.
        WatsonxRateLimitError: Rate limit hit after retries.
        WatsonxResponseError: Malformed API response.
        WatsonxError:         Any other failure.
    """
    if not settings.watsonx_project_id:
        raise WatsonxAuthError("WATSONX_PROJECT_ID is not configured.")

    effective_model = model_id or settings.watsonx_model_id
    params = {
        "max_new_tokens": max_new_tokens,
        "temperature":    temperature,
        "top_p":          top_p,
        "stop_sequences": stop_sequences or [],
    }

    logger.info(
        "watsonx generation: model=%s max_tokens=%d temp=%.2f",
        effective_model, max_new_tokens, temperature,
    )

    try:
        result = _generate_via_sdk(prompt, effective_model, params)
        logger.debug(
            "watsonx SDK response: input_tokens=%d generated_tokens=%d stop=%s",
            result.input_token_count, result.generated_token_count, result.stop_reason,
        )
        return result
    except ImportError:
        logger.debug("ibm-watsonx-ai SDK not available — using HTTP fallback")

    result = _generate_via_http(prompt, effective_model, params)
    logger.debug(
        "watsonx HTTP response: input_tokens=%d generated_tokens=%d stop=%s",
        result.input_token_count, result.generated_token_count, result.stop_reason,
    )
    return result
