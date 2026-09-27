"""
Pydantic request/response schemas for all DevFlow CodeLens API operations.
All schemas use strict validation via model_config.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ─────────────────────────────────────────────────────────────────────────────
# Shared base
# ─────────────────────────────────────────────────────────────────────────────

class _StrictModel(BaseModel):
    model_config = ConfigDict(strict=True, from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────

class LoginRequest(_StrictModel):
    email: EmailStr
    password: str = Field(min_length=8)


class TokenResponse(_StrictModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(_StrictModel):
    id: str
    email: str
    full_name: str | None
    is_active: bool
    created_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# Analysis
# ─────────────────────────────────────────────────────────────────────────────

class AnalysisRequest(_StrictModel):
    repository: str = Field(description="Full repository name, e.g. 'acme/api'")
    branch: str = Field(description="Branch to analyse")
    commit_sha: str | None = Field(default=None, description="Specific commit SHA; defaults to HEAD of branch")
    base_branch: str = Field(default="main", description="Base branch for diff comparison")


Severity = Literal["critical", "high", "medium", "low"]
FindingType = Literal["bug", "security", "optimization", "structure"]
FindingSource = Literal["static", "ai"]


class FindingResponse(_StrictModel):
    id: str
    severity: Severity
    finding_type: FindingType
    file_path: str | None
    line_number: int | None
    title: str
    explanation: str | None
    recommendation: str | None
    source: FindingSource
    created_at: datetime


class AnalysisResponse(_StrictModel):
    id: str
    status: str
    files_analyzed: int
    issues_detected: int
    analysis_duration_ms: int | None
    findings: list[FindingResponse]
    created_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# Debugging
# ─────────────────────────────────────────────────────────────────────────────

class DebuggingRequest(_StrictModel):
    code: str = Field(description="Code snippet containing the bug or error")
    error_message: str | None = Field(default=None, description="Error trace or message if available")
    language: str = Field(default="python", description="Programming language of the code")


class DebuggingResponse(_StrictModel):
    root_cause: str
    explanation: str
    fix_suggestion: str
    fixed_code: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Optimization
# ─────────────────────────────────────────────────────────────────────────────

class OptimizationRequest(_StrictModel):
    code: str = Field(description="Code to optimise")
    language: str = Field(default="python")
    context: str | None = Field(default=None, description="Optional surrounding context")


class OptimizationSuggestionItem(_StrictModel):
    file_path: str | None
    suggestion: str
    rationale: str | None


class OptimizationResponse(_StrictModel):
    suggestions: list[OptimizationSuggestionItem]
    optimized_code: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Testing
# ─────────────────────────────────────────────────────────────────────────────

class TestingRequest(_StrictModel):
    code: str = Field(description="Code to generate tests for")
    language: str = Field(default="python")
    framework: str | None = Field(default=None, description="Test framework, e.g. 'pytest', 'jest'")


class TestingResponse(_StrictModel):
    test_code: str
    test_file_path: str | None = None
    framework_used: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Summaries
# ─────────────────────────────────────────────────────────────────────────────

class PRDescriptionRequest(_StrictModel):
    repository: str
    branch: str
    commit_sha: str | None = None


class PRDescriptionResponse(_StrictModel):
    title: str
    summary: str
    changes: list[str]
    testing_notes: str | None = None
    full_description: str


class ReturnSummaryRequest(_StrictModel):
    repository: str
    since_date: datetime = Field(description="Summarise activity since this date")
    branch: str = Field(default="main")


class ReturnSummaryResponse(_StrictModel):
    period: str
    highlights: list[str]
    pull_requests_merged: int
    issues_closed: int
    full_summary: str


# ─────────────────────────────────────────────────────────────────────────────
# GitHub
# ─────────────────────────────────────────────────────────────────────────────

class GitHubWebhookPayload(_StrictModel):
    """Minimal shape of an inbound GitHub push/PR webhook. Extra fields ignored."""
    model_config = ConfigDict(extra="ignore", strict=False)

    action: str | None = None
    ref: str | None = None
    repository: dict | None = None
    pull_request: dict | None = None
    sender: dict | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Jira
# ─────────────────────────────────────────────────────────────────────────────

class JiraDraftRequest(_StrictModel):
    finding_id: str


class JiraDraftResponse(_StrictModel):
    finding_id: str
    jira_issue_key: str | None
    jira_issue_url: str | None
    status: str   # draft | created | failed
    title: str
    description: str


# ─────────────────────────────────────────────────────────────────────────────
# Analytics / Friction
# ─────────────────────────────────────────────────────────────────────────────

class FrictionMetricItem(_StrictModel):
    metric: str
    value: float
    unit: str


class FrictionMetricsResponse(_StrictModel):
    repository: str
    period_days: int
    metrics: list[FrictionMetricItem]
    recorded_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    environment: str
