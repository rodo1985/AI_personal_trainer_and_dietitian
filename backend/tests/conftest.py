"""Shared pytest fixtures for Strava integration tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from backend.app.config import AppSettings, resolve_sqlite_path
from backend.app.db import initialize_database
from backend.app.repositories.strava_repository import StravaRepository
from backend.app.services.strava_client import StravaTokenResponse
from backend.app.services.token_crypto import TokenCrypto


@dataclass
class FakeStravaClient:
    """Test double for Strava API interactions.

    Parameters:
        connect_url: OAuth connect URL to return.
        exchange_response: Token response for callback exchange.
        refresh_response: Token response for refresh operations.
        activities_response: Raw activities returned during sync.
        exchanged_codes: Captured callback codes.
        refreshed_tokens: Captured refresh tokens.
        activity_requests: Captured sync window requests.

    Returns:
        FakeStravaClient: Configured test double.

    Raises:
        None.

    Example:
        >>> fake = FakeStravaClient()
        >>> fake.build_connect_url("state")
        'https://strava.test/connect'
    """

    connect_url: str = "https://strava.test/connect"
    exchange_response: StravaTokenResponse | None = None
    refresh_response: StravaTokenResponse | None = None
    activities_response: list[dict[str, Any]] = field(default_factory=list)
    exchanged_codes: list[str] = field(default_factory=list)
    refreshed_tokens: list[str] = field(default_factory=list)
    activity_requests: list[tuple[datetime, datetime]] = field(default_factory=list)

    def build_connect_url(self, state: str) -> str:
        """Return a fixed connect URL.

        Parameters:
            state: OAuth state token (ignored by the fake).

        Returns:
            str: Fixed connect URL.

        Raises:
            None.

        Example:
            >>> FakeStravaClient().build_connect_url("x")
            'https://strava.test/connect'
        """

        _ = state
        return self.connect_url

    def exchange_code_for_token(self, code: str) -> StravaTokenResponse:
        """Return preconfigured callback token response.

        Parameters:
            code: OAuth callback code captured for assertions.

        Returns:
            StravaTokenResponse: Configured callback response.

        Raises:
            RuntimeError: Raised when no callback response was configured.

        Example:
            >>> # fake.exchange_code_for_token("code")
        """

        self.exchanged_codes.append(code)
        if self.exchange_response is None:
            raise RuntimeError("FakeStravaClient.exchange_response must be configured.")
        return self.exchange_response

    def refresh_access_token(self, refresh_token: str) -> StravaTokenResponse:
        """Return preconfigured token refresh response.

        Parameters:
            refresh_token: Refresh token captured for assertions.

        Returns:
            StravaTokenResponse: Configured refresh response.

        Raises:
            RuntimeError: Raised when no refresh response was configured.

        Example:
            >>> # fake.refresh_access_token("refresh")
        """

        self.refreshed_tokens.append(refresh_token)
        if self.refresh_response is None:
            raise RuntimeError("FakeStravaClient.refresh_response must be configured.")
        return self.refresh_response

    def get_recent_activities(
        self, access_token: str, window_start: datetime, window_end: datetime
    ) -> list[dict[str, Any]]:
        """Return preconfigured activity payload for sync tests.

        Parameters:
            access_token: Access token captured for assertions.
            window_start: Start of requested sync window.
            window_end: End of requested sync window.

        Returns:
            list[dict[str, Any]]: Configured activity list.

        Raises:
            None.

        Example:
            >>> # fake.get_recent_activities("token", start, end)
        """

        _ = access_token
        self.activity_requests.append((window_start, window_end))
        return list(self.activities_response)


@pytest.fixture
def app_settings(tmp_path: Path) -> AppSettings:
    """Build test settings with temporary local SQLite storage.

    Parameters:
        tmp_path: Pytest temporary path fixture.

    Returns:
        AppSettings: Settings object bound to temporary resources.

    Raises:
        pydantic.ValidationError: Raised when fixture values are invalid.

    Example:
        >>> # settings = app_settings(tmp_path)
    """

    return AppSettings(
        STRAVA_CLIENT_ID="test-client",
        STRAVA_CLIENT_SECRET="test-secret",
        STRAVA_REDIRECT_URI="http://localhost:8000/api/strava/callback",
        DATABASE_URL=f"sqlite:///{tmp_path / 'test.db'}",
        STRAVA_TOKEN_ENCRYPTION_KEY="test-encryption-key",
        STRAVA_SYNC_DAYS=7,
        STRAVA_ACTIVITY_PAGE_SIZE=50,
    )


@pytest.fixture
def database_path(app_settings: AppSettings) -> Path:
    """Create and initialize a temporary SQLite database path.

    Parameters:
        app_settings: Test app settings fixture.

    Returns:
        Path: Temporary SQLite file path.

    Raises:
        sqlite3.Error: Raised when schema initialization fails.

    Example:
        >>> # db_path = database_path(app_settings)
    """

    db_path = resolve_sqlite_path(app_settings.database_url)
    initialize_database(db_path)
    return db_path


@pytest.fixture
def repository(database_path: Path) -> StravaRepository:
    """Return a repository bound to the temporary test database.

    Parameters:
        database_path: Initialized SQLite file path fixture.

    Returns:
        StravaRepository: Repository instance.

    Raises:
        None.

    Example:
        >>> # repo = repository(database_path)
    """

    return StravaRepository(database_path)


@pytest.fixture
def token_crypto(app_settings: AppSettings) -> TokenCrypto:
    """Return a deterministic token encryption helper for tests.

    Parameters:
        app_settings: Test settings fixture with encryption key.

    Returns:
        TokenCrypto: Encryption helper.

    Raises:
        ValueError: Raised when fixture secret is blank.

    Example:
        >>> # crypto = token_crypto(app_settings)
    """

    assert app_settings.strava_token_encryption_key is not None
    return TokenCrypto(app_settings.strava_token_encryption_key)


@pytest.fixture
def fixed_now() -> datetime:
    """Return a stable UTC timestamp for deterministic sync tests.

    Parameters:
        None.

    Returns:
        datetime: Fixed timezone-aware UTC timestamp.

    Raises:
        None.

    Example:
        >>> # now = fixed_now()
    """

    return datetime(2026, 1, 14, 9, 30, 0, tzinfo=UTC)
