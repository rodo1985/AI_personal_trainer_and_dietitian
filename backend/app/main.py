"""FastAPI entrypoint for the Personal Endurance Trainer Log backend."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.api.router import build_api_router
from backend.app.config import get_settings
from backend.app.database import initialize_database


def create_application() -> FastAPI:
    """Build and configure the FastAPI application instance.

    Parameters:
        None.

    Returns:
        FastAPI: Configured FastAPI application ready for local development.

    Raises:
        ValueError: Raised if ``DATABASE_URL`` is not a supported SQLite URL.
        sqlite3.DatabaseError: Raised if SQLite initialization fails during startup.

    Example:
        >>> app = create_application()
        >>> app.title
        'Personal Endurance Trainer Log Prototype API'
    """

    settings = get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        """Initialize local resources before the API starts handling requests.

        Parameters:
            _: FastAPI instance provided by FastAPI lifespan hooks.

        Returns:
            AsyncIterator[None]: Lifespan context manager for startup and shutdown.

        Raises:
            ValueError: Raised when ``DATABASE_URL`` is malformed.
            sqlite3.DatabaseError: Raised when SQLite initialization fails.

        Example:
            >>> # FastAPI executes this automatically during app startup.
            >>> True
            True
        """

        initialize_database(settings.database_url)
        # Uploads are local-first in v1, so we guarantee the directory exists.
        settings.upload_dir.mkdir(parents=True, exist_ok=True)
        yield

    application = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        lifespan=lifespan,
    )
    application.include_router(build_api_router(), prefix=settings.api_prefix)
    return application


app = create_application()
