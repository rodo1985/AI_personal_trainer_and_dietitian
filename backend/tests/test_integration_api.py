"""Integration tests for API behavior required by Prompt 5 hardening."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient


def test_day_log_starts_with_empty_sections(client: TestClient) -> None:
    """Verify day aggregates include empty-state payloads for a new date.

    Parameters:
        client: Isolated API test client fixture.

    Returns:
        None.

    Raises:
        AssertionError: If payload shape or totals are incorrect.

    Example:
        >>> test_day_log_starts_with_empty_sections  # doctest: +ELLIPSIS
        <function ...>
    """

    response = client.get("/api/day/2026-03-05")

    assert response.status_code == 200
    payload = response.json()

    assert payload["meal_entries"] == []
    assert payload["activity_entries"] == []
    assert payload["glucose_uploads"] == []
    assert payload["daily_totals"] == {
        "calories": 0.0,
        "protein_g": 0.0,
        "carbs_g": 0.0,
        "fat_g": 0.0,
    }


def test_meal_draft_save_and_edit_flow(client: TestClient) -> None:
    """Verify meal draft generation, save, and edit endpoints work end-to-end.

    Parameters:
        client: Isolated API test client fixture.

    Returns:
        None.

    Raises:
        AssertionError: If any step of the flow fails.

    Example:
        >>> test_meal_draft_save_and_edit_flow  # doctest: +ELLIPSIS
        <function ...>
    """

    day = "2026-03-05"
    draft_response = client.post(
        f"/api/day/{day}/assistant/draft",
        json={"text": "Breakfast: oats and banana", "meal_slot_hint": "breakfast"},
    )

    assert draft_response.status_code == 200
    draft_payload = draft_response.json()
    assert draft_payload["confirm_before_save"] is True
    assert draft_payload["normalized_payload"]["meal_slot"] == "breakfast"

    save_response = client.post(f"/api/day/{day}/meals", json=draft_payload["normalized_payload"])
    assert save_response.status_code == 200
    meal_entry = save_response.json()
    assert meal_entry["id"] > 0

    edit_response = client.put(
        f"/api/day/{day}/meals/{meal_entry['id']}",
        json={"source_text": "Breakfast: oats, banana, and yogurt", "status": "edited"},
    )
    assert edit_response.status_code == 200
    assert edit_response.json()["status"] == "edited"

    day_response = client.get(f"/api/day/{day}")
    assert day_response.status_code == 200
    assert len(day_response.json()["meal_entries"]) == 1


def test_strava_sync_is_idempotent_on_repeated_calls(client: TestClient) -> None:
    """Verify repeated sync calls do not create duplicate activity records.

    Parameters:
        client: Isolated API test client fixture.

    Returns:
        None.

    Raises:
        AssertionError: If idempotent upsert behavior regresses.

    Example:
        >>> test_strava_sync_is_idempotent_on_repeated_calls  # doctest: +ELLIPSIS
        <function ...>
    """

    first_sync = client.post("/api/strava/sync/recent")
    assert first_sync.status_code == 200
    first_payload = first_sync.json()
    assert first_payload["imported_count"] == 7
    assert first_payload["updated_count"] == 0

    second_sync = client.post("/api/strava/sync/recent")
    assert second_sync.status_code == 200
    second_payload = second_sync.json()
    assert second_payload["imported_count"] == 0
    assert second_payload["updated_count"] == 7

    today = datetime.now(tz=UTC).date().isoformat()
    day_payload = client.get(f"/api/day/{today}").json()
    assert len(day_payload["activity_entries"]) == 1


def test_glucose_upload_is_saved_and_visible_in_day_log(client: TestClient) -> None:
    """Verify glucose upload metadata is persisted and rendered in day aggregates.

    Parameters:
        client: Isolated API test client fixture.

    Returns:
        None.

    Raises:
        AssertionError: If upload persistence or retrieval fails.

    Example:
        >>> test_glucose_upload_is_saved_and_visible_in_day_log  # doctest: +ELLIPSIS
        <function ...>
    """

    day = "2026-03-05"
    upload_response = client.post(
        f"/api/day/{day}/glucose-uploads",
        files={"file": ("glucose.png", b"image-bytes", "image/png")},
        data={"user_note": "After long run"},
    )

    assert upload_response.status_code == 200
    upload_payload = upload_response.json()
    assert upload_payload["file_url"].startswith("/uploads/2026-03-05/")
    assert "observational only" in upload_payload["ai_summary"]

    day_response = client.get(f"/api/day/{day}")
    assert day_response.status_code == 200
    uploads = day_response.json()["glucose_uploads"]
    assert len(uploads) == 1
    assert uploads[0]["user_note"] == "After long run"
