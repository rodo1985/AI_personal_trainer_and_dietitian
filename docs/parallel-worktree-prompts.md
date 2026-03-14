# Parallel Worktree Agent Prompts

Use these prompts as copy-paste starting points for parallel Codex worktrees.
Each prompt references the shared plan at [docs/implementation-plan.md](./implementation-plan.md) so all branches work from the same assumptions.

## Shared instructions for every agent
- Read [docs/implementation-plan.md](./implementation-plan.md) before making changes.
- Keep the project single-user and local-first for v1.
- Use only OpenAI models for AI features.
- Do not add multi-user auth, direct Abbott/Libre API integration, MyFitnessPal sync, realtime Strava webhooks, or medical recommendations.
- Do not delete or rewrite another worktree's scope without a clear reason.
- Update `README.md` and docs whenever your changes affect setup, behavior, configuration, or developer workflow.
- Add or update tests for behavior changes in your scope.

## Prompt 1: `codex/foundation`
```text
You are working in the `codex/foundation` worktree for the Personal Endurance Trainer Log Prototype.

Start by reading:
- docs/implementation-plan.md
- README.md

Your mission is to create the initial project scaffold that every other worktree will build on.

Scope you own:
- Root repository structure
- Python project initialization with uv
- FastAPI backend shell
- React + TypeScript frontend shell
- SQLite initialization approach
- Shared API contract documentation
- Environment loading and `.env.example`
- Root README rewrite so a new contributor can set up and run the scaffold
- Any initial docs needed to explain the chosen structure

Target stack:
- Backend: Python + FastAPI
- Frontend: React + TypeScript
- Persistence: SQLite
- AI provider: OpenAI only

Deliverables:
- A runnable FastAPI starter app with a health endpoint
- A runnable React starter app with a simple shell page
- A documented folder structure for backend, frontend, docs, uploads, and local data
- A clear `README.md` with setup, run, configuration, project structure, and development notes
- A shared API contract document that the frontend and backend branches can both follow
- Environment variable documentation including OpenAI and Strava settings

Suggested file ownership:
- `pyproject.toml`
- backend scaffold under `backend/`
- frontend scaffold under `frontend/`
- `.env.example`
- shared docs under `docs/`
- root `README.md`

Constraints:
- Optimize for clarity and maintainability over cleverness
- Add docstrings for every new Python function, method, and class
- Add inline comments for non-obvious setup decisions
- Keep the app shell intentionally small; do not implement full meal, Strava, or upload features here
- If you introduce a shared schema format, document it in a way that the other worktrees can import or copy without ambiguity

Acceptance criteria:
- Backend and frontend both start locally with documented commands
- The repository has a concrete `uv` workflow
- The README is accurate and useful for a new contributor
- Other worktrees can start from the scaffold without guessing folder names or API shapes

Before finishing:
- Run the setup, lint, and tests that exist in your scaffold
- Summarize any decisions that downstream worktrees must know about
```

## Prompt 2: `codex/frontend-day-log`
```text
You are working in the `codex/frontend-day-log` worktree for the Personal Endurance Trainer Log Prototype.

Start by reading:
- docs/implementation-plan.md
- README.md
- Any API contract or mock data docs created by `codex/foundation`

Your mission is to build the first usable day-log interface against mocked backend responses.

Scope you own:
- Day selector UI
- Meal sections for breakfast, lunch, dinner, and snacks
- Activity panel
- Glucose upload panel
- Assistant composer
- Microphone input trigger in the UI
- Draft preview and save confirmation flow
- Mobile-first responsive layout
- Frontend tests for the main logging flow

Expected behavior:
- The selected day shows meals, activities, and glucose uploads together
- The composer accepts typed text and can start a voice-to-text flow
- The user can review an AI-generated draft before saving it to the day
- The UI gracefully handles empty days, loading states, and save errors

Suggested file ownership:
- React components under `frontend/src/components/`
- Route or page files under `frontend/src/`
- UI state hooks and local adapters under `frontend/src/`
- Frontend mocks and fixtures
- Frontend tests

Constraints:
- Preserve the shared contracts from the foundation branch
- Use mocked API adapters if the live backend is not ready yet
- Do not implement Strava OAuth or backend persistence logic in the frontend branch
- Keep the UI intentionally practical for daily use on mobile and desktop
- Make the microphone action visible in the UI even if the final backend transcription is not merged yet

Design goals:
- Clear day-based workflow
- Low-friction meal entry
- Strong visibility of draft review before save
- Distinct sections for meals, activities, and glucose observations

Acceptance criteria:
- A user can navigate between days and understand the page immediately
- A mocked meal draft can be created, reviewed, and saved into a meal section
- Mocked activities and glucose uploads render in a coherent daily summary
- The UI has empty, loading, and error states
- Frontend smoke tests cover the main day-log flow

Before finishing:
- Re-read the plan doc and confirm the implemented UI still matches v1 scope
- Document any backend assumptions you had to make
```

