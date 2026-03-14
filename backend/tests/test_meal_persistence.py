"""Tests for meal persistence and confirmation validation rules."""

from __future__ import annotations


def test_save_meal_rejects_ambiguous_draft_without_confirmation(client) -> None:
    """Reject save calls when confirmation is required but not acknowledged.

    Parameters:
        client: FastAPI test client fixture.

    Returns:
        None.
    """

    draft_response = client.post(
        "/api/day/2026-03-02/assistant/draft",
        json={"text": "breakfast: oats and unknown spread", "source": "typed"},
    )
    assert draft_response.status_code == 200

    save_response = client.post(
        "/api/day/2026-03-02/meals",
        json={
            "draft": draft_response.json(),
            "confirmation_acknowledged": False,
        },
    )

    assert save_response.status_code == 409
    assert "requires explicit confirmation" in save_response.json()["detail"]


def test_save_meal_persists_confirmed_draft_and_updates_day_totals(client) -> None:
    """Persist confirmed draft and expose it in aggregate day response.

    Parameters:
        client: FastAPI test client fixture.

    Returns:
        None.
    """

    draft_response = client.post(
        "/api/day/2026-03-02/assistant/draft",
        json={"text": "lunch: chicken and rice", "source": "typed"},
    )
    assert draft_response.status_code == 200

    save_response = client.post(
        "/api/day/2026-03-02/meals",
        json={
            "draft": draft_response.json(),
            "confirmation_acknowledged": False,
        },
    )
    assert save_response.status_code == 201

    day_response = client.get("/api/day/2026-03-02")
    assert day_response.status_code == 200

    payload = day_response.json()
    assert len(payload["meal_entries"]) == 1
    assert payload["meal_entries"][0]["meal_slot"] == "lunch"
    assert payload["daily_totals"]["calories"] > 0
