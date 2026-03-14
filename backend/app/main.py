"""FastAPI application entrypoint for the prototype backend."""

from __future__ import annotations

from fastapi import FastAPI

from backend.app.routers.strava import router as strava_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Parameters:
        None.

    Returns:
        FastAPI: Configured API application.

    Raises:
        None.

    Example:
        >>> app = create_app()
        >>> app.title
        'Personal Endurance Trainer Log API'
    """

    app = FastAPI(title="Personal Endurance Trainer Log API", version="0.1.0")

    @app.get("/health")
    def health_check() -> dict[str, str]:
        """Return a simple health status for local development checks.

        Parameters:
            None.

        Returns:
            dict[str, str]: Health status payload.

        Raises:
            None.

        Example:
            >>> # GET /health
        """

        return {"status": "ok"}

    app.include_router(strava_router)
    return app


app = create_app()
