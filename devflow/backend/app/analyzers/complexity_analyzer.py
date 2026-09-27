"""
Complexity analyzer.

Computes:
  - Cyclomatic complexity  (McCabe: decision points + 1)
  - Cognitive complexity   (nesting-weighted branch count)
  - Function length        (line count)
  - Nesting depth          (max indentation depth)
  - Parameter count

Works on Python source via the stdlib ``ast`` module (no extra deps).
For other languages, a regex-based heuristic fallback estimates complexity
from branch-keyword counting.

Flags:
  - Cyclomatic complexity > 10   → medium  (> 20 → high)
  - Cognitive complexity  > 15   → medium  (> 30 → high)
  - Function length > 50 lines   → low     (> 100 → medium)
  - Nesting depth > 4            → medium
  - Parameter count > 7          → low
"""

from __future__ import annotations

import ast
import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Thresholds
# ─────────────────────────────────────────────────────────────────────────────

_CYCLOMATIC_MEDIUM = 10
_CYCLOMATIC_HIGH   = 20
_COGNITIVE_MEDIUM  = 15
_COGNITIVE_HIGH    = 30
_LENGTH_LOW        = 50
_LENGTH_MEDIUM     = 100
_NESTING_MEDIUM    = 4
_PARAMS_LOW        = 7


# ─────────────────────────────────────────────────────────────────────────────
# Output types
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FunctionMetrics:
    name:             str
    file:             str
    line:             int
    cyclomatic:       int
    cognitive:        int
    length:           int
    max_nesting:      int
    param_count:      int
    language:         str

    def findings(self) -> list["ComplexityFinding"]:
        """Convert metrics into a list of findings for any exceeded threshold."""
        result: list[ComplexityFinding] = []

        # Cyclomatic
        if self.cyclomatic > _CYCLOMATIC_HIGH:
            result.append(ComplexityFinding(
                function=self.name, file=self.file, line=self.line,
                metric="cyclomatic_complexity", value=self.cyclomatic,
                threshold=_CYCLOMATIC_HIGH, severity="high",
                message=f"Cyclomatic complexity {self.cyclomatic} is very high (threshold: {_CYCLOMATIC_HIGH})",
                recommendation="Break this function into smaller, single-responsibility units.",
            ))
        elif self.cyclomatic > _CYCLOMATIC_MEDIUM:
            result.append(ComplexityFinding(
                function=self.name, file=self.file, line=self.line,
                metric="cyclomatic_complexity", value=self.cyclomatic,
                threshold=_CYCLOMATIC_MEDIUM, severity="medium",
                message=f"Cyclomatic complexity {self.cyclomatic} exceeds threshold ({_CYCLOMATIC_MEDIUM})",
                recommendation="Consider extracting conditional blocks into helper functions.",
            ))

        # Cognitive
        if self.cognitive > _COGNITIVE_HIGH:
            result.append(ComplexityFinding(
                function=self.name, file=self.file, line=self.line,
                metric="cognitive_complexity", value=self.cognitive,
                threshold=_COGNITIVE_HIGH, severity="high",
                message=f"Cognitive complexity {self.cognitive} is very high (threshold: {_COGNITIVE_HIGH})",
                recommendation="Reduce nesting and early-return where possible.",
            ))
        elif self.cognitive > _COGNITIVE_MEDIUM:
            result.append(ComplexityFinding(
                function=self.name, file=self.file, line=self.line,
                metric="cognitive_complexity", value=self.cognitive,
                threshold=_COGNITIVE_MEDIUM, severity="medium",
                message=f"Cognitive complexity {self.cognitive} exceeds threshold ({_COGNITIVE_MEDIUM})",
                recommendation="Flatten conditional logic and extract nested blocks.",
            ))

        # Length
        if self.length > _LENGTH_MEDIUM:
            result.append(ComplexityFinding(
                function=self.name, file=self.file, line=self.line,
                metric="function_length", value=self.length,
                threshold=_LENGTH_MEDIUM, severity="medium",
                message=f"Function is {self.length} lines long",
                recommendation="Functions longer than 100 lines are difficult to test and maintain. Split them up.",
            ))
        elif self.length > _LENGTH_LOW:
            result.append(ComplexityFinding(
                function=self.name, file=self.file, line=self.line,
                metric="function_length", value=self.length,
                threshold=_LENGTH_LOW, severity="low",
                message=f"Function is {self.length} lines long",
                recommendation="Consider splitting functions longer than 50 lines.",
            ))

        # Nesting
        if self.max_nesting > _NESTING_MEDIUM:
            result.append(ComplexityFinding(
                function=self.name, file=self.file, line=self.line,
                metric="nesting_depth", value=self.max_nesting,
                threshold=_NESTING_MEDIUM, severity="medium",
                message=f"Maximum nesting depth is {self.max_nesting}",
                recommendation="Use guard clauses and early returns to reduce nesting.",
            ))

        # Parameter count
        if self.param_count > _PARAMS_LOW:
            result.append(ComplexityFinding(
                function=self.name, file=self.file, line=self.line,
                metric="parameter_count", value=self.param_count,
                threshold=_PARAMS_LOW, severity="low",
                message=f"Function has {self.param_count} parameters",
                recommendation=(
                    "Consider grouping related parameters into a dataclass or config object."
                ),
            ))

        return result


