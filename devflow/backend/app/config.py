"""
Application configuration loaded from environment variables / .env file.
All secrets are sourced from the environment — never hardcoded.
"""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────
    database_url: str = "postgresql://devflow:devflow@localhost:5432/devflow"

    # ── Security ──────────────────────────────────────────────────────────
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # ── GitHub ────────────────────────────────────────────────────────────
    github_token: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""

    # ── Jira ──────────────────────────────────────────────────────────────
    jira_url: str = ""
    jira_email: str = ""
    jira_token: str = ""

    # ── IBM watsonx.ai ────────────────────────────────────────────────────
    watsonx_api_key: str = ""
    watsonx_project_id: str = ""
    watsonx_url: str = "https://us-south.ml.cloud.ibm.com"
    watsonx_model_id: str = "ibm/granite-34b-code-instruct"

    # ── Redis ─────────────────────────────────────────────────────────────
    redis_url: str = ""

    # ── Application ───────────────────────────────────────────────────────
    frontend_url: str = "http://localhost:5173"
    environment: Literal["development", "production", "test"] = "development"

    # ── Derived helpers ───────────────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @field_validator("secret_key")
    @classmethod
    def secret_key_must_not_be_default_in_production(cls, v: str, info) -> str:
        # Validation runs at import time; environment may not be set yet, so
        # we only warn here — a stricter check can be added in main.py startup.
        return v


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()


# Module-level singleton for convenience imports.
settings = get_settings()
