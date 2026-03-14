# Backend AI Log (Prompt 3)

This document captures the backend behaviors implemented for the `codex/backend-ai-log` scope.

## Implemented endpoints

- `GET /api/day/{date}`
  - Returns one aggregate day payload with meals, activities, uploads, and daily nutrition totals.
- `POST /api/day/{date}/assistant/draft`
  - Accepts typed or transcript text.
  - Returns normalized `AssistantDraft` with assumptions, warnings, and `confirm_before_save`.
- `POST /api/day/{date}/assistant/transcribe`
  - Accepts audio upload.
  - Transcribes audio with OpenAI and sends transcript through the same draft pipeline as typed text.
- `POST /api/day/{date}/meals`
  - Persists reviewed meal draft.
  - Returns `409` when confirmation is required but not acknowledged.
- `POST /api/day/{date}/glucose-uploads`
  - Accepts image upload, stores file locally, and returns metadata with AI summary.

## Confirmation and ambiguity rules

- The draft always keeps unresolved food items visible (`matched=false`) with an `unresolved_reason`.
- Unmatched nutrition items are excluded from totals to avoid false precision.
- Missing meal slot or unresolved nutrition matches set `confirm_before_save=true`.
- `POST /meals` requires `confirmation_acknowledged=true` when `confirm_before_save=true`.

## Nutrition lookup limitations

- v1 uses an intentionally small local food catalog in `backend/app/services/nutrition.py`.
- Unknown foods are not silently mapped to approximate values.
- Quantity parsing supports basic numbers and common words (`half`, `quarter`) but not full recipe-level parsing.

## AI behavior notes

- OpenAI model IDs are configured through:
  - `OPENAI_MEAL_MODEL`
  - `OPENAI_TRANSCRIBE_MODEL`
  - `OPENAI_VISION_MODEL`
- If `OPENAI_API_KEY` is missing:
  - Audio transcription endpoint returns `503` with a clear setup message.
  - Glucose upload still saves files and returns a transparent fallback summary warning.

## Local storage details

- SQLite path comes from `DATABASE_URL` and defaults to `sqlite:///data/app.db`.
- Glucose images are stored under `UPLOAD_DIR/<date>/<uuid>-<filename>`.
