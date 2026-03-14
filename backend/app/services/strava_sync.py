"""Strava OAuth orchestration and rolling 7-day sync service."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol
from uuid import uuid4

from backend.app.config import AppSettings
from backend.app.repositories.strava_repository import ActivityRecord, StravaRepository
from backend.app.services.strava_client import StravaTokenResponse
from backend.app.services.token_crypto import TokenCrypto


class StravaClientProtocol(Protocol):
    """Define the Strava client behaviors required by the sync service.

    Parameters:
        None.

    Returns:
        None.

    Raises:
        None.

    Example:
        >>> # Any class implementing these methods can be injected into StravaSyncService.
    """

    def build_connect_url(self, state: str) -> str:
        """Build a Strava OAuth connect URL.

        Parameters:
            state: CSRF-protection state token.

        Returns:
            str: Connect URL.

        Raises:
            None.

        Example:
            >>> # url = client.build_connect_url("state")
        """

    def exchange_code_for_token(self, code: str) -> StravaTokenResponse:
        """Exchange callback code for token credentials.

        Parameters:
            code: OAuth callback code.

        Returns:
            StravaTokenResponse: Parsed token response.

        Raises:
            Exception: Client-specific API failures.

        Example:
            >>> # token = client.exchange_code_for_token("code")
        """

    def refresh_access_token(self, refresh_token: str) -> StravaTokenResponse:
        """Refresh an expired access token.

        Parameters:
            refresh_token: Existing refresh token.

        Returns:
            StravaTokenResponse: Fresh token response.

        Raises:
            Exception: Client-specific API failures.

        Example:
            >>> # token = client.refresh_access_token("refresh")
        """

    def get_recent_activities(
        self, access_token: str, window_start: datetime, window_end: datetime
    ) -> list[dict[str, Any]]:
        """Fetch activities from Strava for the sync window.

        Parameters:
            access_token: OAuth access token.
            window_start: Inclusive UTC start.
            window_end: Inclusive UTC end.

        Returns:
            list[dict[str, Any]]: Raw Strava activity payloads.

        Raises:
            Exception: Client-specific API failures.

        Example:
            >>> # activities = client.get_recent_activities(token, start, end)
        """


@dataclass(slots=True)
class CallbackResult:
    """Represent a successful OAuth callback completion.

    Parameters:
        connected: Whether the callback flow completed successfully.
        athlete_id: Connected Strava athlete identifier.
        expires_at: UTC expiry timestamp of the stored access token.

    Returns:
        CallbackResult: Structured callback completion payload.

    Raises:
        None.

    Example:
        >>> CallbackResult(connected=True, athlete_id=12, expires_at=datetime.now(timezone.utc))
    """

    connected: bool
    athlete_id: int
    expires_at: datetime


@dataclass(slots=True)
class SyncResult:
    """Represent a completed sync response payload.

    Parameters:
        run_id: Sync metadata record identifier.
        status: Terminal sync status (`success` or `failed`).
        window_start: Inclusive UTC sync-window start.
        window_end: Inclusive UTC sync-window end.
        fetched_count: Number of raw activities returned by Strava.
        upserted_count: Number of activities upserted locally.
        activities: Normalized persisted activities in the sync window.

    Returns:
        SyncResult: Structured sync result object.

    Raises:
        None.

    Example:
        >>> SyncResult(
        ...     run_id=1,
        ...     status="success",
        ...     window_start=datetime.now(timezone.utc),
        ...     window_end=datetime.now(timezone.utc),
        ...     fetched_count=2,
        ...     upserted_count=2,
        ...     activities=[],
        ... )
    """

    run_id: int
    status: str
    window_start: datetime
    window_end: datetime
    fetched_count: int
    upserted_count: int
    activities: list[ActivityRecord]


class StravaSyncService:
    """Coordinate OAuth, token refresh, and rolling recent activity sync.

    Parameters:
        settings: Runtime application settings.
        repository: Persistence adapter for Strava data.
        client: Strava API client.
        token_crypto: Encryption helper for token-at-rest security.

    Returns:
        StravaSyncService: Service instance.

    Raises:
        None.

    Example:
        >>> # service = StravaSyncService(settings, repo, client, crypto)
    """

    def __init__(
        self,
        settings: AppSettings,
        repository: StravaRepository,
        client: StravaClientProtocol,
        token_crypto: TokenCrypto,
    ) -> None:
        """Initialize service dependencies.

        Parameters:
            settings: Application configuration.
            repository: Repository for token/activity persistence.
            client: Strava API client implementation.
            token_crypto: Token encryption helper.

        Returns:
            None.

        Raises:
            None.

        Example:
            >>> # service = StravaSyncService(settings, repo, client, crypto)
        """

        self._settings = settings
        self._repository = repository
        self._client = client
        self._token_crypto = token_crypto

    def build_connect_url(self, state: str | None = None) -> str:
        """Return a Strava OAuth connect URL.

        Parameters:
            state: Optional state token. A random one is generated when omitted.

        Returns:
            str: Authorization URL used by the frontend to start OAuth.

        Raises:
            None.

        Example:
            >>> # url = service.build_connect_url()
        """

        oauth_state = state or uuid4().hex
        return self._client.build_connect_url(oauth_state)

    def handle_callback(self, code: str) -> CallbackResult:
        """Exchange callback code and persist encrypted token state.

        Parameters:
            code: OAuth authorization code from Strava callback.

        Returns:
            CallbackResult: Connection success payload.

        Raises:
            Exception: Propagates Strava client or persistence failures.

        Example:
            >>> # result = service.handle_callback("code")
        """

        token_response = self._client.exchange_code_for_token(code)
        self._store_tokens(token_response)
        return CallbackResult(
            connected=True,
            athlete_id=token_response.athlete_id,
            expires_at=token_response.expires_at,
        )

    def sync_recent(self, now: datetime | None = None) -> SyncResult:
        """Sync Strava activities for the rolling configured window.

        Parameters:
            now: Optional UTC override used by tests. Defaults to current UTC time.

        Returns:
            SyncResult: Persisted sync summary and normalized activities.

        Raises:
            RuntimeError: Raised when the account has not been connected yet.
            Exception: Propagates Strava API and persistence errors.

        Example:
            >>> # result = service.sync_recent()
        """

        current_time = now.astimezone(UTC) if now else datetime.now(UTC)
        window_end = current_time
        window_start = current_time - timedelta(days=self._settings.strava_sync_days)

        run_id = self._repository.create_sync_run(window_start=window_start, window_end=window_end)

        try:
            access_token = self._get_valid_access_token(current_time)
            raw_activities = self._client.get_recent_activities(
                access_token,
                window_start,
                window_end,
            )

            normalized_activities = [
                self._normalize_activity(raw_activity=activity, synced_at=current_time)
                for activity in raw_activities
                if self._is_within_window(
                    raw_activity=activity,
                    window_start=window_start,
                    window_end=window_end,
                )
            ]

            upserted_count = self._repository.upsert_activities(normalized_activities)
            summary = self._repository.complete_sync_run(
                run_id=run_id,
                status="success",
                fetched_count=len(raw_activities),
                upserted_count=upserted_count,
                error_message=None,
            )
        except Exception as exc:
            self._repository.complete_sync_run(
                run_id=run_id,
                status="failed",
                fetched_count=0,
                upserted_count=0,
                error_message=str(exc),
            )
            raise

        activities = self._repository.list_activities_between(
            window_start=window_start,
            window_end=window_end,
        )

        return SyncResult(
            run_id=summary.id,
            status=summary.status,
            window_start=summary.window_start,
            window_end=summary.window_end,
            fetched_count=summary.fetched_count,
            upserted_count=summary.upserted_count,
            activities=activities,
        )

    def update_rpe_override(self, strava_activity_id: str, rpe_override: int) -> ActivityRecord:
        """Set a manual RPE override for a normalized activity row.

        Parameters:
            strava_activity_id: Strava activity identifier.
            rpe_override: Manual perceived effort value (1-10).

        Returns:
            ActivityRecord: Updated activity record.

        Raises:
            RuntimeError: Raised when the activity is missing.
            sqlite3.Error: Raised when persistence fails.

        Example:
            >>> # updated = service.update_rpe_override("123", 7)
        """

        return self._repository.update_rpe_override(strava_activity_id, rpe_override)

    def _get_valid_access_token(self, now: datetime) -> str:
        """Return a usable access token, refreshing it when close to expiry.

        Parameters:
            now: Current UTC timestamp used to evaluate token freshness.

        Returns:
            str: Plain-text access token.

        Raises:
            RuntimeError: Raised if no Strava account has been connected yet.
            Exception: Propagates refresh call or persistence failures.

        Example:
            >>> # token = service._get_valid_access_token(datetime.now(UTC))
        """

        tokens = self._repository.get_tokens()
        if tokens is None:
            raise RuntimeError("No connected Strava account. Complete OAuth connect first.")

        access_token = self._token_crypto.decrypt(tokens.encrypted_access_token)
        refresh_token = self._token_crypto.decrypt(tokens.encrypted_refresh_token)

        # We refresh early to avoid edge cases where the token expires during pagination.
        if tokens.expires_at <= now + timedelta(seconds=60):
            refreshed = self._client.refresh_access_token(refresh_token)
            self._store_tokens(refreshed)
            return refreshed.access_token

        return access_token

    def _store_tokens(self, token_response: StravaTokenResponse) -> None:
        """Encrypt and persist token response values.

        Parameters:
            token_response: Parsed token payload from Strava.

        Returns:
            None.

        Raises:
            Exception: Propagates persistence failures.

        Example:
            >>> # service._store_tokens(token_response)
        """

        self._repository.upsert_tokens(
            athlete_id=token_response.athlete_id,
            encrypted_access_token=self._token_crypto.encrypt(token_response.access_token),
            encrypted_refresh_token=self._token_crypto.encrypt(token_response.refresh_token),
            expires_at=token_response.expires_at,
            scope=token_response.scope,
            token_type=token_response.token_type,
        )

    def _is_within_window(
        self, raw_activity: dict[str, Any], window_start: datetime, window_end: datetime
    ) -> bool:
        """Check whether a Strava activity belongs in the rolling sync window.

        Parameters:
            raw_activity: Raw Strava activity payload.
            window_start: Inclusive UTC window start.
            window_end: Inclusive UTC window end.

        Returns:
            bool: `True` when activity starts within the desired window.

        Raises:
            ValueError: Raised if activity is missing start time fields.

        Example:
            >>> # in_window = service._is_within_window(raw, start, end)
        """

        activity_start = self._parse_strava_datetime(raw_activity)
        return window_start <= activity_start <= window_end

    def _normalize_activity(
        self, raw_activity: dict[str, Any], synced_at: datetime
    ) -> ActivityRecord:
        """Normalize a raw Strava activity into local `ActivityRecord` format.

        Parameters:
            raw_activity: Raw activity JSON object from Strava.
            synced_at: UTC timestamp representing current sync run time.

        Returns:
            ActivityRecord: Normalized activity data for local persistence.

        Raises:
            KeyError: Raised if required `id` field is missing.
            ValueError: Raised when start time fields are missing or malformed.

        Example:
            >>> # record = service._normalize_activity(raw, datetime.now(UTC))
        """

        calories_raw = raw_activity.get("calories")
        suffer_score_raw = raw_activity.get("suffer_score")

        return ActivityRecord(
            strava_activity_id=str(raw_activity["id"]),
            name=str(raw_activity.get("name") or "Unnamed activity"),
            sport_type=str(
                raw_activity.get("sport_type") or raw_activity.get("type") or "Unknown"
            ),
            start_time=self._parse_strava_datetime(raw_activity),
            elapsed_time_s=int(
                raw_activity.get("elapsed_time") or raw_activity.get("moving_time") or 0
            ),
            calories=float(calories_raw) if calories_raw is not None else None,
            suffer_score=int(suffer_score_raw) if suffer_score_raw is not None else None,
            rpe_override=None,
            source_raw_json=json.dumps(raw_activity, sort_keys=True),
            synced_at=synced_at,
        )

    def _parse_strava_datetime(self, raw_activity: dict[str, Any]) -> datetime:
        """Parse activity start timestamp from Strava payload into UTC datetime.

        Parameters:
            raw_activity: Raw Strava activity payload.

        Returns:
            datetime: UTC-aware activity start timestamp.

        Raises:
            ValueError: Raised when start time fields are missing or malformed.

        Example:
            >>> # start = service._parse_strava_datetime(raw)
        """

        start_value = raw_activity.get("start_date") or raw_activity.get("start_date_local")
        if not start_value:
            raise ValueError("Strava activity is missing both start_date and start_date_local.")

        iso_value = str(start_value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(iso_value)

        if parsed.tzinfo is None:
            # Strava `start_date_local` can be timezone-naive, so we normalize to UTC.
            return parsed.replace(tzinfo=UTC)

        return parsed.astimezone(UTC)
