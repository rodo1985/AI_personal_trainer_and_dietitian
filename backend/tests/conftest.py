"""Pytest fixtures shared across backend API tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.core.dependencies import get_ai_client, get_settings
from backend.app.main import create_app
from backend.app.models.schemas import GlucoseSummaryResult, MealStructureHint


class FakeAIClient:
    """Deterministic fake AI client for endpoint tests.

    This fake keeps tests offline and stable while still exercising endpoint
    behavior that depends on transcription and screenshot summarization.
    """

    def extract_meal_structure(self, text: str) -> MealStructureHint | None:
        """Return no structure hint so parser logic is exercised in tests.

        Parameters:
            text: Meal source text.

        Returns:
            MealStructureHint | None: Always `None`.
        """

        return None

    def transcribe_audio(self, audio_bytes: bytes, filename: str, content_type: str) -> str:
        """Return a fixed transcript text for deterministic tests.

        Parameters:
            audio_bytes: Uploaded audio bytes.
            filename: Original upload filename.
            content_type: MIME type from upload metadata.

        Returns:
            str: Deterministic transcript text.
        """

        return "dinner: rice and salmon"

    def summarize_glucose_screenshot(
        self,
        image_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> GlucoseSummaryResult:
        """Return a deterministic non-medical screenshot summary.

        Parameters:
            image_bytes: Uploaded image bytes.
            filename: Original upload filename.
            content_type: MIME type from upload metadata.

        Returns:
            GlucoseSummaryResult: Summary with one warning.
        """

        return GlucoseSummaryResult(
            summary_text="Line chart appears to fluctuate with a late visible rise.",
            warnings=["Descriptive summary only; not medical advice."],
        )


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """Create isolated settings for each test.

    Parameters:
        tmp_path: Built-in pytest temporary path fixture.

    Returns:
        Settings: Settings using temp SQLite and upload paths.
    """

    database_path = tmp_path / "test.db"
    upload_dir = tmp_path / "uploads"
    return Settings(
        openai_api_key=None,
        openai_meal_model="gpt-test-meal",
        openai_transcribe_model="gpt-test-transcribe",
        openai_vision_model="gpt-test-vision",
        database_url=f"sqlite:///{database_path}",
        upload_dir=upload_dir,
    )


@pytest.fixture
def client(test_settings: Settings) -> TestClient:
    """Create a FastAPI test client with deterministic dependency overrides.

    Parameters:
        test_settings: Isolated test settings fixture.

    Returns:
        TestClient: Ready-to-use API client.
    """

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_ai_client] = lambda: FakeAIClient()
    return TestClient(app)
