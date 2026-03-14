# Shared API Contract (Foundation)

This document defines the baseline HTTP contract for the phase-1 scaffold.
Feature branches should extend these shapes instead of redefining them.

## Base settings
- API prefix: `/api`
- Content type: `application/json`
- Date format for day routes: `YYYY-MM-DD` (ISO-8601 calendar date)

## Canonical domain objects

### `DayLog`
```json
{
  "date": "2026-03-06",
  "meal_entries": [],
  "activity_entries": [],
  "glucose_uploads": [],
  "daily_notes": "",
  "daily_totals": {
    "calories": 0,
    "protein_g": 0,
    "carbs_g": 0,
    "fat_g": 0
  }
}
```

### `MealEntry`
```json
{
  "id": 1,
  "date": "2026-03-06",
  "meal_slot": "breakfast",
  "source_text": "oats with banana",
  "items": [],
  "calories": 0,
  "protein_g": 0,
  "carbs_g": 0,
  "fat_g": 0,
  "confidence": "low",
  "status": "draft"
}
```

### `ActivityEntry`
```json
{
  "id": 1,
  "date": "2026-03-06",
  "strava_activity_id": "123456",
  "name": "Morning Run",
  "sport_type": "Run",
  "start_time": "2026-03-06T06:30:00Z",
  "elapsed_time_s": 3600,
  "calories": 650,
  "suffer_score": 72,
  "rpe_override": null
}
```

### `GlucoseUpload`
```json
{
  "id": 1,
  "date": "2026-03-06",
  "file_path": "uploads/2026-03-06/glucose-1.png",
  "uploaded_at": "2026-03-06T09:30:00Z",
  "summary": "Glucose rises after breakfast and stabilizes by midday.",
  "user_note": "Felt normal"
}
```

### `AssistantDraft`
```json
{
  "draft_type": "meal",
  "normalized_payload": {},
  "assumptions": [],
  "warnings": [],
  "confirm_before_save": true
}
```

## Endpoint contracts

### `GET /api/health`
Purpose: health check for local development and smoke tests.

Response `200`:
```json
{
  "status": "ok",
  "service": "backend",
  "environment": "development"
}
```

### `GET /api/day/{date}`
Status: planned for `codex/backend-ai-log`.

Response `200`:
- Returns a `DayLog` aggregate for the requested date.

### `POST /api/day/{date}/assistant/draft`
Status: planned for `codex/backend-ai-log`.

Request:
```json
{
  "input_text": "breakfast: oats, banana, yogurt",
  "source": "typed"
}
```

Response `200`:
- Returns an `AssistantDraft` object.

### `POST /api/day/{date}/meals`
Status: planned for `codex/backend-ai-log`.

Request:
- Confirmed meal payload derived from `AssistantDraft.normalized_payload`.

Response `201`:
- Returns persisted `MealEntry` and updated totals.

### `POST /api/day/{date}/glucose-uploads`
Status: planned for `codex/backend-ai-log`.

Request:
- `multipart/form-data` with image file and optional note.

Response `201`:
- Returns saved `GlucoseUpload` plus optional AI summary.

### `POST /api/strava/sync/recent`
Status: planned for `codex/strava-sync`.

Response `200`:
```json
{
  "synced_count": 0,
  "window_days": 7,
  "activities": []
}
```

### `GET /api/strava/connect`
Status: planned for `codex/strava-sync`.

Response `200`:
- Returns redirect URL or redirects directly.

### `GET /api/strava/callback`
Status: planned for `codex/strava-sync`.

Response `200`:
- Confirms OAuth callback processing.

## Compatibility rules for parallel branches
- Additive changes are preferred; avoid breaking existing field names.
- If a field must change, update this document and explain migration impact in PR notes.
- Keep uncertain AI outputs explicit through `assumptions`, `warnings`, and `confirm_before_save`.
