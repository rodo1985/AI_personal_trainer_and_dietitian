"""Glucose upload file handling and descriptive summary helpers."""

from __future__ import annotations

import re
from datetime import date
from uuid import uuid4

from fastapi import UploadFile

from backend.app.config import Settings


def sanitize_filename(original_filename: str) -> str:
    """Return a filesystem-safe filename preserving extension when possible.

    Parameters:
        original_filename: Raw filename from client upload metadata.

    Returns:
        str: Sanitized filename safe for local storage.

    Raises:
        None.

    Example:
        >>> sanitize_filename("My Chart (1).png")
        'my-chart-1.png'
    """

    lowered = original_filename.strip().lower() or "upload"
    normalized = re.sub(r"[^a-z0-9._-]", "-", lowered)
    collapsed = re.sub(r"-+", "-", normalized).strip("-")
    return collapsed or "upload"


async def persist_upload_file(
    settings: Settings,
    target_date: date,
    upload_file: UploadFile,
) -> str:
    """Persist an uploaded glucose image and return a frontend-accessible URL.

    Parameters:
        settings: Application settings that define upload storage path.
        target_date: Date folder used to group uploads by day.
        upload_file: Uploaded file object provided by FastAPI.

    Returns:
        str: Relative URL path that frontend can render.

    Raises:
        OSError: If writing to disk fails.

    Example:
        >>> isinstance(persist_upload_file, object)
        True
    """

    safe_name = sanitize_filename(upload_file.filename or "upload.png")
    unique_name = f"{uuid4().hex}-{safe_name}"

    day_folder = settings.upload_path / target_date.isoformat()
    day_folder.mkdir(parents=True, exist_ok=True)

    destination = day_folder / unique_name
    payload = await upload_file.read()

    # File writes stay local-first by design for v1 to keep setup simple.
    destination.write_bytes(payload)

    return f"/uploads/{target_date.isoformat()}/{unique_name}"


def build_descriptive_summary(original_filename: str, user_note: str | None = None) -> str:
    """Build a non-medical, descriptive summary for a glucose screenshot.

    Parameters:
        original_filename: Name of the uploaded image file.
        user_note: Optional user note added during upload.

    Returns:
        str: Descriptive text suitable for day-log display.

    Raises:
        None.

    Example:
        >>> "descriptive" in build_descriptive_summary("chart.png")
        True
    """

    note_clause = ""
    if user_note:
        note_clause = f" User note: {user_note.strip()}"

    return (
        "AI descriptive summary: screenshot uploaded successfully for manual review. "
        "This summary is observational only and does not provide medical guidance. "
        f"Source file: {original_filename}.{note_clause}"
    )
