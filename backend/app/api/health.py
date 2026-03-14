"""Health endpoint definitions for the API shell."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.app.config import Settings, get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Response payload for the health check endpoint.

    Parameters:
        status: Service liveness indicator.
        service: Identifier for the responding service.
        environment: Environment label pulled from runtime settings.

    Returns:
        HealthResponse: Serialized JSON payload for `/api/health`.

    Raises:
        None.

    Example:
        >>> HealthResponse(status="ok", service="backend", environment="development")
    """

    status: str
    service: str
    environment: str


@router.get("/health", response_model=HealthResponse)
def read_health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    """Return a simple health payload to confirm the API is reachable.

    Parameters:
        settings: Runtime configuration injected by FastAPI dependencies.

    Returns:
        HealthResponse: Health payload that frontend and tests can rely on.

    Raises:
        None.

    Example:
        >>> payload = read_health(get_settings())
        >>> payload.status
        'ok'
    """

    return HealthResponse(
        status="ok",
        service="backend",
        environment=settings.app_env,
    )
