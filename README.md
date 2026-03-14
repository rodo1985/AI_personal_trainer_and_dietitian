# Personal Endurance Trainer Log Prototype

## What this repo is
This repository contains a single-user training log prototype that combines meals, activities, and glucose screenshots into one day view.
The current branch now includes a runnable React + TypeScript frontend for the day-log flow, backed by mocked API adapters.
The backend service is still planned and documented, so the UI uses local fixtures and predictable mock responses for now.
The goal is to keep the product local-first and practical for daily logging on mobile and desktop.

## Key features / scope
- Includes a day selector, meal sections (`breakfast`, `lunch`, `dinner`, `snacks`), activity panel, glucose panel, assistant composer, microphone trigger, and draft review flow.
- Includes mocked draft generation and save confirmation flow with empty, loading, and save-error states.
- Includes frontend smoke tests for the main day-log interactions.
- Uses only mocked frontend adapters on this branch; backend persistence and live API wiring are not merged yet.
- Keeps v1 out of scope for multi-user auth, direct Abbott/Libre APIs, MyFitnessPal sync, realtime Strava webhooks, and medical recommendations.

## Setup
Prerequisites:
- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) for backend environment management
- Node.js 20+ and npm

Backend `uv` workflow (for the planned FastAPI scaffold):

```bash
make setup
# Equivalent uv commands once pyproject.toml exists:
uv venv
uv sync
```

Frontend setup (available now):

```bash
make frontend-install
# or
npm --prefix frontend install
```

## How to run
Frontend development server:

```bash
make frontend-dev
# or
npm --prefix frontend run dev
```

Frontend tests:

```bash
npm --prefix frontend test
```

Frontend production build:

```bash
make build
# or
npm --prefix frontend run build
```

Combined target (runs frontend tests and skips backend tests until backend scaffold exists):

```bash
make test
```

## Configuration
No environment variables are required for the current mocked frontend flow.
Planned backend configuration variables remain:

- `OPENAI_API_KEY`
- `OPENAI_MEAL_MODEL`
- `OPENAI_TRANSCRIBE_MODEL`
- `OPENAI_VISION_MODEL`
- `STRAVA_CLIENT_ID`
- `STRAVA_CLIENT_SECRET`
- `STRAVA_REDIRECT_URI`
- `DATABASE_URL`
- `UPLOAD_DIR`

When backend scaffolding lands, add a `.env.example` with concrete local values and keep secrets out of version control.

## Project structure
- `frontend/`: React + TypeScript day-log UI, mocked adapters, styles, and frontend tests.
- `docs/implementation-plan.md`: shared product/architecture plan.
- `docs/parallel-worktree-prompts.md`: branch ownership prompts for parallel execution.
- `docs/frontend-day-log-assumptions.md`: mocked API contract and integration handoff notes for backend wiring.
- `Makefile`: common commands for setup, run, test, and build.

## Contributing / Development notes
- Start from the plan docs before implementation changes:
  - `docs/implementation-plan.md`
  - `docs/parallel-worktree-prompts.md`
- Keep frontend/backend contracts aligned with `docs/frontend-day-log-assumptions.md` when replacing mocks.
- If you change setup, commands, behavior, or config assumptions, update this README in the same PR.
