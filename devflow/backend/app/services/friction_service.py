"""
Friction service — tracks and aggregates developer-friction metrics.

Friction metrics capture everything that slows engineers down:
  - Time-to-review (PR open → first review)
  - Time-to-merge  (PR open → merged)
  - Review cycles  (number of review round-trips per PR)
  - CI failure rate per repository
  - Finding recurrence rate (same issue re-introduced after fix)
  - Hotspot churn (files changed repeatedly in a short period)

Data is recorded into the FrictionLog table and aggregated on-demand.
All calculations are purely statistical — no AI is involved.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models import FrictionLog, PullRequest, Repository

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Domain types
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MetricItem:
    metric: str
    value:  float
    unit:   str

    def to_dict(self) -> dict:
        return {"metric": self.metric, "value": self.value, "unit": self.unit}


@dataclass
class FrictionReport:
    repository:  str
    period_days: int
    metrics:     list[MetricItem]
    recorded_at: datetime

    def to_dict(self) -> dict:
        return {
            "repository":  self.repository,
            "period_days": self.period_days,
            "metrics":     [m.to_dict() for m in self.metrics],
            "recorded_at": self.recorded_at.isoformat(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _hours_between(a: datetime | None, b: datetime | None) -> float | None:
    """Return hours between two datetimes, or None if either is missing."""
    if a is None or b is None:
        return None
    delta = b - a
    return max(delta.total_seconds() / 3600, 0.0)


def _safe_avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Service
# ─────────────────────────────────────────────────────────────────────────────

class FrictionService:

    # ── Recording ─────────────────────────────────────────────────────────────

    def record_pr_metrics(self, pr: PullRequest, db: Session) -> None:
        """
        Calculate and record friction metrics for a single pull request.
        Called after a PR is closed/merged (e.g. from GitHub webhook).
        """
        if pr.merged_at is None and pr.closed_at is None:
            return  # PR still open — nothing to record yet

        close_time = pr.merged_at or pr.closed_at
        ttr_hours  = _hours_between(pr.created_at, close_time)

        if ttr_hours is not None:
            db.add(FrictionLog(
                repository=pr.repository,
                metric_name="time_to_merge_hours",
                metric_value=ttr_hours,
                pr_number=pr.pr_number,
                recorded_at=datetime.now(timezone.utc),
            ))

        review_cycles = getattr(pr, "review_cycles", None)
        if review_cycles is not None:
            db.add(FrictionLog(
                repository=pr.repository,
                metric_name="review_cycles",
                metric_value=float(review_cycles),
                pr_number=pr.pr_number,
                recorded_at=datetime.now(timezone.utc),
            ))

        db.commit()
        logger.debug("Recorded friction metrics for PR #%s in %s", pr.pr_number, pr.repository)

    def record_raw(
        self,
        repository: str,
        metric_name: str,
        metric_value: float,
        db: Session,
        pr_number: int | None = None,
    ) -> None:
        """Record a single arbitrary friction metric."""
        db.add(FrictionLog(
            repository=repository,
            metric_name=metric_name,
            metric_value=metric_value,
            pr_number=pr_number,
            recorded_at=datetime.now(timezone.utc),
        ))
        db.commit()

    # ── Aggregation ───────────────────────────────────────────────────────────

    def get_metrics(
        self,
        repository: str,
        db: Session,
        period_days: int = 30,
    ) -> FrictionReport:
        """
        Aggregate friction metrics for *repository* over the last *period_days*.

        Returns a :class:`FrictionReport` with the following metrics:
        - avg_time_to_merge_hours
        - avg_review_cycles
        - total_prs_analysed
        - p90_time_to_merge_hours   (90th-percentile merge time)
        - finding_recurrence_rate   (% findings seen in >1 analysis)
        """
        since = datetime.now(timezone.utc) - timedelta(days=period_days)

        rows = (
            db.query(FrictionLog)
            .filter(
                FrictionLog.repository == repository,
                FrictionLog.recorded_at >= since,
            )
            .all()
        )

        # Group by metric name
        grouped: dict[str, list[float]] = {}
        for row in rows:
            grouped.setdefault(row.metric_name, []).append(row.metric_value)

        metrics: list[MetricItem] = []

        # avg_time_to_merge_hours
        ttm = grouped.get("time_to_merge_hours", [])
        metrics.append(MetricItem(
            metric="avg_time_to_merge_hours",
            value=round(_safe_avg(ttm), 2),
            unit="hours",
        ))

        # p90_time_to_merge_hours
        if ttm:
            sorted_ttm = sorted(ttm)
            p90_idx = max(0, int(len(sorted_ttm) * 0.9) - 1)
            metrics.append(MetricItem(
                metric="p90_time_to_merge_hours",
                value=round(sorted_ttm[p90_idx], 2),
                unit="hours",
            ))
        else:
            metrics.append(MetricItem(metric="p90_time_to_merge_hours", value=0.0, unit="hours"))

        # avg_review_cycles
        rc = grouped.get("review_cycles", [])
        metrics.append(MetricItem(
            metric="avg_review_cycles",
            value=round(_safe_avg(rc), 2),
            unit="cycles",
        ))

        # total_prs_analysed (distinct PR numbers)
        pr_numbers = {r.pr_number for r in rows if r.pr_number is not None}
        metrics.append(MetricItem(
            metric="total_prs_analysed",
            value=float(len(pr_numbers)),
            unit="count",
        ))

        # finding_recurrence_rate — computed from DB (findings seen in >1 analysis for this repo)
        recurrence_rate = self._finding_recurrence_rate(repository, since, db)
        metrics.append(MetricItem(
            metric="finding_recurrence_rate",
            value=round(recurrence_rate, 4),
            unit="ratio",
        ))

        return FrictionReport(
            repository=repository,
            period_days=period_days,
            metrics=metrics,
            recorded_at=datetime.now(timezone.utc),
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _finding_recurrence_rate(
        self,
        repository: str,
        since: datetime,
        db: Session,
    ) -> float:
        """
        Ratio of recurring finding titles to total unique finding titles
        for this repository in the given time window.
        """
        from app.models import Finding, CodeAnalysis  # local import avoids circular
        try:
            # Count distinct finding titles that appear in >1 analysis
            recurring = (
                db.query(Finding.title)
                .join(CodeAnalysis, Finding.analysis_id == CodeAnalysis.id)
                .filter(
                    CodeAnalysis.repository == repository,
                    CodeAnalysis.created_at >= since,
                )
                .group_by(Finding.title)
                .having(func.count(Finding.title) > 1)
                .count()
            )
            total = (
                db.query(func.count(func.distinct(Finding.title)))
                .join(CodeAnalysis, Finding.analysis_id == CodeAnalysis.id)
                .filter(
                    CodeAnalysis.repository == repository,
                    CodeAnalysis.created_at >= since,
                )
                .scalar() or 0
            )
            return recurring / total if total > 0 else 0.0
        except Exception as exc:
            logger.warning("Could not compute recurrence rate: %s", exc)
            return 0.0
