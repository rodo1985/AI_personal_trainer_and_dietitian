# Frontend Day-Log Mock Contracts and Backend Assumptions

## Purpose
This document captures the mocked API behavior used by the `codex/frontend-day-log` implementation.
It exists so the backend integration branch can replace adapters without guessing UI expectations.

## Implemented UI scope
The frontend now includes:
- Day selector with previous/next controls and a date picker.
- Meal sections for `breakfast`, `lunch`, `dinner`, and `snacks`.
- Activity panel.
- Glucose upload panel.
- Assistant composer with typed input and visible microphone trigger.
- Draft preview that requires confirmation before save.
- Empty, loading, and save-error states.

## Mocked endpoint assumptions

### `GET /api/day/{date}`
Expected response shape:
- `date`
- `meal_entries[]`
- `activity_entries[]`
- `glucose_uploads[]`
- `daily_notes`
- `daily_totals`

Frontend behavior assumptions:
- Request starts on first page render and when day changes.
- Empty arrays are valid and should render empty states.
- A fetch failure returns an error message string suitable for display.

### `POST /api/day/{date}/assistant/draft`
Expected request shape:
- `meal_slot`
- `source_text`

Expected response shape (`AssistantDraft`):
- `draft_type`
- `meal_slot`
- `source_text`
- `items[]`
- `totals`
- `assumptions[]`
- `warnings[]`
- `confirm_before_save`
- `confidence`

Frontend behavior assumptions:
- Empty `source_text` should return a user-friendly validation error.
- `confirm_before_save` is treated as required in v1.
- Warnings and assumptions are shown before save.

### `POST /api/day/{date}/meals`
Expected request shape:
- full `AssistantDraft` payload plus `date` context.

Expected response shape:
- updated `DayLog` aggregate for the selected date.

Frontend behavior assumptions:
- Save success returns updated meal entries and totals.
- Save failures return an explicit message the UI can show inline.

## Temporary mock-specific triggers
These are local test hooks and should be removed once live APIs are connected:
- Date `2026-03-04` intentionally throws a load error to exercise retry UI.
- Including `#fail-save` in draft source text forces a save error.
- Microphone flow inserts a mock transcript (`eggs, toast, avocado`) after a short delay.

## Test coverage summary
Frontend smoke tests (`frontend/src/__tests__/DayLogPage.test.tsx`) currently cover:
- Loading and initial day rendering.
- Day navigation with empty-state rendering.
- Draft creation and confirmed save flow.
- Save-error handling.
- Microphone trigger feedback and transcript insertion.
