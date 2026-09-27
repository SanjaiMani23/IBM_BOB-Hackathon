-- DevFlow CodeLens — PostgreSQL schema
-- Run with:  psql -U devflow -d devflow -f schema.sql

-- ─────────────────────────────────────────────────────────────────────────────
-- Extensions
-- ─────────────────────────────────────────────────────────────────────────────

CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- gen_random_uuid()

-- ─────────────────────────────────────────────────────────────────────────────
-- Users
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS users (
    id           TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    email        TEXT        NOT NULL UNIQUE,
    full_name    TEXT,
    hashed_password TEXT     NOT NULL,
    is_active    BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────────────────
-- Repositories
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS repositories (
    id           TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    full_name    TEXT        NOT NULL UNIQUE,   -- owner/repo
    owner_id     TEXT        NOT NULL,
    description  TEXT,
    default_branch TEXT      NOT NULL DEFAULT 'main',
    language     TEXT,
    github_id    INTEGER,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────────────────
-- Pull Requests
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS pull_requests (
    id           TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    repository   TEXT        NOT NULL,
    pr_number    INTEGER     NOT NULL,
    title        TEXT,
    state        TEXT        NOT NULL DEFAULT 'open',
    author       TEXT,
    base_branch  TEXT,
    head_branch  TEXT,
    created_at   TIMESTAMPTZ,
    merged_at    TIMESTAMPTZ,
    closed_at    TIMESTAMPTZ,
    url          TEXT,
    UNIQUE (repository, pr_number)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- Code Analyses
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS code_analyses (
    id           TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    repository   TEXT        NOT NULL,
    branch       TEXT        NOT NULL,
    commit_sha   TEXT,
    files_analyzed INTEGER   NOT NULL DEFAULT 0,
    total_findings INTEGER   NOT NULL DEFAULT 0,
    duration_ms  INTEGER,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analyses_repository ON code_analyses (repository);
CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON code_analyses (created_at);

-- ─────────────────────────────────────────────────────────────────────────────
-- Findings
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS findings (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    analysis_id     TEXT        NOT NULL REFERENCES code_analyses(id) ON DELETE CASCADE,
    title           TEXT        NOT NULL,
    severity        TEXT        NOT NULL,   -- critical | high | medium | low
    finding_type    TEXT        NOT NULL,   -- security | bug | optimization | structure | quality
    explanation     TEXT,
    recommendation  TEXT,
    file_path       TEXT,
    line_number     INTEGER,
    confidence      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_findings_analysis_id ON findings (analysis_id);
CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings (severity);

-- ─────────────────────────────────────────────────────────────────────────────
-- Optimization Suggestions
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS optimization_suggestions (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    analysis_id     TEXT        NOT NULL REFERENCES code_analyses(id) ON DELETE CASCADE,
    title           TEXT        NOT NULL,
    priority        TEXT        NOT NULL,
    explanation     TEXT,
    suggestion      TEXT,
    suggested_code  TEXT,
    trade_offs      TEXT,
    file_path       TEXT,
    line_number     INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────────────────
-- Test Checklists
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS test_checklists (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    analysis_id     TEXT        REFERENCES code_analyses(id) ON DELETE CASCADE,
    test_name       TEXT        NOT NULL,
    category        TEXT        NOT NULL,
    description     TEXT,
    code            TEXT,
    rationale       TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────────────────
-- Jira Tickets
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS jira_tickets (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    finding_id      TEXT        REFERENCES findings(id) ON DELETE SET NULL,
    jira_issue_key  TEXT        NOT NULL UNIQUE,
    jira_issue_url  TEXT,
    status          TEXT        NOT NULL DEFAULT 'created',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────────────────
-- Summaries
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS summaries (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    repository      TEXT        NOT NULL,
    summary_type    TEXT        NOT NULL,   -- pr_description | return_summary
    content         TEXT        NOT NULL,
    pr_number       INTEGER,
    branch          TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────────────────
-- Friction Logs
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS friction_logs (
    id              TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    repository      TEXT        NOT NULL,
    metric_name     TEXT        NOT NULL,
    metric_value    FLOAT       NOT NULL,
    pr_number       INTEGER,
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_friction_repository ON friction_logs (repository);
CREATE INDEX IF NOT EXISTS idx_friction_recorded_at ON friction_logs (recorded_at);
