"""FastAPI route handlers for day-log and integration workflows."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from backend.app.config import Settings, get_settings
from backend.app.schemas import (
    AssistantDraft,
    AssistantDraftRequest,
    DayLogResponse,
    GlucoseUpload,
    MealEntry,
    MealSaveRequest,
    MealUpdateRequest,
    StravaConnectResponse,
    StravaSyncResult,
)
from backend.app.services.day_log_service import (
    get_day_log,
    save_glucose_upload,
    save_meal_entry,
    update_meal_entry,
)
from backend.app.services.glucose_service import build_descriptive_summary, persist_upload_file
from backend.app.services.meal_draft_service import build_meal_draft
from backend.app.services.strava_sync_service import build_connect_payload, sync_recent_activities

router = APIRouter()


def parse_iso_date(day_iso: str) -> date:
    """Parse path date values and raise user-facing errors when invalid.

    Parameters:
        day_iso: Date string expected in ``YYYY-MM-DD`` format.

    Returns:
        date: Parsed Python date object.

    Raises:
        fastapi.HTTPException: If the date format is invalid.

    Example:
        >>> parse_iso_date("2026-01-01").isoformat()
        '2026-01-01'
    """

    try:
        return date.fromisoformat(day_iso)
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail="Date must be formatted as YYYY-MM-DD.",
        ) from error


@router.get("/day/{day_iso}", response_model=DayLogResponse)
def read_day_log(
    day_iso: str,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> DayLogResponse:
    """Return the aggregate day log for one selected date.

    Parameters:
        day_iso: Date path parameter in ISO format.
        settings: Injected application settings.

    Returns:
        DayLogResponse: Full day aggregate payload.

    Raises:
        fastapi.HTTPException: If date parsing fails.

    Example:
        >>> read_day_log.__name__
        'read_day_log'
    """

    target_date = parse_iso_date(day_iso)
    return get_day_log(settings, target_date)


@router.post("/day/{day_iso}/assistant/draft", response_model=AssistantDraft)
def create_assistant_draft(
    day_iso: str,
    payload: AssistantDraftRequest,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> AssistantDraft:
    """Generate a meal draft from free text for preview before save.

    Parameters:
        day_iso: Date path parameter in ISO format.
        payload: Draft request containing free text and optional slot hint.
        settings: Injected application settings.

    Returns:
        AssistantDraft: Parsed draft payload including assumptions and warnings.

    Raises:
        fastapi.HTTPException: If text parsing fails.

    Example:
        >>> create_assistant_draft.__name__
        'create_assistant_draft'
    """

    _ = settings  # Reserved for future OpenAI-backed draft calls.
    _ = parse_iso_date(day_iso)

    try:
        return build_meal_draft(payload.text, payload.meal_slot_hint)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/day/{day_iso}/meals", response_model=MealEntry)
def create_meal_entry(
    day_iso: str,
    payload: MealSaveRequest,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> MealEntry:
    """Persist a confirmed meal draft.

    Parameters:
        day_iso: Date path parameter in ISO format.
        payload: Reviewed meal payload to save.
        settings: Injected application settings.

    Returns:
        MealEntry: Newly created meal entry.

    Raises:
        fastapi.HTTPException: If date parsing fails.

    Example:
        >>> create_meal_entry.__name__
        'create_meal_entry'
    """

    target_date = parse_iso_date(day_iso)
    return save_meal_entry(settings, target_date, payload)


@router.put("/day/{day_iso}/meals/{meal_id}", response_model=MealEntry)
def edit_meal_entry(
    day_iso: str,
    meal_id: int,
    payload: MealUpdateRequest,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> MealEntry:
    """Edit a saved meal entry without re-running AI parsing.

    Parameters:
        day_iso: Date path parameter in ISO format.
        meal_id: Numeric meal entry identifier.
        payload: Partial update payload for editable fields.
        settings: Injected application settings.

    Returns:
        MealEntry: Updated meal entry.

    Raises:
        fastapi.HTTPException: If the meal entry is missing.

    Example:
        >>> edit_meal_entry.__name__
        'edit_meal_entry'
    """

    target_date = parse_iso_date(day_iso)
    return update_meal_entry(settings, target_date, meal_id, payload)


@router.post("/day/{day_iso}/glucose-uploads", response_model=GlucoseUpload)
async def create_glucose_upload(
    day_iso: str,
    file: UploadFile = File(...),  # noqa: B008
    user_note: str | None = Form(default=None),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> GlucoseUpload:
    """Store an uploaded glucose screenshot and return metadata for day rendering.

    Parameters:
        day_iso: Date path parameter in ISO format.
        file: Uploaded glucose screenshot file.
        user_note: Optional user note supplied by the client.
        settings: Injected application settings.

    Returns:
        GlucoseUpload: Persisted upload metadata.

    Raises:
        fastapi.HTTPException: If file type is unsupported.

    Example:
        >>> create_glucose_upload.__name__
        'create_glucose_upload'
    """

    target_date = parse_iso_date(day_iso)

    if not file.filename:
        raise HTTPException(status_code=400, detail="Upload file name is required.")

    accepted_extensions = (".png", ".jpg", ".jpeg", ".webp")
    if not file.filename.lower().endswith(accepted_extensions):
        raise HTTPException(
            status_code=400,
            detail="Only image uploads (.png, .jpg, .jpeg, .webp) are supported.",
        )

    file_url = await persist_upload_file(settings, target_date, file)
    ai_summary = build_descriptive_summary(file.filename, user_note)

    return save_glucose_upload(
        settings=settings,
        target_date=target_date,
        file_path=file_url,
        original_filename=file.filename,
        ai_summary=ai_summary,
        user_note=user_note,
    )


@router.post("/strava/sync/recent", response_model=StravaSyncResult)
def run_recent_strava_sync(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> StravaSyncResult:
    """Run the rolling seven-day Strava sync and return summary metadata.

    Parameters:
        settings: Injected application settings.

    Returns:
        StravaSyncResult: Sync summary counts and date window.

    Raises:
        Exception: Propagates unexpected persistence errors.

    Example:
        >>> run_recent_strava_sync.__name__
        'run_recent_strava_sync'
    """

    return sync_recent_activities(settings)


@router.get("/strava/connect", response_model=StravaConnectResponse)
def get_strava_connect(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> StravaConnectResponse:
    """Return OAuth connection details for Strava setup.

    Parameters:
        settings: Injected application settings.

    Returns:
        StravaConnectResponse: Connection state and optional OAuth URL.

    Raises:
        None.

    Example:
        >>> get_strava_connect.__name__
        'get_strava_connect'
    """

    return build_connect_payload(settings)


@router.get("/strava/callback")
def strava_oauth_callback(code: str | None = None, state: str | None = None) -> dict[str, str]:
    """Handle OAuth callback for local prototype diagnostics.

    Parameters:
        code: Optional authorization code returned by Strava.
        state: Optional state string returned by Strava.

    Returns:
        dict[str, str]: Human-readable callback acknowledgement.

    Raises:
        None.

    Example:
        >>> strava_oauth_callback(code="abc")["status"]
        'received'
    """

    if code:
        return {
            "status": "received",
            "message": (
                "OAuth callback received. Token exchange should be "
                "completed in Strava branch integration."
            ),
            "state": state or "",
        }

    return {
        "status": "missing_code",
        "message": "No code was provided by Strava callback request.",
        "state": state or "",
    }
