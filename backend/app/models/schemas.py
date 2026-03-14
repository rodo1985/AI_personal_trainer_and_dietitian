"""Shared API schemas for day logs, AI drafts, meals, and uploads."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MealSlot(str, Enum):
    """Supported meal slots for a single day.

    Attributes:
        BREAKFAST: Morning meal slot.
        LUNCH: Midday meal slot.
        DINNER: Evening meal slot.
        SNACKS: Snacks grouped under one slot.
    """

    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACKS = "snacks"


class NutritionTotals(BaseModel):
    """Macro nutrition totals used by meal items and day summaries.

    Attributes:
        calories: Estimated calories in kilocalories.
        protein_g: Protein grams.
        carbs_g: Carbohydrate grams.
        fat_g: Fat grams.
    """

    calories: float = Field(default=0.0, ge=0)
    protein_g: float = Field(default=0.0, ge=0)
    carbs_g: float = Field(default=0.0, ge=0)
    fat_g: float = Field(default=0.0, ge=0)


class DraftFoodItem(BaseModel):
    """One parsed food item within an assistant meal draft.

    Attributes:
        raw_text: Raw text fragment parsed from user input.
        canonical_name: Matched canonical food name when a catalog match exists.
        quantity: Human-readable quantity extracted from the text.
        estimated_servings: Numeric serving multiplier used for totals.
        matched: Whether nutrition lookup matched this food.
        match_confidence: Confidence score for the catalog match when available.
        nutrition: Matched nutrition totals for this item when available.
        unresolved_reason: Why the item could not be matched with confidence.
    """

    raw_text: str = Field(min_length=1)
    canonical_name: str | None = None
    quantity: str | None = None
    estimated_servings: float | None = Field(default=None, ge=0)
    matched: bool
    match_confidence: float | None = Field(default=None, ge=0, le=1)
    nutrition: NutritionTotals | None = None
    unresolved_reason: str | None = None


class MealDraftPayload(BaseModel):
    """Normalized draft payload that the frontend can preview before save.

    Attributes:
        meal_slot: Parsed meal slot when present in the source text.
        source_text: Original text used to generate the draft.
        items: Parsed food items with match metadata.
        totals: Totals from matched foods only.
    """

    meal_slot: MealSlot | None = None
    source_text: str = Field(min_length=1)
    items: list[DraftFoodItem] = Field(default_factory=list)
    totals: NutritionTotals = Field(default_factory=NutritionTotals)


class AssistantDraft(BaseModel):
    """Root assistant draft shape returned by draft endpoints.

    Attributes:
        draft_type: Type of draft payload; currently only meal drafts are supported.
        normalized_payload: Structured draft payload for UI review.
        assumptions: Explicit assumptions made by parsing logic.
        warnings: Cautions that should be visible before save.
        confirm_before_save: Indicates whether extra confirmation is required.
    """

    draft_type: Literal["meal"] = "meal"
    normalized_payload: MealDraftPayload
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confirm_before_save: bool = False


class AssistantDraftRequest(BaseModel):
    """Input schema for creating a structured assistant draft.

    Attributes:
        text: Typed text or transcript text from the user.
        source: Origin of text, used for downstream assumptions.
    """

    text: str = Field(min_length=1)
    source: Literal["typed", "transcript"] = "typed"


class SaveMealRequest(BaseModel):
    """Request schema for persisting a confirmed meal draft.

    Attributes:
        draft: Assistant draft that was reviewed by the user.
        confirmation_acknowledged: Explicit acknowledgment for ambiguous drafts.
    """

    draft: AssistantDraft
    confirmation_acknowledged: bool = False


class MealEntryResponse(BaseModel):
    """Persisted meal entry returned after save and in day aggregates.

    Attributes:
        id: Database identifier.
        date: ISO date for the day log (`YYYY-MM-DD`).
        meal_slot: Saved meal slot.
        source_text: Original text used for the draft.
        items: Saved parsed item list.
        totals: Final saved meal totals.
        confidence: Aggregate confidence score for the draft.
        status: Entry state; v1 uses `confirmed` only.
        assumptions: Assumptions stored with the entry.
        warnings: Warnings stored with the entry.
        created_at: UTC timestamp for creation.
    """

    model_config = ConfigDict(use_enum_values=True)

    id: int
    date: str
    meal_slot: MealSlot
    source_text: str
    items: list[DraftFoodItem] = Field(default_factory=list)
    totals: NutritionTotals
    confidence: float = Field(ge=0, le=1)
    status: Literal["confirmed"] = "confirmed"
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime


class ActivityEntryResponse(BaseModel):
    """Normalized activity entry in the day aggregate response.

    Attributes:
        id: Database identifier.
        strava_activity_id: Strava activity identifier when synced.
        name: Activity name.
        sport_type: Activity type from Strava.
        start_time: Activity start timestamp.
        elapsed_time_s: Duration in seconds.
        calories: Optional calorie value from Strava.
        suffer_score: Optional suffer score from Strava.
        rpe_override: Optional manual RPE override.
    """

    id: int
    strava_activity_id: str | None = None
    name: str
    sport_type: str
    start_time: datetime
    elapsed_time_s: int = Field(ge=0)
    calories: float | None = Field(default=None, ge=0)
    suffer_score: float | None = Field(default=None, ge=0)
    rpe_override: int | None = Field(default=None, ge=0, le=10)


class GlucoseUploadResponse(BaseModel):
    """Metadata for one glucose screenshot upload.

    Attributes:
        id: Database identifier.
        date: ISO date for the day log (`YYYY-MM-DD`).
        original_filename: Original uploaded filename.
        stored_path: Relative filesystem path used by the backend.
        mime_type: MIME type recorded for the uploaded image.
        size_bytes: Uploaded file size in bytes.
        summary_text: AI-generated descriptive summary.
        summary_warnings: Warnings or caveats for the summary.
        user_note: Optional user note provided with the upload.
        created_at: UTC timestamp for upload creation.
    """

    id: int
    date: str
    original_filename: str
    stored_path: str
    mime_type: str
    size_bytes: int = Field(ge=0)
    summary_text: str
    summary_warnings: list[str] = Field(default_factory=list)
    user_note: str | None = None
    created_at: datetime


class DayLogResponse(BaseModel):
    """Aggregate day-log object combining meals, activities, and uploads.

    Attributes:
        date: ISO day key (`YYYY-MM-DD`).
        meal_entries: All meal entries saved for the day.
        activity_entries: All activity entries for the day.
        glucose_uploads: All glucose uploads for the day.
        daily_notes: Optional plain-text notes for the day.
        daily_totals: Macro totals aggregated from meal entries.
    """

    date: str
    meal_entries: list[MealEntryResponse] = Field(default_factory=list)
    activity_entries: list[ActivityEntryResponse] = Field(default_factory=list)
    glucose_uploads: list[GlucoseUploadResponse] = Field(default_factory=list)
    daily_notes: str | None = None
    daily_totals: NutritionTotals = Field(default_factory=NutritionTotals)


class TranscriptionDraftResponse(BaseModel):
    """Response schema for audio transcription followed by draft parsing.

    Attributes:
        transcript_text: Transcript generated from uploaded audio.
        draft: Structured meal draft generated from that transcript.
    """

    transcript_text: str = Field(min_length=1)
    draft: AssistantDraft


class GlucoseSummaryResult(BaseModel):
    """Structured glucose summary emitted by the AI service layer.

    Attributes:
        summary_text: Descriptive text about the visible chart patterns.
        warnings: Safety or confidence caveats attached to the summary.
    """

    summary_text: str = Field(min_length=1)
    warnings: list[str] = Field(default_factory=list)


class MealStructureHint(BaseModel):
    """Optional AI-extracted structure hint used by the draft pipeline.

    Attributes:
        meal_slot: Suggested meal slot inferred by AI.
        food_items: Suggested item list from the source text.
        assumptions: Assumptions surfaced by the model.
        warnings: Model warnings about ambiguity.
    """

    meal_slot: MealSlot | None = None
    food_items: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
