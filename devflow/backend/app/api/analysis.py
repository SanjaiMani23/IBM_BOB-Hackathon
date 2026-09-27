"""
Analysis router — full pipeline endpoint.

POST /analysis
  1. Fetch diff from GitHub
  2. Parse diff
  3. Run all static analyzers (syntax, security, complexity, quality)
  4. Enrich findings with AI (watsonx.ai)
  5. Persist to database
  6. Return structured response

GET /analysis/{analysis_id}
  Return a previously computed analysis result.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models import CodeAnalysis, Finding, PullRequest, Repository, User
from app.services.diff_service import parse_diff, reconstruct_new_source
from app.analyzers.syntax_analyzer import analyze_syntax
from app.analyzers.security_analyzer import analyze_security
from app.analyzers.complexity_analyzer import analyze_complexity
from app.analyzers.code_quality import analyze_quality
from app.services import ai_service
from app.services.github_service import get_github_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Request / Response schemas
# ─────────────────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    repository:   str   # e.g. "acme/checkout-service"
    branch:       str   # source branch
    base_branch:  str = "main"
    pull_request: int | None = None   # PR number (preferred over branch diff)
    commit_sha:   str | None = None


class FindingOut(BaseModel):
    id:             str
    severity:       str
    finding_type:   str
    file_path:      str | None
    line_number:    int | None
    title:          str
    explanation:    str | None
    recommendation: str | None
    source:         str
    created_at:     datetime

    model_config = {"from_attributes": True}


class AnalysisOut(BaseModel):
    id:                   str
    status:               str
    files_analyzed:       int
    issues_detected:      int
    analysis_duration_ms: int | None
    findings:             list[FindingOut]
    created_at:           datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Severity helpers
# ─────────────────────────────────────────────────────────────────────────────

_SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _top_severity(severities: list[str]) -> str:
    if not severities:
        return "low"
    return min(severities, key=lambda s: _SEV_ORDER.get(s, 3))


# ─────────────────────────────────────────────────────────────────────────────
# Core pipeline (sync — runs inline; can be moved to background for large diffs)
# ─────────────────────────────────────────────────────────────────────────────

def _run_pipeline(
    owner: str,
    repo: str,
    branch: str,
    base_branch: str,
    pr_number: int | None,
    db: Session,
) -> CodeAnalysis:
    """
    Execute the full analysis pipeline and persist results.

    Returns the saved :class:`CodeAnalysis` ORM instance.
    """
    t_start = time.perf_counter()
    svc = get_github_service()

    # ── 1. Fetch diff ─────────────────────────────────────────────────────────
    try:
        if pr_number is not None:
            raw_diff = svc.get_pull_request_diff(owner, repo, pr_number)
        else:
            raw_diff = svc.get_compare_diff(owner, repo, base_branch, branch)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch diff from GitHub: {exc}")

    # ── 2. Parse diff ─────────────────────────────────────────────────────────
    parsed = parse_diff(raw_diff)

    # ── 3. Ensure PR / repository records exist ───────────────────────────────
    full_name = f"{owner}/{repo}"
    db_repo = db.query(Repository).filter(Repository.full_name == full_name).first()
    if db_repo is None:
        db_repo = Repository(
            full_name=full_name,
            default_branch=base_branch,
            owner_id="system",   # replaced when auth is fully wired
        )
        db.add(db_repo)
        db.flush()

    db_pr = PullRequest(
        repository_id=db_repo.id,
        github_pr_number=pr_number,
        branch=branch,
        base_branch=base_branch,
        state="open",
    )
    db.add(db_pr)
    db.flush()

    db_analysis = CodeAnalysis(
        pull_request_id=db_pr.id,
        status="running",
    )
    db.add(db_analysis)
    db.flush()

    # ── 4. Run static analyzers ───────────────────────────────────────────────
    all_findings: list[Finding] = []

    for cf in parsed.files:
        source = reconstruct_new_source(cf)
        if not source.strip():
            continue

        # syntax
        for f in analyze_syntax(source, cf.language, cf.path):
            all_findings.append(Finding(
                analysis_id=db_analysis.id,
                severity=f.severity,
                finding_type="bug",
                file_path=cf.path,
                line_number=f.line,
                title=f.message,
                explanation=f.explanation,
                recommendation="Fix the syntax error.",
                source="static",
            ))

        # security
        for f in analyze_security(source, cf.language, cf.path):
            all_findings.append(Finding(
                analysis_id=db_analysis.id,
                severity=f.severity,
                finding_type="security",
                file_path=cf.path,
                line_number=f.line,
                title=f.message,
                explanation=f.message,
                recommendation=f.recommendation,
                source="static",
            ))

        # complexity
        for f in analyze_complexity(source, cf.language, cf.path):
            all_findings.append(Finding(
                analysis_id=db_analysis.id,
                severity=f.severity,
                finding_type="optimization",
                file_path=cf.path,
                line_number=f.line,
                title=f.message,
                explanation=f.message,
                recommendation=f.recommendation,
                source="static",
            ))

        # quality
        for f in analyze_quality(source, cf.language, cf.path):
            all_findings.append(Finding(
                analysis_id=db_analysis.id,
                severity=f.severity,
                finding_type="structure",
                file_path=cf.path,
                line_number=f.line,
                title=f.message,
                explanation=f.explanation,
                recommendation=f.recommendation,
                source="static",
            ))

    # ── 5. AI enrichment — enhance top findings with explanations ─────────────
    _enrich_with_ai(all_findings, parsed.files)

    # ── 6. Persist ────────────────────────────────────────────────────────────
    for f in all_findings:
        db.add(f)

    duration_ms = int((time.perf_counter() - t_start) * 1000)
    db_analysis.files_analyzed  = len(parsed.files)
    db_analysis.issues_detected = len(all_findings)
    db_analysis.analysis_duration_ms = duration_ms
    db_analysis.status = "done"

    db.commit()
    db.refresh(db_analysis)
    logger.info(
        "Analysis complete: id=%s files=%d findings=%d duration=%dms",
        db_analysis.id, db_analysis.files_analyzed,
        db_analysis.issues_detected, duration_ms,
    )
    return db_analysis


def _enrich_with_ai(findings: list[Finding], changed_files: list) -> None:
    """
    Use watsonx.ai to add richer explanations to high/critical findings.
    Runs silently — failures are logged but do not abort the pipeline.
    """
    high_sev = [f for f in findings if f.severity in ("critical", "high")]
    if not high_sev or not changed_files:
        return

    # Pick the first changed file with source as representative context
    representative_file = changed_files[0]
    source = reconstruct_new_source(representative_file)
    if not source.strip():
        return

    static_ctx = [
        {"severity": f.severity, "title": f.title, "file_path": f.file_path, "line": f.line_number}
        for f in high_sev[:5]
    ]

    try:
        ai_resp = ai_service.analyze_for_debugging(
            code=source,
            error_message=None,
            language=representative_file.language,
            static_findings=static_ctx,
        )
        # Attach AI explanation to the top finding only (avoid over-inflation)
        if high_sev and ai_resp.get("explanation"):
            high_sev[0].explanation = ai_resp["explanation"]
            high_sev[0].recommendation = ai_resp.get("suggested_fix") or high_sev[0].recommendation
            high_sev[0].source = "ai"
    except Exception as exc:
        logger.warning("AI enrichment failed: %s", exc)


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=AnalysisOut,
    status_code=status.HTTP_201_CREATED,
    summary="Run full analysis pipeline on a PR or branch diff",
)
def run_analysis(
    body: AnalyzeRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> AnalysisOut:
    """
    Trigger the complete analysis pipeline:
    GitHub diff → parse → static analyzers → AI enrichment → database → response.
    """
    parts = body.repository.split("/")
    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="repository must be in 'owner/repo' format.",
        )
    owner, repo = parts

    db_analysis = _run_pipeline(
        owner=owner,
        repo=repo,
        branch=body.branch,
        base_branch=body.base_branch,
        pr_number=body.pull_request,
        db=db,
    )
    return AnalysisOut.model_validate(db_analysis)


@router.get(
    "/{analysis_id}",
    response_model=AnalysisOut,
    summary="Retrieve a previously computed analysis result",
)
def get_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> AnalysisOut:
    db_analysis = db.query(CodeAnalysis).filter(CodeAnalysis.id == analysis_id).first()
    if db_analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found.")
    return AnalysisOut.model_validate(db_analysis)
