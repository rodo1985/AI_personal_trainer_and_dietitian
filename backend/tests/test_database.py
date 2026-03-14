"""Tests for SQLite initialization helpers."""

import sqlite3
from pathlib import Path

import pytest

from backend.app.database import SCHEMA_STATEMENTS, initialize_database, sqlite_path_from_url


@pytest.mark.parametrize(
    "database_url",
    ["postgresql://localhost/example", "sqlite://data/app.db", "sqlite:/data/app.db"],
)
def test_sqlite_path_from_url_rejects_non_scaffold_urls(database_url: str) -> None:
    """Ensure unsupported URL formats fail fast with a clear error.

    Parameters:
        database_url: Invalid database URL variant under test.

    Returns:
        None.

    Raises:
        AssertionError: Raised when the helper does not reject malformed URLs.

    Example:
        >>> test_sqlite_path_from_url_rejects_non_scaffold_urls("sqlite://data/app.db")
    """

    with pytest.raises(ValueError):
        sqlite_path_from_url(database_url)


def test_initialize_database_creates_file_and_schema(tmp_path: Path) -> None:
    """Verify that startup initialization creates the DB file and base tables.

    Parameters:
        tmp_path: Pytest-provided temporary filesystem path.

    Returns:
        None.

    Raises:
        AssertionError: Raised when expected schema artifacts are missing.

    Example:
        >>> # Pytest injects tmp_path during test execution.
        >>> True
        True
    """

    database_url = f"sqlite:///{tmp_path / 'app.db'}"
    database_path = initialize_database(database_url)

    assert database_path.exists()

    with sqlite3.connect(database_path) as connection:
        result = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()

    table_names = {name for (name,) in result}

    assert "day_logs" in table_names
    assert "meal_entries" in table_names
    assert "activity_entries" in table_names
    assert "glucose_uploads" in table_names

    # Guard that the schema tuple stays non-empty so future refactors do not
    # accidentally remove all bootstrap statements.
    assert len(SCHEMA_STATEMENTS) >= 4
