"""Centralized environment-driven configuration for the backend service."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables.

    Parameters:
        app_name: Human-readable API title used in OpenAPI docs.
        app_env: Environment label such as development, test, or production.
        app_debug: Whether FastAPI debug mode is enabled.
        api_prefix: Base URL prefix for all API routes.
        database_url: SQLite connection string in ``sqlite:///path/to/file.db`` format.
        upload_dir: Directory where local upload files are stored.
        openai_api_key: API key used for OpenAI calls in later phases.
        openai_meal_model: Model name planned for meal drafting tasks.
        openai_transcribe_model: Model name planned for audio transcription tasks.
        openai_vision_model: Model name planned for image interpretation tasks.
        strava_client_id: OAuth client identifier for Strava integration.
        strava_client_secret: OAuth client secret for Strava integration.
        strava_redirect_uri: Redirect callback URI for Strava OAuth.

    Returns:
        Settings: A validated settings object.

    Raises:
        pydantic.ValidationError: Raised when environment values do not match expected types.

    Example:
        >>> settings = Settings()
        >>> settings.api_prefix
        '/api'
    """

    app_name: str = "Personal Endurance Trainer Log Prototype API"
    app_env: str = "development"
    app_debug: bool = True
    api_prefix: str = "/api"

    database_url: str = "sqlite:///data/app.db"
    upload_dir: Path = Path("uploads")

    openai_api_key: str = ""
    openai_meal_model: str = "gpt-5.2-mini"
    openai_transcribe_model: str = "gpt-4o-mini-transcribe"
    openai_vision_model: str = "gpt-5.2-mini"

    strava_client_id: str = ""
    strava_client_secret: str = ""
    strava_redirect_uri: str = "http://localhost:8000/api/strava/callback"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance for dependency injection.

    Parameters:
        None.

    Returns:
        Settings: The singleton-like settings instance for the process.

    Raises:
        pydantic.ValidationError: Raised when one or more environment values are invalid.

    Example:
        >>> settings = get_settings()
        >>> settings.app_env
        'development'
    """

    return Settings()


def clear_settings_cache() -> None:
    """Clear the settings cache to support isolated tests.

    Parameters:
        None.

    Returns:
        None.

    Raises:
        None.

    Example:
        >>> clear_settings_cache()
    """

    get_settings.cache_clear()
