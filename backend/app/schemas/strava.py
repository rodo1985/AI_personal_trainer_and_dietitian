"""Pydantic schema models for Strava API routes."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class StravaConnectResponse(BaseModel):
    """Response payload for the OAuth connect endpoint.

    Parameters:
        authorization_url: URL where the user authorizes Strava access.

    Returns:
        StravaConnectResponse: Serialized connect response.

    Raises:
        pydantic.ValidationError: Raised when response data is invalid.

    Example:
        >>> StravaConnectResponse(authorization_url="https://www.strava.com/oauth/authorize")
    """

    authorization_url: str


class StravaCallbackResponse(BaseModel):
    """Response payload for successful OAuth callback handling.

    Parameters:
        connected: Indicates whether account connection succeeded.
        athlete_id: Connected Strava athlete identifier.
        expires_at: UTC token expiration timestamp.

    Returns:
        StravaCallbackResponse: Serialized callback response.

    Raises:
        pydantic.ValidationError: Raised when response data is invalid.

    Example:
        >>> StravaCallbackResponse(connected=True, athlete_id=1, expires_at=datetime.now())
    """

    connected: bool
    athlete_id: int
    expires_at: datetime


class ActivityEntryResponse(BaseModel):
    """Normalized activity shape returned by Strava sync and override endpoints.

    Parameters:
        strava_activity_id: Strava activity identifier.
        name: Activity title.
        sport_type: Strava sport type.
        start_time: UTC activity start timestamp.
        elapsed_time_s: Activity duration in seconds.
        calories: Optional calorie estimate.
        suffer_score: Optional Strava suffer score.
        rpe_override: Optional manual perceived exertion override.

    Returns:
        ActivityEntryResponse: Serialized activity payload.

    Raises:
        pydantic.ValidationError: Raised when response data is invalid.

    Example:
        >>> ActivityEntryResponse(
        ...     strava_activity_id="1",
        ...     name="Run",
        ...     sport_type="Run",
        ...     start_time=datetime.now(),
        ...     elapsed_time_s=1800,
        ...     calories=None,
        ...     suffer_score=None,
        ...     rpe_override=6,
        ... )
    """

    strava_activity_id: str
    name: str
    sport_type: str
    start_time: datetime
    elapsed_time_s: int
    calories: float | None
    suffer_score: int | None
    rpe_override: int | None


class StravaSyncRecentResponse(BaseModel):
    """Response payload for rolling recent Strava sync operations.

    Parameters:
        run_id: Sync metadata record identifier.
        status: Terminal sync status string.
        window_start: Inclusive UTC start of sync window.
        window_end: Inclusive UTC end of sync window.
        fetched_count: Number of records returned by Strava API.
        upserted_count: Number of records upserted locally.
        activities: Normalized local activity rows for the synced window.

    Returns:
        StravaSyncRecentResponse: Serialized sync result.

    Raises:
        pydantic.ValidationError: Raised when response data is invalid.

    Example:
        >>> StravaSyncRecentResponse(
        ...     run_id=1,
        ...     status="success",
        ...     window_start=datetime.now(),
        ...     window_end=datetime.now(),
        ...     fetched_count=0,
        ...     upserted_count=0,
        ...     activities=[],
        ... )
    """

    run_id: int
    status: str
    window_start: datetime
    window_end: datetime
    fetched_count: int
    upserted_count: int
    activities: list[ActivityEntryResponse]


class RPEOverrideRequest(BaseModel):
    """Request payload for setting manual perceived effort on an activity.

    Parameters:
        rpe_override: Perceived effort value on a 1-10 scale.

    Returns:
        RPEOverrideRequest: Parsed request payload.

    Raises:
        pydantic.ValidationError: Raised when input is outside allowed range.

    Example:
        >>> RPEOverrideRequest(rpe_override=7)
    """

    rpe_override: int = Field(ge=1, le=10)


class RPEOverrideResponse(BaseModel):
    """Response payload for successful RPE override updates.

    Parameters:
        activity: Updated normalized activity record.

    Returns:
        RPEOverrideResponse: Serialized update payload.

    Raises:
        pydantic.ValidationError: Raised when response data is invalid.

    Example:
        >>> RPEOverrideResponse(
        ...     activity=ActivityEntryResponse(
        ...         strava_activity_id="1",
        ...         name="Ride",
        ...         sport_type="Ride",
        ...         start_time=datetime.now(),
        ...         elapsed_time_s=1200,
        ...         calories=500,
        ...         suffer_score=60,
        ...         rpe_override=8,
        ...     )
        ... )
    """

    activity: ActivityEntryResponse
