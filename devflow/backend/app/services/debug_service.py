"""
Debugging service.

Workflow:
  Code / Diff
    ↓ reconstruct source
  Static analysis (syntax + security + complexity + quality)
    ↓ structured findings
  Error information (optional)
    ↓ combined context
  watsonx.ai via ai_service (debugging prompt)
    ↓
  Structured root cause + suggested fix

The AI layer is consulted AFTER static analysis — it interprets and explains
findings; it does not replace the deterministic layer.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.services import ai_service
from app.analyzers.syntax_analyzer import analyze_syntax
from app.analyzers.security_analyzer import analyze_security
from app.analyzers.complexity_analyzer import analyze_complexity
from app.analyzers.code_quality import analyze_quality

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Output type
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DebugResult:
    root_cause:    str
    explanation:   str
    evidence:      list[str]
    suggested_fix: str
    confidence:    str     # "confirmed" | "likely" | "possible"
    severity:      str     # "critical" | "high" | "medium" | "low"
    static_finding_count: int = 0

    def to_dict(self) -> dict:
        return {
            "root_cause":           self.root_cause,
            "explanation":          self.explanation,
            "evidence":             self.evidence,
            "suggested_fix":        self.suggested_fix,
            "confidence":           self.confidence,
            "severity":             self.severity,
            "static_finding_count": self.static_finding_count,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Service
# ─────────────────────────────────────────────────────────────────────────────

def debug_code(
    code: str,
    language: str,
    file_path: str = "<unknown>",
    error_message: str | None = None,
) -> DebugResult:
    """
    Run static analysis on *code*, then ask watsonx.ai to identify the
    root cause and suggest a minimal fix.

    Args:
        code:          Source code to debug (reconstructed from diff or raw).
        language:      Language name normalised to lowercase.
        file_path:     Path for reporting context.
        error_message: Optional runtime error / stack trace.

    Returns:
        :class:`DebugResult` with root cause, explanation, and fix suggestion.
    """
    # ── Stage 1: deterministic static analysis ────────────────────────────────
    static_findings: list[dict] = []

    for finding in analyze_syntax(code, language, file_path):
        static_findings.append({
            "source": "syntax",
            "severity": finding.severity,
            "line": finding.line,
            "message": finding.message,
        })

    for finding in analyze_security(code, language, file_path):
        static_findings.append({
            "source": "security",
            "rule": finding.rule,
            "severity": finding.severity,
            "line": finding.line,
            "message": finding.message,
            "confidence": finding.confidence,
        })

    for finding in analyze_complexity(code, language, file_path):
        static_findings.append({
            "source": "complexity",
            "metric": finding.metric,
            "severity": finding.severity,
            "line": finding.line,
            "message": finding.message,
        })

    for finding in analyze_quality(code, language, file_path):
        static_findings.append({
            "source": "quality",
            "rule": finding.rule,
            "severity": finding.severity,
            "line": finding.line,
            "message": finding.message,
        })

    logger.info(
        "debug_code: %d static findings for %s (%s)",
        len(static_findings), file_path, language,
    )

    # ── Stage 2: AI interpretation ────────────────────────────────────────────
    try:
        ai_response = ai_service.analyze_for_debugging(
            code=code,
            error_message=error_message,
            language=language,
            static_findings=static_findings,
        )
    except Exception as exc:
        logger.error("AI debugging call failed: %s", exc)
        # Graceful degradation — return a result derived from static findings only
        return _fallback_debug_result(static_findings, exc)

    return DebugResult(
        root_cause=ai_response.get("root_cause", "Root cause could not be determined."),
        explanation=ai_response.get("explanation", ""),
        evidence=ai_response.get("evidence", []),
        suggested_fix=ai_response.get("suggested_fix", ""),
        confidence=ai_response.get("confidence", "possible"),
        severity=ai_response.get("severity", "medium"),
        static_finding_count=len(static_findings),
    )


def debug_from_diff(
    changed_files: list,
    error_message: str | None = None,
) -> list[DebugResult]:
    """
    Run debugging analysis across all files in a parsed diff.

    Args:
        changed_files: list[ChangedFile] from diff_service.
        error_message: Optional error message to provide context to the AI.

    Returns:
        List of :class:`DebugResult`, one per file that has findings.
    """
    from app.services.diff_service import reconstruct_new_source

    results: list[DebugResult] = []
    for cf in changed_files:
        source = reconstruct_new_source(cf)
        if not source.strip():
            continue
        result = debug_code(
            code=source,
            language=cf.language,
            file_path=cf.path,
            error_message=error_message,
        )
        # Only include files where something was found
        if result.static_finding_count > 0 or result.confidence != "possible":
            results.append(result)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Graceful degradation
# ─────────────────────────────────────────────────────────────────────────────

def _fallback_debug_result(static_findings: list[dict], exc: Exception) -> DebugResult:
    """
    Build a degraded DebugResult from static findings when the AI call fails.
    This ensures the endpoint always returns something useful.
    """
    if not static_findings:
        return DebugResult(
            root_cause="No issues detected by static analysis.",
            explanation=f"AI analysis was unavailable: {exc}",
            evidence=[],
            suggested_fix="Review the code manually.",
            confidence="possible",
            severity="low",
            static_finding_count=0,
        )

    # Surface the highest-severity static finding as the root cause
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    top = min(static_findings, key=lambda f: severity_order.get(f.get("severity", "low"), 3))

    return DebugResult(
        root_cause=top.get("message", "Static analysis finding."),
        explanation=(
            f"AI analysis was unavailable ({exc}). "
            f"{len(static_findings)} static finding(s) were detected. "
            "Review the evidence list for details."
        ),
        evidence=[f"{f.get('source','?')} line {f.get('line','?')}: {f.get('message','')}"
                  for f in static_findings[:5]],
        suggested_fix="Resolve the static analysis findings listed above.",
        confidence="possible",
        severity=top.get("severity", "medium"),
        static_finding_count=len(static_findings),
    )