@dataclass
class ComplexityFinding:
    function:       str
    file:           str
    line:           int
    metric:         str
    value:          int
    threshold:      int
    severity:       str
    message:        str
    recommendation: str
    source:         str = "static"

    def to_dict(self) -> dict:
        return {
            "function":       self.function,
            "file":           self.file,
            "line":           self.line,
            "metric":         self.metric,
            "complexity":     self.value,
            "threshold":      self.threshold,
            "severity":       self.severity,
            "message":        self.message,
            "recommendation": self.recommendation,
            "source":         self.source,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Python analyzer (AST-based, stdlib only)
# ─────────────────────────────────────────────────────────────────────────────

# AST node types that add a branch (McCabe)
_CYCLOMATIC_NODES = (
    ast.If, ast.For, ast.While, ast.ExceptHandler,
    ast.With, ast.Assert, ast.comprehension,
    ast.BoolOp,   # and / or
    ast.IfExp,    # ternary
)


class _PythonComplexityVisitor(ast.NodeVisitor):
    """Walk an AST function/method body and compute metrics."""

    def __init__(self, func_node: ast.FunctionDef | ast.AsyncFunctionDef, file: str):
        self.file       = file
        self.name       = func_node.name
        self.line       = func_node.lineno
        self.param_count = len(func_node.args.args) + len(func_node.args.posonlyargs)
        self.cyclomatic  = 1   # base complexity
        self.cognitive   = 0
        self._nesting    = 0
        self._max_nesting = 0
        self._length     = (
            (func_node.end_lineno or func_node.lineno) - func_node.lineno + 1
            if hasattr(func_node, "end_lineno")
            else 0
        )
        self.visit(func_node)

    # Nodes that increment cyclomatic AND cognitive
    def _enter_branch(self, node):
        self.cyclomatic += 1
        self.cognitive  += 1 + self._nesting  # nesting-weighted
        self._nesting   += 1
        self._max_nesting = max(self._max_nesting, self._nesting)
        self.generic_visit(node)
        self._nesting -= 1

    def visit_If(self, node):       self._enter_branch(node)
    def visit_For(self, node):      self._enter_branch(node)
    def visit_While(self, node):    self._enter_branch(node)
    def visit_With(self, node):     self._enter_branch(node)
    def visit_ExceptHandler(self, node): self._enter_branch(node)
    def visit_comprehension(self, node): self._enter_branch(node)

    def visit_BoolOp(self, node):
        # Each additional operand adds 1 to cyclomatic
        self.cyclomatic += len(node.values) - 1
        self.cognitive  += 1
        self.generic_visit(node)

    def visit_IfExp(self, node):
        self.cyclomatic += 1
        self.cognitive  += 1
        self.generic_visit(node)

    def visit_Assert(self, node):
        self.cyclomatic += 1
        self.generic_visit(node)

    def to_metrics(self) -> FunctionMetrics:
        return FunctionMetrics(
            name=self.name,
            file=self.file,
            line=self.line,
            cyclomatic=self.cyclomatic,
            cognitive=self.cognitive,
            length=self._length,
            max_nesting=self._max_nesting,
            param_count=self.param_count,
            language="python",
        )


def _analyze_python(source: str, file_path: str) -> list[FunctionMetrics]:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        logger.debug("ast.parse failed for %s: %s — skipping complexity", file_path, exc)
        return []

    metrics: list[FunctionMetrics] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            visitor = _PythonComplexityVisitor(node, file_path)
            metrics.append(visitor.to_metrics())
    return metrics


# ─────────────────────────────────────────────────────────────────────────────
# Heuristic fallback (regex-based, language-agnostic)
# ─────────────────────────────────────────────────────────────────────────────

# Patterns that signal a branch in C-style languages
_BRANCH_KEYWORDS = re.compile(
    r'\b(?:if|else\s+if|elif|for|while|switch|case|catch|except|&&|\|\|)\b'
)
_FUNCTION_START   = re.compile(
    r'(?:function\s+(\w+)|(?:public|private|protected|static)?\s*\w[\w<>\[\]]*\s+(\w+)\s*\(|(\w+)\s*[:=]\s*(?:async\s*)?\(.*\)\s*[={])'
)
_INDENT_RE        = re.compile(r'^(\s+)')


def _analyze_heuristic(source: str, language: str, file_path: str) -> list[FunctionMetrics]:
    """
    Estimate complexity from raw source using keyword counting.
    Groups lines into approximate function blocks by tracking
    curly-brace depth or indentation.
    """
    lines = source.splitlines()
    metrics: list[FunctionMetrics] = []

    # Simple approach: count all branch keywords across the whole file
    # as a single "file-level" metric if we can't isolate functions.
    branches    = sum(1 for l in lines if _BRANCH_KEYWORDS.search(l))
    max_depth   = 0
    for l in lines:
        m = _INDENT_RE.match(l)
        if m:
            depth = len(m.group(1).replace("\t", "    ")) // 4
            max_depth = max(max_depth, depth)

    if branches > 0:
        metrics.append(FunctionMetrics(
            name="<file>",
            file=file_path,
            line=1,
            cyclomatic=branches + 1,
            cognitive=branches,
            length=len(lines),
            max_nesting=max_depth,
            param_count=0,
            language=language,
        ))

    return metrics


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def analyze_complexity(
    source: str,
    language: str,
    file_path: str,
) -> list[ComplexityFinding]:
    """
    Compute complexity metrics for *source* and return findings for
    any function that exceeds a threshold.

    Args:
        source:    Full (reconstructed) source text.
        language:  Normalised language name.
        file_path: File path for reporting.

    Returns:
        List of :class:`ComplexityFinding` objects.
    """
    if not source.strip():
        return []

    if language == "python":
        all_metrics = _analyze_python(source, file_path)
    else:
        all_metrics = _analyze_heuristic(source, language, file_path)

    return [f for m in all_metrics for f in m.findings()]


def analyze_complexity_from_diff(changed_files: list) -> list[ComplexityFinding]:
    """Run complexity analysis over all files in a parsed diff."""
    from app.services.diff_service import reconstruct_new_source

    all_findings: list[ComplexityFinding] = []
    for cf in changed_files:
        source = reconstruct_new_source(cf)
        findings = analyze_complexity(source, cf.language, cf.path)
        all_findings.extend(findings)
    return all_findings
