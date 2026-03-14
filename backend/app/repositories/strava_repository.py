"""Persistence operations for Strava OAuth state, activities, and sync metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from backend.app.db import get_connection


@dataclass(slots=True)
class StoredStravaTokens:
    """Represent encrypted OAuth token state stored in SQLite.

    Parameters:
        athlete_id: Numeric Strava athlete identifier.
        encrypted_access_token: Encrypted access token.
        encrypted_refresh_token: Encrypted refresh token.
        expires_at: UTC token expiry timestamp.
        scope: Granted OAuth scope string.
        token_type: Token type returned by Strava.

    Returns:
        StoredStravaTokens: Token state object.

    Raises:
        None.

    Example:
        >>> tokens = StoredStravaTokens(
        ...     1, "enc_a", "enc_r", datetime.now(UTC), None, "Bearer"
        ... )
        >>> tokens.athlete_id
        1
    """

    athlete_id: int
    encrypted_access_token: str
    encrypted_refresh_token: str
    expires_at: datetime
    scope: str | None
    token_type: str | None


@dataclass(slots=True)
class ActivityRecord:
    """Represent a normalized activity row persisted locally.

    Parameters:
        strava_activity_id: Unique Strava activity identifier.
        name: Activity title.
        sport_type: Strava sport type value.
        start_time: UTC start time.
        elapsed_time_s: Activity duration in seconds.
        calories: Optional calorie estimate.
        suffer_score: Optional suffer score.
        rpe_override: Optional manual perceived effort override.
        source_raw_json: Original Strava payload, serialized as JSON.
        synced_at: UTC timestamp indicating last sync update.

    Returns:
        ActivityRecord: Activity row object.

    Raises:
        None.

    Example:
        >>> record = ActivityRecord(
        ...     "1",
        ...     "Morning Run",
        ...     "Run",
        ...     datetime.now(UTC),
        ...     1800,
        ...     None,
        ...     None,
        ...     None,
        ...     "{}",
        ...     datetime.now(UTC),
        ... )
        >>> record.sport_type
        'Run'
    """

    strava_activity_id: str
    name: str
    sport_type: str
    start_time: datetime
    elapsed_time_s: int
    calories: float | None
    suffer_score: int | None
    rpe_override: int | None
    source_raw_json: str
    synced_at: datetime


@dataclass(slots=True)
class SyncRunSummary:
    """Represent persisted sync metadata for a single sync execution.

    Parameters:
        id: Unique sync run identifier in SQLite.
        status: Terminal sync status string.
        window_start: Inclusive UTC sync window start.
        window_end: Inclusive UTC sync window end.
        fetched_count: Number of raw activities fetched from Strava.
        upserted_count: Number of activities upserted locally.
        error_message: Optional failure details when status is `failed`.

    Returns:
        SyncRunSummary: Structured sync metadata object.

    Raises:
        None.

    Example:
        >>> SyncRunSummary(
        ...     1, "success", datetime.now(UTC), datetime.now(UTC), 0, 0, None
        ... )
    """

    id: int
    status: str
    window_start: datetime
    window_end: datetime
    fetched_count: int
    upserted_count: int
    error_message: str | None


class StravaRepository:
    """Encapsulate all SQLite reads and writes for Strava integration.

    Parameters:
        database_path: Filesystem path to the SQLite database file.

    Returns:
        StravaRepository: Repository instance bound to one database.

    Raises:
        sqlite3.Error: Raised when SQL operations fail.

    Example:
        >>> from pathlib import Path
        >>> repo = StravaRepository(Path("data/app.db"))
        >>> isinstance(repo, StravaRepository)
        True
    """

    def __init__(self, database_path: Path) -> None:
        """Initialize repository with a database path.

        Parameters:
            database_path: SQLite file path.

        Returns:
            None.

        Raises:
            None.

        Example:
            >>> from pathlib import Path
            >>> StravaRepository(Path("data/app.db"))
            <...StravaRepository object ...>
        """

        self._database_path = database_path

    def upsert_tokens(
        self,
        athlete_id: int,
        encrypted_access_token: str,
        encrypted_refresh_token: str,
        expires_at: datetime,
        scope: str | None,
        token_type: str | None,
    ) -> None:
        """Insert or update the single-user token row.

        Parameters:
            athlete_id: Numeric Strava athlete identifier.
            encrypted_access_token: Encrypted access token.
            encrypted_refresh_token: Encrypted refresh token.
            expires_at: UTC expiry time for access token.
            scope: OAuth scope returned by Strava.
            token_type: OAuth token type returned by Strava.

        Returns:
            None.

        Raises:
            sqlite3.Error: Raised when token persistence fails.

        Example:
            >>> # repo.upsert_tokens(...)
        """

        with get_connection(self._database_path) as connection:
            connection.execute(
                """
                INSERT INTO strava_tokens (
                    id,
                    athlete_id,
                    encrypted_access_token,
                    encrypted_refresh_token,
                    expires_at,
                    scope,
                    token_type,
                    updated_at
                )
                VALUES (1, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    athlete_id = excluded.athlete_id,
                    encrypted_access_token = excluded.encrypted_access_token,
                    encrypted_refresh_token = excluded.encrypted_refresh_token,
                    expires_at = excluded.expires_at,
                    scope = excluded.scope,
                    token_type = excluded.token_type,
                    updated_at = excluded.updated_at
                """,
                (
                    athlete_id,
                    encrypted_access_token,
                    encrypted_refresh_token,
                    int(expires_at.timestamp()),
                    scope,
                    token_type,
                    datetime.now(UTC).isoformat(),
                ),
            )
            connection.commit()

    def get_tokens(self) -> StoredStravaTokens | None:
        """Return stored OAuth tokens for the connected account, if present.

        Parameters:
            None.

        Returns:
            StoredStravaTokens | None: Token state, or `None` when not connected.

        Raises:
            sqlite3.Error: Raised when token reads fail.

        Example:
            >>> # tokens = repo.get_tokens()
        """

        with get_connection(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT
                    athlete_id,
                    encrypted_access_token,
                    encrypted_refresh_token,
                    expires_at,
                    scope,
                    token_type
                FROM strava_tokens
                WHERE id = 1
                """
            ).fetchone()

        if row is None:
            return None

        return StoredStravaTokens(
            athlete_id=int(row["athlete_id"]),
            encrypted_access_token=str(row["encrypted_access_token"]),
            encrypted_refresh_token=str(row["encrypted_refresh_token"]),
            expires_at=datetime.fromtimestamp(int(row["expires_at"]), tz=UTC),
            scope=row["scope"],
            token_type=row["token_type"],
        )

    def create_sync_run(self, window_start: datetime, window_end: datetime) -> int:
        """Create a sync run record before fetching activities.

        Parameters:
            window_start: UTC sync window start.
            window_end: UTC sync window end.

        Returns:
            int: Database identifier for the created sync run.

        Raises:
            sqlite3.Error: Raised when insert fails.

        Example:
            >>> # run_id = repo.create_sync_run(start, end)
        """

        with get_connection(self._database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO strava_sync_runs (
                    started_at,
                    status,
                    window_start,
                    window_end,
                    fetched_count,
                    upserted_count,
                    error_message
                )
                VALUES (?, 'running', ?, ?, 0, 0, NULL)
                """,
                (
                    datetime.now(UTC).isoformat(),
                    window_start.isoformat(),
                    window_end.isoformat(),
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def complete_sync_run(
        self,
        run_id: int,
        status: str,
        fetched_count: int,
        upserted_count: int,
        error_message: str | None,
    ) -> SyncRunSummary:
        """Finalize a sync run with counts and terminal status.

        Parameters:
            run_id: Existing sync run ID.
            status: Terminal status (`success` or `failed`).
            fetched_count: Number of Strava activities fetched.
            upserted_count: Number of activities upserted.
            error_message: Optional error text for failure diagnostics.

        Returns:
            SyncRunSummary: The persisted summary after update.

        Raises:
            RuntimeError: Raised when the run ID does not exist.
            sqlite3.Error: Raised when update fails.

        Example:
            >>> # summary = repo.complete_sync_run(1, 'success', 4, 4, None)
        """

        with get_connection(self._database_path) as connection:
            connection.execute(
                """
                UPDATE strava_sync_runs
                SET
                    completed_at = ?,
                    status = ?,
                    fetched_count = ?,
                    upserted_count = ?,
                    error_message = ?
                WHERE id = ?
                """,
                (
                    datetime.now(UTC).isoformat(),
                    status,
                    fetched_count,
                    upserted_count,
                    error_message,
                    run_id,
                ),
            )

            row = connection.execute(
                """
                SELECT
                    id,
                    status,
                    window_start,
                    window_end,
                    fetched_count,
                    upserted_count,
                    error_message
                FROM strava_sync_runs
                WHERE id = ?
                """,
                (run_id,),
            ).fetchone()
            connection.commit()

        if row is None:
            raise RuntimeError(f"Sync run {run_id} was not found after completion update.")

        return SyncRunSummary(
            id=int(row["id"]),
            status=str(row["status"]),
            window_start=datetime.fromisoformat(str(row["window_start"])),
            window_end=datetime.fromisoformat(str(row["window_end"])),
            fetched_count=int(row["fetched_count"]),
            upserted_count=int(row["upserted_count"]),
            error_message=row["error_message"],
        )

    def upsert_activities(self, activities: list[ActivityRecord]) -> int:
        """Upsert activities by Strava activity ID for idempotent sync behavior.

        Parameters:
            activities: Normalized activity records to write.

        Returns:
            int: Number of processed activities.

        Raises:
            sqlite3.Error: Raised when write operations fail.

        Example:
            >>> # count = repo.upsert_activities([activity])
        """

        if not activities:
            return 0

        with get_connection(self._database_path) as connection:
            for activity in activities:
                connection.execute(
                    """
                    INSERT INTO strava_activities (
                        strava_activity_id,
                        name,
                        sport_type,
                        start_time,
                        elapsed_time_s,
                        calories,
                        suffer_score,
                        rpe_override,
                        source_raw_json,
                        synced_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(strava_activity_id) DO UPDATE SET
                        name = excluded.name,
                        sport_type = excluded.sport_type,
                        start_time = excluded.start_time,
                        elapsed_time_s = excluded.elapsed_time_s,
                        calories = excluded.calories,
                        suffer_score = excluded.suffer_score,
                        source_raw_json = excluded.source_raw_json,
                        synced_at = excluded.synced_at
                    """,
                    (
                        activity.strava_activity_id,
                        activity.name,
                        activity.sport_type,
                        activity.start_time.isoformat(),
                        activity.elapsed_time_s,
                        activity.calories,
                        activity.suffer_score,
                        activity.rpe_override,
                        activity.source_raw_json,
                        activity.synced_at.isoformat(),
                    ),
                )
            connection.commit()

        return len(activities)

    def list_activities_between(
        self, window_start: datetime, window_end: datetime
    ) -> list[ActivityRecord]:
        """List normalized activities within an inclusive UTC time window.

        Parameters:
            window_start: Inclusive lower timestamp bound.
            window_end: Inclusive upper timestamp bound.

        Returns:
            list[ActivityRecord]: Persisted activity records in time order.

        Raises:
            sqlite3.Error: Raised when read fails.

        Example:
            >>> # activities = repo.list_activities_between(start, end)
        """

        with get_connection(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT
                    strava_activity_id,
                    name,
                    sport_type,
                    start_time,
                    elapsed_time_s,
                    calories,
                    suffer_score,
                    rpe_override,
                    source_raw_json,
                    synced_at
                FROM strava_activities
                WHERE start_time >= ? AND start_time <= ?
                ORDER BY start_time DESC
                """,
                (window_start.isoformat(), window_end.isoformat()),
            ).fetchall()

        return [self._map_activity_row(row) for row in rows]

    def update_rpe_override(self, strava_activity_id: str, rpe_override: int) -> ActivityRecord:
        """Persist a manual RPE override for an activity.

        Parameters:
            strava_activity_id: Strava activity identifier.
            rpe_override: Manual perceived exertion value from 1-10.

        Returns:
            ActivityRecord: Updated activity row.

        Raises:
            RuntimeError: Raised when the requested activity does not exist.
            sqlite3.Error: Raised for persistence errors.

        Example:
            >>> # updated = repo.update_rpe_override("123", 7)
        """

        with get_connection(self._database_path) as connection:
            connection.execute(
                """
                UPDATE strava_activities
                SET rpe_override = ?
                WHERE strava_activity_id = ?
                """,
                (rpe_override, strava_activity_id),
            )

            row = connection.execute(
                """
                SELECT
                    strava_activity_id,
                    name,
                    sport_type,
                    start_time,
                    elapsed_time_s,
                    calories,
                    suffer_score,
                    rpe_override,
                    source_raw_json,
                    synced_at
                FROM strava_activities
                WHERE strava_activity_id = ?
                """,
                (strava_activity_id,),
            ).fetchone()
            connection.commit()

        if row is None:
            raise RuntimeError(f"Activity {strava_activity_id} was not found.")

        return self._map_activity_row(row)

    def count_activities(self) -> int:
        """Return total number of stored activities.

        Parameters:
            None.

        Returns:
            int: Number of rows in `strava_activities`.

        Raises:
            sqlite3.Error: Raised when count query fails.

        Example:
            >>> # total = repo.count_activities()
        """

        with get_connection(self._database_path) as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM strava_activities").fetchone()

        return int(row["total"]) if row is not None else 0

    def get_raw_token_row(self) -> tuple[str, str] | None:
        """Return encrypted token strings for testing and diagnostics.

        Parameters:
            None.

        Returns:
            tuple[str, str] | None: `(encrypted_access_token, encrypted_refresh_token)` pair.

        Raises:
            sqlite3.Error: Raised when query fails.

        Example:
            >>> # encrypted = repo.get_raw_token_row()
        """

        with get_connection(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT encrypted_access_token, encrypted_refresh_token
                FROM strava_tokens
                WHERE id = 1
                """
            ).fetchone()

        if row is None:
            return None

        return (str(row["encrypted_access_token"]), str(row["encrypted_refresh_token"]))

    def _map_activity_row(self, row: object) -> ActivityRecord:
        """Convert a SQLite row object into an `ActivityRecord`.

        Parameters:
            row: SQLite row object with activity columns.

        Returns:
            ActivityRecord: Normalized row object.

        Raises:
            KeyError: Raised when required columns are missing.

        Example:
            >>> # record = repo._map_activity_row(sqlite_row)
        """

        return ActivityRecord(
            strava_activity_id=str(row["strava_activity_id"]),
            name=str(row["name"]),
            sport_type=str(row["sport_type"]),
            start_time=datetime.fromisoformat(str(row["start_time"])),
            elapsed_time_s=int(row["elapsed_time_s"]),
            calories=float(row["calories"]) if row["calories"] is not None else None,
            suffer_score=int(row["suffer_score"]) if row["suffer_score"] is not None else None,
            rpe_override=int(row["rpe_override"]) if row["rpe_override"] is not None else None,
            source_raw_json=json.dumps(json.loads(str(row["source_raw_json"]))),
            synced_at=datetime.fromisoformat(str(row["synced_at"])),
        )
