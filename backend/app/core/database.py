"""SQLite database helper and schema initialization for the backend."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class Database:
    """Small SQLite wrapper used by repositories.

    Parameters:
        db_path: Location of the SQLite file.

    Example:
        >>> db = Database(Path("data/app.db"))
        >>> db.initialize()
    """

    def __init__(self, db_path: Path) -> None:
        """Store database location without opening a connection yet.

        Parameters:
            db_path: Filesystem path for the SQLite file.

        Returns:
            None.
        """

        self._db_path = db_path

    def initialize(self) -> None:
        """Create tables needed by Prompt 3 backend flows.

        Returns:
            None.

        Raises:
            sqlite3.DatabaseError: If schema creation fails.

        Example:
            >>> db = Database(Path("data/app.db"))
            >>> db.initialize()
        """

        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS meal_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_date TEXT NOT NULL,
                    meal_slot TEXT NOT NULL,
                    source_text TEXT NOT NULL,
                    items_json TEXT NOT NULL,
                    calories REAL NOT NULL,
                    protein_g REAL NOT NULL,
                    carbs_g REAL NOT NULL,
                    fat_g REAL NOT NULL,
                    confidence REAL NOT NULL,
                    status TEXT NOT NULL,
                    assumptions_json TEXT NOT NULL,
                    warnings_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_meal_entries_log_date
                    ON meal_entries (log_date);

                CREATE TABLE IF NOT EXISTS activity_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_date TEXT NOT NULL,
                    strava_activity_id TEXT,
                    name TEXT NOT NULL,
                    sport_type TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    elapsed_time_s INTEGER NOT NULL,
                    calories REAL,
                    suffer_score REAL,
                    rpe_override INTEGER
                );

                CREATE INDEX IF NOT EXISTS idx_activity_entries_log_date
                    ON activity_entries (log_date);

                CREATE TABLE IF NOT EXISTS glucose_uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_date TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    stored_path TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    summary_text TEXT NOT NULL,
                    summary_warnings_json TEXT NOT NULL,
                    user_note TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_glucose_uploads_log_date
                    ON glucose_uploads (log_date);
                """
            )

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Yield a configured SQLite connection and commit on success.

        Returns:
            Iterator[sqlite3.Connection]: Active SQLite connection.

        Raises:
            sqlite3.DatabaseError: If any query or commit fails.

        Example:
            >>> db = Database(Path("data/app.db"))
            >>> with db.connection() as conn:
            ...     _ = conn.execute("SELECT 1").fetchone()
        """

        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
