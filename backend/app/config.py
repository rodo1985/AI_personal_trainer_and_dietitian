"""Application configuration helpers.

This module centralizes environment-driven settings so service and router code can
focus on behavior rather than parsing environment variables.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Load runtime configuration from environment variables.

    Parameters:
        strava_client_id: OAuth client identifier from Strava.
        strava_client_secret: OAuth client secret from Strava.
        strava_redirect_uri: Callback URI configured in the Strava app settings.
        strava_auth_base_url: Base URL used to generate the OAuth consent URL.
        strava_token_url: URL used to exchange and refresh OAuth tokens.
        strava_api_base_url: Base URL for Strava API activity endpoints.
        strava_scopes: Comma-separated scopes to request during OAuth consent.
        strava_sync_days: Number of trailing days to sync on each run.
        strava_activity_page_size: Activity page size passed to Strava pagination.
        strava_token_encryption_key: Optional encryption key for token-at-rest encryption.
        database_url: SQLite URL where local data is persisted.

    Returns:
        AppSettings: Parsed settings instance.

    Raises:
        pydantic.ValidationError: Raised when environment values are invalid.

    Example:
        >>> settings = AppSettings(strava_client_id="123", strava_client_secret="secret")
        >>> settings.strava_sync_days
        7
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    strava_client_id: str = Field(default="", alias="STRAVA_CLIENT_ID")
    strava_client_secret: str = Field(default="", alias="STRAVA_CLIENT_SECRET")
    strava_redirect_uri: str = Field(
        default="http://localhost:8000/api/strava/callback", alias="STRAVA_REDIRECT_URI"
    )
    strava_auth_base_url: str = Field(
        default="https://www.strava.com/oauth/authorize", alias="STRAVA_AUTH_BASE_URL"
    )
    strava_token_url: str = Field(
        default="https://www.strava.com/oauth/token", alias="STRAVA_TOKEN_URL"
    )
    strava_api_base_url: str = Field(
        default="https://www.strava.com/api/v3", alias="STRAVA_API_BASE_URL"
    )
    strava_scopes: str = Field(default="activity:read_all,profile:read_all", alias="STRAVA_SCOPES")
    strava_sync_days: int = Field(default=7, alias="STRAVA_SYNC_DAYS")
    strava_activity_page_size: int = Field(default=200, alias="STRAVA_ACTIVITY_PAGE_SIZE")
    strava_token_encryption_key: str | None = Field(
        default=None,
        alias="STRAVA_TOKEN_ENCRYPTION_KEY",
    )

    database_url: str = Field(default="sqlite:///data/app.db", alias="DATABASE_URL")


def resolve_sqlite_path(database_url: str) -> Path:
    """Resolve a local filesystem path from a SQLite URL.

    Parameters:
        database_url: URL-like database setting, for example `sqlite:///data/app.db`.

    Returns:
        Path: Filesystem path where SQLite data should be stored.

    Raises:
        ValueError: Raised if the URL does not use a supported SQLite format.

    Example:
        >>> resolve_sqlite_path("sqlite:///data/app.db")
        PosixPath('data/app.db')
    """

    if database_url.startswith("sqlite:///"):
        return Path(database_url.removeprefix("sqlite:///"))

    if database_url.startswith("sqlite://"):
        # We only support simple local paths for this single-user prototype.
        return Path(database_url.removeprefix("sqlite://"))

    raise ValueError(
        "DATABASE_URL must use sqlite:// or sqlite:/// format for this prototype."
    )


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return a cached `AppSettings` instance for dependency injection.

    Parameters:
        None.

    Returns:
        AppSettings: Shared settings object.

    Raises:
        pydantic.ValidationError: Raised when environment variables fail validation.

    Example:
        >>> settings = get_settings()
        >>> isinstance(settings.strava_client_id, str)
        True
    """

    return AppSettings()
