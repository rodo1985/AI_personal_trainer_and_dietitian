# Personal Endurance Trainer Log Prototype

## What this repo is
This repository contains a single-user, local-first web app scaffold for tracking endurance training days.
It combines meals, Strava activities, and glucose screenshot notes into one day-based workflow.
The scaffold already includes a FastAPI backend, a React + TypeScript frontend shell, shared API contracts, and local SQLite bootstrapping.
It is designed so parallel worktrees can add features without guessing architecture or setup.

## Key features / scope
- Includes a runnable FastAPI backend shell with `GET /api/health`.
- Includes a runnable React + TypeScript frontend shell with a basic landing page and tests.
- Uses `uv` for Python environment and dependency management.
- Uses SQLite for local persistence bootstrap and `uploads/` for local files.
- Defines shared contracts in `docs/api-contract.md` for backend/frontend alignment.
- Uses OpenAI-only configuration placeholders for planned AI features.
- Does not yet implement meal drafting, Strava OAuth flows, transcription, or glucose analysis logic.

## Setup

### 1. Prerequisites
- Python 3.11+
- Node.js 20+
- `uv` installed

Install `uv` (macOS/Linux):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and enter the project
```bash
git clone <your-repo-url>
cd AI_personal_trainer_and_dietitian
```

### 3. Python environment with uv
```bash
make setup
```

Equivalent explicit commands:
```bash
uv venv
uv sync
```

### 4. Frontend dependencies
```bash
make frontend-install
```

Equivalent explicit command:
```bash
npm --prefix frontend install
```

### 5. Environment configuration
Copy `.env.example` into a local `.env` file and adjust values as needed:
```bash
cp .env.example .env
```

For scaffold-only local development, the defaults are enough to start backend and frontend.

## How to run

### Development servers
Backend (FastAPI):
```bash
make backend-dev
```

Frontend (Vite + React):
```bash
make frontend-dev
```

### Tests
Run backend and frontend tests:
```bash
make test
```

Run only backend tests:
```bash
make backend-test
```

Run only frontend tests:
```bash
make frontend-test
```

### Lint / type checks
```bash
make lint
```

### Frontend production build
```bash
make build
```

## Configuration
The scaffold reads environment variables from `.env` (see `.env.example`).

| Variable | Required | Purpose |
| --- | --- | --- |
| `APP_ENV` | No | Runtime label (`development`, `test`, `production`). |
| `APP_DEBUG` | No | Enables FastAPI debug mode when `true`. |
| `API_PREFIX` | No | Base prefix for API routes (`/api`). |
| `DATABASE_URL` | Yes | SQLite URL, e.g. `sqlite:///data/app.db`. |
| `UPLOAD_DIR` | Yes | Local folder for uploaded files. |
| `OPENAI_API_KEY` | Later | API key for planned AI features. |
| `OPENAI_MEAL_MODEL` | Later | Planned model for meal draft parsing. |
| `OPENAI_TRANSCRIBE_MODEL` | Later | Planned model for audio transcription. |
| `OPENAI_VISION_MODEL` | Later | Planned model for glucose screenshot interpretation. |
| `STRAVA_CLIENT_ID` | Later | Planned Strava OAuth client ID. |
| `STRAVA_CLIENT_SECRET` | Later | Planned Strava OAuth client secret. |
| `STRAVA_REDIRECT_URI` | Later | Planned Strava OAuth callback URI. |
| `FRONTEND_API_BASE_URL` | No | Frontend base URL for backend API requests. |

## Project structure
```text
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py
│   └── tests/
├── frontend/
│   ├── src/
│   ├── index.html
│   └── package.json
├── docs/
│   ├── api-contract.md
│   ├── foundation-scaffold.md
│   ├── implementation-plan.md
│   └── parallel-worktree-prompts.md
├── data/
├── uploads/
├── .env.example
├── Makefile
└── pyproject.toml
```

## Contributing / Development notes
- Start from `docs/implementation-plan.md` before implementing features.
- Keep changes local-first and single-user for v1.
- Preserve contract names in `docs/api-contract.md` unless a documented migration is required.
- Add or update tests for all behavior changes.
- Update this README and relevant docs whenever setup, behavior, or configuration changes.
- Keep Python code explicit and readable, with docstrings on every new function/method/class.
