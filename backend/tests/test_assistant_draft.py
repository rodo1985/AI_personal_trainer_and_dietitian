"""Tests for draft generation and transcription pipeline behavior."""

from __future__ import annotations


def test_assistant_draft_flags_unmatched_food_and_requires_confirmation(client) -> None:
    """Ensure unmatched foods stay visible and force confirmation before save.

    Parameters:
        client: FastAPI test client fixture.

    Returns:
        None.
    """

    response = client.post(
        "/api/day/2026-03-01/assistant/draft",
        json={"text": "breakfast: oats, mystery powder", "source": "typed"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["confirm_before_save"] is True
    assert payload["normalized_payload"]["meal_slot"] == "breakfast"

    items = payload["normalized_payload"]["items"]
    unmatched = next(item for item in items if item["raw_text"] == "mystery powder")
    assert unmatched["matched"] is False
    assert unmatched["unresolved_reason"] is not None

    # Totals should only include matched items and never fake precision for unknown foods.
    assert payload["normalized_payload"]["totals"]["calories"] == 154.0


def test_assistant_draft_requires_slot_confirmation_when_slot_missing(client) -> None:
    """Ensure missing meal slot is surfaced and requires confirmation.

    Parameters:
        client: FastAPI test client fixture.

    Returns:
        None.
    """

    response = client.post(
        "/api/day/2026-03-01/assistant/draft",
        json={"text": "oats and banana", "source": "typed"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["confirm_before_save"] is True
    assert payload["normalized_payload"]["meal_slot"] is None
    assert any("Meal slot is missing" in warning for warning in payload["warnings"])


def test_audio_transcription_uses_same_draft_pipeline(client) -> None:
    """Ensure transcript text is routed through the same meal draft flow.

    Parameters:
        client: FastAPI test client fixture.

    Returns:
        None.
    """

    response = client.post(
        "/api/day/2026-03-01/assistant/transcribe",
        files={"file": ("meal.m4a", b"audio-bytes", "audio/m4a")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["transcript_text"] == "dinner: rice and salmon"
    assert payload["draft"]["normalized_payload"]["meal_slot"] == "dinner"
    assert payload["draft"]["confirm_before_save"] is False
