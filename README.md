# Personal Endurance Trainer Log Prototype

## What this repo is
This repository is a single-user, local-first prototype for tracking endurance training, meals, and glucose observations in one daily log.
This branch now includes a runnable FastAPI backend slice for Strava OAuth and rolling activity sync.
The frontend and AI meal/glucose pipelines are still planned and documented, but not implemented on this worktree yet.

## Key features / scope
- Implemented in this branch:
  - FastAPI backend app scaffold with health and Strava routes
  - Strava OAuth connect/callback flow
  - Encrypted token storage in SQLite
  - Rolling 7-day Strava sync with idempotent upsert by `strava_activity_id`
  - Optional manual `rpe_override` updates per activity
  - Backend tests for OAuth, refresh, sync window filtering, and duplicate prevention
- Planned (not yet implemented here):
  - Day-log aggregate API
  - AI-assisted meal parsing and save flow
  - Glucose screenshot upload and summarization
  - React day-log UI
- Out of scope for v1:
  - Multi-user auth
  - Direct Abbott/Libre API integration
  - MyFitnessPal sync
  - Realtime Strava webhooks
  - Medical recommendations

## Setup
1. Install `uv` (see [uv docs](https://docs.astral.sh/uv/getting-started/installation/)).
2. Create and sync the Python environment:

```bash
make setup
# equivalent explicit commands:
uv venv
uv sync
```

3. Create local environment config:

```bash
cp .env.example .env
```

4. Fill `.env` values, especially Strava credentials:
- `STRAVA_CLIENT_ID`
- `STRAVA_CLIENT_SECRET`
- `STRAVA_REDIRECT_URI` (default local callback: `http://localhost:8000/api/strava/callback`)
- `STRAVA_TOKEN_ENCRYPTION_KEY` (recommended)
- `DATABASE_URL`

Frontend setup is documented for future branches, but no `frontend/` app exists on this worktree yet.

## How to run
Backend dev server:

```bash
make backend-dev
# equivalent:
uv run fastapi dev backend/app/main.py
```

Backend tests:

```bash
make test
# equivalent:
uv run pytest
```

Backend lint:

```bash
make lint
# equivalent:
uv run ruff check .
```

Strava OAuth + sync flow (example):

```bash
# 1) Start backend
uv run fastapi dev backend/app/main.py

# 2) Request connect URL
curl "http://localhost:8000/api/strava/connect"

# 3) Complete Strava authorization in browser using returned URL
# 4) Trigger rolling sync
curl -X POST "http://localhost:8000/api/strava/sync/recent"
```

## Configuration
Environment variables used now or reserved by planned features:

- `OPENAI_API_KEY`
- `OPENAI_MEAL_MODEL`
- `OPENAI_TRANSCRIBE_MODEL`
- `OPENAI_VISION_MODEL`
- `STRAVA_CLIENT_ID`
- `STRAVA_CLIENT_SECRET`
- `STRAVA_REDIRECT_URI`
- `STRAVA_SCOPES`
- `STRAVA_SYNC_DAYS` (defaults to `7`)
- `STRAVA_ACTIVITY_PAGE_SIZE`
- `STRAVA_TOKEN_ENCRYPTION_KEY` (recommended)
- `DATABASE_URL`
- `UPLOAD_DIR`

Use `.env.example` as the template. Keep real secrets in `.env`, which should stay uncommitted.

## Project structure
- `backend/app/main.py`: FastAPI application entrypoint.
- `backend/app/routers/strava.py`: Strava connect/callback/sync/override routes.
- `backend/app/services/`: Strava client, sync orchestration, and token crypto helpers.
- `backend/app/repositories/strava_repository.py`: SQLite persistence for tokens, activities, and sync metadata.
- `backend/tests/`: Route and service tests for Strava integration behavior.
- `docs/implementation-plan.md`: Shared product and architecture plan.
- `docs/parallel-worktree-prompts.md`: Parallel branch ownership prompts.
- `docs/integrations/strava-sync.md`: Strava setup, usage, and caveats.
- `data/`: Local SQLite data directory (created at runtime).

## Contributing / Development notes
- Read [implementation plan](/Users/REDONSX1/.codex/worktrees/de69/AI_personal_trainer_and_dietitian/docs/implementation-plan.md) before major changes.
- Keep implementation local-first and single-user for v1.
- For this branch, stay focused on Strava integration scope and avoid unrelated meal/upload/frontend rewrites.
- Update `README.md` and `docs/` whenever setup, behavior, or configuration changes.
- Run tests and lint locally before finalizing:

```bash
uv run pytest
uv run ruff check .
```
