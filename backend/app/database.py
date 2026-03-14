"""SQLite connection and schema bootstrap helpers."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from backend.app.config import Settings


def sqlite_path_from_url(database_url: str) -> Path:
    """Convert a SQLite URL into a filesystem path.

    Parameters:
        database_url: Database URL expected to start with ``sqlite:///``.

    Returns:
        Path: Resolved path to the SQLite database file.

    Raises:
        ValueError: If the URL does not use the supported SQLite format.

    Example:
        >>> sqlite_path_from_url("sqlite:///./data/app.db").name
        'app.db'
    """

    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("Only sqlite:/// URLs are supported in this prototype.")

    raw_path = database_url.removeprefix(prefix)
    return Path(raw_path).expanduser().resolve()


@contextmanager
def get_connection(settings: Settings) -> Iterator[sqlite3.Connection]:
    """Yield a configured SQLite connection with transaction management.

    Parameters:
        settings: Application settings that include the SQLite URL.

    Returns:
        Iterator[sqlite3.Connection]: Context-managed SQLite connection.

    Raises:
        sqlite3.Error: If opening or committing the connection fails.

    Example:
        >>> from backend.app.config import Settings
        >>> with get_connection(Settings()) as conn:
        ...     isinstance(conn, sqlite3.Connection)
        True
    """

    path = sqlite_path_from_url(settings.database_url)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def initialize_database(settings: Settings) -> None:
    """Create the SQLite schema required by the prototype if it is missing.

    Parameters:
        settings: Application settings with database and storage paths.

    Returns:
        None.

    Raises:
        sqlite3.Error: If schema creation fails.

    Example:
        >>> initialize_database(Settings())
    """

    # Ensure upload storage exists before routes attempt to write files.
    settings.upload_path.mkdir(parents=True, exist_ok=True)

    schema = """
    CREATE TABLE IF NOT EXISTS meal_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day_date TEXT NOT NULL,
        meal_slot TEXT NOT NULL,
        source_text TEXT NOT NULL,
        items_json TEXT NOT NULL,
        calories REAL NOT NULL,
        protein_g REAL NOT NULL,
        carbs_g REAL NOT NULL,
        fat_g REAL NOT NULL,
        confidence REAL NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        strava_activity_id TEXT NOT NULL UNIQUE,
        day_date TEXT NOT NULL,
        name TEXT NOT NULL,
        sport_type TEXT NOT NULL,
        start_time TEXT NOT NULL,
        elapsed_time_s INTEGER NOT NULL,
        calories REAL,
        suffer_score REAL,
        rpe_override INTEGER,
        synced_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS glucose_uploads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day_date TEXT NOT NULL,
        file_path TEXT NOT NULL,
        original_filename TEXT NOT NULL,
        uploaded_at TEXT NOT NULL,
        ai_summary TEXT,
        user_note TEXT
    );

    CREATE TABLE IF NOT EXISTS sync_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        started_at TEXT NOT NULL,
        finished_at TEXT NOT NULL,
        status TEXT NOT NULL,
        imported_count INTEGER NOT NULL,
        updated_count INTEGER NOT NULL,
        error_message TEXT
    );
    """

    with get_connection(settings) as conn:
        conn.executescript(schema)
