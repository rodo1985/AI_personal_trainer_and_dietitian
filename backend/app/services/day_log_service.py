"""Persistence and aggregation helpers for day-log workflows."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from sqlite3 import Row

from fastapi import HTTPException

from backend.app.config import Settings
from backend.app.database import get_connection
from backend.app.schemas import (
    ActivityEntry,
    DailyTotals,
    DayLogResponse,
    GlucoseUpload,
    MealEntry,
    MealSaveRequest,
    MealUpdateRequest,
)


def get_day_log(settings: Settings, target_date: date) -> DayLogResponse:
    """Load the full day-log aggregate from SQLite.

    Parameters:
        settings: Application settings used to open the database.
        target_date: Date for which data should be loaded.

    Returns:
        DayLogResponse: Aggregate day payload including meals, activities, uploads, and totals.

    Raises:
        sqlite3.Error: If database read operations fail.

    Example:
        >>> from datetime import date
        >>> isinstance(get_day_log, object)
        True
    """

    day_key = target_date.isoformat()

    with get_connection(settings) as conn:
        meal_rows = conn.execute(
            """
            SELECT id, meal_slot, source_text, items_json, calories, protein_g, carbs_g, fat_g,
                   confidence, status, updated_at
            FROM meal_entries
            WHERE day_date = ?
            ORDER BY id DESC
            """,
            (day_key,),
        ).fetchall()

        activity_rows = conn.execute(
            """
            SELECT strava_activity_id, name, sport_type, start_time, elapsed_time_s,
                   calories, suffer_score, rpe_override
            FROM activities
            WHERE day_date = ?
            ORDER BY start_time DESC
            """,
            (day_key,),
        ).fetchall()

        upload_rows = conn.execute(
            """
            SELECT id, file_path, original_filename, uploaded_at, ai_summary, user_note
            FROM glucose_uploads
            WHERE day_date = ?
            ORDER BY uploaded_at DESC
            """,
            (day_key,),
        ).fetchall()

        totals_row = conn.execute(
            """
            SELECT
                COALESCE(SUM(calories), 0) AS calories,
                COALESCE(SUM(protein_g), 0) AS protein_g,
                COALESCE(SUM(carbs_g), 0) AS carbs_g,
                COALESCE(SUM(fat_g), 0) AS fat_g
            FROM meal_entries
            WHERE day_date = ?
            """,
            (day_key,),
        ).fetchone()

    meals = [meal_entry_from_row(row) for row in meal_rows]
    activities = [activity_entry_from_row(row) for row in activity_rows]
    uploads = [glucose_upload_from_row(row) for row in upload_rows]

    daily_totals = DailyTotals(
        calories=float(totals_row["calories"]),
        protein_g=float(totals_row["protein_g"]),
        carbs_g=float(totals_row["carbs_g"]),
        fat_g=float(totals_row["fat_g"]),
    )

    return DayLogResponse(
        date=day_key,
        meal_entries=meals,
        activity_entries=activities,
        glucose_uploads=uploads,
        daily_notes="",
        daily_totals=daily_totals,
    )


def save_meal_entry(settings: Settings, target_date: date, request: MealSaveRequest) -> MealEntry:
    """Persist a confirmed meal draft into the day log.

    Parameters:
        settings: Application settings used to open the database.
        target_date: Date that owns the meal entry.
        request: Confirmed meal payload from the frontend.

    Returns:
        MealEntry: Newly persisted meal entry.

    Raises:
        sqlite3.Error: If insert operations fail.

    Example:
        >>> isinstance(save_meal_entry, object)
        True
    """

    now = utcnow_iso()
    payload_json = json.dumps([item.model_dump() for item in request.items])

    with get_connection(settings) as conn:
        cursor = conn.execute(
            """
            INSERT INTO meal_entries (
                day_date,
                meal_slot,
                source_text,
                items_json,
                calories,
                protein_g,
                carbs_g,
                fat_g,
                confidence,
                status,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                target_date.isoformat(),
                request.meal_slot,
                request.source_text,
                payload_json,
                request.calories,
                request.protein_g,
                request.carbs_g,
                request.fat_g,
                request.confidence,
                request.status,
                now,
                now,
            ),
        )

        row = conn.execute(
            """
            SELECT id, meal_slot, source_text, items_json, calories, protein_g, carbs_g, fat_g,
                   confidence, status, updated_at
            FROM meal_entries
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

    return meal_entry_from_row(row)


def update_meal_entry(
    settings: Settings,
    target_date: date,
    meal_entry_id: int,
    request: MealUpdateRequest,
) -> MealEntry:
    """Update selected fields of an existing meal entry.

    Parameters:
        settings: Application settings used to open the database.
        target_date: Date that owns the meal entry.
        meal_entry_id: Numeric ID of the meal row to update.
        request: Partial update payload with mutable fields.

    Returns:
        MealEntry: Updated meal entry.

    Raises:
        fastapi.HTTPException: If the meal entry does not exist for the given day.
        sqlite3.Error: If update operations fail.

    Example:
        >>> isinstance(update_meal_entry, object)
        True
    """

    day_key = target_date.isoformat()

    with get_connection(settings) as conn:
        existing = conn.execute(
            """
            SELECT id, meal_slot, source_text, items_json, calories, protein_g, carbs_g, fat_g,
                   confidence, status, updated_at
            FROM meal_entries
            WHERE id = ? AND day_date = ?
            """,
            (meal_entry_id, day_key),
        ).fetchone()

        if existing is None:
            raise HTTPException(
                status_code=404,
                detail="Meal entry not found for the selected day.",
            )

        updated_meal_slot = request.meal_slot or existing["meal_slot"]
        updated_source_text = request.source_text or existing["source_text"]
        updated_status = request.status or "edited"

        # Keep nutritional totals unchanged when editing text-only fields. This keeps
        # v1 deterministic and avoids silently re-running uncertain nutrition parsing.
        conn.execute(
            """
            UPDATE meal_entries
            SET meal_slot = ?, source_text = ?, status = ?, updated_at = ?
            WHERE id = ? AND day_date = ?
            """,
            (
                updated_meal_slot,
                updated_source_text,
                updated_status,
                utcnow_iso(),
                meal_entry_id,
                day_key,
            ),
        )

        updated_row = conn.execute(
            """
            SELECT id, meal_slot, source_text, items_json, calories, protein_g, carbs_g, fat_g,
                   confidence, status, updated_at
            FROM meal_entries
            WHERE id = ? AND day_date = ?
            """,
            (meal_entry_id, day_key),
        ).fetchone()

    return meal_entry_from_row(updated_row)


def save_glucose_upload(
    settings: Settings,
    target_date: date,
    file_path: str,
    original_filename: str,
    ai_summary: str,
    user_note: str | None,
) -> GlucoseUpload:
    """Persist one glucose upload metadata row.

    Parameters:
        settings: Application settings used to open the database.
        target_date: Date that owns the upload.
        file_path: Relative path to stored upload file.
        original_filename: Original file name from the client.
        ai_summary: Descriptive AI summary text.
        user_note: Optional user note supplied during upload.

    Returns:
        GlucoseUpload: Newly persisted upload metadata.

    Raises:
        sqlite3.Error: If insert operations fail.

    Example:
        >>> isinstance(save_glucose_upload, object)
        True
    """

    now = utcnow_iso()

    with get_connection(settings) as conn:
        cursor = conn.execute(
            """
            INSERT INTO glucose_uploads (
                day_date,
                file_path,
                original_filename,
                uploaded_at,
                ai_summary,
                user_note
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (target_date.isoformat(), file_path, original_filename, now, ai_summary, user_note),
        )

        row = conn.execute(
            """
            SELECT id, file_path, original_filename, uploaded_at, ai_summary, user_note
            FROM glucose_uploads
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

    return glucose_upload_from_row(row)


def upsert_activity_entries(settings: Settings, activities: list[ActivityEntry]) -> tuple[int, int]:
    """Insert or update activity rows keyed by ``strava_activity_id``.

    Parameters:
        settings: Application settings used to open the database.
        activities: Normalized activity entries to persist.

    Returns:
        tuple[int, int]: Number of inserted rows and number of updated rows.

    Raises:
        sqlite3.Error: If upsert operations fail.

    Example:
        >>> upsert_activity_entries.__name__
        'upsert_activity_entries'
    """

    imported_count = 0
    updated_count = 0
    synced_at = utcnow_iso()

    with get_connection(settings) as conn:
        for activity in activities:
            day_key = activity.start_time[:10]
            existing = conn.execute(
                "SELECT id FROM activities WHERE strava_activity_id = ?",
                (activity.strava_activity_id,),
            ).fetchone()

            if existing is None:
                conn.execute(
                    """
                    INSERT INTO activities (
                        strava_activity_id,
                        day_date,
                        name,
                        sport_type,
                        start_time,
                        elapsed_time_s,
                        calories,
                        suffer_score,
                        rpe_override,
                        synced_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        activity.strava_activity_id,
                        day_key,
                        activity.name,
                        activity.sport_type,
                        activity.start_time,
                        activity.elapsed_time_s,
                        activity.calories,
                        activity.suffer_score,
                        activity.rpe_override,
                        synced_at,
                    ),
                )
                imported_count += 1
                continue

            conn.execute(
                """
                UPDATE activities
                SET day_date = ?,
                    name = ?,
                    sport_type = ?,
                    start_time = ?,
                    elapsed_time_s = ?,
                    calories = ?,
                    suffer_score = ?,
                    rpe_override = ?,
                    synced_at = ?
                WHERE strava_activity_id = ?
                """,
                (
                    day_key,
                    activity.name,
                    activity.sport_type,
                    activity.start_time,
                    activity.elapsed_time_s,
                    activity.calories,
                    activity.suffer_score,
                    activity.rpe_override,
                    synced_at,
                    activity.strava_activity_id,
                ),
            )
            updated_count += 1

    return imported_count, updated_count


def record_sync_run(
    settings: Settings,
    started_at: str,
    finished_at: str,
    status: str,
    imported_count: int,
    updated_count: int,
    error_message: str | None = None,
) -> None:
    """Persist sync metadata so repeated failures are diagnosable.

    Parameters:
        settings: Application settings used to open the database.
        started_at: ISO sync start timestamp.
        finished_at: ISO sync completion timestamp.
        status: Sync status string.
        imported_count: Number of inserted rows.
        updated_count: Number of updated rows.
        error_message: Optional error message for failed runs.

    Returns:
        None.

    Raises:
        sqlite3.Error: If insert operations fail.

    Example:
        >>> isinstance(record_sync_run, object)
        True
    """

    with get_connection(settings) as conn:
        conn.execute(
            """
            INSERT INTO sync_runs (
                started_at,
                finished_at,
                status,
                imported_count,
                updated_count,
                error_message
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (started_at, finished_at, status, imported_count, updated_count, error_message),
        )


def meal_entry_from_row(row: Row) -> MealEntry:
    """Convert a SQLite meal row into ``MealEntry`` schema.

    Parameters:
        row: SQLite row containing meal columns.

    Returns:
        MealEntry: Parsed meal entry.

    Raises:
        json.JSONDecodeError: If ``items_json`` is malformed.

    Example:
        >>> isinstance(meal_entry_from_row, object)
        True
    """

    parsed_items = json.loads(row["items_json"])
    return MealEntry(
        id=int(row["id"]),
        meal_slot=row["meal_slot"],
        source_text=row["source_text"],
        items=parsed_items,
        calories=float(row["calories"]),
        protein_g=float(row["protein_g"]),
        carbs_g=float(row["carbs_g"]),
        fat_g=float(row["fat_g"]),
        confidence=float(row["confidence"]),
        status=row["status"],
        updated_at=row["updated_at"],
    )


def activity_entry_from_row(row: Row) -> ActivityEntry:
    """Convert a SQLite activity row into ``ActivityEntry`` schema.

    Parameters:
        row: SQLite row containing activity columns.

    Returns:
        ActivityEntry: Parsed activity entry.

    Raises:
        None.

    Example:
        >>> isinstance(activity_entry_from_row, object)
        True
    """

    return ActivityEntry(
        strava_activity_id=row["strava_activity_id"],
        name=row["name"],
        sport_type=row["sport_type"],
        start_time=row["start_time"],
        elapsed_time_s=int(row["elapsed_time_s"]),
        calories=float(row["calories"]) if row["calories"] is not None else None,
        suffer_score=float(row["suffer_score"]) if row["suffer_score"] is not None else None,
        rpe_override=int(row["rpe_override"]) if row["rpe_override"] is not None else None,
    )


def glucose_upload_from_row(row: Row) -> GlucoseUpload:
    """Convert a SQLite upload row into ``GlucoseUpload`` schema.

    Parameters:
        row: SQLite row containing upload columns.

    Returns:
        GlucoseUpload: Parsed upload metadata.

    Raises:
        None.

    Example:
        >>> isinstance(glucose_upload_from_row, object)
        True
    """

    return GlucoseUpload(
        id=int(row["id"]),
        file_url=row["file_path"],
        original_filename=row["original_filename"],
        uploaded_at=row["uploaded_at"],
        ai_summary=row["ai_summary"],
        user_note=row["user_note"],
    )


def utcnow_iso() -> str:
    """Return the current UTC timestamp in ISO-8601 format.

    Parameters:
        None.

    Returns:
        str: UTC timestamp with timezone suffix.

    Raises:
        None.

    Example:
        >>> isinstance(utcnow_iso(), str)
        True
    """

    return datetime.now(tz=UTC).isoformat()
