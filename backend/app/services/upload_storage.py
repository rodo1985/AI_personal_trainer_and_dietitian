"""Local filesystem storage service for glucose screenshot uploads."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True)
class StoredUpload:
    """Metadata returned after writing an uploaded file to disk.

    Attributes:
        relative_path: Relative path from the configured upload root.
        absolute_path: Absolute file path where content was stored.
        size_bytes: Persisted byte length.
    """

    relative_path: str
    absolute_path: Path
    size_bytes: int


class LocalUploadStorage:
    """Persist uploaded glucose images under a date-based folder structure.

    Parameters:
        upload_root: Root folder for upload storage.

    Example:
        >>> storage = LocalUploadStorage(Path("uploads"))
        >>> storage.upload_root.name
        'uploads'
    """

    def __init__(self, upload_root: Path) -> None:
        """Store upload root path and ensure it exists.

        Parameters:
            upload_root: Root directory for file uploads.

        Returns:
            None.
        """

        self.upload_root = upload_root
        self.upload_root.mkdir(parents=True, exist_ok=True)

    def save_glucose_image(self, log_date: str, filename: str, content: bytes) -> StoredUpload:
        """Persist an uploaded glucose screenshot and return metadata.

        Parameters:
            log_date: Day key in ISO format (`YYYY-MM-DD`).
            filename: Client-provided filename.
            content: Raw image bytes.

        Returns:
            StoredUpload: Metadata for persisted file.

        Raises:
            ValueError: If filename is blank or resolves to an invalid value.

        Example:
            >>> storage = LocalUploadStorage(Path("uploads"))
            >>> result = storage.save_glucose_image("2026-01-01", "chart.png", b"123")
            >>> result.size_bytes
            3
        """

        clean_name = _sanitize_filename(filename)
        if not clean_name:
            raise ValueError("Filename is required for upload storage.")

        date_folder = self.upload_root / log_date
        date_folder.mkdir(parents=True, exist_ok=True)

        unique_name = f"{uuid4().hex[:12]}-{clean_name}"
        absolute_path = date_folder / unique_name
        absolute_path.write_bytes(content)

        relative_path = str(absolute_path.relative_to(self.upload_root))
        return StoredUpload(
            relative_path=relative_path,
            absolute_path=absolute_path,
            size_bytes=len(content),
        )


def _sanitize_filename(filename: str) -> str:
    """Return a safe filename without path traversal or odd characters.

    Parameters:
        filename: Raw filename from upload metadata.

    Returns:
        str: Sanitized filename.

    Example:
        >>> _sanitize_filename("../chart 1.png")
        'chart_1.png'
    """

    basename = Path(filename).name.strip()
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", basename)
    return cleaned.strip("._")
