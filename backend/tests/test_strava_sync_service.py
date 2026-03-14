"""Unit tests for Strava sync service behavior."""

from __future__ import annotations

from datetime import datetime, timedelta

from backend.app.config import AppSettings
from backend.app.repositories.strava_repository import StravaRepository
from backend.app.services.strava_client import StravaTokenResponse
from backend.app.services.strava_sync import StravaSyncService
from backend.app.services.token_crypto import TokenCrypto
from backend.tests.conftest import FakeStravaClient


def _create_service(
    app_settings: AppSettings,
    repository: StravaRepository,
    token_crypto: TokenCrypto,
    fake_client: FakeStravaClient,
) -> StravaSyncService:
    """Construct a sync service instance with test doubles.

    Parameters:
        app_settings: Test settings fixture.
        repository: SQLite-backed repository fixture.
        token_crypto: Encryption helper fixture.
        fake_client: Fake Strava API client.

    Returns:
        StravaSyncService: Configured service for tests.

    Raises:
        None.

    Example:
        >>> # service = _create_service(settings, repo, crypto, fake)
    """

    return StravaSyncService(
        settings=app_settings,
        repository=repository,
        client=fake_client,
        token_crypto=token_crypto,
    )


def test_callback_persists_encrypted_tokens(
    app_settings: AppSettings,
    repository: StravaRepository,
    token_crypto: TokenCrypto,
    fixed_now: datetime,
) -> None:
    """Store encrypted token values after successful OAuth callback exchange.

    Parameters:
        app_settings: Test settings fixture.
        repository: Repository fixture.
        token_crypto: Encryption helper fixture.
        fixed_now: Stable test timestamp fixture.

    Returns:
        None.

    Raises:
        AssertionError: Raised when expected callback persistence is incorrect.

    Example:
        >>> # pytest executes this assertion-based test.
    """

    fake_client = FakeStravaClient(
        exchange_response=StravaTokenResponse(
            athlete_id=12,
            access_token="plain-access",
            refresh_token="plain-refresh",
            expires_at=fixed_now + timedelta(hours=6),
            scope="activity:read_all",
            token_type="Bearer",
        )
    )
    service = _create_service(app_settings, repository, token_crypto, fake_client)

    result = service.handle_callback(code="oauth-code")

    assert result.connected is True
    assert result.athlete_id == 12
    encrypted_row = repository.get_raw_token_row()
    assert encrypted_row is not None
    assert "plain-access" not in encrypted_row[0]
    assert "plain-refresh" not in encrypted_row[1]


def test_sync_refreshes_expired_token(
    app_settings: AppSettings,
    repository: StravaRepository,
    token_crypto: TokenCrypto,
    fixed_now: datetime,
) -> None:
    """Refresh access token when the stored one is expired during sync.

    Parameters:
        app_settings: Test settings fixture.
        repository: Repository fixture.
        token_crypto: Encryption helper fixture.
        fixed_now: Stable test timestamp fixture.

    Returns:
        None.

    Raises:
        AssertionError: Raised when refresh behavior does not match expectations.

    Example:
        >>> # pytest executes this assertion-based test.
    """

    repository.upsert_tokens(
        athlete_id=12,
        encrypted_access_token=token_crypto.encrypt("expired-access"),
        encrypted_refresh_token=token_crypto.encrypt("refresh-token"),
        expires_at=fixed_now - timedelta(minutes=1),
        scope="activity:read_all",
        token_type="Bearer",
    )

    fake_client = FakeStravaClient(
        refresh_response=StravaTokenResponse(
            athlete_id=12,
            access_token="fresh-access",
            refresh_token="fresh-refresh",
            expires_at=fixed_now + timedelta(hours=6),
            scope="activity:read_all",
            token_type="Bearer",
        ),
        activities_response=[
            {
                "id": 1001,
                "name": "Tempo Run",
                "sport_type": "Run",
                "start_date": (fixed_now - timedelta(days=1)).isoformat().replace("+00:00", "Z"),
                "elapsed_time": 3600,
                "calories": 780,
                "suffer_score": 82,
            }
        ],
    )

    service = _create_service(app_settings, repository, token_crypto, fake_client)
    result = service.sync_recent(now=fixed_now)

    assert fake_client.refreshed_tokens == ["refresh-token"]
    assert result.status == "success"
    assert result.fetched_count == 1
    assert result.upserted_count == 1

    stored_tokens = repository.get_tokens()
    assert stored_tokens is not None
    assert token_crypto.decrypt(stored_tokens.encrypted_access_token) == "fresh-access"


