"""Dependency wiring helpers for FastAPI route handlers."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from backend.app.config import AppSettings, get_settings, resolve_sqlite_path
from backend.app.db import initialize_database
from backend.app.repositories.strava_repository import StravaRepository
from backend.app.services.strava_client import StravaClient
from backend.app.services.strava_sync import StravaSyncService
from backend.app.services.token_crypto import TokenCrypto


@lru_cache(maxsize=1)
def get_database_path() -> Path:
    """Return the configured SQLite path and initialize schema on first use.

    Parameters:
        None.

    Returns:
        Path: SQLite file path resolved from configuration.

    Raises:
        ValueError: Raised when `DATABASE_URL` is unsupported.
        sqlite3.Error: Raised if schema initialization fails.

    Example:
        >>> path = get_database_path()
        >>> path.name.endswith('.db')
        True
    """

    settings = get_settings()
    database_path = resolve_sqlite_path(settings.database_url)
    initialize_database(database_path)
    return database_path


@lru_cache(maxsize=1)
def get_strava_repository() -> StravaRepository:
    """Return a cached `StravaRepository` instance.

    Parameters:
        None.

    Returns:
        StravaRepository: Repository bound to the configured SQLite path.

    Raises:
        None.

    Example:
        >>> repository = get_strava_repository()
        >>> isinstance(repository, StravaRepository)
        True
    """

    return StravaRepository(get_database_path())


@lru_cache(maxsize=1)
def get_token_crypto() -> TokenCrypto:
    """Return the token encryption helper configured for local storage.

    Parameters:
        None.

    Returns:
        TokenCrypto: Encryption helper.

    Raises:
        ValueError: Raised if no encryption secret can be determined.

    Example:
        >>> crypto = get_token_crypto()
        >>> isinstance(crypto, TokenCrypto)
        True
    """

    settings = get_settings()

    # The dedicated encryption key is preferred. We fall back to client secret
    # so local development can still run without extra setup steps.
    secret_material = settings.strava_token_encryption_key or settings.strava_client_secret
    return TokenCrypto(secret_material)


@lru_cache(maxsize=1)
def get_strava_client() -> StravaClient:
    """Return a cached Strava API client.

    Parameters:
        None.

    Returns:
        StravaClient: Client for OAuth and activity API operations.

    Raises:
        None.

    Example:
        >>> client = get_strava_client()
        >>> isinstance(client, StravaClient)
        True
    """

    return StravaClient(get_settings())


def get_strava_sync_service() -> StravaSyncService:
    """Build and return the Strava sync service for request handlers.

    Parameters:
        None.

    Returns:
        StravaSyncService: Ready-to-use service object.

    Raises:
        None.

    Example:
        >>> service = get_strava_sync_service()
        >>> isinstance(service, StravaSyncService)
        True
    """

    settings: AppSettings = get_settings()
    return StravaSyncService(
        settings=settings,
        repository=get_strava_repository(),
        client=get_strava_client(),
        token_crypto=get_token_crypto(),
    )
