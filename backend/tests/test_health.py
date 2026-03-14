"""Tests for the FastAPI health endpoint and startup wiring."""

from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import clear_settings_cache
from backend.app.main import create_application


def make_test_client(tmp_path: Path) -> TestClient:
    """Create a TestClient with isolated local storage paths.

    Parameters:
        tmp_path: Pytest temporary directory used for per-test isolation.

    Returns:
        TestClient: Client bound to a newly created FastAPI app instance.

    Raises:
        None.

    Example:
        >>> # Used from tests to avoid sharing DB files across runs.
        >>> True
        True
    """

    database_path = tmp_path / "test.db"
    upload_path = tmp_path / "uploads"

    # Environment overrides are done inside this helper so every test uses the
    # same setup pattern and avoids stale cached settings.
    import os

    os.environ["APP_ENV"] = "test"
    os.environ["DATABASE_URL"] = f"sqlite:///{database_path}"
    os.environ["UPLOAD_DIR"] = str(upload_path)

    clear_settings_cache()
    return TestClient(create_application())


def test_health_endpoint_returns_expected_payload(tmp_path: Path) -> None:
    """Check that `/api/health` returns the documented scaffold payload.

    Parameters:
        tmp_path: Pytest temporary directory for isolated settings.

    Returns:
        None.

    Raises:
        AssertionError: Raised when the endpoint response changes unexpectedly.

    Example:
        >>> # Executed by pytest.
        >>> True
        True
    """

    with make_test_client(tmp_path) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "backend",
        "environment": "test",
    }


def test_startup_creates_database_and_upload_directory(tmp_path: Path) -> None:
    """Ensure startup side effects prepare both SQLite and upload storage.

    Parameters:
        tmp_path: Pytest temporary directory for isolated settings.

    Returns:
        None.

    Raises:
        AssertionError: Raised when startup does not create expected directories/files.

    Example:
        >>> # Executed by pytest.
        >>> True
        True
    """

    database_path = tmp_path / "test.db"
    upload_path = tmp_path / "uploads"

    with make_test_client(tmp_path) as client:
        # Trigger at least one request so startup runs inside the context.
        _ = client.get("/api/health")

    assert database_path.exists()
    assert upload_path.exists()