def test_sync_is_idempotent_and_handles_missing_optional_fields(
    app_settings: AppSettings,
    repository: StravaRepository,
    token_crypto: TokenCrypto,
    fixed_now: datetime,
) -> None:
    """Prevent duplicates and persist activities with missing optional Strava fields.

    Parameters:
        app_settings: Test settings fixture.
        repository: Repository fixture.
        token_crypto: Encryption helper fixture.
        fixed_now: Stable test timestamp fixture.

    Returns:
        None.

    Raises:
        AssertionError: Raised when idempotency or optional field behavior fails.

    Example:
        >>> # pytest executes this assertion-based test.
    """

    repository.upsert_tokens(
        athlete_id=99,
        encrypted_access_token=token_crypto.encrypt("valid-access"),
        encrypted_refresh_token=token_crypto.encrypt("valid-refresh"),
        expires_at=fixed_now + timedelta(hours=2),
        scope="activity:read_all",
        token_type="Bearer",
    )

    activity_start = (fixed_now - timedelta(days=2)).isoformat().replace("+00:00", "Z")
    fake_client = FakeStravaClient(
        activities_response=[
            {
                "id": 222,
                "name": "Endurance Ride",
                "sport_type": "Ride",
                "start_date": activity_start,
                "elapsed_time": 7200,
            }
        ]
    )

    service = _create_service(app_settings, repository, token_crypto, fake_client)

    first_sync = service.sync_recent(now=fixed_now)
    second_sync = service.sync_recent(now=fixed_now)

    assert first_sync.status == "success"
    assert second_sync.status == "success"
    assert repository.count_activities() == 1

    activity = second_sync.activities[0]
    assert activity.calories is None
    assert activity.suffer_score is None

    updated = service.update_rpe_override(strava_activity_id="222", rpe_override=7)
    assert updated.rpe_override == 7


def test_sync_uses_rolling_seven_day_window(
    app_settings: AppSettings,
    repository: StravaRepository,
    token_crypto: TokenCrypto,
    fixed_now: datetime,
) -> None:
    """Sync only activities whose start times fall inside the trailing 7-day window.

    Parameters:
        app_settings: Test settings fixture.
        repository: Repository fixture.
        token_crypto: Encryption helper fixture.
        fixed_now: Stable test timestamp fixture.

    Returns:
        None.

    Raises:
        AssertionError: Raised when window filtering is incorrect.

    Example:
        >>> # pytest executes this assertion-based test.
    """

    repository.upsert_tokens(
        athlete_id=7,
        encrypted_access_token=token_crypto.encrypt("window-access"),
        encrypted_refresh_token=token_crypto.encrypt("window-refresh"),
        expires_at=fixed_now + timedelta(hours=1),
        scope="activity:read_all",
        token_type="Bearer",
    )

    inside_window = (fixed_now - timedelta(days=3)).isoformat().replace("+00:00", "Z")
    outside_window = (fixed_now - timedelta(days=10)).isoformat().replace("+00:00", "Z")
    fake_client = FakeStravaClient(
        activities_response=[
            {
                "id": 300,
                "name": "Within Window",
                "sport_type": "Run",
                "start_date": inside_window,
                "elapsed_time": 1800,
            },
            {
                "id": 301,
                "name": "Outside Window",
                "sport_type": "Run",
                "start_date": outside_window,
                "elapsed_time": 1800,
            },
        ]
    )

    service = _create_service(app_settings, repository, token_crypto, fake_client)
    result = service.sync_recent(now=fixed_now)

    assert result.fetched_count == 2
    assert repository.count_activities() == 1
    assert result.activities[0].strava_activity_id == "300"
