"""API route tests for Strava integration endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from backend.app.dependencies import get_strava_sync_service
from backend.app.main import create_app
from backend.app.repositories.strava_repository import ActivityRecord
from backend.app.services.strava_sync import CallbackResult, SyncResult


class StubStravaService:
    """Small route-level service stub used to verify FastAPI behavior.

    Parameters:
        None.

    Returns:
        StubStravaService: Configurable route test double.

    Raises:
        None.

    Example:
        >>> stub = StubStravaService()
        >>> stub.build_connect_url("abc")
        'https://strava.test/connect'
    """

    def __init__(self) -> None:
        """Initialize deterministic response values for route tests.

        Parameters:
            None.

        Returns:
            None.

        Raises:
            None.

        Example:
            >>> StubStravaService()
            <...StubStravaService object ...>
        """

        self.received_callback_code: str | None = None

    def build_connect_url(self, state: str | None = None) -> str:
        """Return a deterministic connect URL.

        Parameters:
            state: Optional state token passed by route handler.

        Returns:
            str: Connect URL string.

        Raises:
            None.

        Example:
            >>> StubStravaService().build_connect_url("state")
            'https://strava.test/connect'
        """

        _ = state
        return "https://strava.test/connect"

    def handle_callback(self, code: str) -> CallbackResult:
        """Capture callback code and return a deterministic success payload.

        Parameters:
            code: OAuth callback code from route query params.

        Returns:
            CallbackResult: Successful callback result.

        Raises:
            None.

        Example:
            >>> # stub.handle_callback("code")
        """

        self.received_callback_code = code
        return CallbackResult(connected=True, athlete_id=42, expires_at=datetime.now(UTC))

    def sync_recent(self) -> SyncResult:
        """Return a deterministic sync payload used by API route tests.

        Parameters:
            None.

        Returns:
            SyncResult: Static sync result object.

        Raises:
            None.

        Example:
            >>> # stub.sync_recent()
        """

        now = datetime.now(UTC)
        return SyncResult(
            run_id=1,
            status="success",
            window_start=now,
            window_end=now,
            fetched_count=1,
            upserted_count=1,
            activities=[
                ActivityRecord(
                    strava_activity_id="123",
                    name="Morning Run",
                    sport_type="Run",
                    start_time=now,
                    elapsed_time_s=1800,
                    calories=620.0,
                    suffer_score=None,
                    rpe_override=None,
                    source_raw_json="{}",
                    synced_at=now,
                )
            ],
        )

    def update_rpe_override(self, strava_activity_id: str, rpe_override: int) -> ActivityRecord:
        """Return a deterministic updated activity for override route tests.

        Parameters:
            strava_activity_id: Activity ID provided by route path parameter.
            rpe_override: Requested manual effort override.

        Returns:
            ActivityRecord: Updated activity record.

        Raises:
            None.

        Example:
            >>> # stub.update_rpe_override("123", 6)
        """

        now = datetime.now(UTC)
        return ActivityRecord(
            strava_activity_id=strava_activity_id,
            name="Morning Run",
            sport_type="Run",
            start_time=now,
            elapsed_time_s=1800,
            calories=620.0,
            suffer_score=None,
            rpe_override=rpe_override,
            source_raw_json="{}",
            synced_at=now,
        )


def test_connect_route_returns_authorization_url() -> None:
    """Return the connect URL payload from the Strava connect endpoint.

    Parameters:
        None.

    Returns:
        None.

    Raises:
        AssertionError: Raised when response payload is incorrect.

    Example:
        >>> # pytest executes this assertion-based test.
    """

    app = create_app()
    app.dependency_overrides[get_strava_sync_service] = StubStravaService

    with TestClient(app) as client:
        response = client.get("/api/strava/connect")

    assert response.status_code == 200
    assert response.json()["authorization_url"] == "https://strava.test/connect"


def test_callback_route_forwards_code_to_service() -> None:
    """Pass callback query code to service and return connection metadata.

    Parameters:
        None.

    Returns:
        None.

    Raises:
        AssertionError: Raised when callback behavior is incorrect.

    Example:
        >>> # pytest executes this assertion-based test.
    """

    stub_service = StubStravaService()
    app = create_app()
    app.dependency_overrides[get_strava_sync_service] = lambda: stub_service

    with TestClient(app) as client:
        response = client.get("/api/strava/callback?code=oauth-code")

    assert response.status_code == 200
    assert response.json()["connected"] is True
    assert stub_service.received_callback_code == "oauth-code"


def test_sync_route_returns_sync_metadata_and_activities() -> None:
    """Expose sync run metadata and normalized activities from sync endpoint.

    Parameters:
        None.

    Returns:
        None.

    Raises:
        AssertionError: Raised when sync response payload is incorrect.

    Example:
        >>> # pytest executes this assertion-based test.
    """

    app = create_app()
    app.dependency_overrides[get_strava_sync_service] = StubStravaService

    with TestClient(app) as client:
        response = client.post("/api/strava/sync/recent")

    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "success"
    assert payload["fetched_count"] == 1
    assert payload["activities"][0]["strava_activity_id"] == "123"


def test_rpe_override_route_updates_activity() -> None:
    """Update manual RPE override through the route handler.

    Parameters:
        None.

    Returns:
        None.

    Raises:
        AssertionError: Raised when override response payload is incorrect.

    Example:
        >>> # pytest executes this assertion-based test.
    """

    app = create_app()
    app.dependency_overrides[get_strava_sync_service] = StubStravaService

    with TestClient(app) as client:
        response = client.patch("/api/strava/activities/123/rpe-override", json={"rpe_override": 8})

    payload = response.json()
    assert response.status_code == 200
    assert payload["activity"]["strava_activity_id"] == "123"
    assert payload["activity"]["rpe_override"] == 8
