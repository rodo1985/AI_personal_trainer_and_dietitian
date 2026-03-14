"""Day-log API routes for drafts, meal persistence, transcription, and uploads."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from backend.app.core.dependencies import (
    get_ai_client,
    get_day_log_repository,
    get_meal_draft_service,
    get_upload_storage,
)
from backend.app.models.schemas import (
    AssistantDraft,
    AssistantDraftRequest,
    DayLogResponse,
    GlucoseSummaryResult,
    GlucoseUploadResponse,
    MealEntryResponse,
    SaveMealRequest,
    TranscriptionDraftResponse,
)
from backend.app.repositories.day_log_repository import DayLogRepository
from backend.app.services.ai_client import AIClientProtocol
from backend.app.services.draft_pipeline import MealDraftService, estimate_draft_confidence
from backend.app.services.upload_storage import LocalUploadStorage

router = APIRouter(prefix="/api", tags=["day-log"])


@router.get("/day/{log_date}", response_model=DayLogResponse)
def get_day_log(
    log_date: str,
    repository: DayLogRepository = Depends(get_day_log_repository),
) -> DayLogResponse:
    """Return aggregate day data for the requested date.

    Parameters:
        log_date: Requested date in `YYYY-MM-DD` format.
        repository: Injected day-log repository.

    Returns:
        DayLogResponse: Aggregate payload for meals, activities, and uploads.

    Raises:
        HTTPException: If date format is invalid.

    Example:
        GET /api/day/2026-03-01
    """

    parsed_date = _parse_iso_date(log_date)
    return repository.get_day_log(parsed_date)


@router.post("/day/{log_date}/assistant/draft", response_model=AssistantDraft)
def create_assistant_draft(
    log_date: str,
    request: AssistantDraftRequest,
    draft_service: MealDraftService = Depends(get_meal_draft_service),
) -> AssistantDraft:
    """Generate a structured meal draft from typed or transcript text.

    Parameters:
        log_date: Day context in `YYYY-MM-DD` format.
        request: Draft request payload.
        draft_service: Injected draft generation service.

    Returns:
        AssistantDraft: Structured draft suitable for frontend preview.

    Raises:
        HTTPException: If date format or draft text is invalid.

    Example:
        POST /api/day/2026-03-01/assistant/draft
    """

    _parse_iso_date(log_date)
    try:
        return draft_service.build_draft(text=request.text, source=request.source)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post(
    "/day/{log_date}/assistant/transcribe",
    response_model=TranscriptionDraftResponse,
)
async def transcribe_audio_and_build_draft(
    log_date: str,
    file: UploadFile = File(...),
    draft_service: MealDraftService = Depends(get_meal_draft_service),
    ai_client: AIClientProtocol = Depends(get_ai_client),
) -> TranscriptionDraftResponse:
    """Transcribe uploaded audio and push transcript through the same draft pipeline.

    Parameters:
        log_date: Day context in `YYYY-MM-DD` format.
        file: Uploaded audio file.
        draft_service: Injected draft generation service.
        ai_client: Injected AI client used for transcription.

    Returns:
        TranscriptionDraftResponse: Transcript text plus structured draft.

    Raises:
        HTTPException: If date is invalid, file is empty, or transcription fails.

    Example:
        POST /api/day/2026-03-01/assistant/transcribe
    """

    _parse_iso_date(log_date)
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded audio file is empty.",
        )

    try:
        transcript_text = ai_client.transcribe_audio(
            audio_bytes=audio_bytes,
            filename=file.filename or "audio.wav",
            content_type=file.content_type or "application/octet-stream",
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    draft = draft_service.build_draft(text=transcript_text, source="transcript")
    return TranscriptionDraftResponse(transcript_text=transcript_text, draft=draft)


@router.post(
    "/day/{log_date}/meals",
    response_model=MealEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
def save_meal_entry(
    log_date: str,
    request: SaveMealRequest,
    repository: DayLogRepository = Depends(get_day_log_repository),
) -> MealEntryResponse:
    """Persist a confirmed assistant meal draft for the selected day.

    Parameters:
        log_date: Day context in `YYYY-MM-DD` format.
        request: Save request payload.
        repository: Injected day-log repository.

    Returns:
        MealEntryResponse: Persisted meal entry.

    Raises:
        HTTPException: If date is invalid, meal slot is missing, or confirmation is required.

    Example:
        POST /api/day/2026-03-01/meals
    """

    parsed_date = _parse_iso_date(log_date)

    if request.draft.confirm_before_save and not request.confirmation_acknowledged:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Draft requires explicit confirmation because the parser detected ambiguity "
                "or unresolved nutrition matches."
            ),
        )

    if request.draft.normalized_payload.meal_slot is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Meal slot is required before saving a meal.",
        )

    confidence = estimate_draft_confidence(request.draft)
    return repository.save_meal_entry(
        log_date=parsed_date,
        draft=request.draft,
        confidence=confidence,
    )


@router.post(
    "/day/{log_date}/glucose-uploads",
    response_model=GlucoseUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_glucose_screenshot(
    log_date: str,
    file: UploadFile = File(...),
    user_note: str | None = Form(default=None),
    repository: DayLogRepository = Depends(get_day_log_repository),
    ai_client: AIClientProtocol = Depends(get_ai_client),
    upload_storage: LocalUploadStorage = Depends(get_upload_storage),
) -> GlucoseUploadResponse:
    """Store glucose screenshot and return metadata plus descriptive AI summary.

    Parameters:
        log_date: Day context in `YYYY-MM-DD` format.
        file: Uploaded image file.
        user_note: Optional note to store with the upload.
        repository: Injected day-log repository.
        ai_client: Injected AI client used for screenshot summary.
        upload_storage: Injected local file storage service.

    Returns:
        GlucoseUploadResponse: Saved upload metadata and summary.

    Raises:
        HTTPException: If date is invalid, file is empty, or MIME type is not an image.

    Example:
        POST /api/day/2026-03-01/glucose-uploads
    """

    parsed_date = _parse_iso_date(log_date)
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Glucose upload endpoint only accepts image files.",
        )

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image file is empty.",
        )

    stored_upload = upload_storage.save_glucose_image(
        log_date=parsed_date,
        filename=file.filename or "glucose-image",
        content=image_bytes,
    )

    try:
        summary = ai_client.summarize_glucose_screenshot(
            image_bytes=image_bytes,
            filename=file.filename or "glucose-image",
            content_type=file.content_type,
        )
    except Exception:
        # Upload persistence should succeed even if AI summarization fails.
        summary = GlucoseSummaryResult(
            summary_text=(
                "Upload saved successfully, but AI summary failed. Review the screenshot manually."
            ),
            warnings=["AI summarization failed for this upload."],
        )

    return repository.save_glucose_upload(
        log_date=parsed_date,
        original_filename=file.filename or "glucose-image",
        stored_path=stored_upload.relative_path,
        mime_type=file.content_type,
        size_bytes=stored_upload.size_bytes,
        summary_text=summary.summary_text,
        summary_warnings=summary.warnings,
        user_note=user_note,
    )


def _parse_iso_date(raw_date: str) -> str:
    """Validate and normalize an ISO date path parameter.

    Parameters:
        raw_date: Raw date string from route parameter.

    Returns:
        str: Normalized `YYYY-MM-DD` date string.

    Raises:
        HTTPException: If the input does not follow ISO date format.

    Example:
        >>> _parse_iso_date("2026-03-01")
        '2026-03-01'
    """

    try:
        parsed = date.fromisoformat(raw_date)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Date must be in YYYY-MM-DD format.",
        ) from exc
    return parsed.isoformat()
