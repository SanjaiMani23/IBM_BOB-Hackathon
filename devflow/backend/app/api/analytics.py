"""
Analytics router — developer friction metrics.

GET /analytics/friction?repository=owner/repo&period_days=30
  Return aggregated friction metrics for a repository.

POST /analytics/friction/record
  Record a raw friction metric (used internally or by webhooks).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models import User
from app.services.friction_service import FrictionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────

class MetricItemOut(BaseModel):
    metric: str
    value:  float
    unit:   str


class FrictionMetricsResponse(BaseModel):
    repository:  str
    period_days: int
    metrics:     list[MetricItemOut]
    recorded_at: str


class RecordMetricRequest(BaseModel):
    repository:   str   = Field(description="Full repository name, e.g. 'acme/api'")
    metric_name:  str   = Field(description="Metric identifier, e.g. 'ci_failure'")
    metric_value: float = Field(description="Numeric value")
    pr_number:    int | None = Field(default=None, description="Optional linked PR number")


class RecordMetricResponse(BaseModel):
    recorded: bool


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/friction", response_model=FrictionMetricsResponse)
def get_friction_metrics(
    repository:  str = Query(description="Full repository name, e.g. 'acme/api'"),
    period_days: int = Query(default=30, ge=1, le=365, description="Look-back window in days"),
    db:          Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> FrictionMetricsResponse:
    """
    Return aggregated friction metrics for *repository* over the last *period_days*.

    Metrics included:
    - avg_time_to_merge_hours
    - p90_time_to_merge_hours
    - avg_review_cycles
    - total_prs_analysed
    - finding_recurrence_rate
    """
    svc    = FrictionService()
    report = svc.get_metrics(repository=repository, db=db, period_days=period_days)

    return FrictionMetricsResponse(
        repository=report.repository,
        period_days=report.period_days,
        metrics=[MetricItemOut(**m.to_dict()) for m in report.metrics],
        recorded_at=report.recorded_at.isoformat(),
    )


@router.post("/friction/record", response_model=RecordMetricResponse)
def record_metric(
    req: RecordMetricRequest,
    db:  Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> RecordMetricResponse:
    """
    Record a single friction metric value.

    Intended for internal use and CI/CD integrations (e.g. recording a CI failure).
    """
    svc = FrictionService()
    svc.record_raw(
        repository=req.repository,
        metric_name=req.metric_name,
        metric_value=req.metric_value,
        pr_number=req.pr_number,
        db=db,
    )
    logger.info("Recorded metric '%s'=%.4f for %s", req.metric_name, req.metric_value, req.repository)
    return RecordMetricResponse(recorded=True)
