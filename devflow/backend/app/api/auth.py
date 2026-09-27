"""
Authentication router — JWT-based login, token refresh, and current user.

Endpoints:
  POST /auth/login    — email + password → access token
  POST /auth/refresh  — existing token → new token
  GET  /auth/me       — return current authenticated user

Passwords are hashed with bcrypt via passlib.
Plain-text passwords are never stored or logged.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

logger = logging.getLogger(__name__)
router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
# Crypto helpers
# ─────────────────────────────────────────────────────────────────────────────

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(plain: str) -> str:
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> str:
    """Decode token and return the subject (user id). Raises HTTPException on failure."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        subject: str | None = payload.get("sub")
        if subject is None:
            raise JWTError("Missing sub claim")
        return subject
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ─────────────────────────────────────────────────────────────────────────────
# Current user dependency
# ─────────────────────────────────────────────────────────────────────────────

def get_current_user(
    token: str = Depends(_oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency — resolve the Bearer token to a User ORM object."""
    user_id = decode_token(token)
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# ─────────────────────────────────────────────────────────────────────────────
# Response schemas (local — keep auth self-contained)
# ─────────────────────────────────────────────────────────────────────────────

class TokenOut(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    expires_in:   int  # seconds


class UserOut(BaseModel):
    id:         str
    email:      str
    full_name:  str | None
    is_active:  bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenOut,
    summary="Authenticate and receive a JWT access token",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenOut:
    """
    Accepts OAuth2 password grant form fields (username = email, password).
    Returns a signed JWT access token on success.
    """
    user = db.query(User).filter(User.email == form_data.username).first()

    if user is None or not verify_password(form_data.password, user.hashed_password):
        logger.warning("Failed login attempt for email=%s", form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled.",
        )

    token = create_access_token(subject=user.id)
    logger.info("Successful login: user_id=%s", user.id)

    return TokenOut(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/refresh",
    response_model=TokenOut,
    summary="Refresh an existing JWT access token",
)
def refresh_token(
    current_user: User = Depends(get_current_user),
) -> TokenOut:
    """
    Issue a new token for the currently authenticated user.
    The existing token must still be valid to call this endpoint.
    """
    token = create_access_token(subject=current_user.id)
    return TokenOut(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get(
    "/me",
    response_model=UserOut,
    summary="Return the currently authenticated user",
)
def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)
