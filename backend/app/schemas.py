"""Pydantic schemas shared by API routes and services."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

MealSlot = Literal["breakfast", "lunch", "dinner", "snacks"]
MealStatus = Literal["needs_review", "confirmed", "edited"]


class FoodItem(BaseModel):
    """Normalized representation of one parsed food line item.

    Parameters:
        name: Canonical food name.
        quantity_text: Human-readable quantity extracted from user text.
        matched: Whether nutrition lookup found a known food profile.
        calories: Estimated calories for this item.
        protein_g: Estimated grams of protein.
        carbs_g: Estimated grams of carbohydrates.
        fat_g: Estimated grams of fat.

    Returns:
        FoodItem: Structured item data.

    Raises:
        pydantic.ValidationError: If provided fields fail validation.

    Example:
        >>> FoodItem(
        ...     name="banana",
        ...     quantity_text="1",
        ...     matched=True,
        ...     calories=105,
        ...     protein_g=1.3,
        ...     carbs_g=27,
        ...     fat_g=0.3,
        ... )
    """

    name: str
    quantity_text: str
    matched: bool
    calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None


class MealDraftPayload(BaseModel):
    """Meal payload returned by draft generation and accepted for persistence.

    Parameters:
        meal_slot: Destination meal slot.
        source_text: Original user text used to create the draft.
        items: Parsed list of food items.
        calories: Total estimated calories.
        protein_g: Total estimated protein.
        carbs_g: Total estimated carbohydrates.
        fat_g: Total estimated fat.
        confidence: Confidence score in the range ``0`` to ``1``.
        status: Current review status for this meal payload.

    Returns:
        MealDraftPayload: Normalized meal payload.

    Raises:
        pydantic.ValidationError: If payload values are invalid.

    Example:
        >>> MealDraftPayload(
        ...     meal_slot="breakfast",
        ...     source_text="oats and banana",
        ...     items=[],
        ...     calories=0,
        ...     protein_g=0,
        ...     carbs_g=0,
        ...     fat_g=0,
        ...     confidence=0.5,
        ...     status="needs_review",
        ... )
    """

    meal_slot: MealSlot
    source_text: str
    items: list[FoodItem]
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    confidence: float = Field(ge=0.0, le=1.0)
    status: MealStatus


class MealEntry(MealDraftPayload):
    """Persisted meal entry shape returned by the day-log APIs.

    Parameters:
        id: Database identifier.
        updated_at: ISO timestamp indicating the latest update.

    Returns:
        MealEntry: Meal payload with persistence metadata.

    Raises:
        pydantic.ValidationError: If persisted data is malformed.

    Example:
        >>> entry = MealEntry(
        ...     id=1,
        ...     meal_slot="lunch",
        ...     source_text="rice bowl",
        ...     items=[],
        ...     calories=0,
        ...     protein_g=0,
        ...     carbs_g=0,
        ...     fat_g=0,
        ...     confidence=0.8,
        ...     status="confirmed",
        ...     updated_at="2026-01-01T00:00:00Z",
        ... )
        >>> entry.id
        1
    """

    id: int
    updated_at: str


class ActivityEntry(BaseModel):
    """Normalized activity record used for Strava sync and day rendering.

    Parameters:
        strava_activity_id: Stable Strava activity identifier.
        name: Activity title.
        sport_type: Activity sport type.
        start_time: Activity start timestamp.
        elapsed_time_s: Duration in seconds.
        calories: Optional calories value from Strava.
        suffer_score: Optional suffer score value from Strava.
        rpe_override: Optional user-provided perceived effort override.

    Returns:
        ActivityEntry: Activity entry payload.

    Raises:
        pydantic.ValidationError: If activity values are invalid.

    Example:
        >>> ActivityEntry(
        ...     strava_activity_id="123",
        ...     name="Morning Run",
        ...     sport_type="Run",
        ...     start_time="2026-01-01T07:30:00Z",
        ...     elapsed_time_s=3600,
        ... )
    """

    strava_activity_id: str
    name: str
    sport_type: str
    start_time: str
    elapsed_time_s: int
    calories: float | None = None
    suffer_score: float | None = None
    rpe_override: int | None = None


class GlucoseUpload(BaseModel):
    """Metadata for one saved glucose screenshot upload.

    Parameters:
        id: Database identifier.
        file_url: Relative URL the frontend can render.
        original_filename: Original uploaded file name.
        uploaded_at: Upload timestamp.
        ai_summary: Descriptive non-medical summary.
        user_note: Optional user-authored note.

    Returns:
        GlucoseUpload: Upload metadata payload.

    Raises:
        pydantic.ValidationError: If upload values are invalid.

    Example:
        >>> GlucoseUpload(
        ...     id=1,
        ...     file_url="/uploads/2026-01-01/example.png",
        ...     original_filename="example.png",
        ...     uploaded_at="2026-01-01T09:00:00Z",
        ... )
    """

    id: int
    file_url: str
    original_filename: str
    uploaded_at: str
    ai_summary: str | None = None
    user_note: str | None = None


class DailyTotals(BaseModel):
    """Aggregated daily nutrition totals computed from saved meals.

    Parameters:
        calories: Sum of saved meal calories.
        protein_g: Sum of saved meal protein grams.
        carbs_g: Sum of saved meal carbohydrates grams.
        fat_g: Sum of saved meal fat grams.

    Returns:
        DailyTotals: Aggregate nutrition totals.

    Raises:
        pydantic.ValidationError: If totals are invalid.

    Example:
        >>> DailyTotals(calories=500, protein_g=20, carbs_g=70, fat_g=10)
    """

    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


class DayLogResponse(BaseModel):
    """Complete day-log aggregate returned by ``GET /api/day/{date}``.

    Parameters:
        date: ISO date string for the selected day.
        meal_entries: Saved meal entries for the date.
        activity_entries: Synced activities for the date.
        glucose_uploads: Uploaded glucose screenshots for the date.
        daily_notes: Optional free-form day note (unused in v1, reserved for parity).
        daily_totals: Aggregated nutrition totals.

    Returns:
        DayLogResponse: Full day aggregate payload.

    Raises:
        pydantic.ValidationError: If nested payloads are invalid.

    Example:
        >>> DayLogResponse(
        ...     date="2026-01-01",
        ...     meal_entries=[],
        ...     activity_entries=[],
        ...     glucose_uploads=[],
        ...     daily_notes="",
        ...     daily_totals=DailyTotals(calories=0, protein_g=0, carbs_g=0, fat_g=0),
        ... )
    """

    date: str
    meal_entries: list[MealEntry]
    activity_entries: list[ActivityEntry]
    glucose_uploads: list[GlucoseUpload]
    daily_notes: str
    daily_totals: DailyTotals


class AssistantDraft(BaseModel):
    """AI-assisted meal draft that the user must review before save.

    Parameters:
        draft_type: Draft category; currently always ``meal``.
        normalized_payload: Meal payload candidate ready for confirmation.
        assumptions: Human-readable assumptions made during parsing.
        warnings: Human-readable warnings about ambiguity or unknown foods.
        confirm_before_save: Whether user confirmation is required before persistence.

    Returns:
        AssistantDraft: Draft response payload.

    Raises:
        pydantic.ValidationError: If draft values are invalid.

    Example:
        >>> AssistantDraft(
        ...     draft_type="meal",
        ...     normalized_payload=MealDraftPayload(
        ...         meal_slot="breakfast",
        ...         source_text="oats",
        ...         items=[],
        ...         calories=0,
        ...         protein_g=0,
        ...         carbs_g=0,
        ...         fat_g=0,
        ...         confidence=0.5,
        ...         status="needs_review",
        ...     ),
        ...     assumptions=[],
        ...     warnings=[],
        ...     confirm_before_save=True,
        ... )
    """

    draft_type: Literal["meal"] = "meal"
    normalized_payload: MealDraftPayload
    assumptions: list[str]
    warnings: list[str]
    confirm_before_save: bool


class AssistantDraftRequest(BaseModel):
    """Request payload for generating a meal draft from free text.

    Parameters:
        text: Raw user-provided meal note.
        meal_slot_hint: Optional slot selected by the user in the UI.

    Returns:
        AssistantDraftRequest: Parsed request payload.

    Raises:
        pydantic.ValidationError: If input values are invalid.

    Example:
        >>> AssistantDraftRequest(text="banana and yogurt", meal_slot_hint="breakfast")
    """

    text: str = Field(min_length=1)
    meal_slot_hint: MealSlot | None = None


class MealSaveRequest(BaseModel):
    """Request payload for saving a confirmed meal draft.

    Parameters:
        meal_slot: Meal slot selected by the user.
        source_text: Original draft source text.
        items: Final reviewed food items.
        calories: Total calories.
        protein_g: Total protein grams.
        carbs_g: Total carbohydrates grams.
        fat_g: Total fat grams.
        confidence: Final confidence score.
        status: Meal status after confirmation.

    Returns:
        MealSaveRequest: Payload used for persistence.

    Raises:
        pydantic.ValidationError: If fields are invalid.

    Example:
        >>> MealSaveRequest(
        ...     meal_slot="dinner",
        ...     source_text="rice and chicken",
        ...     items=[],
        ...     calories=0,
        ...     protein_g=0,
        ...     carbs_g=0,
        ...     fat_g=0,
        ...     confidence=0.7,
        ...     status="confirmed",
        ... )
    """

    meal_slot: MealSlot
    source_text: str = Field(min_length=1)
    items: list[FoodItem]
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    confidence: float = Field(ge=0.0, le=1.0)
    status: MealStatus


class MealUpdateRequest(BaseModel):
    """Request payload for editing a previously saved meal entry.

    Parameters:
        meal_slot: Optional replacement meal slot.
        source_text: Optional replacement source text.
        status: Optional replacement meal status.

    Returns:
        MealUpdateRequest: Partial update payload.

    Raises:
        pydantic.ValidationError: If provided fields are invalid.

    Example:
        >>> MealUpdateRequest(source_text="updated text", status="edited")
    """

    meal_slot: MealSlot | None = None
    source_text: str | None = None
    status: MealStatus | None = None


class StravaSyncResult(BaseModel):
    """Summary payload returned after running recent Strava sync.

    Parameters:
        started_at: ISO timestamp for sync start.
        finished_at: ISO timestamp for sync completion.
        imported_count: Number of newly inserted activities.
        updated_count: Number of activities updated in-place.
        window_start: First synced date (inclusive).
        window_end: Last synced date (inclusive).
        status: Sync result status.

    Returns:
        StravaSyncResult: Sync summary payload.

    Raises:
        pydantic.ValidationError: If result fields are invalid.

    Example:
        >>> StravaSyncResult(
        ...     started_at="2026-01-01T00:00:00Z",
        ...     finished_at="2026-01-01T00:00:01Z",
        ...     imported_count=1,
        ...     updated_count=0,
        ...     window_start="2025-12-26",
        ...     window_end="2026-01-01",
        ...     status="success",
        ... )
    """

    started_at: str
    finished_at: str
    imported_count: int
    updated_count: int
    window_start: str
    window_end: str
    status: Literal["success", "partial", "failed"]


class StravaConnectResponse(BaseModel):
    """Payload for exposing Strava OAuth connect URL in the frontend.

    Parameters:
        configured: Whether required Strava environment settings are present.
        connect_url: OAuth URL to open when configured.
        message: Human-readable guidance for the current configuration state.

    Returns:
        StravaConnectResponse: OAuth connect payload.

    Raises:
        pydantic.ValidationError: If values are invalid.

    Example:
        >>> StravaConnectResponse(configured=False, connect_url=None, message="missing")
    """

    configured: bool
    connect_url: str | None
    message: str
