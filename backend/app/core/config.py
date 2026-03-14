"""Application settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True)
class Settings:
    """Runtime settings for API, storage, and OpenAI integrations.

    Attributes:
        openai_api_key: API key used for OpenAI-powered endpoints.
        openai_meal_model: Model ID used for meal structure extraction.
        openai_transcribe_model: Model ID used for audio transcription.
        openai_vision_model: Model ID used for glucose screenshot summaries.
        database_url: SQLite URL in the form `sqlite:///relative/or/absolute/path.db`.
        upload_dir: Base directory used for local file uploads.

    Raises:
        ValueError: If `database_url` does not use SQLite syntax.

    Example:
        >>> settings = Settings.from_env()
        >>> settings.database_path.name
        'app.db'
    """

    openai_api_key: str | None
    openai_meal_model: str
    openai_transcribe_model: str
    openai_vision_model: str
    database_url: str
    upload_dir: Path

    @property
    def database_path(self) -> Path:
        """Return the concrete SQLite file path resolved from `database_url`.

        Returns:
            Path: Resolved filesystem path for the SQLite file.

        Raises:
            ValueError: If the URL does not use `sqlite` as the scheme.

        Example:
            >>> Settings.from_env().database_path.suffix
            '.db'
        """

        parsed = urlparse(self.database_url)
        if parsed.scheme != "sqlite":
            raise ValueError(
                "DATABASE_URL must use sqlite:///... format for this prototype backend."
            )

        if not self.database_url.startswith("sqlite:///"):
            raise ValueError(
                "DATABASE_URL must start with sqlite:/// for local-first SQLite storage."
            )

        raw_path = self.database_url.removeprefix("sqlite:///")

        if not raw_path:
            raise ValueError("DATABASE_URL must include a database file path.")

        # The `sqlite:///` URL form supports both relative and absolute paths.
        # Absolute paths keep a leading slash (`sqlite:////tmp/app.db`).
        path = Path(raw_path if raw_path.startswith("/") else raw_path)
        return path if path.is_absolute() else Path.cwd() / path

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables with sensible local defaults.

        Returns:
            Settings: Fully populated settings object.

        Example:
            >>> settings = Settings.from_env()
            >>> settings.upload_dir.name
            'uploads'
        """

        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_meal_model=os.getenv("OPENAI_MEAL_MODEL", "gpt-4o-mini"),
            openai_transcribe_model=os.getenv(
                "OPENAI_TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe"
            ),
            openai_vision_model=os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini"),
            database_url=os.getenv("DATABASE_URL", "sqlite:///data/app.db"),
            upload_dir=Path(os.getenv("UPLOAD_DIR", "uploads")),
        )
