# Personal Endurance Trainer Log Prototype

## Summary
- Build a single-user, local-first web app that combines meals, Strava activities, and glucose screenshots into one daily log.
- Use `React + TypeScript` for the frontend, `FastAPI + Python` for the backend, `uv` for Python setup, `SQLite` for v1 persistence, and local file storage for glucose screenshots.
- Use only OpenAI models for AI features: meal parsing, glucose screenshot summarization, and audio transcription.
- Ship v1 with meal logging, voice-to-text input, 7-day Strava sync, glucose screenshot upload, and a day summary view.
- Keep v1 out of scope for multi-user auth, direct Abbott/Libre API integration, MyFitnessPal sync, realtime Strava webhooks, and medical recommendations.

## Product goals
- Make it fast to capture what was eaten, what training happened, and what glucose patterns were observed on a specific day.
- Keep the logging flow simple enough for daily use on mobile and desktop.
- Let the user review AI-generated drafts before they are committed to the day log.
- Keep the first version grounded in descriptive tracking, not coaching claims or medical advice.

## Core user flows
1. Open the app and land on a day view with the current date selected.
2. Trigger a recent Strava sync for the rolling last 7 days and show any activities already associated with the selected day.
3. Type or dictate a meal note into the assistant composer, review the generated structured draft, and confirm it into the correct meal slot.
4. Upload a glucose screenshot for the selected day, store the image, and generate a descriptive summary of what is visible in the chart.
5. Review meals, activities, glucose uploads, and day totals together in one summary screen.

## Proposed architecture

### Frontend
- `React + TypeScript`
- Mobile-first day log UI
- Assistant composer with text input, microphone capture, draft preview, and save action
- Separate panels for meals, activities, and glucose uploads

### Backend
- `FastAPI` application with modular routers
- SQLite persistence for day logs, meals, activities, uploads, and sync metadata
- Local file storage for uploaded glucose screenshots
- Service layer for OpenAI calls, nutrition matching, and Strava synchronization

### AI stack
- Use OpenAI structured outputs for meal draft parsing and screenshot interpretation
- Use an OpenAI transcription model for microphone uploads
- Keep model IDs configurable through environment variables
- Return assumptions and confidence notes whenever the model output needs user confirmation

## Parallel worktrees
The project is intentionally split so multiple agents can work at the same time with minimal overlap.

1. `codex/foundation`
   - Create the repo scaffold, `pyproject.toml`, uv workflow, FastAPI app shell, React app shell, SQLite setup, shared API contract, env loading, and the project README.
   - If there is legacy Strava setup documentation in the root README at implementation time, move it into `docs/integrations/strava-mcp.md`.

2. `codex/frontend-day-log`
   - Build the day selector, meal sections, activity panel, glucose panel, assistant composer, mic button, draft preview, save button, and responsive layout against mocked backend responses.

3. `codex/backend-ai-log`
   - Build the day-log aggregate endpoints, assistant draft pipeline, nutrition lookup service, meal persistence, audio transcription endpoint, glucose screenshot upload endpoint, and AI-generated glucose summary.

4. `codex/strava-sync`
   - Implement Strava OAuth connect flow, token storage and refresh, recent-activity sync for the rolling last 7 days, idempotent upserts by Strava activity ID, and normalized activity records.

5. `codex/integration-hardening`
   - Replace mocks with live APIs, add loading and error states, add empty states and edit flows, verify idempotent sync behavior, add automated tests, and finish docs.

## Public interfaces and behavior

### Domain objects
- `DayLog`
  - `date`
  - `meal_entries`
  - `activity_entries`
  - `glucose_uploads`
  - `daily_notes`
  - `daily_totals`

- `MealEntry`
  - `meal_slot`
  - `source_text`
  - `items`
  - `calories`
  - `protein_g`
  - `carbs_g`
  - `fat_g`
  - `confidence`
  - `status`

- `ActivityEntry`
  - `strava_activity_id`
  - `name`
  - `sport_type`
  - `start_time`
  - `elapsed_time_s`
  - `calories`
  - `suffer_score`
  - optional `rpe_override`

- `GlucoseUpload`
  - image file metadata
  - upload timestamp
  - optional AI summary
  - optional user note

- `AssistantDraft`
  - draft type
  - normalized structured payload
  - assumptions
  - warnings
  - `confirm_before_save`

