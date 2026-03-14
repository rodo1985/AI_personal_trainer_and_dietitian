"""SQLite connection and schema helpers for the local prototype backend."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def get_connection(database_path: Path) -> sqlite3.Connection:
    """Create a SQLite connection configured for row-based access.

    Parameters:
        database_path: Filesystem path to the SQLite database file.

    Returns:
        sqlite3.Connection: Opened SQLite connection.

    Raises:
        sqlite3.Error: Raised when SQLite cannot open the file.

    Example:
        >>> from pathlib import Path
        >>> conn = get_connection(Path("data/app.db"))
        >>> isinstance(conn, sqlite3.Connection)
        True
    """

    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(database_path: Path) -> None:
    """Create Strava-related tables used by this integration.

    Parameters:
        database_path: Filesystem path to the SQLite database file.

    Returns:
        None.

    Raises:
        sqlite3.Error: Raised when schema initialization fails.

    Example:
        >>> from pathlib import Path
        >>> initialize_database(Path("data/app.db"))
    """

    with get_connection(database_path) as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS strava_tokens (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                athlete_id INTEGER NOT NULL,
                encrypted_access_token TEXT NOT NULL,
                encrypted_refresh_token TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                scope TEXT,
                token_type TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS strava_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strava_activity_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                sport_type TEXT NOT NULL,
                start_time TEXT NOT NULL,
                elapsed_time_s INTEGER NOT NULL,
                calories REAL,
                suffer_score INTEGER,
                rpe_override INTEGER,
                source_raw_json TEXT NOT NULL,
                synced_at TEXT NOT NULL,
                CHECK (rpe_override IS NULL OR (rpe_override >= 1 AND rpe_override <= 10))
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS strava_sync_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,
                window_start TEXT NOT NULL,
                window_end TEXT NOT NULL,
                fetched_count INTEGER NOT NULL DEFAULT 0,
                upserted_count INTEGER NOT NULL DEFAULT 0,
                error_message TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_strava_activities_start_time
            ON strava_activities(start_time)
            """
        )

        connection.commit()
