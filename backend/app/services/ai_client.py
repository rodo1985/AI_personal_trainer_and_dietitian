"""OpenAI-backed AI adapters for parsing, transcription, and screenshot summaries."""

from __future__ import annotations

import base64
import io
import json
from typing import Protocol

from backend.app.core.config import Settings
from backend.app.models.schemas import GlucoseSummaryResult, MealStructureHint

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - guarded by dependency management.
    OpenAI = None


class AIClientProtocol(Protocol):
    """Protocol for AI tasks used by the backend service layer."""

    def extract_meal_structure(self, text: str) -> MealStructureHint | None:
        """Extract a structured meal hint from free text.

        Parameters:
            text: User-entered meal text.

        Returns:
            MealStructureHint | None: Structured hint when available.
        """

    def transcribe_audio(
        self,
        audio_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> str:
        """Transcribe uploaded audio to text.

        Parameters:
            audio_bytes: Raw audio bytes.
            filename: Original upload name.
            content_type: MIME type for the upload.

        Returns:
            str: Transcript text.

        Raises:
            RuntimeError: If transcription cannot be produced.
        """

    def summarize_glucose_screenshot(
        self,
        image_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> GlucoseSummaryResult:
        """Generate a descriptive summary from a glucose screenshot.

        Parameters:
            image_bytes: Raw image bytes.
            filename: Original upload name.
            content_type: MIME type for the upload.

        Returns:
            GlucoseSummaryResult: Structured summary text and warnings.
        """


class DisabledAIClient:
    """Fallback client used when OpenAI credentials are not configured.

    This allows local tests and non-AI endpoints to run while surfacing a clear,
    explicit message on AI-dependent actions.
    """

    def extract_meal_structure(self, text: str) -> MealStructureHint | None:
        """Return no AI hint so the rule-based parser can proceed.

        Parameters:
            text: User-entered meal text.

        Returns:
            MealStructureHint | None: Always `None`.

        Example:
            >>> DisabledAIClient().extract_meal_structure("oats") is None
            True
        """

        return None

    def transcribe_audio(
        self,
        audio_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> str:
        """Raise an explicit error because transcription needs OpenAI.

        Parameters:
            audio_bytes: Raw audio bytes.
            filename: Original upload name.
            content_type: MIME type for the upload.

        Returns:
            str: Never returned.

        Raises:
            RuntimeError: Always raised to request OpenAI configuration.
        """

        raise RuntimeError(
            "Audio transcription requires OPENAI_API_KEY. "
            "Set it in your environment before calling this endpoint."
        )

    def summarize_glucose_screenshot(
        self,
        image_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> GlucoseSummaryResult:
        """Return a transparent placeholder summary without fake precision.

        Parameters:
            image_bytes: Raw image bytes.
            filename: Original upload name.
            content_type: MIME type for the upload.

        Returns:
            GlucoseSummaryResult: Placeholder summary with warning.
        """

        return GlucoseSummaryResult(
            summary_text=(
                "AI summary unavailable because OPENAI_API_KEY is not configured. "
                "Upload was saved and can be reviewed manually."
            ),
            warnings=[
                "No AI analysis was run. Add OPENAI_API_KEY to enable screenshot summaries."
            ],
        )


class OpenAIAssistantClient:
    """OpenAI implementation for structured meal parsing, transcription, and vision."""

    def __init__(self, settings: Settings) -> None:
        """Construct a reusable OpenAI client with environment-configured models.

        Parameters:
            settings: Application settings with model IDs and API key.

        Returns:
            None.

        Raises:
            RuntimeError: If OpenAI dependency is unavailable at runtime.
        """

        if OpenAI is None:
            raise RuntimeError("OpenAI dependency is not installed.")
        self._settings = settings
        self._client = OpenAI(api_key=settings.openai_api_key)

    def extract_meal_structure(self, text: str) -> MealStructureHint | None:
        """Use OpenAI structured output to suggest meal slot and food items.

        Parameters:
            text: User-entered meal text.

        Returns:
            MealStructureHint | None: Structured hint, or `None` if parsing fails.
        """

        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "meal_structure_hint",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "meal_slot": {
                            "type": ["string", "null"],
                            "enum": ["breakfast", "lunch", "dinner", "snacks", None],
                        },
                        "food_items": {
                            "type": "array",
                            "items": {"type": "string"},
                            "default": [],
                        },
                        "assumptions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "default": [],
                        },
                        "warnings": {
                            "type": "array",
                            "items": {"type": "string"},
                            "default": [],
                        },
                    },
                    "required": ["meal_slot", "food_items", "assumptions", "warnings"],
                    "additionalProperties": False,
                },
            },
        }

        try:
            completion = self._client.chat.completions.create(
                model=self._settings.openai_meal_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You structure athlete meal notes into JSON. Keep warnings explicit "
                            "when input is ambiguous and do not invent exact nutrition values."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Extract meal_slot and food_items from the text. "
                            "Return warnings for uncertainty.\n\n"
                            f"Text: {text}"
                        ),
                    },
                ],
                response_format=response_format,
            )
            message_content = completion.choices[0].message.content
            if not message_content:
                return None
            payload = json.loads(message_content)
            return MealStructureHint.model_validate(payload)
        except Exception:
            # We intentionally fall back to deterministic parsing if this call fails.
            return None

    def transcribe_audio(
        self,
        audio_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> str:
        """Transcribe audio bytes with an OpenAI transcription model.

        Parameters:
            audio_bytes: Raw audio bytes.
            filename: Original upload name.
            content_type: MIME type for the upload.

        Returns:
            str: Transcript text.

        Raises:
            RuntimeError: If OpenAI returns no transcript text.
        """

        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename
        transcript = self._client.audio.transcriptions.create(
            model=self._settings.openai_transcribe_model,
            file=audio_file,
        )
        transcript_text = (getattr(transcript, "text", "") or "").strip()
        if not transcript_text:
            raise RuntimeError("OpenAI transcription returned no text.")
        return transcript_text

    def summarize_glucose_screenshot(
        self,
        image_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> GlucoseSummaryResult:
        """Create a non-medical descriptive summary of a glucose chart screenshot.

        Parameters:
            image_bytes: Raw image bytes.
            filename: Original upload name.
            content_type: MIME type for the upload.

        Returns:
            GlucoseSummaryResult: Structured summary text and warnings.

        Raises:
            RuntimeError: If OpenAI returns an invalid JSON payload.
        """

        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "glucose_summary",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "summary_text": {"type": "string"},
                        "warnings": {
                            "type": "array",
                            "items": {"type": "string"},
                            "default": [],
                        },
                    },
                    "required": ["summary_text", "warnings"],
                    "additionalProperties": False,
                },
            },
        }

        completion = self._client.chat.completions.create(
            model=self._settings.openai_vision_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Describe what is visible in glucose chart screenshots in plain language. "
                        "Do not provide medical advice, diagnosis, or treatment guidance."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Summarize visible chart patterns and annotate uncertainty. "
                                "Keep the summary descriptive and non-medical."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{content_type};base64,{encoded_image}",
                            },
                        },
                    ],
                },
            ],
            response_format=response_format,
        )

        message_content = completion.choices[0].message.content
        if not message_content:
            raise RuntimeError("OpenAI vision summary returned empty content.")
        payload = json.loads(message_content)
        return GlucoseSummaryResult.model_validate(payload)


def build_ai_client(settings: Settings) -> AIClientProtocol:
    """Build an AI client implementation based on current environment settings.

    Parameters:
        settings: Runtime settings with optional OpenAI credentials.

    Returns:
        AIClientProtocol: OpenAI client when configured, otherwise a fallback client.

    Example:
        >>> client = build_ai_client(Settings.from_env())
        >>> hasattr(client, "extract_meal_structure")
        True
    """

    if settings.openai_api_key:
        return OpenAIAssistantClient(settings)
    return DisabledAIClient()
