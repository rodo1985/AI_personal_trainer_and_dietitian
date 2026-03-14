"""Tests for aggregate day endpoint behavior."""

from __future__ import annotations


def test_day_endpoint_returns_empty_aggregate_for_new_day(client) -> None:
    """Return empty arrays and zero totals when no day data exists.

    Parameters:
        client: FastAPI test client fixture.

    Returns:
        None.
    """

    response = client.get("/api/day/2026-03-04")
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
