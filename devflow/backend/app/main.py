"""
DevFlow CodeLens API — FastAPI application factory.

Start with:
    uvicorn app.main:app --reload
"""

import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import (
    analysis,
    analytics,
    auth,
    debugging,
    github,
    jira,
    optimization,
    summaries,
    testing,
)
from app.config import settings
from app.schemas import HealthResponse

# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.DEBUG if settings.is_development else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("devflow")

# ─────────────────────────────────────────────────────────────────────────────
# Application
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="DevFlow CodeLens API",
    version="0.1.0",
    description=(
        "AI-powered developer intelligence platform. "
        "Analyses code diffs, surfaces findings, and integrates with GitHub and Jira."
    ),
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# ─────────────────────────────────────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Request timing middleware (development only)
# ─────────────────────────────────────────────────────────────────────────────

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Process-Time-Ms"] = str(duration_ms)
    return response

# ─────────────────────────────────────────────────────────────────────────────
# Exception handlers
# ─────────────────────────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url)
    # Never expose stack traces to clients in production.
    detail = str(exc) if settings.is_development else "An unexpected error occurred."
    return JSONResponse(status_code=500, content={"detail": detail})

# ─────────────────────────────────────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────────────────────────────────────

app.include_router(auth.router,         prefix="/auth",       tags=["auth"])
app.include_router(analysis.router,     prefix="/analysis",   tags=["analysis"])
app.include_router(analytics.router,    prefix="/analytics",  tags=["analytics"])
app.include_router(debugging.router,    prefix="/debug",      tags=["debug"])
app.include_router(github.router,       prefix="/github",     tags=["github"])
app.include_router(jira.router,         prefix="/jira",       tags=["jira"])
app.include_router(optimization.router, prefix="/optimize",   tags=["optimize"])
app.include_router(summaries.router,    prefix="/summaries",  tags=["summaries"])
app.include_router(testing.router,      prefix="/testing",    tags=["testing"])

# ─────────────────────────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    """Liveness probe — returns 200 when the service is up."""
    return HealthResponse(
        status="ok",
        version=app.version,
        environment=settings.environment,
    )

# ─────────────────────────────────────────────────────────────────────────────
# Startup / shutdown events
# ─────────────────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def on_startup():
    if settings.is_production and settings.secret_key == "dev-secret-key-change-in-production":
        raise RuntimeError("SECRET_KEY must be changed before running in production.")
    logger.info(
        "DevFlow CodeLens API started  env=%s  model=%s",
        settings.environment,
        settings.watsonx_model_id,
    )


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("DevFlow CodeLens API shutting down.")
