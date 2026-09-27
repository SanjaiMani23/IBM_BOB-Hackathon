"""
SQLAlchemy ORM models for DevFlow CodeLens.

Hierarchy:
    User → Repository → PullRequest → CodeAnalysis → Finding
    Finding ─(optional)→ JiraTicket
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _uuid() -> str:
    return str(uuid.uuid4())


# ─────────────────────────────────────────────────────────────────────────────
# User
# ─────────────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    repositories: Mapped[list["Repository"]] = relationship(
        "Repository", back_populates="owner", cascade="all, delete-orphan"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Repository
# ─────────────────────────────────────────────────────────────────────────────

class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g. "acme/api"
    github_url: Mapped[str] = mapped_column(String(512), nullable=True)
    default_branch: Mapped[str] = mapped_column(String(255), default="main")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship("User", back_populates="repositories")
    pull_requests: Mapped[list["PullRequest"]] = relationship(
        "PullRequest", back_populates="repository", cascade="all, delete-orphan"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Pull Request
# ─────────────────────────────────────────────────────────────────────────────

class PullRequest(Base):
    __tablename__ = "pull_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    repository_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("repositories.id"), nullable=False, index=True
    )
    github_pr_number: Mapped[int] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=True)
    branch: Mapped[str] = mapped_column(String(255), nullable=False)
    base_branch: Mapped[str] = mapped_column(String(255), default="main")
    commit_sha: Mapped[str] = mapped_column(String(40), nullable=True)
    state: Mapped[str] = mapped_column(String(50), default="open")  # open | closed | merged
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    merged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    repository: Mapped["Repository"] = relationship("Repository", back_populates="pull_requests")
    analyses: Mapped[list["CodeAnalysis"]] = relationship(
        "CodeAnalysis", back_populates="pull_request", cascade="all, delete-orphan"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Code Analysis
# ─────────────────────────────────────────────────────────────────────────────

class CodeAnalysis(Base):
    __tablename__ = "code_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    pull_request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pull_requests.id"), nullable=False, index=True
    )
    files_analyzed: Mapped[int] = mapped_column(Integer, default=0)
    issues_detected: Mapped[int] = mapped_column(Integer, default=0)
    analysis_duration_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending | running | done | failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    pull_request: Mapped["PullRequest"] = relationship("PullRequest", back_populates="analyses")
    findings: Mapped[list["Finding"]] = relationship(
        "Finding", back_populates="analysis", cascade="all, delete-orphan"
    )
    optimization_suggestions: Mapped[list["OptimizationSuggestion"]] = relationship(
        "OptimizationSuggestion", back_populates="analysis", cascade="all, delete-orphan"
    )
    test_checklists: Mapped[list["TestChecklist"]] = relationship(
        "TestChecklist", back_populates="analysis", cascade="all, delete-orphan"
    )
    summaries: Mapped[list["Summary"]] = relationship(
        "Summary", back_populates="analysis", cascade="all, delete-orphan"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Finding
# ─────────────────────────────────────────────────────────────────────────────

class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("code_analyses.id"), nullable=False, index=True
    )
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # critical | high | medium | low
    finding_type: Mapped[str] = mapped_column(String(50), nullable=False)  # bug | security | optimization | structure
    file_path: Mapped[str] = mapped_column(String(512), nullable=True)
    line_number: Mapped[int] = mapped_column(Integer, nullable=True)
    commit_sha: Mapped[str] = mapped_column(String(40), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="static")  # static | ai
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    analysis: Mapped["CodeAnalysis"] = relationship("CodeAnalysis", back_populates="findings")
    jira_ticket: Mapped["JiraTicket"] = relationship(
        "JiraTicket", back_populates="finding", uselist=False, cascade="all, delete-orphan"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Optimization Suggestion
# ─────────────────────────────────────────────────────────────────────────────

class OptimizationSuggestion(Base):
    __tablename__ = "optimization_suggestions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("code_analyses.id"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(String(512), nullable=True)
    suggestion: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    analysis: Mapped["CodeAnalysis"] = relationship("CodeAnalysis", back_populates="optimization_suggestions")


# ─────────────────────────────────────────────────────────────────────────────
# Test Checklist
# ─────────────────────────────────────────────────────────────────────────────

class TestChecklist(Base):
    __tablename__ = "test_checklists"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("code_analyses.id"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(String(512), nullable=True)
    test_cases: Mapped[str] = mapped_column(Text, nullable=False)   # AI-generated test scaffold (markdown / code)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    analysis: Mapped["CodeAnalysis"] = relationship("CodeAnalysis", back_populates="test_checklists")


# ─────────────────────────────────────────────────────────────────────────────
# Jira Ticket
# ─────────────────────────────────────────────────────────────────────────────

class JiraTicket(Base):
    __tablename__ = "jira_tickets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    finding_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("findings.id"), nullable=False, unique=True, index=True
    )
    jira_issue_key: Mapped[str] = mapped_column(String(50), nullable=True)   # e.g. "PROJ-42"
    jira_issue_url: Mapped[str] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft")         # draft | created | failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    finding: Mapped["Finding"] = relationship("Finding", back_populates="jira_ticket")


# ─────────────────────────────────────────────────────────────────────────────
# Summary  (PR description or return-to-work summary)
# ─────────────────────────────────────────────────────────────────────────────

class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("code_analyses.id"), nullable=False, index=True
    )
    summary_type: Mapped[str] = mapped_column(String(50), nullable=False)  # pr_description | return_summary
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    analysis: Mapped["CodeAnalysis"] = relationship("CodeAnalysis", back_populates="summaries")


# ─────────────────────────────────────────────────────────────────────────────
# Friction Log  (developer friction / analytics events)
# ─────────────────────────────────────────────────────────────────────────────

class FrictionLog(Base):
    __tablename__ = "friction_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    repository_id: Mapped[str] = mapped_column(String(36), ForeignKey("repositories.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)  # pr_opened | pr_merged | review_lag | etc.
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=True)        # arbitrary JSON string
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    repository: Mapped["Repository"] = relationship("Repository")
