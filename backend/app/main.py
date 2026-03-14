"""FastAPI entrypoint for the backend AI logging APIs."""

from __future__ import annotations

from fastapi import FastAPI

from backend.app.api.routes.day_logs import router as day_log_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured app instance with routers and health endpoint.

    Example:
        >>> app = create_app()
        >>> app.title
        'Personal Endurance Trainer Log API'
    """

    app = FastAPI(
        title="Personal Endurance Trainer Log API",
        version="0.1.0",
        description=(
            "Backend APIs for AI-assisted meal logging, transcription, and "
            "glucose screenshot uploads."
        ),
    )

    app.include_router(day_log_router)

    @app.get("/health")
    def health_check() -> dict[str, str]:
        """Return a simple health payload for local checks.

        Returns:
            dict[str, str]: Health indicator payload.

        Example:
            GET /health
        """

        return {"status": "ok"}

    return app


app = create_app()
