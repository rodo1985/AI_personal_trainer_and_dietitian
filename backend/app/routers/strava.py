"""FastAPI router for Strava OAuth and recent sync endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.dependencies import get_strava_sync_service
from backend.app.repositories.strava_repository import ActivityRecord
from backend.app.schemas.strava import (
    ActivityEntryResponse,
    RPEOverrideRequest,
    RPEOverrideResponse,
    StravaCallbackResponse,
    StravaConnectResponse,
    StravaSyncRecentResponse,
)
from backend.app.services.strava_client import StravaAPIError
from backend.app.services.strava_sync import StravaSyncService

router = APIRouter(prefix="/api/strava", tags=["strava"])
StravaServiceDependency = Annotated[StravaSyncService, Depends(get_strava_sync_service)]


@router.get("/connect", response_model=StravaConnectResponse)
def get_strava_connect_url(
    service: StravaServiceDependency,
    state: str | None = Query(default=None),
) -> StravaConnectResponse:
    """Generate a Strava OAuth connect URL for the frontend flow.

    Parameters:
        state: Optional state token passed through OAuth redirect flow.
        service: Injected Strava sync service.

    Returns:
        StravaConnectResponse: Contains the authorization URL.

    Raises:
        None.

    Example:
        >>> # GET /api/strava/connect
    """

    return StravaConnectResponse(
        authorization_url=service.build_connect_url(state=state)
    )


@router.get("/callback", response_model=StravaCallbackResponse)
def handle_strava_callback(
    service: StravaServiceDependency,
    code: str = Query(..., description="OAuth callback code from Strava"),
) -> StravaCallbackResponse:
    """Handle Strava OAuth callback and persist encrypted token state.

    Parameters:
        code: OAuth callback code from Strava.
        service: Injected Strava sync service.

    Returns:
        StravaCallbackResponse: Connection result with athlete and expiry metadata.

    Raises:
        HTTPException: Raised for Strava API or persistence failures.

    Example:
        >>> # GET /api/strava/callback?code=abc
    """

    try:
        result = service.handle_callback(code)
    except StravaAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return StravaCallbackResponse(
        connected=result.connected,
        athlete_id=result.athlete_id,
        expires_at=result.expires_at,
    )


@router.post("/sync/recent", response_model=StravaSyncRecentResponse)
def sync_recent_strava_activities(
    service: StravaServiceDependency,
) -> StravaSyncRecentResponse:
    """Sync the rolling recent activity window from Strava into local storage.

    Parameters:
        service: Injected Strava sync service.

    Returns:
        StravaSyncRecentResponse: Sync summary and normalized activities.

    Raises:
        HTTPException: Raised for not-connected, Strava API, or persistence failures.

    Example:
        >>> # POST /api/strava/sync/recent
    """

    try:
        result = service.sync_recent()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except StravaAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return StravaSyncRecentResponse(
        run_id=result.run_id,
        status=result.status,
        window_start=result.window_start,
        window_end=result.window_end,
        fetched_count=result.fetched_count,
        upserted_count=result.upserted_count,
        activities=[
            _map_activity_response(activity) for activity in result.activities
        ],
    )


@router.patch(
    "/activities/{strava_activity_id}/rpe-override",
    response_model=RPEOverrideResponse,
)
def update_activity_rpe_override(
    strava_activity_id: str,
    payload: RPEOverrideRequest,
    service: StravaServiceDependency,
) -> RPEOverrideResponse:
    """Set manual perceived effort when Strava does not expose a direct value.

    Parameters:
        strava_activity_id: Unique Strava activity identifier.
        payload: Override payload containing a 1-10 `rpe_override` value.
        service: Injected Strava sync service.

    Returns:
        RPEOverrideResponse: Updated normalized activity payload.

    Raises:
        HTTPException: Raised when activity does not exist or persistence fails.

    Example:
        >>> # PATCH /api/strava/activities/123/rpe-override
    """

    try:
        updated_activity = service.update_rpe_override(
            strava_activity_id,
            payload.rpe_override,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return RPEOverrideResponse(activity=_map_activity_response(updated_activity))


def _map_activity_response(activity: ActivityRecord) -> ActivityEntryResponse:
    """Convert repository activity records to API response models.

    Parameters:
        activity: Repository activity object.

    Returns:
        ActivityEntryResponse: API-friendly activity payload.

    Raises:
        pydantic.ValidationError: Raised when mapped values are invalid.

    Example:
        >>> # response = _map_activity_response(activity)
    """

    return ActivityEntryResponse(
        strava_activity_id=activity.strava_activity_id,
        name=activity.name,
        sport_type=activity.sport_type,
        start_time=activity.start_time,
        elapsed_time_s=activity.elapsed_time_s,
        calories=activity.calories,
        suffer_score=activity.suffer_score,
        rpe_override=activity.rpe_override,
    )
