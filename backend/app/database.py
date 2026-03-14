"""SQLite helpers used by the backend scaffold.

The goal of this module is to provide a tiny, explicit foundation that other
worktrees can extend without needing a migration framework in phase 1.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

SQLITE_URL_PREFIX = "sqlite:///"

# The initial schema is intentionally minimal and descriptive. Future branches
# can add columns or proper migration tooling once behavior stabilizes.
SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS day_logs (
        date TEXT PRIMARY KEY,
        daily_notes TEXT DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS meal_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        meal_slot TEXT NOT NULL,
        source_text TEXT NOT NULL,
        structured_payload TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(date) REFERENCES day_logs(date)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS activity_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        strava_activity_id TEXT UNIQUE,
        name TEXT NOT NULL,
        sport_type TEXT NOT NULL,
        start_time TEXT NOT NULL,
        elapsed_time_s INTEGER NOT NULL,
        calories REAL,
        suffer_score REAL,
        rpe_override REAL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(date) REFERENCES day_logs(date)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS glucose_uploads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        file_path TEXT NOT NULL,
        summary TEXT,
        user_note TEXT,
        uploaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(date) REFERENCES day_logs(date)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_meal_entries_date ON meal_entries(date)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_activity_entries_date ON activity_entries(date)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_glucose_uploads_date ON glucose_uploads(date)
    """,
)


def sqlite_path_from_url(database_url: str) -> Path:
    """Convert a SQLite URL into a concrete filesystem path.

    Parameters:
        database_url: Database URL in ``sqlite:///relative/or/absolute/path.db`` form.

    Returns:
        Path: Absolute path for the SQLite file.

    Raises:
        ValueError: Raised if the URL is not a SQLite URL with the expected prefix.

    Example:
        >>> sqlite_path_from_url("sqlite:///data/app.db")
        PosixPath('/abs/path/to/data/app.db')
    """

    if not database_url.startswith(SQLITE_URL_PREFIX):
        raise ValueError(
            "Only sqlite:/// URLs are supported by the phase-1 scaffold. "
            f"Received: {database_url!r}"
        )

    relative_or_absolute = database_url.removeprefix(SQLITE_URL_PREFIX)
    return Path(relative_or_absolute).expanduser().resolve()


def initialize_database(database_url: str) -> Path:
    """Create the SQLite database file and bootstrap the initial schema.

    Parameters:
        database_url: SQLite URL that points to the local database file.

    Returns:
        Path: The resolved path to the SQLite file that was initialized.

    Raises:
        ValueError: Raised when ``database_url`` is not a supported SQLite URL.
        sqlite3.DatabaseError: Raised when SQLite cannot create the file or schema.

    Example:
        >>> initialize_database("sqlite:///data/app.db")
        PosixPath('/abs/path/to/data/app.db')
    """

    database_path = sqlite_path_from_url(database_url)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_path) as connection:
        # Foreign keys are disabled by default in SQLite, so we enable them once
        # during initialization to keep behavior consistent from day one.
        connection.execute("PRAGMA foreign_keys = ON;")

        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)

        connection.commit()

    return database_path


@contextmanager
def open_database_connection(database_url: str) -> Iterator[sqlite3.Connection]:
    """Yield a short-lived SQLite connection configured for row access by name.

    Parameters:
        database_url: SQLite URL for the database that should be opened.

    Returns:
        Iterator[sqlite3.Connection]: Context-managed SQLite connection.

    Raises:
        ValueError: Raised when ``database_url`` is not a supported SQLite URL.
        sqlite3.DatabaseError: Raised when the SQLite connection cannot be opened.

    Example:
        >>> with open_database_connection("sqlite:///data/app.db") as connection:
        ...     _ = connection.execute("SELECT 1").fetchone()
    """

    database_path = sqlite_path_from_url(database_url)
    connection = sqlite3.connect(database_path)

    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON;")
        yield connection
    finally:
        connection.close()
