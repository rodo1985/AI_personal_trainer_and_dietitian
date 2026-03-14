# Personal Endurance Trainer Log Prototype

## What this repo is
This repository now includes a runnable FastAPI backend for a single-user, local-first endurance logging prototype.
It is designed to combine AI-assisted meal logging, glucose screenshot uploads, and future Strava activity sync into one daily view.
The backend implemented in this branch focuses on Prompt 3 (`codex/backend-ai-log`) from the parallel worktree plan.

## Key features / scope
- Implements day-log aggregate read endpoint: `GET /api/day/{date}`.
- Implements assistant draft endpoint for typed and transcript text: `POST /api/day/{date}/assistant/draft`.
- Implements meal persistence with ambiguity confirmation rules: `POST /api/day/{date}/meals`.
- Implements glucose screenshot upload with local storage and AI summary: `POST /api/day/{date}/glucose-uploads`.
- Implements audio transcription endpoint that feeds the same draft pipeline: `POST /api/day/{date}/assistant/transcribe`.
- Includes backend tests for parsing, confirmation validation, persistence, and upload behavior.
- Out of scope in this branch: Strava OAuth/sync implementation, frontend React implementation, multi-user auth, medical advice logic.

## Setup
1. Install `uv` (see [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/)).
2. Create and activate the project virtual environment:

```bash
uv venv
source .venv/bin/activate
```

3. Sync dependencies (runtime + dev):

```bash
uv sync --all-groups
```

4. Copy environment variables and adjust values:

```bash
cp .env.example .env
```

5. Optional shortcut targets:

```bash
make help
make setup
```

## How to run

```bash
# Backend API (FastAPI dev server)
make backend-dev
# equivalent:
uv run fastapi dev backend/app/main.py

# Backend tests
make test
# equivalent backend-only:
uv run pytest

# Lint
make lint
# equivalent:
uv run ruff check .

# Frontend placeholders until Prompt 2/foundation frontend scaffold is merged
make frontend-install
make frontend-dev
make build
```

Frontend commands remain placeholders until the frontend scaffold is merged.

## Configuration
Environment variables are loaded from your shell (or `.env` if your shell loads it):

- `OPENAI_API_KEY`: required for audio transcription and full AI screenshot summarization.
- `OPENAI_MEAL_MODEL`: model ID for optional structured meal parsing hints.
- `OPENAI_TRANSCRIBE_MODEL`: model ID for audio transcription.
- `OPENAI_VISION_MODEL`: model ID for glucose screenshot summaries.
- `DATABASE_URL`: SQLite URL, default `sqlite:///data/app.db`.
- `UPLOAD_DIR`: local folder for glucose screenshots, default `uploads`.
- `STRAVA_CLIENT_ID`: reserved for Prompt 4 Strava integration.
- `STRAVA_CLIENT_SECRET`: reserved for Prompt 4 Strava integration.
- `STRAVA_REDIRECT_URI`: reserved for Prompt 4 Strava integration.

Notes:
- If `OPENAI_API_KEY` is missing, transcription returns `503` and glucose uploads return a transparent fallback summary warning.
- Nutrition totals are computed only for confidently matched catalog foods; unmatched foods stay unresolved.

## Project structure
- `backend/app/main.py`: FastAPI app entrypoint.
- `backend/app/api/routes/day_logs.py`: Prompt 3 API routes.
- `backend/app/services/`: meal draft pipeline, nutrition lookup, OpenAI client adapters, upload storage.
- `backend/app/repositories/day_log_repository.py`: SQLite persistence and day aggregate reads.
- `backend/tests/`: backend test coverage for Prompt 3 behavior.
- `docs/implementation-plan.md`: product and architecture plan.
- `docs/parallel-worktree-prompts.md`: parallel worktree ownership prompts.
- `docs/backend-ai-log.md`: backend Prompt 3 behavior notes and known limitations.
- `.env.example`: local environment variable template.

## Contributing / Development notes
- Start with the plan docs before expanding scope:
  - `docs/implementation-plan.md`
  - `docs/parallel-worktree-prompts.md`
- Keep the backend single-user and local-first for v1.
- Preserve explicit confirmation behavior when ambiguity or unmatched nutrition exists.
- Update tests and docs in the same change whenever endpoint behavior or configuration changes.
