# Personal Endurance Trainer Log Prototype

## What this repo is
This repository contains a single-user, local-first prototype that combines meals, recent Strava activity, and glucose screenshots into one day-based log.
It ships with a FastAPI backend, a React + TypeScript frontend, SQLite persistence, and local upload storage.
The goal is practical daily tracking with AI-assisted draft workflows and explicit user confirmation before saving uncertain data.

## Key features / scope
- Unified day view for meals, activities, glucose uploads, and nutrition totals.
- Assistant meal draft endpoint plus frontend review-and-save flow.
- Meal edit flow so users can recover from bad drafts without dead ends.
- Rolling 7-day activity sync endpoint with idempotent upsert behavior.
- Current integration-hardening build uses deterministic local activity payloads for sync while preserving the final Strava API contract.
- Glucose screenshot upload with descriptive (non-medical) summary text.
- Frontend loading, empty, and error states with explicit retry actions.
- Out of scope for v1: multi-user auth, MyFitnessPal sync, direct Abbott/Libre API integration, realtime Strava webhooks, and medical recommendations.

## Setup
### 1) Install prerequisites
- Python 3.11+
- Node.js 20+
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/)

### 2) Clone and enter the repository
```bash
git clone <your-repo-url>
cd AI_personal_trainer_and_dietitian
```

### 3) Backend environment with `uv`
```bash
make setup
# Equivalent manual commands:
# uv venv
# uv sync --group dev
```

### 4) Frontend dependencies
```bash
make frontend-install
# Equivalent manual command:
# npm --prefix frontend install
```

### 5) Environment variables
```bash
cp .env.example .env
```
Fill in values as needed. The app can run locally with default values for most fields.

## How to run
### Development servers
```bash
# Terminal 1: backend
make backend-dev
# uv run fastapi dev backend/app/main.py

# Terminal 2: frontend
make frontend-dev
# npm --prefix frontend run dev
```

### Tests
```bash
# All tests
make test

# Backend only
make test-backend
# uv run pytest

# Frontend only
make test-frontend
# npm --prefix frontend test
```

### Lint and build
```bash
make lint
# uv run ruff check .

make build
# npm --prefix frontend run build
```

## Configuration
Environment variables used by the prototype:

- `OPENAI_API_KEY`: OpenAI API key (reserved for direct model integration).
- `OPENAI_MEAL_MODEL`: Model ID for meal parsing tasks.
- `OPENAI_TRANSCRIBE_MODEL`: Model ID for audio transcription tasks.
- `OPENAI_VISION_MODEL`: Model ID for glucose screenshot interpretation.
- `STRAVA_CLIENT_ID`: Strava OAuth client ID.
- `STRAVA_CLIENT_SECRET`: Strava OAuth client secret.
- `STRAVA_REDIRECT_URI`: Strava OAuth callback URL.
- `DATABASE_URL`: SQLite URL (default: `sqlite:///./data/app.db`).
- `UPLOAD_DIR`: Local folder for glucose screenshot files.
- `FRONTEND_ORIGIN`: Allowed frontend origin for backend CORS.
- `VITE_API_BASE_URL`: Frontend API base URL.

See [`.env.example`](/Users/REDONSX1/.codex/worktrees/b446/AI_personal_trainer_and_dietitian/.env.example) for a copy/paste baseline.

## Project structure
- [`backend/app/main.py`](/Users/REDONSX1/.codex/worktrees/b446/AI_personal_trainer_and_dietitian/backend/app/main.py): FastAPI app entrypoint and middleware.
- [`backend/app/api/routes.py`](/Users/REDONSX1/.codex/worktrees/b446/AI_personal_trainer_and_dietitian/backend/app/api/routes.py): API routes for day logs, meals, uploads, and sync.
- `backend/app/services/`: Service layer for draft parsing, persistence orchestration, upload handling, and sync behavior.
- `backend/tests/`: Backend integration tests.
- [`frontend/src/App.tsx`](/Users/REDONSX1/.codex/worktrees/b446/AI_personal_trainer_and_dietitian/frontend/src/App.tsx): Main React day-log UI wired to live APIs.
- `frontend/src/api/`: Frontend API client wrappers.
- `frontend/src/test/`: Frontend test setup files.
- `docs/`: Implementation plan, worktree prompts, and hardening handoff notes.
- `data/`: Local SQLite database path (created at runtime).
- `uploads/`: Local glucose screenshot storage (created at runtime).

## Contributing / Development notes
- Read [implementation plan](/Users/REDONSX1/.codex/worktrees/b446/AI_personal_trainer_and_dietitian/docs/implementation-plan.md) and [parallel prompts](/Users/REDONSX1/.codex/worktrees/b446/AI_personal_trainer_and_dietitian/docs/parallel-worktree-prompts.md) before broad changes.
- Keep v1 single-user and local-first.
- Preserve non-medical wording for glucose interpretation and summaries.
- If you change API contracts, update both backend and frontend together and document the reason.
- Keep `README.md`, `.env.example`, `Makefile`, and real commands aligned in the same change.
- See [integration hardening notes](/Users/REDONSX1/.codex/worktrees/b446/AI_personal_trainer_and_dietitian/docs/integration-hardening.md) for deferred items.