### Planned API endpoints
- `GET /api/day/{date}` returns the full aggregate day log.
- `POST /api/day/{date}/assistant/draft` accepts typed text or transcript text and returns a structured draft for preview.
- `POST /api/day/{date}/meals` saves a confirmed meal draft.
- `POST /api/day/{date}/glucose-uploads` stores a screenshot and returns the saved upload plus AI summary.
- `POST /api/strava/sync/recent` syncs the rolling last 7 days and upserts activities without duplicates.
- `GET /api/strava/connect` and `GET /api/strava/callback` handle OAuth setup.

## Phased delivery plan

### Phase 1: Foundation and contracts
- Create the Python and frontend scaffolds.
- Establish folder structure, environment loading, and SQLite initialization.
- Define shared data contracts and mock API responses.
- Rewrite `README.md` for the actual application instead of placeholder content.

### Phase 2: Daily logging UI
- Build the day selector and day summary layout.
- Implement meal sections and assistant draft review in the UI.
- Add microphone capture in the frontend and wire it to a mocked transcription flow first.
- Support glucose screenshot upload in the day view.

### Phase 3: AI-assisted logging backend
- Implement meal parsing with OpenAI structured outputs.
- Match parsed foods against a nutrition source and calculate totals.
- Add save flows for confirmed meal drafts.
- Add audio transcription and glucose screenshot summarization endpoints.

### Phase 4: Strava integration
- Implement connect, callback, token refresh, and recent sync.
- Normalize Strava activity fields into local activity records.
- Make repeated sync operations idempotent.
- Trigger sync when the app opens or when the user switches to a recent day.

### Phase 5: Integration and hardening
- Replace mocks with live backend and frontend wiring.
- Add loading, empty, and error states throughout the app.
- Add tests across backend services and frontend user flows.
- Finish README, env docs, and contributor guidance.

## Testing plan
- Meal draft parsing turns natural language such as `breakfast: oats with banana and yogurt` into the correct meal slot, food items, quantities, and totals.
- Ambiguous meal text returns assumptions and requires confirmation before save.
- Voice input records audio, transcribes it, and sends the transcript through the same draft pipeline.
- Nutrition lookup calculates stable totals for matched foods and clearly flags unmatched foods instead of silently inventing precise values.
- Opening the app or changing to a recent day syncs the last 7 days from Strava and does not create duplicates on repeated syncs.
- Activities render correctly when `calories` or `suffer_score` are missing.
- Glucose screenshot upload stores the file, shows the image in the day view, and displays a descriptive AI summary without claiming medical certainty.
- Day totals update after saving meals, and the summary screen shows meals, activities, and glucose data together.
- Frontend smoke tests cover desktop and mobile layouts for log creation, review, and save flows.

## README deliverable
- Rewrite `README.md` to describe the app instead of a placeholder stub.
- Include these exact sections: `What this repo is`, `Key features / scope`, `Setup`, `How to run`, `Configuration`, `Project structure`, and `Contributing / Development notes`.
- In `Setup`, document `uv venv`, `uv sync`, frontend install, and exact local startup commands once the scaffold exists.
- In `How to run`, include backend dev, frontend dev, tests, lint, and build commands.
- In `Configuration`, include `OPENAI_API_KEY`, `OPENAI_MEAL_MODEL`, `OPENAI_TRANSCRIBE_MODEL`, `OPENAI_VISION_MODEL`, `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_REDIRECT_URI`, `DATABASE_URL`, and `UPLOAD_DIR`.
- In `Project structure`, explain the backend app, frontend app, docs folder, and local uploads or data area.

## Assumptions and defaults
- Phase 1 is for one personal user only, so there is no auth system in v1.
- The first shipped prototype is local-first and uses rolling 7-day polling instead of webhooks.
- Meals are AI-parsed but still manually confirmed before persistence.
- Glucose handling is descriptive and observational only, not medical guidance.
- Model IDs should be env-configured, with a GPT-5.2-class model for structured meal and screenshot interpretation and an OpenAI transcription model for audio.

## Coordination rules for parallel work
- Every worktree should read this document before implementation starts.
- `codex/foundation` defines the baseline structure and shared contracts; other worktrees should avoid rewriting those files unless absolutely necessary.
- Feature worktrees should document assumptions when the foundation scaffold is not available yet.
- Any branch that changes setup, configuration, or folder structure must also update `README.md`.
- Save merge-conflict-prone decisions in docs instead of hiding them in code comments or commit messages.
