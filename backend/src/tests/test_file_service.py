"""Unit tests for file_service formatting helpers (no DB required)."""
from __future__ import annotations

from datetime import datetime

from services.file_service import (
    clean_filename,
    ext_of,
    initials_of,
    pretty_date,
    pretty_size,
)


def test_pretty_size_handles_every_boundary() -> None:
    assert pretty_size(0) == "0 B"
    assert pretty_size(1023) == "1023 B"
    assert pretty_size(1024).endswith(" KB")
    assert pretty_size(1_500_000).endswith(" MB")
    assert pretty_size(2 * 1024**3).endswith(" GB")


def test_initials_of_mixed_inputs() -> None:
    assert initials_of("") == ""
    assert initials_of("Alice") == "A"
    assert initials_of("alice smith") == "AS"
    assert initials_of("  alice   jones-doe  ") == "AJ"


def test_pretty_date_format() -> None:
    assert pretty_date(datetime(2025, 1, 15)) == "Jan 15, 2025"


def test_clean_filename_is_defensive() -> None:
    assert clean_filename("my file.pdf") == "my_file.pdf"
    assert clean_filename("../etc/passwd") == "..etcpasswd"


def test_ext_of_is_lowercased() -> None:
    assert ext_of("slides.PDF") == ".pdf"
    assert ext_of("deck.PPTX") == ".pptx"
