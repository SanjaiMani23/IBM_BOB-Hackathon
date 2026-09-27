"""
Deterministic security analyzer.

Scans source code for common vulnerability patterns using regex-based rules
inspired by Semgrep. All findings include a confidence level — findings with
weak evidence are reported as LOW confidence, not suppressed.

Categories detected:
  - hardcoded secrets / credentials
  - SQL injection risks
  - command injection
  - unsafe deserialization
  - insecure subprocess usage
  - dangerous dynamic execution (eval / exec)
  - weak cryptography
  - unsafe file operations
  - exposed API keys / tokens
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Output type
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SecurityFinding:
    category:       str = "security"
    severity:       str = "high"
    file:           str = ""
    line:           int | None = None
    rule:           str = ""
    message:        str = ""
    recommendation: str = ""
    confidence:     float = 0.9
    source:         str = "static"

    def to_dict(self) -> dict:
        return {
            "category":       self.category,
            "severity":       self.severity,
            "file":           self.file,
            "line":           self.line,
            "rule":           self.rule,
            "message":        self.message,
            "recommendation": self.recommendation,
            "confidence":     self.confidence,
            "source":         self.source,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Rule definitions
# Each rule: (rule_id, severity, pattern, message, recommendation, confidence)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class _Rule:
    rule_id:        str
    severity:       str
    pattern:        re.Pattern
    message:        str
    recommendation: str
    confidence:     float
    # Optional: languages this rule applies to (empty = all languages)
    languages:      frozenset[str] = field(default_factory=frozenset)


_RULES: list[_Rule] = [

    # ── Hardcoded secrets ─────────────────────────────────────────────────
    _Rule(
        rule_id="SEC001",
        severity="critical",
        pattern=re.compile(
            r'(?i)(?:password|passwd|pwd|secret|api[_-]?key|auth[_-]?token)\s*=\s*["\'][^"\']{4,}["\']'
        ),
        message="Hardcoded credential detected",
        recommendation=(
            "Move credentials to environment variables and load them via os.environ "
            "or a secrets manager. Never commit credentials to source control."
        ),
        confidence=0.85,
    ),
    _Rule(
        rule_id="SEC002",
        severity="critical",
        pattern=re.compile(
            r'(?i)(?:aws_access_key_id|aws_secret|AKIA[0-9A-Z]{16})'
        ),
        message="AWS credential pattern detected",
        recommendation="Rotate the key immediately. Use IAM roles or AWS Secrets Manager.",
        confidence=0.95,
    ),
    _Rule(
        rule_id="SEC003",
        severity="high",
        pattern=re.compile(
            r'(?i)(?:private_key|rsa_key|ssh_key)\s*=\s*["\']'
        ),
        message="Possible hardcoded private key",
        recommendation="Load private keys from a secure key store or environment variable.",
        confidence=0.80,
    ),

    # ── SQL injection ─────────────────────────────────────────────────────
    _Rule(
        rule_id="SEC010",
        severity="critical",
        pattern=re.compile(
            r'(?:execute|query|raw)\s*\(\s*["\'].*%[sf].*["\']'
            r'|f["\'].*SELECT.*{.*}.*["\']'
            r'|["\'].*SELECT.*["\'].*%.*(?:user|id|name|input)'
        ),
        message="Possible SQL injection via string formatting",
        recommendation="Use parameterised queries or an ORM. Never interpolate user input into SQL.",
        confidence=0.80,
        languages=frozenset({"python", "javascript", "typescript", "java"}),
    ),
    _Rule(
        rule_id="SEC011",
        severity="critical",
        pattern=re.compile(
            r'`[^`]*\$\{[^}]*\}[^`]*(?:SELECT|INSERT|UPDATE|DELETE|DROP)',
            re.IGNORECASE,
        ),
        message="SQL query built with template literal — SQL injection risk",
        recommendation="Use parameterised queries ($1, $2, ...) with pg, mysql2, or a query builder.",
        confidence=0.90,
        languages=frozenset({"javascript", "typescript"}),
    ),

    # ── Command injection ─────────────────────────────────────────────────
    _Rule(
        rule_id="SEC020",
        severity="critical",
        pattern=re.compile(
            r'subprocess\.(?:call|run|Popen|check_output)\s*\([^)]*shell\s*=\s*True'
        ),
        message="subprocess called with shell=True — command injection risk",
        recommendation=(
            "Pass arguments as a list and set shell=False. "
            "If shell=True is necessary, sanitise all user-supplied input with shlex.quote()."
        ),
        confidence=0.95,
        languages=frozenset({"python"}),
    ),
    _Rule(
        rule_id="SEC021",
        severity="high",
        pattern=re.compile(
            r'os\.system\s*\([^)]*(?:request|input|param|arg|query)',
            re.IGNORECASE,
        ),
        message="os.system called with possibly unsanitised input",
        recommendation="Use subprocess with a list of arguments instead of os.system.",
        confidence=0.75,
        languages=frozenset({"python"}),
    ),

    # ── Unsafe deserialization ────────────────────────────────────────────
    _Rule(
        rule_id="SEC030",
        severity="critical",
        pattern=re.compile(r'\bpickle\.loads?\s*\('),
        message="pickle.load/loads is unsafe with untrusted data",
        recommendation=(
            "Never unpickle data from untrusted sources. "
            "Use JSON, MessagePack, or a signed serialisation format instead."
        ),
        confidence=0.90,
        languages=frozenset({"python"}),
    ),
    _Rule(
        rule_id="SEC031",
        severity="high",
        pattern=re.compile(r'\byaml\.load\s*\([^)]*(?!Loader=yaml\.SafeLoader)'),
        message="yaml.load without SafeLoader — arbitrary code execution risk",
        recommendation="Use yaml.safe_load() or yaml.load(data, Loader=yaml.SafeLoader).",
        confidence=0.85,
        languages=frozenset({"python"}),
    ),

    # ── Dynamic execution ─────────────────────────────────────────────────
    _Rule(
        rule_id="SEC040",
        severity="high",
        pattern=re.compile(r'\beval\s*\('),
        message="eval() detected — dynamic code execution risk",
        recommendation=(
            "Avoid eval(). If dynamic evaluation is required, "
            "use ast.literal_eval() for safe literal parsing."
        ),
        confidence=0.85,
    ),
    _Rule(
        rule_id="SEC041",
        severity="high",
        pattern=re.compile(r'\bexec\s*\('),
        message="exec() detected — arbitrary code execution risk",
        recommendation="Remove exec(). Consider alternatives such as importlib or explicit dispatch.",
        confidence=0.80,
        languages=frozenset({"python", "javascript"}),
    ),

    # ── Weak cryptography ─────────────────────────────────────────────────
    _Rule(
        rule_id="SEC050",
        severity="high",
        pattern=re.compile(r'\bhashlib\.(?:md5|sha1)\s*\('),
        message="Weak hash algorithm (MD5/SHA-1) used",
        recommendation="Use SHA-256 or stronger (hashlib.sha256). MD5 and SHA-1 are cryptographically broken.",
        confidence=0.90,
        languages=frozenset({"python"}),
    ),
    _Rule(
        rule_id="SEC051",
        severity="medium",
        pattern=re.compile(r'(?i)(?:DES|RC4|MD5|SHA1)\s*[\(=]'),
        message="Weak or deprecated cryptographic algorithm reference",
        recommendation="Use AES-GCM (symmetric) or RSA-2048+/ECDSA (asymmetric). Avoid DES, RC4, MD5, SHA-1.",
        confidence=0.70,
    ),

    # ── Unsafe file operations ────────────────────────────────────────────
    _Rule(
        rule_id="SEC060",
        severity="medium",
        pattern=re.compile(
            r'open\s*\([^)]*(?:request|input|param|arg|query)',
            re.IGNORECASE,
        ),
        message="File opened with possibly unsanitised path",
        recommendation=(
            "Validate and sanitise all file paths. "
            "Use pathlib.Path.resolve() and check the path is within an allowed directory."
        ),
        confidence=0.65,
        languages=frozenset({"python"}),
    ),
    _Rule(
        rule_id="SEC061",
        severity="high",
        pattern=re.compile(r'(?i)\.\./|path\.\.'),
        message="Possible path traversal pattern",
        recommendation=(
            "Never use user input to construct file paths directly. "
            "Resolve to an absolute path and verify it stays within the intended root."
        ),
        confidence=0.75,
    ),

    # ── Exposed tokens / generic secrets ─────────────────────────────────
    _Rule(
        rule_id="SEC070",
        severity="high",
        pattern=re.compile(
            r'(?i)(?:bearer|token|Authorization)\s*[=:]\s*["\'][A-Za-z0-9\-._~+/]{20,}["\']'
        ),
        message="Possible hardcoded auth token or bearer credential",
        recommendation="Store tokens in environment variables or a secrets manager.",
        confidence=0.75,
    ),

    # ── Debug / development flags left in code ────────────────────────────
    _Rule(
        rule_id="SEC080",
        severity="medium",
        pattern=re.compile(r'(?i)DEBUG\s*=\s*True'),
        message="DEBUG=True left in code",
        recommendation=(
            "Ensure DEBUG is set via environment variable and defaults to False in production."
        ),
        confidence=0.95,
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# Analyzer
# ─────────────────────────────────────────────────────────────────────────────

def analyze_security(
    source: str,
    language: str,
    file_path: str,
) -> list[SecurityFinding]:
    """
    Run all applicable security rules against *source*.

    Args:
        source:    Full (or reconstructed) source text.
        language:  Language name normalised to lowercase (e.g. ``"python"``).
        file_path: File path for reporting.

    Returns:
        List of :class:`SecurityFinding` objects, one per matched line per rule.
        Lines that match multiple rules produce multiple findings.
    """
    if not source.strip():
        return []

    findings: list[SecurityFinding] = []
    source_lines = source.splitlines()

    for rule in _RULES:
        # Skip rules that target a different language
        if rule.languages and language not in rule.languages:
            continue

        for lineno, line in enumerate(source_lines, start=1):
            if rule.pattern.search(line):
                findings.append(SecurityFinding(
                    severity=rule.severity,
                    file=file_path,
                    line=lineno,
                    rule=rule.rule_id,
                    message=rule.message,
                    recommendation=rule.recommendation,
                    confidence=rule.confidence,
                ))

    return findings


def analyze_security_from_diff(changed_files: list) -> list[SecurityFinding]:
    """
    Run security analysis over all files in a parsed diff.
    Only scans the *changed* (add + context) lines reconstructed from the diff,
    not the full repository.
    """
    from app.services.diff_service import reconstruct_new_source

    all_findings: list[SecurityFinding] = []
    for cf in changed_files:
        source = reconstruct_new_source(cf)
        findings = analyze_security(source, cf.language, cf.path)
        all_findings.extend(findings)
    return all_findings
