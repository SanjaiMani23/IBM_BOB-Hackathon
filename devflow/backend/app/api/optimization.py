"""
Optimization router.

POST /optimize
  Accept code + language + optional context.
  Run static complexity/quality analysis then AI-assisted optimization.
  Return ranked suggestion list. Suggested code is never auto-applied.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.auth import get_current_user
from app.models import User
from app.services.optimization_service import (
    OptimizationResult,
    OptimizationSuggestion,
    optimize_code,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────

class OptimizeRequest(BaseModel):
    code:     str
    language: str = "python"
    context:  str | None = None
    file_path: str | None = None


class SuggestionOut(BaseModel):
    priority:             str
    title:                str
    current_approach:     str
    problem:              str
    recommended_approach: str
    complexity_before:    str | None
    complexity_after:     str | None
    expected_impact:      str
    suggested_code:       str | None
    trade_off:            str | None
    confidence:           float
    source:               str


class OptimizeOut(BaseModel):
    file:               str
    language:           str
    suggestions:        list[SuggestionOut]
    optimized_code:     str | None
    static_issue_count: int


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=OptimizeOut,
    summary="Analyse code for performance and structural optimization opportunities",
)
def optimize(
    body: OptimizeRequest,
    _current_user: User = Depends(get_current_user),
) -> OptimizeOut:
    """
    Returns ranked optimization suggestions from static analysis and watsonx.ai.
    Suggested code changes are presented for developer review — never applied automatically.
    """
    if not body.code.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="code must not be empty.",
        )

    result: OptimizationResult = optimize_code(
        code=body.code,
        language=body.language,
        file_path=body.file_path or "<snippet>",
        context=body.context,
    )

    return OptimizeOut(**result.to_dict())
