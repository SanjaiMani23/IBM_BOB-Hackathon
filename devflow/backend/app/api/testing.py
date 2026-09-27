"""
Testing router.

POST /testing
  Accept code + language + optional framework.
  Generate test plan (test cases) and optional test scaffolding via watsonx.ai.
  Generated tests have NOT been executed — disclaimer is always included.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.auth import get_current_user
from app.models import User
from app.services.test_service import TestCase, TestResult, generate_tests

logger = logging.getLogger(__name__)
router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────

class TestingRequest(BaseModel):
    code:      str
    language:  str = "python"
    framework: str | None = None
    file_path: str | None = None


class TestCaseOut(BaseModel):
    name:        str
    description: str
    category:    str


class TestingOut(BaseModel):
    file:           str
    language:       str
    framework:      str
    test_cases:     list[TestCaseOut]
    test_code:      str
    security_tests: bool
    disclaimer:     str


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=TestingOut,
    summary="Generate a test plan and optional scaffolding for a code snippet",
)
def generate(
    body: TestingRequest,
    _current_user: User = Depends(get_current_user),
) -> TestingOut:
    """
    Generates test cases (happy path, edge case, error, regression, security)
    and a runnable test file scaffold using watsonx.ai.

    The disclaimer field in the response confirms that tests have NOT been executed.
    """
    if not body.code.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="code must not be empty.",
        )

    result: TestResult = generate_tests(
        code=body.code,
        language=body.language,
        file_path=body.file_path or "<snippet>",
        framework=body.framework,
    )

    return TestingOut(**result.to_dict())
