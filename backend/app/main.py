"""FastAPI application entrypoint for the endurance day-log prototype."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes import router as api_router
from backend.app.config import get_settings
from backend.app.database import initialize_database


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance.

    Parameters:
        None.

    Returns:
        FastAPI: Configured application with routes and middleware.

    Raises:
        OSError: If filesystem setup for database or upload storage fails.

    Example:
        >>> isinstance(create_app(), FastAPI)
        True
    """

    settings = get_settings()
    initialize_database(settings)

    app = FastAPI(title="Personal Endurance Trainer Log", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")
    app.mount("/uploads", StaticFiles(directory=settings.upload_path), name="uploads")

    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        """Return a simple liveness payload for local diagnostics.

        Parameters:
            None.

        Returns:
            dict[str, str]: Static health response.

        Raises:
            None.

        Example:
            >>> healthcheck()["status"]
            'ok'
        """

        return {"status": "ok"}

    return app


app = create_app()
