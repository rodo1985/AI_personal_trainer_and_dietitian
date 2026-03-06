# Repository Guidelines

## Project Structure & Module Organization
This branch is documentation-first. The root [README.md](/Users/REDONSX1/Documents/code/01 personal/AI_personal_trainer_and_dietitian/README.md) explains product scope, and `docs/` holds the implementation plan and parallel worktree prompts. Start with `docs/implementation-plan.md`, then `docs/parallel-worktree-prompts.md` before adding code. The planned runtime structure is `backend/` for FastAPI services, `frontend/` for the React app, and optional `data/` and `uploads/` folders for local development storage.

## Build, Test, and Development Commands
There is no runnable app scaffold on this branch yet. Contributors should align new work to the documented target workflow:

```bash
make help
make setup
uv venv
uv sync
make backend-dev
uv run fastapi dev backend/app/main.py
make test
uv run pytest
make lint
uv run ruff check .
make frontend-install
npm install
make frontend-dev
npm run dev
npm test
make build
npm run build
```

Prefer adding and maintaining `Makefile` targets for common workflows so contributors can rely on `make help` as the quickest entry point. Use `uv run <command>` for Python tooling once the backend scaffold exists, and keep the `Makefile`, `README.md`, and real commands in sync whenever setup or run behavior changes.

## Coding Style & Naming Conventions
Optimize for readability over cleverness. Python should use type hints, small functions, and docstrings for every function, method, and class. Add inline comments for non-obvious decisions and edge cases. Follow `snake_case` for Python modules and functions, `PascalCase` for React components, and clear descriptive filenames such as `meal_draft_service.py` or `DaySummaryCard.tsx`.

## Testing Guidelines
Every behavior change should include tests. Planned conventions are `backend/tests/test_*.py` for Python and `*.test.tsx` for frontend flows. Focus coverage on draft parsing, day-log aggregation, Strava sync idempotency, upload handling, and responsive UI smoke tests. If a branch changes behavior but the scaffold is not ready, document the missing test coverage in the PR.

## Commit & Pull Request Guidelines
Current history is minimal (`Initial commit`), so keep commit subjects short, imperative, and specific, for example `Add FastAPI health endpoint`. PRs should describe scope, note any plan assumptions, link the relevant issue or worktree prompt, and include screenshots for UI changes once the frontend exists. If setup, configuration, or folder structure changes, update `README.md` and related docs in the same PR.

## Agent Notes
Stay within the scope defined by the implementation plan and worktree prompts. Avoid rewriting another branch's ownership area unless a shared contract truly requires it.
