"""Repository for day-log aggregation and persistence operations."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from backend.app.core.database import Database
from backend.app.models.schemas import (
    ActivityEntryResponse,
    AssistantDraft,
    DayLogResponse,
    DraftFoodItem,
    GlucoseUploadResponse,
    MealEntryResponse,
    MealSlot,
    NutritionTotals,
)


class DayLogRepository:
    """Handle persistence and reads for day logs, meals, and uploads.

    Parameters:
        database: Database helper used for SQLite access.

    Example:
        >>> from pathlib import Path
        >>> repo = DayLogRepository(Database(Path("data/example.db")))
        >>> isinstance(repo, DayLogRepository)
        True
    """

    def __init__(self, database: Database) -> None:
        """Store the database dependency for later repository calls.

        Parameters:
            database: Configured database helper.

        Returns:
            None.
        """

        self._database = database

    def get_day_log(self, log_date: str) -> DayLogResponse:
        """Return aggregate day data including meals, activities, and uploads.

        Parameters:
            log_date: Day key in ISO format (`YYYY-MM-DD`).

        Returns:
            DayLogResponse: Aggregate day payload.

        Raises:
            json.JSONDecodeError: If persisted JSON columns are malformed.

        Example:
            >>> isinstance(self.get_day_log("2026-01-01"), DayLogResponse)  # doctest: +SKIP
            True
        """

        with self._database.connection() as conn:
            meal_rows = conn.execute(
                "SELECT * FROM meal_entries WHERE log_date = ? ORDER BY id ASC",
                (log_date,),
            ).fetchall()
            activity_rows = conn.execute(
                "SELECT * FROM activity_entries WHERE log_date = ? ORDER BY id ASC",
                (log_date,),
            ).fetchall()
            upload_rows = conn.execute(
                "SELECT * FROM glucose_uploads WHERE log_date = ? ORDER BY id ASC",
                (log_date,),
            ).fetchall()

        meal_entries = [_meal_entry_from_row(dict(row)) for row in meal_rows]
        activity_entries = [_activity_from_row(dict(row)) for row in activity_rows]
        uploads = [_glucose_upload_from_row(dict(row)) for row in upload_rows]

        daily_totals = NutritionTotals(
            calories=round(sum(entry.totals.calories for entry in meal_entries), 2),
            protein_g=round(sum(entry.totals.protein_g for entry in meal_entries), 2),
            carbs_g=round(sum(entry.totals.carbs_g for entry in meal_entries), 2),
            fat_g=round(sum(entry.totals.fat_g for entry in meal_entries), 2),
        )

        return DayLogResponse(
            date=log_date,
            meal_entries=meal_entries,
            activity_entries=activity_entries,
            glucose_uploads=uploads,
            daily_notes=None,
            daily_totals=daily_totals,
        )

    def save_meal_entry(
        self,
        log_date: str,
        draft: AssistantDraft,
        confidence: float,
    ) -> MealEntryResponse:
        """Persist a confirmed meal draft and return the saved entry.

        Parameters:
            log_date: Day key in ISO format (`YYYY-MM-DD`).
            draft: Reviewed assistant draft payload.
            confidence: Aggregate confidence score for the draft.

        Returns:
            MealEntryResponse: Saved meal entry.

        Raises:
            ValueError: If draft does not contain a meal slot.

        Example:
            >>> # See integration tests for a full save/load example.
            >>> isinstance(confidence, float)
            True
        """

        payload = draft.normalized_payload
        if payload.meal_slot is None:
            raise ValueError("Meal slot must be selected before saving a meal entry.")

        created_at = datetime.now(timezone.utc)
        with self._database.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO meal_entries (
                    log_date,
                    meal_slot,
                    source_text,
                    items_json,
                    calories,
                    protein_g,
                    carbs_g,
                    fat_g,
                    confidence,
                    status,
                    assumptions_json,
                    warnings_json,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log_date,
                    payload.meal_slot.value,
                    payload.source_text,
                    _json_dump([item.model_dump(mode="json") for item in payload.items]),
                    payload.totals.calories,
                    payload.totals.protein_g,
                    payload.totals.carbs_g,
                    payload.totals.fat_g,
                    confidence,
                    "confirmed",
                    _json_dump(draft.assumptions),
                    _json_dump(draft.warnings),
                    created_at.isoformat(),
                ),
            )
            meal_id = int(cursor.lastrowid)

        return MealEntryResponse(
            id=meal_id,
            date=log_date,
            meal_slot=payload.meal_slot,
            source_text=payload.source_text,
            items=payload.items,
            totals=payload.totals,
            confidence=confidence,
            status="confirmed",
            assumptions=draft.assumptions,
            warnings=draft.warnings,
            created_at=created_at,
        )

    def save_glucose_upload(
        self,
        log_date: str,
        original_filename: str,
        stored_path: str,
        mime_type: str,
        size_bytes: int,
        summary_text: str,
        summary_warnings: list[str],
        user_note: str | None,
    ) -> GlucoseUploadResponse:
        """Persist glucose screenshot metadata and summary.

        Parameters:
            log_date: Day key in ISO format (`YYYY-MM-DD`).
            original_filename: Client-provided filename.
            stored_path: Relative storage path for the saved file.
            mime_type: MIME type from upload metadata.
            size_bytes: File size in bytes.
            summary_text: AI-generated summary text.
            summary_warnings: AI-generated warning messages.
            user_note: Optional note captured at upload time.

        Returns:
            GlucoseUploadResponse: Saved upload metadata.

        Example:
            >>> isinstance(size_bytes, int)
            True
        """

        created_at = datetime.now(timezone.utc)
        with self._database.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO glucose_uploads (
                    log_date,
                    original_filename,
                    stored_path,
                    mime_type,
                    size_bytes,
                    summary_text,
                    summary_warnings_json,
                    user_note,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log_date,
                    original_filename,
                    stored_path,
                    mime_type,
                    size_bytes,
                    summary_text,
                    _json_dump(summary_warnings),
                    user_note,
                    created_at.isoformat(),
                ),
            )
            upload_id = int(cursor.lastrowid)

        return GlucoseUploadResponse(
            id=upload_id,
            date=log_date,
            original_filename=original_filename,
            stored_path=stored_path,
            mime_type=mime_type,
            size_bytes=size_bytes,
            summary_text=summary_text,
            summary_warnings=summary_warnings,
            user_note=user_note,
            created_at=created_at,
        )


def _meal_entry_from_row(row: dict) -> MealEntryResponse:
    """Convert a SQLite row dictionary into a meal response model.

    Parameters:
        row: Meal row from SQLite.

    Returns:
        MealEntryResponse: Parsed response model.

    Example:
        >>> _meal_entry_from_row({})  # doctest: +SKIP
    """

    item_models = [DraftFoodItem.model_validate(item) for item in _json_load(row["items_json"])]
    return MealEntryResponse(
        id=int(row["id"]),
        date=row["log_date"],
        meal_slot=MealSlot(row["meal_slot"]),
        source_text=row["source_text"],
        items=item_models,
        totals=NutritionTotals(
            calories=float(row["calories"]),
            protein_g=float(row["protein_g"]),
            carbs_g=float(row["carbs_g"]),
            fat_g=float(row["fat_g"]),
        ),
        confidence=float(row["confidence"]),
        status="confirmed",
        assumptions=_json_load(row["assumptions_json"]),
        warnings=_json_load(row["warnings_json"]),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _activity_from_row(row: dict) -> ActivityEntryResponse:
    """Convert a SQLite row dictionary into an activity response model.

    Parameters:
        row: Activity row from SQLite.

    Returns:
        ActivityEntryResponse: Parsed response model.

    Example:
        >>> _activity_from_row({})  # doctest: +SKIP
    """

    return ActivityEntryResponse(
        id=int(row["id"]),
        strava_activity_id=row["strava_activity_id"],
        name=row["name"],
        sport_type=row["sport_type"],
        start_time=datetime.fromisoformat(row["start_time"]),
        elapsed_time_s=int(row["elapsed_time_s"]),
        calories=float(row["calories"]) if row["calories"] is not None else None,
        suffer_score=float(row["suffer_score"]) if row["suffer_score"] is not None else None,
        rpe_override=int(row["rpe_override"]) if row["rpe_override"] is not None else None,
    )


def _glucose_upload_from_row(row: dict) -> GlucoseUploadResponse:
    """Convert a SQLite row dictionary into a glucose upload response model.

    Parameters:
        row: Upload row from SQLite.

    Returns:
        GlucoseUploadResponse: Parsed response model.

    Example:
        >>> _glucose_upload_from_row({})  # doctest: +SKIP
    """

    return GlucoseUploadResponse(
        id=int(row["id"]),
        date=row["log_date"],
        original_filename=row["original_filename"],
        stored_path=row["stored_path"],
        mime_type=row["mime_type"],
        size_bytes=int(row["size_bytes"]),
        summary_text=row["summary_text"],
        summary_warnings=_json_load(row["summary_warnings_json"]),
        user_note=row["user_note"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _json_dump(value: object) -> str:
    """Serialize data into stable JSON for SQLite text columns.

    Parameters:
        value: JSON-serializable object.

    Returns:
        str: Serialized JSON string.

    Example:
        >>> _json_dump(["x"]) 
        '["x"]'
    """

    return json.dumps(value, separators=(",", ":"))


def _json_load(raw: str) -> list:
    """Deserialize JSON string stored in SQLite.

    Parameters:
        raw: Raw JSON text.

    Returns:
        list: Parsed list payload.

    Example:
        >>> _json_load('["x"]')
        ['x']
    """

    parsed = json.loads(raw)
    if not isinstance(parsed, list):
        raise ValueError("Expected JSON array payload.")
    return parsed
