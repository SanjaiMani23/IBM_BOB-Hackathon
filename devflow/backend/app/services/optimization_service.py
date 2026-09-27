"""
Optimization service.

Combines deterministic complexity/quality analysis with AI-assisted
optimization suggestions. The static layer identifies concrete problems
(N+1 queries, excessive complexity, duplicates); the AI layer explains
them and proposes improvements with trade-off context.

Suggested code changes are NEVER applied automatically.
Developer review and approval is always required.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.services import ai_service
from app.analyzers.complexity_analyzer import analyze_complexity
from app.analyzers.code_quality import analyze_quality

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Output types
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class OptimizationSuggestion:
    priority:             str          # "high" | "medium" | "low"
    title:                str
    current_approach:     str
    problem:              str
    recommended_approach: str
    complexity_before:    str | None   # e.g. "O(n²)"
    complexity_after:     str | None   # e.g. "O(n)"
    expected_impact:      str
    suggested_code:       str | None   # never auto-applied
    trade_off:            str | None
    confidence:           float
    source:               str          # "static" | "ai"

    def to_dict(self) -> dict:
        return {
            "priority":             self.priority,
            "title":                self.title,
            "current_approach":     self.current_approach,
            "problem":              self.problem,
            "recommended_approach": self.recommended_approach,
            "complexity_before":    self.complexity_before,
            "complexity_after":     self.complexity_after,
            "expected_impact":      self.expected_impact,
            "suggested_code":       self.suggested_code,
            "trade_off":            self.trade_off,
            "confidence":           self.confidence,
            "source":               self.source,
        }


@dataclass
class OptimizationResult:
    file:             str
    language:         str
    suggestions:      list[OptimizationSuggestion] = field(default_factory=list)
    optimized_code:   str | None = None
    static_issue_count: int = 0

    def to_dict(self) -> dict:
        return {
            "file":               self.file,
            "language":           self.language,
            "suggestions":        [s.to_dict() for s in self.suggestions],
            "optimized_code":     self.optimized_code,
            "static_issue_count": self.static_issue_count,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Service
# ─────────────────────────────────────────────────────────────────────────────

def optimize_code(
    code: str,
    language: str,
    file_path: str = "<unknown>",
    context: str | None = None,
) -> OptimizationResult:
    """
    Analyse *code* for optimization opportunities.

    Steps:
    1. Run deterministic complexity and quality analyzers.
    2. Convert static findings into preliminary suggestions.
    3. Send code + context to watsonx.ai for AI-assisted analysis.
    4. Merge and deduplicate suggestions, sorted by priority.

    Args:
        code:      Source code to analyse.
        language:  Normalised language name.
        file_path: File path for reporting.
        context:   Optional surrounding context (e.g. how the function is called).

    Returns:
        :class:`OptimizationResult` with a list of suggestions.
        ``optimized_code`` is set only if the AI produces a full rewrite.
    """
    # ── Static analysis ───────────────────────────────────────────────────────
    static_suggestions: list[OptimizationSuggestion] = []

    for cf in analyze_complexity(code, language, file_path):
        static_suggestions.append(OptimizationSuggestion(
            priority=_sev_to_priority(cf.severity),
            title=cf.message,
            current_approach=f"{cf.metric} = {cf.value} in '{cf.function}'",
            problem=cf.message,
            recommended_approach=cf.recommendation,
            complexity_before=None,
            complexity_after=None,
            expected_impact="Reduced cognitive load and improved maintainability.",
            suggested_code=None,
            trade_off=None,
            confidence=0.90,
            source="static",
        ))

    for qf in analyze_quality(code, language, file_path):
        # Only forward optimization-relevant quality findings
        if qf.rule in ("QA003", "QA004", "QA006", "QA007", "QA010", "QA020", "QA021"):
            continue   # bug-category findings — belong to debug_service
        static_suggestions.append(OptimizationSuggestion(
            priority=_sev_to_priority(qf.severity),
            title=qf.message,
            current_approach=qf.explanation,
            problem=qf.message,
            recommended_approach=qf.recommendation,
            complexity_before=None,
            complexity_after=None,
            expected_impact="Improved readability and maintainability.",
            suggested_code=None,
            trade_off=None,
            confidence=0.80,
            source="static",
        ))

    logger.info(
        "optimize_code: %d static issues for %s (%s)",
        len(static_suggestions), file_path, language,
    )

    # ── AI optimization ───────────────────────────────────────────────────────
    ai_suggestions: list[OptimizationSuggestion] = []
    optimized_code: str | None = None

    try:
        ai_response = ai_service.analyze_for_optimization(
            code=code,
            language=language,
            context=context,
        )
        optimized_code = ai_response.get("optimized_code") or None

        for item in ai_response.get("suggestions", []):
            ai_suggestions.append(OptimizationSuggestion(
                priority=item.get("priority", "medium"),
                title=item.get("title", "Optimization suggestion"),
                current_approach=item.get("explanation", ""),
                problem=item.get("explanation", ""),
                recommended_approach=item.get("recommendation", ""),
                complexity_before=None,
                complexity_after=None,
                expected_impact=item.get("trade_off", ""),
                suggested_code=item.get("example"),
                trade_off=item.get("trade_off"),
                confidence=0.75,
                source="ai",
            ))
    except Exception as exc:
        logger.warning("AI optimization call failed for %s: %s", file_path, exc)

    # ── Merge and sort ────────────────────────────────────────────────────────
    _priority_order = {"high": 0, "medium": 1, "low": 2}
    all_suggestions = sorted(
        static_suggestions + ai_suggestions,
        key=lambda s: _priority_order.get(s.priority, 2),
    )

    return OptimizationResult(
        file=file_path,
        language=language,
        suggestions=all_suggestions,
        optimized_code=optimized_code,
        static_issue_count=len(static_suggestions),
    )


def optimize_from_diff(changed_files: list) -> list[OptimizationResult]:
    """
    Run optimization analysis across all files in a parsed diff.
    Returns only files with at least one suggestion.
    """
    from app.services.diff_service import reconstruct_new_source

    results: list[OptimizationResult] = []
    for cf in changed_files:
        source = reconstruct_new_source(cf)
        if not source.strip():
            continue
        result = optimize_code(source, cf.language, cf.path)
        if result.suggestions:
            results.append(result)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _sev_to_priority(severity: str) -> str:
    return {"critical": "high", "high": "high", "medium": "medium", "low": "low"}.get(severity, "low")
