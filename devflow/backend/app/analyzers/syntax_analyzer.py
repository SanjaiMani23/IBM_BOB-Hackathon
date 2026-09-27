"""
Language-aware syntax analyzer.

Uses Tree-sitter (where the grammar package is installed) to build an AST
and detect syntax errors in changed files. Falls back to a regex-based
heuristic analyzer when Tree-sitter is unavailable for a given language,
rather than crashing or silently skipping the file.

Supported languages: Python, JavaScript, TypeScript, Java, Go.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Protocol

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Output type
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SyntaxFinding:
    finding_type: str = "syntax"
    severity:     str = "high"
    file:         str = ""
    line:         int | None = None
    message:      str = ""
    explanation:  str = ""
    confidence:   float = 1.0
    source:       str = "static"

    def to_dict(self) -> dict:
        return {
            "type":        self.finding_type,
            "severity":    self.severity,
            "file":        self.file,
            "line":        self.line,
            "message":     self.message,
            "explanation": self.explanation,
            "confidence":  self.confidence,
            "source":      self.source,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Tree-sitter integration (optional — graceful degradation if not installed)
# ─────────────────────────────────────────────────────────────────────────────

# Mapping language name → (tree_sitter package, language function name)
_TS_PACKAGES: dict[str, tuple[str, str]] = {
    "python":     ("tree_sitter_python",     "language"),
    "javascript": ("tree_sitter_javascript", "language"),
    "typescript": ("tree_sitter_typescript", "language_typescript"),
    "java":       ("tree_sitter_java",       "language"),
    "go":         ("tree_sitter_go",         "language"),
}


def _load_ts_parser(language: str):
    """
    Attempt to load a Tree-sitter parser for *language*.
    Returns a ``tree_sitter.Parser`` instance, or ``None`` if the
    grammar package is not installed.
    """
    pkg_info = _TS_PACKAGES.get(language)
    if pkg_info is None:
        return None
    pkg_name, fn_name = pkg_info
    try:
        import importlib
        from tree_sitter import Language, Parser  # type: ignore

        mod = importlib.import_module(pkg_name)
        lang_fn = getattr(mod, fn_name)
        lang = Language(lang_fn())
        parser = Parser(lang)
        return parser
    except Exception as exc:  # noqa: BLE001
        logger.debug("Tree-sitter parser unavailable for %s: %s", language, exc)
        return None


def _ts_find_errors(source: str, parser) -> list[tuple[int, str]]:
    """
    Walk the Tree-sitter CST and collect ERROR and MISSING nodes.
    Returns a list of (line_number, node_type) tuples.
    """
    tree = parser.parse(source.encode())
    errors: list[tuple[int, str]] = []

    def _walk(node):
        if node.type in ("ERROR", "MISSING"):
            errors.append((node.start_point[0] + 1, node.type))
        for child in node.children:
            _walk(child)

    _walk(tree.root_node)
    return errors


# ─────────────────────────────────────────────────────────────────────────────
# Heuristic fallback analyzers (regex-based, no external deps)
# ─────────────────────────────────────────────────────────────────────────────

# Patterns that strongly suggest a syntax problem in their language
_HEURISTIC_RULES: dict[str, list[tuple[re.Pattern, str, str]]] = {
    "python": [
        (re.compile(r"^\s*def\s+\w+[^(:)]*$"),
         "Malformed function definition", "Function definition is missing parentheses or colon."),
        (re.compile(r"^\s*class\s+\w+[^(:)]*$"),
         "Malformed class definition", "Class definition is missing colon."),
        (re.compile(r"^\s*(?:if|elif|for|while|with)\s+.+[^:]$"),
         "Missing colon on control statement", "Control flow statement is missing a trailing colon."),
        (re.compile(r"print\s+['\"]"),
         "Python 2 print statement", "Use print() function (Python 3 syntax)."),
    ],
    "javascript": [
        (re.compile(r"(?<![=!<>])===?[^=]"),  # very loose guard
         "", ""),   # placeholder — kept intentionally sparse to avoid false positives
        (re.compile(r"^\s*function\s*\("),
         "Anonymous function without assignment",
         "Bare anonymous function expression will be ignored at statement level."),
    ],
    "typescript": [],  # inherits JS checks below
    "java": [
        (re.compile(r"^\s*(?:public|private|protected)?\s+\w+\s+\w+\s*$"),
         "Possible missing semicolon or brace",
         "Statement appears incomplete — check for missing semicolon or opening brace."),
    ],
    "go": [
        (re.compile(r"^\s*func\s+\w+\s*$"),
         "Incomplete function signature",
         "Go function signature is missing parameter list or return type."),
    ],
}

# JavaScript rules also apply to TypeScript
_HEURISTIC_RULES["typescript"] = _HEURISTIC_RULES["javascript"]


def _heuristic_analyze(source: str, language: str, file_path: str) -> list[SyntaxFinding]:
    rules = _HEURISTIC_RULES.get(language, [])
    findings: list[SyntaxFinding] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        for pattern, message, explanation in rules:
            if message and pattern.search(line):
                findings.append(SyntaxFinding(
                    file=file_path,
                    line=lineno,
                    message=message,
                    explanation=explanation,
                    confidence=0.65,
                    severity="medium",
                ))
    return findings


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def analyze_syntax(
    source: str,
    language: str,
    file_path: str,
) -> list[SyntaxFinding]:
    """
    Analyse *source* for syntax errors.

    Strategy:
    1. Try Tree-sitter for the given *language*.
    2. Fall back to regex heuristics if Tree-sitter is unavailable.
    3. Return an empty list (not an error) for unsupported languages.

    Args:
        source:    Full reconstructed source of the changed file.
        language:  Normalised language name (e.g. ``"python"``).
        file_path: File path for reporting purposes.

    Returns:
        List of :class:`SyntaxFinding` objects.
    """
    if not source.strip():
        return []

    parser = _load_ts_parser(language)

    if parser is not None:
        try:
            raw_errors = _ts_find_errors(source, parser)
            findings = []
            for lineno, node_type in raw_errors:
                desc = (
                    "Parser could not understand this construct."
                    if node_type == "ERROR"
                    else "Expected syntax element is missing."
                )
                findings.append(SyntaxFinding(
                    file=file_path,
                    line=lineno,
                    message=f"Syntax {node_type.lower()} detected by Tree-sitter",
                    explanation=desc,
                    confidence=0.98,
                    severity="high",
                ))
            return findings
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Tree-sitter parse failed for %s (%s): %s — falling back to heuristics",
                file_path, language, exc,
            )

    if language not in _HEURISTIC_RULES:
        logger.debug("No syntax analyzer available for language '%s', skipping %s", language, file_path)
        return []

    return _heuristic_analyze(source, language, file_path)


def analyze_syntax_from_diff(
    changed_files: list,   # list[ChangedFile] from diff_service
) -> list[SyntaxFinding]:
    """
    Run syntax analysis over all files in a parsed diff.

    Imports :func:`reconstruct_new_source` from ``diff_service`` to build
    the post-patch source for each file.
    """
    from app.services.diff_service import reconstruct_new_source  # local import avoids circular

    all_findings: list[SyntaxFinding] = []
    for cf in changed_files:
        source = reconstruct_new_source(cf)
        findings = analyze_syntax(source, cf.language, cf.path)
        all_findings.extend(findings)
    return all_findings
