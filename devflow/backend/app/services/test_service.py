"""
Test generation service.

Generates a test plan and optional test scaffolding for changed code.
Uses security and quality findings to ensure edge cases and regression
tests are included.

IMPORTANT: Generated tests are scaffolding only.
They have NOT been executed. The developer must review, complete,
and run them before claiming coverage.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.services import ai_service
from app.analyzers.security_analyzer import analyze_security
from app.analyzers.code_quality import analyze_quality

logger = logging.getLogger(__name__)

# Default framework per language when none is specified
_DEFAULT_FRAMEWORKS: dict[str, str] = {
    "python":     "pytest",
    "javascript": "jest",
    "typescript": "jest",
    "java":       "JUnit 5",
    "go":         "testing (stdlib)",
    "ruby":       "RSpec",
    "csharp":     "xUnit",
}


# ─────────────────────────────────────────────────────────────────────────────
# Output types
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TestCase:
    name:        str
    description: str
    category:    str   # "happy_path" | "edge_case" | "error" | "regression" | "security"

    def to_dict(self) -> dict:
        return {
            "name":        self.name,
            "description": self.description,
            "category":    self.category,
        }


@dataclass
class TestResult:
    file:           str
    language:       str
    framework:      str
    test_cases:     list[TestCase] = field(default_factory=list)
    test_code:      str = ""
    security_tests: bool = False

    # Explicit disclaimer — tests have not been executed
    disclaimer: str = (
        "Generated test scaffolding has NOT been executed. "
        "Review, complete, and run all tests before claiming coverage."
    )

    def to_dict(self) -> dict:
        return {
            "file":           self.file,
            "language":       self.language,
            "framework":      self.framework,
            "test_cases":     [t.to_dict() for t in self.test_cases],
            "test_code":      self.test_code,
            "security_tests": self.security_tests,
            "disclaimer":     self.disclaimer,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Service
# ─────────────────────────────────────────────────────────────────────────────

def generate_tests(
    code: str,
    language: str,
    file_path: str = "<unknown>",
    framework: str | None = None,
    findings: list[dict] | None = None,
) -> TestResult:
    """
    Generate unit test scaffolding for *code*.

    Steps:
    1. Run security and quality analyzers to identify edge cases that
       need regression or security tests.
    2. Call watsonx.ai with the testing prompt to generate scaffolding.
    3. Return a structured result with individual test cases and full
       test code.

    Args:
        code:      Source code to generate tests for.
        language:  Normalised language name.
        file_path: File path for reporting.
        framework: Test framework to use (falls back to language default).
        findings:  Pre-computed findings (avoids double analysis if already done).

    Returns:
        :class:`TestResult` with test scaffolding — NOT executed.
    """
    effective_framework = (
        framework
        or _DEFAULT_FRAMEWORKS.get(language, f"the standard test framework for {language}")
    )

    # ── Augment with static findings to hint at security/edge-case tests ──────
    has_security_findings = False
    if findings is None:
        security_findings = analyze_security(code, language, file_path)
        quality_findings  = analyze_quality(code, language, file_path)
        has_security_findings = len(security_findings) > 0
        findings = (
            [{"source": "security", "rule": f.rule, "message": f.message} for f in security_findings]
            + [{"source": "quality",  "rule": f.rule, "message": f.message} for f in quality_findings]
        )
    else:
        has_security_findings = any(f.get("source") == "security" for f in findings)

    logger.info(
        "generate_tests: %d findings for %s (%s), framework=%s",
        len(findings), file_path, language, effective_framework,
    )

    # ── AI test generation ────────────────────────────────────────────────────
    try:
        ai_response = ai_service.generate_tests(
            code=code,
            language=language,
            framework=effective_framework,
        )
    except Exception as exc:
        logger.error("AI test generation failed for %s: %s", file_path, exc)
        return _fallback_test_result(file_path, language, effective_framework, findings, exc)

    test_cases = [
        TestCase(
            name=tc.get("name", f"test_{i}"),
            description=tc.get("description", ""),
            category=tc.get("category", "happy_path"),
        )
        for i, tc in enumerate(ai_response.get("test_cases", []))
    ]

    # Add security-specific tests if security findings were detected
    if has_security_findings:
        test_cases.append(TestCase(
            name="test_security_input_sanitization",
            description=(
                "Verify that the function rejects or safely handles malicious / "
                "unsanitised inputs identified by static security analysis."
            ),
            category="security",
        ))

    return TestResult(
        file=file_path,
        language=language,
        framework=ai_response.get("framework_used", effective_framework),
        test_cases=test_cases,
        test_code=ai_response.get("test_code", ""),
        security_tests=has_security_findings,
    )


def generate_tests_from_diff(
    changed_files: list,
    framework: str | None = None,
) -> list[TestResult]:
    """
    Generate test scaffolding for all files in a parsed diff.
    Returns only files where test code was produced.
    """
    from app.services.diff_service import reconstruct_new_source

    results: list[TestResult] = []
    for cf in changed_files:
        source = reconstruct_new_source(cf)
        if not source.strip():
            continue
        result = generate_tests(
            code=source,
            language=cf.language,
            file_path=cf.path,
            framework=framework,
        )
        if result.test_code or result.test_cases:
            results.append(result)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Graceful degradation
# ─────────────────────────────────────────────────────────────────────────────

def _fallback_test_result(
    file_path: str,
    language: str,
    framework: str,
    findings: list[dict],
    exc: Exception,
) -> TestResult:
    """
    Return a minimal test plan derived from static findings when AI fails.
    """
    test_cases: list[TestCase] = [
        TestCase(
            name="test_happy_path",
            description="Verify normal expected behaviour with valid inputs.",
            category="happy_path",
        ),
        TestCase(
            name="test_edge_case_empty_input",
            description="Verify behaviour with empty or None inputs.",
            category="edge_case",
        ),
        TestCase(
            name="test_error_handling",
            description="Verify that exceptions are raised or handled appropriately.",
            category="error",
        ),
    ]

    for f in findings[:3]:
        test_cases.append(TestCase(
            name=f"test_regression_{f.get('rule', 'finding').lower().replace('-', '_')}",
            description=f"Regression test for: {f.get('message', 'static finding')}",
            category="regression",
        ))

    return TestResult(
        file=file_path,
        language=language,
        framework=framework,
        test_cases=test_cases,
        test_code=f"# AI test generation unavailable: {exc}\n# Implement the test cases listed above manually.",
        security_tests=any(f.get("source") == "security" for f in findings),
    )
