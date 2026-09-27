"""
Debugging router.

POST /debug
  Accept code + optional error message.
  Run static analysis then watsonx.ai root-cause analysis.
  Return structured debug result.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.auth import get_current_user
from app.models import User
from app.services.debug_service import DebugResult, debug_code

logger = logging.getLogger(__name__)
router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────

class DebugRequest(BaseModel):
    code:          str
    language:      str = "python"
    error_message: str | None = None
    file_path:     str | None = None


class DebugOut(BaseModel):
    root_cause:           str
    explanation:          str
    evidence:             list[str]
    suggested_fix:        str
    confidence:           str
    severity:             str
    static_finding_count: int


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=DebugOut,
    summary="Identify root cause and suggest a fix for a code snippet",
)
def debug(
    body: DebugRequest,
    _current_user: User = Depends(get_current_user),
) -> DebugOut:
    """
    Run static analysis then ask watsonx.ai to identify the root cause.

    The AI distinguishes between confirmed, likely, and possible issues.
    Speculation is never presented as certainty.
    """
    if not body.code.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="code must not be empty.",
        )

    result: DebugResult = debug_code(
        code=body.code,
        language=body.language,
        file_path=body.file_path or "<snippet>",
        error_message=body.error_message,
    )

    return DebugOut(**result.to_dict())
