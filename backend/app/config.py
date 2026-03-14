"""Application settings and environment loading utilities."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed runtime settings loaded from environment variables.

    Parameters:
        openai_api_key: Optional API key used for OpenAI-backed AI helpers.
        openai_meal_model: Model ID used when generating meal drafts.
        openai_transcribe_model: Model ID used when transcribing audio input.
        openai_vision_model: Model ID used for glucose image interpretation.
        strava_client_id: Optional Strava OAuth client ID.
        strava_client_secret: Optional Strava OAuth client secret.
        strava_redirect_uri: Redirect URI used during Strava OAuth flow.
        database_url: SQLite database URL.
        upload_dir: Local folder where glucose screenshots are stored.
        frontend_origin: Frontend origin allowed by CORS middleware.

    Returns:
        Settings: A validated settings object.

    Raises:
        pydantic.ValidationError: If environment values do not match expected types.

    Example:
        >>> settings = Settings()
        >>> settings.database_url.startswith("sqlite:///")
        True
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str | None = None
    openai_meal_model: str = "gpt-5.2-mini"
    openai_transcribe_model: str = "gpt-4o-mini-transcribe"
    openai_vision_model: str = "gpt-5.2-mini"

    strava_client_id: str | None = None
    strava_client_secret: str | None = None
    strava_redirect_uri: str = "http://localhost:8000/api/strava/callback"

    database_url: str = "sqlite:///./data/app.db"
    upload_dir: str = "./uploads"
    frontend_origin: str = "http://localhost:5173"

    @property
    def upload_path(self) -> Path:
        """Return the upload directory as a normalized path.

        Parameters:
            None.

        Returns:
            Path: Absolute path to the upload storage folder.

        Raises:
            OSError: If path resolution fails.

        Example:
            >>> Settings(upload_dir="./uploads").upload_path.name
            'uploads'
        """

        return Path(self.upload_dir).expanduser().resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings object for the running process.

    Parameters:
        None.

    Returns:
        Settings: Process-wide configuration singleton.

    Raises:
        pydantic.ValidationError: If environment settings are invalid.

    Example:
        >>> isinstance(get_settings(), Settings)
        True
    """

    return Settings()