## Prompt 3: `codex/backend-ai-log`
```text
You are working in the `codex/backend-ai-log` worktree for the Personal Endurance Trainer Log Prototype.

Start by reading:
- docs/implementation-plan.md
- README.md
- Any backend scaffold or API contract docs from `codex/foundation`

Your mission is to implement the backend flows for AI-assisted logging.

Scope you own:
- Day-log aggregate read endpoint
- Assistant draft endpoint for typed text or transcript text
- Meal persistence endpoint
- Nutrition lookup and total calculation service
- Audio transcription endpoint using OpenAI
- Glucose screenshot upload endpoint
- AI-generated glucose screenshot summary
- Backend tests for parsing, validation, persistence, and upload behavior

Required product behavior:
- Free-text meal input becomes a structured draft with assumptions and warnings when needed
- Ambiguous input must require confirmation before save
- Nutrition totals should come from a lookup source and must not silently invent precise values for unmatched foods
- Glucose screenshot analysis must stay descriptive and avoid medical claims
- Audio transcription should feed the same draft pipeline as typed text

Suggested file ownership:
- Backend routers and schemas for day logs, meals, uploads, and transcription
- AI service layer under `backend/`
- Nutrition matching logic
- Persistence code for meal entries and glucose uploads
- Backend tests for the flows above

Constraints:
- Use only OpenAI models
- Keep model IDs configurable through environment variables
- Write clear docstrings for every Python function, method, and class
- Add inline comments for non-obvious validation and confidence-handling rules
- Do not implement Strava OAuth or sync logic in this worktree

Implementation notes:
- Use structured outputs for meal draft parsing and glucose screenshot interpretation
- Return a normalized `AssistantDraft` shape that the frontend can preview before save
- Keep unresolved food matches visible to the user instead of hiding uncertainty
- Store uploads locally and return enough metadata for the frontend day view to render them

Acceptance criteria:
- `GET /api/day/{date}` returns an aggregate day object
- `POST /api/day/{date}/assistant/draft` returns a structured preview payload
- `POST /api/day/{date}/meals` persists confirmed meal data
- `POST /api/day/{date}/glucose-uploads` saves the file and returns a summary payload
- Audio transcription and typed text both use the same meal draft pipeline
- Automated tests cover ambiguity handling, unmatched foods, and upload behavior

Before finishing:
- Run backend tests and linting
- Document any nutrition lookup limitations or manual confirmation rules
```

## Prompt 4: `codex/strava-sync`
```text
You are working in the `codex/strava-sync` worktree for the Personal Endurance Trainer Log Prototype.

Start by reading:
- docs/implementation-plan.md
- README.md
- Any backend scaffold and configuration docs from `codex/foundation`

Your mission is to implement the Strava integration for the rolling 7-day activity sync.

Scope you own:
- Strava OAuth connect flow
- OAuth callback handling
- Secure token storage and refresh
- Rolling 7-day recent activity sync
- Idempotent upsert logic keyed by Strava activity ID
- Activity normalization into the local schema
- Backend tests for sync and refresh behavior
- Docs for required Strava setup and local configuration

Required product behavior:
- The app can connect to one Strava account for the single-user prototype
- Sync fetches recent activities for the last 7 days
- Repeated syncs do not create duplicate activities
- Activities persist even when optional Strava fields like calories or suffer score are absent
- If Strava does not expose a clean perceived-effort field, support an optional manual `rpe_override`

Suggested file ownership:
- Strava integration code under `backend/`
- Token persistence and refresh utilities
- Activity mapping and sync services
- Tests focused on OAuth, sync windows, and idempotent writes
- Integration docs for Strava configuration

Constraints:
- Do not add realtime webhook processing in v1
- Keep sync polling-based and triggered from recent-day usage
- Avoid touching meal parsing, upload analysis, or frontend layout beyond what is strictly needed for integration points
- Document the exact env vars and callback expectations in README or docs

Implementation notes:
- Use Strava fields such as name, sport type, start time, elapsed time, calories, and suffer score when available
- Normalize API responses into the shared `ActivityEntry` shape from the plan doc
- Prefer explicit sync metadata so failures and partial syncs are diagnosable

Acceptance criteria:
- Connect and callback routes work locally with documented setup
- Recent sync imports only the rolling last 7 days
- Sync is idempotent on repeated runs
- Missing optional Strava fields do not break persistence or API responses
- Tests cover token refresh and duplicate prevention

Before finishing:
- Run backend tests relevant to the integration
- Document any Strava API caveats that the integration-hardening branch should know about
```

## Prompt 5: `codex/integration-hardening`
```text
You are working in the `codex/integration-hardening` worktree for the Personal Endurance Trainer Log Prototype.

Start by reading:
- docs/implementation-plan.md
- README.md
- The merged or latest outputs from the foundation, frontend, backend AI, and Strava worktrees

Your mission is to wire the pieces together, reduce rough edges, and make the prototype stable enough for end-to-end evaluation.

Scope you own:
- Replace frontend mocks with live backend integrations
- Add loading, empty, and error states across the full app
- Verify recent-day Strava sync behavior from the UI flow
- Add edit and retry flows where the prototype would otherwise dead-end
- Add automated tests across key backend and frontend flows
- Finish documentation and handoff notes

Required product behavior:
- Opening the app or navigating to a recent day can trigger the rolling 7-day sync safely
- Meal draft, review, save, and day-summary flows work against live APIs
- Glucose uploads appear in the day view after save
- Failure states are visible and recoverable instead of silent

Suggested file ownership:
- Integration glue across `frontend/` and `backend/`
- Shared tests, smoke tests, and regression coverage
- Final README and docs polishing

Constraints:
- Respect the architecture and contracts already established unless a change is clearly necessary
- If you must change a shared contract, update both sides and document the reason
- Keep v1 scope tight; do not expand into new product areas
- Preserve the descriptive, non-medical framing around glucose summaries

Acceptance criteria:
- The prototype works end-to-end for day selection, meal logging, recent activity sync, and glucose upload
- Loading, empty, and error states exist in all key flows
- Automated tests cover the highest-risk paths
- README and env docs match the final runnable setup

Before finishing:
- Run the relevant backend and frontend test suites
- Produce a concise list of any remaining gaps that should wait for a later phase instead of slipping into v1
```
