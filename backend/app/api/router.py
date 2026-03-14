"""Central API router assembly for the backend scaffold."""

from fastapi import APIRouter

from backend.app.api.health import router as health_router


def build_api_router() -> APIRouter:
    """Compose all API routes under a single router object.

    Parameters:
        None.

    Returns:
        APIRouter: Root router that includes all endpoint modules.

    Raises:
        None.

    Example:
        >>> api_router = build_api_router()
        >>> isinstance(api_router, APIRouter)
        True
    """

    api_router = APIRouter()
    api_router.include_router(health_router)
    return api_router
