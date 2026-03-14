# Strava Integration Guide (Prompt 4: `codex/strava-sync`)

## What this integration covers
This branch implements the backend Strava slice for the single-user prototype:
- OAuth connect and callback handling
- Encrypted token-at-rest storage in SQLite
- Access-token refresh before sync when tokens are near expiry
- Rolling 7-day activity sync (polling based)
- Idempotent activity upserts keyed by `strava_activity_id`
- Optional manual `rpe_override` updates per activity
- Sync run metadata for diagnostics

## Required Strava app setup
1. Log in to Strava and open the API settings page: [https://www.strava.com/settings/api](https://www.strava.com/settings/api)
2. Create an application (or reuse an existing one).
3. Set the authorization callback domain to `localhost` for local development.
4. Copy `Client ID` and `Client Secret` into your `.env` file.
5. Set redirect URI to exactly:
   - `http://localhost:8000/api/strava/callback`

## Environment variables
Copy `.env.example` to `.env` and set at minimum:
- `STRAVA_CLIENT_ID`
- `STRAVA_CLIENT_SECRET`
- `STRAVA_REDIRECT_URI`
- `STRAVA_TOKEN_ENCRYPTION_KEY` (recommended, dedicated token encryption secret)
- `DATABASE_URL`

Notes:
- If `STRAVA_TOKEN_ENCRYPTION_KEY` is omitted, the app falls back to `STRAVA_CLIENT_SECRET` for encryption key derivation so local development can still run.
- The fallback works, but a dedicated encryption key is preferred for operational hygiene.

## Local run flow
1. Start backend:
   ```bash
   uv run fastapi dev backend/app/main.py
   ```
2. Get OAuth URL:
   ```bash
   curl "http://localhost:8000/api/strava/connect"
   ```
3. Open the returned `authorization_url` in a browser and approve.
4. Strava redirects to callback endpoint. Tokens are exchanged and stored encrypted.
5. Trigger rolling sync:
   ```bash
   curl -X POST "http://localhost:8000/api/strava/sync/recent"
   ```
6. (Optional) Set manual perceived effort override:
   ```bash
   curl -X PATCH "http://localhost:8000/api/strava/activities/<STRAVA_ACTIVITY_ID>/rpe-override" \
     -H "Content-Type: application/json" \
     -d '{"rpe_override": 7}'
   ```

## Data mapping
Strava activity payloads are normalized into:
- `strava_activity_id`
- `name`
- `sport_type`
- `start_time`
- `elapsed_time_s`
- `calories` (optional)
- `suffer_score` (optional)
- `rpe_override` (optional, manual)

Missing optional fields do not break persistence.

## Sync diagnostics
Each sync writes one metadata row in `strava_sync_runs`:
- `status` (`running`, `success`, `failed`)
- `window_start`, `window_end`
- `fetched_count`, `upserted_count`
- `error_message` on failure

This metadata is returned in the sync response to make failures diagnosable.

## Known caveats for `codex/integration-hardening`
- OAuth `state` is generated and forwarded, but state validation persistence is not yet implemented. Hardening can add anti-CSRF state tracking.
- Token storage is encrypted at rest, but key rotation workflows are not implemented yet.
- No webhook ingestion is included in v1 by design (polling only).
- Sync window filtering is UTC-based; if UX requires strict local-day semantics, add explicit timezone controls.
