# Integration Hardening Notes

This document records what was integrated for `codex/integration-hardening` and what is intentionally deferred.

## What was completed

- Replaced frontend mock adapters with live backend API calls.
- Added API-backed flows for:
  - day aggregate load
  - meal draft generation
  - meal save
  - meal edit
  - glucose screenshot upload
  - rolling 7-day activity sync
- Added loading, empty, and error states for key frontend interactions.
- Added explicit retry actions for failed day load, draft generation, activity sync, and upload.
- Added idempotent sync behavior in backend by upserting on `strava_activity_id`.
- Added backend integration tests and frontend flow tests.
- Updated setup and run docs for `uv` + React workflow.

## Intentional v1 limits

- Strava sync currently uses deterministic local demo activity generation while preserving the final API contract and idempotent behavior. OAuth connect URL wiring exists, but token exchange/persistence is deferred.
- Meal draft generation currently uses a local nutrition reference table and deterministic parsing. OpenAI model environment variables are kept in place for later direct model integration.
- Glucose screenshot summarization is intentionally descriptive and non-medical.

## Remaining gaps for later phases

1. Replace deterministic demo Strava activity generation with authenticated Strava API fetch + token refresh persistence.
2. Replace local meal parsing heuristic with OpenAI structured outputs while preserving confirmation behavior for ambiguous meals.
3. Add audio upload + transcription endpoint and wire microphone capture to it in the frontend.
4. Add a richer day notes flow and optional activity edit/annotation support.
5. Add end-to-end browser tests (Playwright) once CI and environment bootstrapping are finalized.
