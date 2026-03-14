"""Recent-day Strava sync helpers used by integration hardening flows."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from urllib.parse import urlencode

from backend.app.config import Settings
from backend.app.schemas import ActivityEntry, StravaConnectResponse, StravaSyncResult
from backend.app.services.day_log_service import (
    record_sync_run,
    upsert_activity_entries,
    utcnow_iso,
)


def sync_recent_activities(
    settings: Settings,
    reference_date: date | None = None,
) -> StravaSyncResult:
    """Sync a rolling seven-day window of activities into local storage.

    Parameters:
        settings: Application settings used for persistence and Strava metadata.
        reference_date: Optional anchor date for deterministic testing.

    Returns:
        StravaSyncResult: Summary counts and sync window details.

    Raises:
        Exception: Propagates unexpected persistence failures after recording metadata.

    Example:
        >>> isinstance(sync_recent_activities, object)
        True
    """

    started_at = utcnow_iso()
    today = reference_date or datetime.now(tz=UTC).date()
    window_start = today - timedelta(days=6)
    window_end = today

    try:
        activities = generate_demo_recent_activities(window_start, window_end)
        imported_count, updated_count = upsert_activity_entries(settings, activities)

        finished_at = utcnow_iso()
        record_sync_run(
            settings=settings,
            started_at=started_at,
            finished_at=finished_at,
            status="success",
            imported_count=imported_count,
            updated_count=updated_count,
        )

        return StravaSyncResult(
            started_at=started_at,
            finished_at=finished_at,
            imported_count=imported_count,
            updated_count=updated_count,
            window_start=window_start.isoformat(),
            window_end=window_end.isoformat(),
            status="success",
        )
    except Exception as error:  # pragma: no cover - exercised via higher-level failure behavior.
        finished_at = utcnow_iso()
        record_sync_run(
            settings=settings,
            started_at=started_at,
            finished_at=finished_at,
            status="failed",
            imported_count=0,
            updated_count=0,
            error_message=str(error),
        )
        raise


def generate_demo_recent_activities(window_start: date, window_end: date) -> list[ActivityEntry]:
    """Generate deterministic local activities for a date window.

    Parameters:
        window_start: Inclusive start of sync window.
        window_end: Inclusive end of sync window.

    Returns:
        list[ActivityEntry]: Deterministic activities, one per day.

    Raises:
        ValueError: If ``window_end`` is before ``window_start``.

    Example:
        >>> len(generate_demo_recent_activities(date(2026, 1, 1), date(2026, 1, 3)))
        3
    """

    if window_end < window_start:
        raise ValueError("window_end cannot be before window_start")

    activities: list[ActivityEntry] = []
    cursor = window_start

    while cursor <= window_end:
        day_index = (cursor - window_start).days
        sport_type = "Run" if day_index % 2 == 0 else "Ride"
        start_at = datetime.combine(cursor, time(hour=7, minute=30), tzinfo=UTC)

        # Purposefully omit optional fields on alternating days to ensure downstream
        # UI and APIs are resilient to sparse Strava payloads.
        calories = float(620 + day_index * 25) if day_index % 3 != 0 else None
        suffer_score = float(45 + day_index * 2) if day_index % 4 != 0 else None

        activities.append(
            ActivityEntry(
                strava_activity_id=f"demo-{cursor.isoformat()}-{sport_type.lower()}",
                name=f"{sport_type} Session {cursor.isoformat()}",
                sport_type=sport_type,
                start_time=start_at.isoformat(),
                elapsed_time_s=3600 + (day_index * 90),
                calories=calories,
                suffer_score=suffer_score,
                rpe_override=None,
            )
        )

        cursor += timedelta(days=1)

    return activities


def build_connect_payload(settings: Settings) -> StravaConnectResponse:
    """Build a frontend-facing payload for starting Strava OAuth.

    Parameters:
        settings: Application settings that may include Strava credentials.

    Returns:
        StravaConnectResponse: OAuth connection state and URL when configured.

    Raises:
        None.

    Example:
        >>> build_connect_payload(Settings()).configured in {True, False}
        True
    """

    required_present = bool(
        settings.strava_client_id and settings.strava_client_secret and settings.strava_redirect_uri
    )

    if not required_present:
        return StravaConnectResponse(
            configured=False,
            connect_url=None,
            message=(
                "Strava OAuth is not configured yet. "
                "Set STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET."
            ),
        )

    params = urlencode(
        {
            "client_id": settings.strava_client_id,
            "response_type": "code",
            "redirect_uri": settings.strava_redirect_uri,
            "approval_prompt": "auto",
            "scope": "activity:read_all",
            "state": "local-prototype",
        }
    )

    return StravaConnectResponse(
        configured=True,
        connect_url=f"https://www.strava.com/oauth/authorize?{params}",
        message="Strava OAuth is configured. Complete the authorization in your browser.",
    )
