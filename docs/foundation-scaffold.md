# Foundation Scaffold Decisions

This document explains practical decisions made by the `codex/foundation` branch.

## Why SQLite initialization is code-first in phase 1
- The prototype is single-user and local-first, so a migration framework is intentionally deferred.
- The startup hook in `backend/app/main.py` calls `initialize_database` to ensure local setup is one command.
- Initial schema is small and designed to be extended by later worktrees.

## Current backend startup guarantees
When the FastAPI app starts, it will:
1. Validate environment settings from `.env` and process env vars.
2. Resolve `DATABASE_URL` and create the SQLite file if needed.
3. Create base tables for `day_logs`, `meal_entries`, `activity_entries`, and `glucose_uploads`.
4. Ensure `UPLOAD_DIR` exists for local file storage.

## Frontend scope in this branch
- The React app is intentionally a shell page only.
- It does not yet implement day-log forms, assistant compose flow, Strava rendering, or uploads.
- It does provide a running test harness (Vitest + Testing Library) so UI branches can add tests immediately.

## Shared contracts
- `docs/api-contract.md` is the source of truth for endpoint and payload naming.
- Feature branches should extend this contract and keep examples in sync with implementation.

## Local data folders
- `data/` is reserved for local SQLite files.
- `uploads/` is reserved for uploaded glucose screenshots.
- Both folders are safe for local development and should not contain committed personal data.
