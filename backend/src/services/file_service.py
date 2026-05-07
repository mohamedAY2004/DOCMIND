"""Centralized file-policy helpers (spec §7.2, §8.2.1).

Single source of truth for:
- size formatting (``pretty_size``)
- date formatting (``pretty_date``)
- initials derivation (``initials_of``)
- MIME / extension validation for material and document uploads
- path sanitization
- subject / conversation upload directories
"""
from __future__ import annotations

import os
import re
import string
import random
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

from fastapi import UploadFile, status

from helpers.config import get_settings
from helpers.errors import APIError, ErrorCode

MATERIAL_ALLOWED_MIME = {
    "application/pdf",
}
MATERIAL_ALLOWED_EXT = {".pdf"}

DOC_ALLOWED_MIME = {
    "application/pdf",
}
DOC_ALLOWED_EXT = {".pdf"}

_FILENAME_SAFE_RE = re.compile(r"[^\w.\- ]")


def pretty_size(size_bytes: int) -> str:
    """Return a human-friendly file size, e.g. ``"2.4 MB"`` (spec §7.1)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    units = ["KB", "MB", "GB", "TB"]
    scaled = float(size_bytes) / 1024.0
    for unit in units:
        if scaled < 1024 or unit == units[-1]:
            if scaled >= 100:
                return f"{scaled:.0f} {unit}"
            if scaled >= 10:
                return f"{scaled:.1f} {unit}"
            return f"{scaled:.2f} {unit}"
        scaled /= 1024.0
    return f"{size_bytes} B"


def pretty_date(value: datetime | date) -> str:
    """Spec §7.1 sample: ``"Jan 15, 2025"``."""
    if isinstance(value, datetime):
        value = value.date()
    return value.strftime("%b %d, %Y")


def initials_of(name: str) -> str:
    """First + last initial, uppercased. Falls back to first letter."""
    parts = [p for p in re.split(r"\s+", name.strip()) if p]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0][:1].upper()
    return (parts[0][:1] + parts[-1][:1]).upper()


def clean_filename(name: str) -> str:
    name = name.strip().replace(" ", "_")
    return _FILENAME_SAFE_RE.sub("", name)[:255]


def random_suffix(length: int = 12) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def ext_of(name: str) -> str:
    return Path(name).suffix.lower()


def validate_material_upload(file: UploadFile) -> None:
    """Raise :class:`APIError` if ``file`` fails spec §7.2."""
    _validate_upload(
        file,
        allowed_mime=MATERIAL_ALLOWED_MIME,
        allowed_ext=MATERIAL_ALLOWED_EXT,
        max_bytes=get_settings().UPLOAD_MATERIAL_MAX_MB * 1024 * 1024,
    )


def validate_doc_upload(file: UploadFile) -> None:
    """Raise :class:`APIError` if ``file`` fails spec §8.2.1."""
    _validate_upload(
        file,
        allowed_mime=DOC_ALLOWED_MIME,
        allowed_ext=DOC_ALLOWED_EXT,
        max_bytes=get_settings().UPLOAD_DOC_MAX_MB * 1024 * 1024,
    )


def _validate_upload(
    file: UploadFile,
    *,
    allowed_mime: Iterable[str],
    allowed_ext: Iterable[str],
    max_bytes: int,
) -> None:
    name = file.filename or ""
    if not name or len(name) > 255:
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            status.HTTP_400_BAD_REQUEST,
            "Invalid filename.",
        )
    ext = ext_of(name)
    mime = (file.content_type or "").lower()
    if ext not in allowed_ext or mime not in allowed_mime:
        raise APIError(
            ErrorCode.UNSUPPORTED_MEDIA_TYPE,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"File type {mime or ext} is not allowed.",
        )
    size = getattr(file, "size", None)
    if size is not None and size > max_bytes:
        raise APIError(
            ErrorCode.FILE_TOO_LARGE,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            "File exceeds the maximum allowed size.",
        )
    if size == 0:
        raise APIError(
            ErrorCode.UNPROCESSABLE,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "File is empty.",
        )


def materials_dir(subject_id: str) -> Path:
    base = Path(get_settings().__dict__.get("FILES_DIR") or _default_files_dir())
    path = base / "materials" / subject_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def doc_files_dir(conversation_id: str) -> Path:
    base = Path(get_settings().__dict__.get("FILES_DIR") or _default_files_dir())
    path = base / "doc_chats" / conversation_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _default_files_dir() -> str:
    # Same layout the legacy code uses: src/assets/files/*.
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "assets",
        "files",
    )
