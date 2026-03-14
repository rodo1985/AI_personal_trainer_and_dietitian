"""Pytest fixtures for backend integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.config import get_settings
from backend.app.main import create_app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Create an isolated API client backed by a temporary SQLite database.

    Parameters:
        tmp_path: Pytest-provided temporary folder for per-test files.
        monkeypatch: Fixture used to override environment variables safely.

    Returns:
        TestClient: FastAPI test client configured with isolated storage.

    Raises:
        RuntimeError: If app initialization fails.

    Example:
        >>> client  # doctest: +SKIP
        <starlette.testclient.TestClient object ...>
    """

    database_path = tmp_path / "test.db"
    uploads_path = tmp_path / "uploads"

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("UPLOAD_DIR", str(uploads_path))
    monkeypatch.setenv("FRONTEND_ORIGIN", "http://localhost:5173")

    # Clear cached settings so each test picks up fresh temporary paths.
    get_settings.cache_clear()

    test_app = create_app()
    with TestClient(test_app) as test_client:
        yield test_client

    get_settings.cache_clear()
