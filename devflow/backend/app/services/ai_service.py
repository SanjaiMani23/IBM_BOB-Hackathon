"""
Central AI service — the single point of entry for all watsonx.ai calls.

Responsibilities:
  - Load and cache prompt templates from disk
  - Build complete prompts (system + context + user content)
  - Call the watsonx integration layer
  - Parse and validate structured JSON responses
  - Handle malformed responses gracefully
  - Log metadata — never secrets or full prompts in production

All AI-consuming services (debug, optimization, test, summary, jira)
must call this service. Direct use of the watsonx integration is prohibited.
"""

from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.integrations.watsonx import (
    GenerationResult,
    WatsonxError,
    generate,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Prompt template loader
# ─────────────────────────────────────────────────────────────────────────────

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


@lru_cache(maxsize=32)
def load_prompt_template(name: str) -> str:
    """
    Load a prompt template by filename (without .txt extension).
    Results are cached for the process lifetime.

    Args:
        name: Template name, e.g. ``"debugging"``.

    Returns:
        Template string with ``{placeholder}`` slots.

    Raises:
        FileNotFoundError: If the template file does not exist.
    """
    path = _PROMPTS_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    text = path.read_text(encoding="utf-8").strip()
    logger.debug("Loaded prompt template: %s (%d chars)", name, len(text))
    return text


def build_prompt(template_name: str, **kwargs: Any) -> str:
    """
    Load *template_name* and render it with keyword substitutions.

    Uses str.format_map so that unknown placeholders raise KeyError early.
    """
    template = load_prompt_template(template_name)
    try:
        return template.format_map(kwargs)
    except KeyError as exc:
        raise ValueError(f"Prompt template '{template_name}' is missing variable: {exc}") from exc


# ─────────────────────────────────────────────────────────────────────────────
# Response parsing
# ─────────────────────────────────────────────────────────────────────────────

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", re.DOTALL)


def _extract_json(text: str) -> Any:
    """
    Extract the first JSON object or array from *text*.

    Tries three strategies in order:
    1. Direct parse (model returned clean JSON).
    2. Extract from a ```json ... ``` code fence.
    3. Find the first ``{`` and last ``}`` and parse the substring.

    Raises:
        ValueError: If no valid JSON is found.
    """
    # 1. Direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # 2. Code fence
    m = _JSON_BLOCK_RE.search(text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # 3. Brace extraction
    start = text.find("{")
    end   = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start: end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"No valid JSON found in model response (first 200 chars): {text[:200]!r}")


# ─────────────────────────────────────────────────────────────────────────────
# Core generation wrapper
# ─────────────────────────────────────────────────────────────────────────────

def _call_ai(
    prompt: str,
    *,
    max_new_tokens: int = 1024,
    temperature: float = 0.2,
    model_id: str | None = None,
) -> GenerationResult:
    """
    Thin wrapper around the watsonx integration ``generate()`` call.
    Centralises logging of token counts and errors.
    """
    try:
        result = generate(
            prompt,
            model_id=model_id,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
        )
        logger.info(
            "AI call completed: input_tokens=%d generated_tokens=%d",
            result.input_token_count,
            result.generated_token_count,
        )
        return result
    except WatsonxError as exc:
        logger.error("watsonx call failed: %s", exc)
        raise


# ─────────────────────────────────────────────────────────────────────────────
# Public API — one method per use-case
# ─────────────────────────────────────────────────────────────────────────────

def analyze_for_debugging(
    code: str,
    error_message: str | None,
    language: str,
    static_findings: list[dict],
) -> dict:
    """
    Ask watsonx.ai to identify the root cause of a bug.

    Args:
        code:             The code snippet under investigation.
        error_message:    Optional runtime error / stack trace.
        language:         Programming language of *code*.
        static_findings:  Findings from the static analyzers for context.

    Returns:
        Parsed JSON dict with keys: root_cause, explanation, evidence,
        suggested_fix, confidence, severity.
    """
    findings_text = json.dumps(static_findings, indent=2) if static_findings else "None"
    error_text    = error_message or "No error message provided."

    prompt = build_prompt(
        "debugging",
        language=language,
        code=code,
        error_message=error_text,
        static_findings=findings_text,
    )
    result = _call_ai(prompt, max_new_tokens=1200, temperature=0.1)
    return _extract_json(result.text)


def analyze_for_optimization(
    code: str,
    language: str,
    context: str | None = None,
) -> dict:
    """
    Ask watsonx.ai for optimization suggestions.

    Returns:
        Parsed JSON dict with a ``suggestions`` list.
    """
    prompt = build_prompt(
        "optimization",
        language=language,
        code=code,
        context=context or "No additional context provided.",
    )
    result = _call_ai(prompt, max_new_tokens=1200, temperature=0.2)
    return _extract_json(result.text)


def generate_tests(
    code: str,
    language: str,
    framework: str | None = None,
) -> dict:
    """
    Ask watsonx.ai to generate unit test scaffolding.

    Returns:
        Parsed JSON dict with keys: test_code, framework_used, test_cases.
    """
    prompt = build_prompt(
        "testing",
        language=language,
        code=code,
        framework=framework or "the idiomatic test framework for " + language,
    )
    result = _call_ai(prompt, max_new_tokens=1500, temperature=0.2)
    return _extract_json(result.text)


def generate_pr_description(
    diff: str,
    repository: str,
    branch: str,
) -> dict:
    """
    Ask watsonx.ai to draft a pull request description.

    Returns:
        Parsed JSON dict with keys: title, summary, changes,
        technical_impact, testing, risks, dependencies, deployment_notes,
        full_description.
    """
    # Truncate very large diffs to avoid token overflow
    truncated = diff[:8000] + "\n...[diff truncated]" if len(diff) > 8000 else diff

    prompt = build_prompt(
        "pr_description",
        repository=repository,
        branch=branch,
        diff=truncated,
    )
    result = _call_ai(prompt, max_new_tokens=1000, temperature=0.3)
    return _extract_json(result.text)


def generate_jira_ticket(
    finding: dict,
    repository: str,
) -> dict:
    """
    Ask watsonx.ai to draft a Jira ticket from a code finding.

    Returns:
        Parsed JSON dict with keys: summary, description, priority,
        component, labels, acceptance_criteria, technical_notes.
    """
    prompt = build_prompt(
        "jira",
        repository=repository,
        finding_title=finding.get("title", ""),
        finding_severity=finding.get("severity", ""),
        finding_type=finding.get("finding_type", ""),
        finding_explanation=finding.get("explanation", ""),
        finding_recommendation=finding.get("recommendation", ""),
        file_path=finding.get("file_path", ""),
        line_number=str(finding.get("line_number", "")),
    )
    result = _call_ai(prompt, max_new_tokens=800, temperature=0.2)
    return _extract_json(result.text)


def generate_return_summary(
    commits: list[dict],
    pull_requests: list[dict],
    repository: str,
    period: str,
) -> dict:
    """
    Ask watsonx.ai to produce a return-to-work summary.

    Returns:
        Parsed JSON dict with keys: period, highlights, prs_merged,
        issues_closed, recommended_actions, full_summary.
    """
    commits_text = json.dumps(commits[:20], indent=2)   # cap to avoid token overflow
    prs_text     = json.dumps(pull_requests[:10], indent=2)

    prompt = build_prompt(
        "return_summary",
        repository=repository,
        period=period,
        commits=commits_text,
        pull_requests=prs_text,
    )
    result = _call_ai(prompt, max_new_tokens=1000, temperature=0.3)
    return _extract_json(result.text)
