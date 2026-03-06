# Personal Endurance Trainer Log Prototype

## What this repo is
This repository holds the planning artifacts for a single-user web app that combines training, nutrition, and glucose observations into one daily log.
The target user is an endurance athlete who wants to review Strava activities, manually log meals with AI assistance, and attach Abbott Libre glucose screenshots to the same day view.
At the moment, the repository is in the planning stage: the implementation roadmap and parallel worktree prompts are ready, but the backend and frontend scaffolds have not been created yet.

## Key features / scope
- Planned v1 combines three inputs in one day log: meals, Strava activities, and glucose screenshots.
- Planned v1 uses AI only through OpenAI models for meal parsing, screenshot summarization, and audio transcription.
- Planned v1 includes a day selector, meal slots for `breakfast`, `lunch`, `dinner`, and `snacks`, a draft-review flow, and a daily summary.
- Planned Strava behavior is a rolling 7-day sync when the app opens or when the user navigates between recent days.
- Planned storage is local-first with `SQLite` for structured data and local file storage for uploaded glucose screenshots.
- Out of scope for v1 are multi-user auth, MyFitnessPal sync, direct Abbott/Libre API integration, realtime Strava webhooks, and medical recommendations.

## Setup
The current branch contains planning documentation only, so there is no runnable application scaffold yet.
The first implementation branch, `codex/foundation`, is responsible for creating the initial `uv`-managed Python project, the FastAPI shell, and the React shell described in the plan.

A root `Makefile` is included now so contributors have one predictable entry point for common workflows. On this planning branch, the targets print guidance until the backend and frontend scaffolds exist.

```bash
make help
```

When the foundation branch lands, local setup should follow this flow:

```bash
make setup
uv venv
uv sync
```

Then install the frontend dependencies from the React app directory that the foundation branch introduces:

```bash
make frontend-install
npm install
```

Reference documents:
- [Implementation plan](/Users/REDONSX1/Documents/code/01 personal/AI_personal_trainer_and_dietitian/docs/implementation-plan.md)
- [Parallel worktree prompts](/Users/REDONSX1/Documents/code/01 personal/AI_personal_trainer_and_dietitian/docs/parallel-worktree-prompts.md)

## How to run
This branch does not yet contain runnable backend or frontend code.
The target commands, once Phase 1 is scaffolded, are:

```bash
# Backend development server
make backend-dev
uv run fastapi dev backend/app/main.py

# Frontend development server
make frontend-dev
npm run dev

# Combined tests
make test
uv run pytest

# Frontend tests
npm test

# Python lint
make lint
uv run ruff check .

# Frontend production build
make build
npm run build
```

These commands are intentionally documented now so that the implementation branches can converge on one expected developer workflow. The `Makefile` should stay aligned with the real commands as the scaffold lands.

## Configuration
The planned environment variables for the first prototype are:

- `OPENAI_API_KEY`
- `OPENAI_MEAL_MODEL`
- `OPENAI_TRANSCRIBE_MODEL`
- `OPENAI_VISION_MODEL`
- `STRAVA_CLIENT_ID`
- `STRAVA_CLIENT_SECRET`
- `STRAVA_REDIRECT_URI`
- `DATABASE_URL`
- `UPLOAD_DIR`

The repository should keep secrets in local environment files that are not committed, and the final scaffold should document exact examples in a `.env.example` file.

## Project structure
The intended structure after the foundation branch lands is:

- `backend/`: FastAPI application, persistence layer, integrations, and tests.
- `frontend/`: React application for day logs, assistant drafting, and review flows.
- `docs/`: implementation planning, integration notes, and contributor guidance.
- `uploads/`: local development storage for glucose screenshots.
- `data/`: local SQLite database files for development, if the final scaffold keeps them in-repo.

Today, only `docs/` planning artifacts are present.

## Contributing / Development notes
Start from the saved implementation plan before creating code:
- [Implementation plan](/Users/REDONSX1/Documents/code/01 personal/AI_personal_trainer_and_dietitian/docs/implementation-plan.md)
- [Parallel worktree prompts](/Users/REDONSX1/Documents/code/01 personal/AI_personal_trainer_and_dietitian/docs/parallel-worktree-prompts.md)

The parallel worktree strategy is designed to reduce merge conflicts:
- `codex/foundation` owns the initial scaffold and shared contracts.
- Feature worktrees should stay within their assigned scope and avoid rewriting shared setup unless required.
- Any change that affects setup, configuration, or developer workflow must also update this `README.md`.
