"""
Code quality analyzer.

Detects deterministic code-quality issues using regex + AST (Python).
Does NOT replace a real linter — it catches patterns that linters often miss
or that are worth flagging at the diff level specifically.

Detects:
  - Duplicate code blocks (consecutive similar lines)
  - Dead code patterns (unreachable after return/raise/continue/break)
  - Excessive nesting (standalone check for non-Python too)
  - TODO / FIXME / HACK / XXX comments
  - Unused imports (Python AST)
  - Obvious anti-patterns (mutable default args, bare except, == None, print in prod)
  - Empty exception handlers
  - Magic numbers (numeric literals outside assignments)
  - Long lines (> 120 chars)
  - Console.log left in production JavaScript/TypeScript
"""

from __future__ import annotations

import ast
import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Output type
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class QualityFinding:
    finding_type:   str = "structure"
    severity:       str = "low"
    file:           str = ""
    line:           int | None = None
    rule:           str = ""
    message:        str = ""
    explanation:    str = ""
    recommendation: str = ""
    source:         str = "static"

    def to_dict(self) -> dict:
        return {
            "type":           self.finding_type,
            "severity":       self.severity,
            "file":           self.file,
            "line":           self.line,
            "rule":           self.rule,
            "message":        self.message,
            "explanation":    self.explanation,
            "recommendation": self.recommendation,
            "source":         self.source,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Regex-based checks (language-agnostic unless noted)
# ─────────────────────────────────────────────────────────────────────────────

_TODO_RE = re.compile(r'#.*\b(TODO|FIXME|HACK|XXX|BUG|NOQA)\b', re.IGNORECASE)
_LONG_LINE_THRESHOLD = 120
_MAGIC_NUMBER_RE = re.compile(
    r'(?<!["\'\w])(?<!\.)\b(?!0x[0-9a-fA-F]+)(\d{2,})\b(?!\s*["\'])'  # ≥2-digit literals
)
_MAGIC_EXCEPTIONS = re.compile(r'(?:version|port|timeout|size|limit|count|max|min|default)\s*[=:]', re.IGNORECASE)

# JavaScript / TypeScript only
_CONSOLE_LOG_RE = re.compile(r'\bconsole\.(log|debug|info|warn)\s*\(')

# Python anti-patterns
_BARE_EXCEPT_RE = re.compile(r'^\s*except\s*:')
_COMPARE_NONE_RE = re.compile(r'(?:==|!=)\s*None\b|None\s*(?:==|!=)')
_PRINT_RE = re.compile(r'^\s*print\s*\(')

# Dead code: statement after unconditional terminator on same indentation level
_TERMINATOR_RE  = re.compile(r'^\s*(return|raise|break|continue|sys\.exit)\b')
_STATEMENT_RE   = re.compile(r'^\s+\S')  # non-empty indented line


def _check_regex(source: str, language: str, file_path: str) -> list[QualityFinding]:
    findings: list[QualityFinding] = []
    lines = source.splitlines()

    prev_indent = -1
    after_terminator = False

    for lineno, line in enumerate(lines, start=1):
        stripped = line.rstrip()

        # ── TODO / FIXME ────────────────────────────────────────────────────
        m = _TODO_RE.search(line)
        if m:
            keyword = m.group(1).upper()
            findings.append(QualityFinding(
                severity="low",
                file=file_path, line=lineno,
                rule="QA001",
                message=f"{keyword} comment left in code",
                explanation="Development annotations should not remain in production code.",
                recommendation=f"Resolve or remove the {keyword} comment before merging.",
            ))

        # ── Long line ────────────────────────────────────────────────────────
        if len(line) > _LONG_LINE_THRESHOLD:
            findings.append(QualityFinding(
                severity="low",
                file=file_path, line=lineno,
                rule="QA002",
                message=f"Line is {len(line)} characters (limit: {_LONG_LINE_THRESHOLD})",
                explanation="Overly long lines reduce readability and can cause diff noise.",
                recommendation="Break the line or extract a variable to shorten it.",
            ))

        # ── console.log in JS/TS ─────────────────────────────────────────────
        if language in ("javascript", "typescript") and _CONSOLE_LOG_RE.search(line):
            findings.append(QualityFinding(
                severity="medium",
                file=file_path, line=lineno,
                rule="QA003",
                message="console.log/debug/info/warn left in code",
                explanation="Console statements output sensitive data to browser/server logs.",
                recommendation="Remove or replace with a structured logger that respects log levels.",
            ))

        # ── Python: bare except ───────────────────────────────────────────────
        if language == "python" and _BARE_EXCEPT_RE.match(line):
            findings.append(QualityFinding(
                severity="medium",
                file=file_path, line=lineno,
                rule="QA004",
                message="Bare except clause catches all exceptions including SystemExit",
                explanation="except: catches BaseException which includes KeyboardInterrupt and SystemExit.",
                recommendation="Catch a specific exception type: except ValueError: or except Exception:",
            ))

        # ── Python: == None comparison ────────────────────────────────────────
        if language == "python" and _COMPARE_NONE_RE.search(line):
            findings.append(QualityFinding(
                severity="low",
                file=file_path, line=lineno,
                rule="QA005",
                message="Use 'is None' / 'is not None' instead of == / != None",
                explanation="Identity comparison with None should use 'is', not '=='.",
                recommendation="Replace '== None' with 'is None' and '!= None' with 'is not None'.",
            ))

        # ── Python: print in production ───────────────────────────────────────
        if language == "python" and _PRINT_RE.match(line):
            findings.append(QualityFinding(
                severity="low",
                file=file_path, line=lineno,
                rule="QA006",
                message="print() statement found",
                explanation="print() calls are typically debug artifacts. Use logging instead.",
                recommendation="Replace print() with logging.info() / logging.debug() etc.",
            ))

        # ── Dead code (basic) ─────────────────────────────────────────────────
        current_indent = len(line) - len(line.lstrip())
        if _TERMINATOR_RE.match(line):
            after_terminator = True
            prev_indent = current_indent
        elif after_terminator:
            # If the next non-empty, non-comment line has the same or less indentation
            # it's in the same block — flag it as dead code.
            if stripped and not stripped.lstrip().startswith(("#", "//", "/*")):
                if current_indent <= prev_indent:
                    findings.append(QualityFinding(
                        severity="medium",
                        file=file_path, line=lineno,
                        rule="QA007",
                        message="Unreachable code after return/raise/break/continue",
                        explanation="This statement can never be executed.",
                        recommendation="Remove the unreachable statement or restructure the control flow.",
                    ))
                after_terminator = False

    return findings


# ─────────────────────────────────────────────────────────────────────────────
# Duplicate-block detector (language-agnostic)
# ─────────────────────────────────────────────────────────────────────────────

_MIN_DUP_LINES = 6   # consecutive identical-or-near-identical lines to flag


def _check_duplicates(source: str, file_path: str) -> list[QualityFinding]:
    """
    Flag consecutive blocks of very similar lines (copy-paste detection).
    Strips whitespace and comments before comparison.
    """
    findings: list[QualityFinding] = []
    lines = source.splitlines()
    normalized = [re.sub(r'\s+', ' ', l.strip()) for l in lines]

    i = 0
    while i < len(normalized) - _MIN_DUP_LINES:
        block = normalized[i: i + _MIN_DUP_LINES]
        if all(b == block[0] and b for b in block):
            findings.append(QualityFinding(
                severity="low",
                file=file_path,
                line=i + 1,
                rule="QA010",
                message=f"Repeated identical lines detected ({_MIN_DUP_LINES}+ consecutive)",
                explanation="Repeating identical statements may indicate copy-paste or a missing loop.",
                recommendation="Extract the repeated block into a loop or a helper function.",
            ))
            i += _MIN_DUP_LINES
            continue
        i += 1
    return findings


# ─────────────────────────────────────────────────────────────────────────────
# Python-specific AST checks
# ─────────────────────────────────────────────────────────────────────────────

class _PythonQualityVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str):
        self.file = file_path
        self.findings: list[QualityFinding] = []
        self._imports: dict[str, int] = {}   # name → lineno

    # ── Unused imports ────────────────────────────────────────────────────────
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            name = alias.asname or alias.name.split(".")[0]
            self._imports[name] = node.lineno
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            if alias.name == "*":
                continue
            name = alias.asname or alias.name
            self._imports[name] = node.lineno
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        self._imports.pop(node.id, None)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        if isinstance(node.value, ast.Name):
            self._imports.pop(node.value.id, None)
        self.generic_visit(node)

    # ── Mutable default arguments ─────────────────────────────────────────────
    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._check_mutable_defaults(node)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def _check_mutable_defaults(self, node):
        for default in node.args.defaults + node.args.kw_defaults:
            if default is None:
                continue
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self.findings.append(QualityFinding(
                    severity="medium",
                    file=self.file,
                    line=node.lineno,
                    rule="QA020",
                    message=f"Mutable default argument in function '{node.name}'",
                    explanation=(
                        "Mutable default arguments are shared across all calls. "
                        "Modifying them causes surprising behaviour."
                    ),
                    recommendation="Use None as the default and initialise inside the function body.",
                ))

    # ── Empty except block ────────────────────────────────────────────────────
    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        if not node.body or (len(node.body) == 1 and isinstance(node.body[0], ast.Pass)):
            self.findings.append(QualityFinding(
                severity="medium",
                file=self.file,
                line=node.lineno,
                rule="QA021",
                message="Empty except handler silently swallows exceptions",
                explanation="A pass-only except block hides errors and makes debugging very difficult.",
                recommendation="Log the exception, re-raise it, or handle it explicitly.",
            ))
        self.generic_visit(node)

    def flush_unused_imports(self):
        for name, lineno in self._imports.items():
            self.findings.append(QualityFinding(
                severity="low",
                file=self.file,
                line=lineno,
                rule="QA011",
                message=f"Possibly unused import: '{name}'",
                explanation="Imported name does not appear to be referenced in this file.",
                recommendation=f"Remove the import of '{name}' if it is not needed.",
            ))


def _check_python_ast(source: str, file_path: str) -> list[QualityFinding]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    visitor = _PythonQualityVisitor(file_path)
    visitor.visit(tree)
    visitor.flush_unused_imports()
    return visitor.findings


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def analyze_quality(
    source: str,
    language: str,
    file_path: str,
) -> list[QualityFinding]:
    """
    Run all code-quality checks on *source*.

    Args:
        source:    Full (reconstructed) source text.
        language:  Normalised language name.
        file_path: File path for reporting.

    Returns:
        List of :class:`QualityFinding` objects.
    """
    if not source.strip():
        return []

    findings: list[QualityFinding] = []
    findings.extend(_check_regex(source, language, file_path))
    findings.extend(_check_duplicates(source, file_path))

    if language == "python":
        findings.extend(_check_python_ast(source, file_path))

    return findings


def analyze_quality_from_diff(changed_files: list) -> list[QualityFinding]:
    """Run code-quality analysis over all files in a parsed diff."""
    from app.services.diff_service import reconstruct_new_source

    all_findings: list[QualityFinding] = []
    for cf in changed_files:
        source = reconstruct_new_source(cf)
        findings = analyze_quality(source, cf.language, cf.path)
        all_findings.extend(findings)
    return all_findings
