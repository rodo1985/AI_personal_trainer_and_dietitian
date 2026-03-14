"""Tests for glucose screenshot upload behavior and persistence."""

from __future__ import annotations

from backend.app.core.config import Settings


def test_glucose_upload_rejects_non_image_files(client) -> None:
    """Ensure upload endpoint accepts only image MIME types.

    Parameters:
        client: FastAPI test client fixture.

    Returns:
        None.
    """

    response = client.post(
        "/api/day/2026-03-03/glucose-uploads",
        files={"file": ("notes.txt", b"not-an-image", "text/plain")},
    )

    assert response.status_code == 415


def test_glucose_upload_saves_file_and_returns_summary(client, test_settings: Settings) -> None:
    """Persist uploaded image, save metadata, and include AI summary payload.

    Parameters:
        client: FastAPI test client fixture.
        test_settings: Isolated app settings fixture.

    Returns:
        None.
    """

    response = client.post(
        "/api/day/2026-03-03/glucose-uploads",
        files={"file": ("chart.png", b"png-bytes", "image/png")},
        data={"user_note": "Post long run"},
    )

    assert response.status_code == 201
    payload = response.json()
    saved_path = test_settings.upload_dir / payload["stored_path"]

    assert saved_path.exists()
    assert payload["summary_text"] == "Line chart appears to fluctuate with a late visible rise."
    assert payload["summary_warnings"] == ["Descriptive summary only; not medical advice."]

    day_response = client.get("/api/day/2026-03-03")
    assert day_response.status_code == 200
    day_payload = day_response.json()
    assert len(day_payload["glucose_uploads"]) == 1
