# DevFlow — CodeLens

> **Developer Intelligence** — Turn one Git code change into actionable engineering intelligence.

---

## Overview

DevFlow CodeLens is an AI-powered developer intelligence platform that analyses GitHub pull requests and branch diffs, runs deterministic static analysis, and uses IBM watsonx.ai to produce structured debugging reports, optimisation suggestions, test scaffolding, PR descriptions, Jira ticket drafts, and return-to-work summaries.

---

## Problem

Every pull request creates invisible overhead:

- **Context switching** — re-reading old code to understand what changed
- **Debugging friction** — hours finding root causes that should take minutes
- **PR administration** — writing descriptions, updating Jira, preparing review notes
- **Testing preparation** — identifying what to test after a diff
- **Return-to-work overhead** — catching up after leave or switching context

---

## Solution

CodeLens analyses the Git diff and produces:

| Feature | What it does |
|---|---|
| **Code Analysis** | Syntax, security, complexity, and quality findings from the diff |
| **Debugging** | Static analysis + watsonx.ai root-cause identification with evidence |
| **Optimization** | Complexity metrics + AI-assisted improvement suggestions |
| **Test Checklist** | AI-generated test scaffolding (not auto-run — review required) |
| **PR Description** | Structured, professional PR description from the diff |
| **Jira Draft** | AI ticket draft — requires developer confirmation before creation |
| **Return Summary** | Prioritised briefing after time away from the codebase |
| **Friction Analytics** | Merge time, review cycles, and recurring-findings metrics |

---

## Architecture

```
GitHub Repository / Pull Request
            ↓
        Git Diff
            ↓
       Diff Parser
            ↓
        AST Parser
            ↓
   Deterministic Static Analysis
            ↓
 ┌─────────────────────────────┐
 │ Syntax                      │
 │ Security                    │
 │ Complexity                  │
 │ Code Quality                │
 └─────────────────────────────┘
            ↓
       IBM watsonx.ai
            ↓
 ┌─────────────────────────────┐
 │ Debugging                   │
 │ Optimization                │
 │ Testing                     │
 │ PR Description              │
 │ Jira Draft                  │
 │ Return-to-Work Summary      │
 └─────────────────────────────┘
            ↓
      FastAPI Backend
            ↓
       PostgreSQL
            ↓
      React / CodeLens UI
```

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 14+ (or Docker)

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The React app starts at `http://localhost:5173`.

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Linux / macOS
# .venv\Scripts\activate           # Windows PowerShell
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The FastAPI server starts at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### Database

```bash
# Create and seed the database
psql -U devflow -d devflow -f database/schema.sql
psql -U devflow -d devflow -f database/seed.sql

# Or use the helper script
python scripts/seed_database.py
```

### Docker (full stack)

```bash
# Copy and fill in your credentials
cp .env.example .env

docker compose up --build
```

Services:
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

---

## Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required for full functionality:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing key (generate with `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `GITHUB_TOKEN` | GitHub personal access token (repo + read:user scopes) |
| `WATSONX_API_KEY` | IBM Cloud API key |
| `WATSONX_PROJECT_ID` | watsonx.ai project ID |
| `JIRA_URL` | Atlassian instance URL |
| `JIRA_EMAIL` | Jira account email |
| `JIRA_TOKEN` | Jira API token |

The backend starts in Demo Mode if external credentials are not configured.

---

## API

The FastAPI backend provides:

```
POST /auth/login           — JWT authentication
GET  /auth/me              — Current user

POST /analysis             — Full analysis pipeline (GitHub diff → findings)
GET  /analysis/{id}        — Retrieve analysis result

POST /debug                — Debug a code snippet
POST /optimize             — Optimization analysis
POST /testing              — Generate test scaffolding

POST /summaries/pr         — Generate PR description
POST /summaries/return     — Return-to-work summary

GET  /github/repositories  — List GitHub repositories
GET  /github/repositories/{owner}/{repo}/pulls — List PRs
GET  /github/repositories/{owner}/{repo}/pulls/{n}/diff — Raw diff
POST /github/webhook       — GitHub webhook receiver

GET  /jira/projects        — List Jira projects
POST /jira/draft           — Generate Jira ticket draft
POST /jira/issues          — Create issue (requires confirmed: true)

GET  /analytics/friction   — Developer friction metrics

GET  /api/health           — Liveness probe
```

---

## Product Principles

1. Deterministic static analysis comes before AI.
2. AI augments findings — it does not replace static analysis.
3. AI results must be explainable.
4. Suggestions are always presented as suggestions.
5. Code is never automatically modified.
6. Jira issues are never created without explicit developer approval.
7. GitHub PRs are never modified automatically.
8. API keys and credentials are never exposed to the frontend.
9. Mock/demo data is never presented as live data.

---

## Project Structure

```
devflow/
├── backend/
│   ├── app/
│   │   ├── main.py          FastAPI application factory
│   │   ├── config.py        Environment-based configuration
│   │   ├── analyzers/       Syntax, security, complexity, quality
│   │   ├── api/             FastAPI routers
│   │   ├── integrations/    GitHub, Jira, watsonx.ai clients
│   │   ├── models/          SQLAlchemy ORM models
│   │   ├── prompts/         AI prompt templates
│   │   ├── schemas/         Pydantic request/response schemas
│   │   └── services/        Business logic layer
│   ├── Dockerfile
│   └── requirements.txt
├── database/
│   ├── schema.sql           PostgreSQL DDL
│   └── seed.sql             Demo data
├── frontend/                React + Vite + Tailwind
├── scripts/
│   └── seed_database.py     Database seeding helper
├── docker-compose.yml
├── .env.example
└── README.md
```
