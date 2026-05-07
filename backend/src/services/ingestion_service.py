"""Parse uploaded files into text chunks.

Supports PDF (via PyMuPDF), PPTX (via python-pptx), PNG (OCR not yet
implemented — returns a descriptive stub), and plain text / markdown files.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

logger = logging.getLogger("docmind.ingestion")


@dataclass
class IngestedChunk:
    text: str
    metadata: dict


def _clean(text: str) -> str:
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"-\n(\w)", r"\1", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def _split(text: str, chunk_size: int = 800, overlap: int = 120) -> List[str]:
    """Simple char-based splitter with overlap. No external dependency."""
    if not text:
        return []
    chunks: List[str] = []
    start = 0
    length = len(text)
    step = max(1, chunk_size - overlap)
    while start < length:
        end = min(start + chunk_size, length)
        chunks.append(text[start:end])
        if end >= length:
            break
        start += step
    return chunks


def ingest_pdf(path: Path) -> List[IngestedChunk]:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.error("PyMuPDF not installed; cannot ingest PDF.")
        return []

    chunks: List[IngestedChunk] = []
    with fitz.open(str(path)) as doc:
        for page_idx, page in enumerate(doc):
            raw = page.get_text("text")
            cleaned = _clean(raw)
            for i, piece in enumerate(_split(cleaned)):
                chunks.append(
                    IngestedChunk(
                        text=piece,
                        metadata={
                            "source": path.name,
                            "page": page_idx + 1,
                            "part": i,
                        },
                    )
                )
    return chunks


def ingest_pptx(path: Path) -> List[IngestedChunk]:
    try:
        from pptx import Presentation
    except ImportError:
        logger.error("python-pptx not installed; cannot ingest PPTX.")
        return []

    chunks: List[IngestedChunk] = []
    prs = Presentation(str(path))
    for slide_idx, slide in enumerate(prs.slides):
        buffer: List[str] = []
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text:
                buffer.append(shape.text)
        cleaned = _clean("\n".join(buffer))
        for i, piece in enumerate(_split(cleaned)):
            chunks.append(
                IngestedChunk(
                    text=piece,
                    metadata={
                        "source": path.name,
                        "slide": slide_idx + 1,
                        "part": i,
                    },
                )
            )
    return chunks


def ingest_png(path: Path) -> List[IngestedChunk]:
    """OCR hook. Deferred — returns a stub so the pipeline still completes."""
    logger.warning("PNG OCR is not implemented; returning placeholder chunk for %s", path)
    return [
        IngestedChunk(
            text=f"[Image upload: {path.name}. Visual content has not yet been transcribed.]",
            metadata={"source": path.name, "kind": "png_placeholder"},
        )
    ]


def ingest_file(path: Path) -> List[IngestedChunk]:
    """Dispatch based on extension."""
    ext = path.suffix.lower()
    if ext == ".pdf":
        return ingest_pdf(path)
    if ext == ".pptx":
        return ingest_pptx(path)
    if ext == ".png":
        return ingest_png(path)
    if ext in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="replace")
        return [
            IngestedChunk(text=piece, metadata={"source": path.name, "part": i})
            for i, piece in enumerate(_split(_clean(text)))
        ]
    logger.warning("Unsupported extension %s for %s", ext, path)
    return []


def detect_pdf_encrypted(path: Path) -> bool:
    """Return True only if the PDF is actually locked behind a user password.

    Many PDFs produced by Word, Google Docs, macOS Preview, and "print to PDF"
    pipelines carry an owner-permissions dictionary that ``pypdf`` reports as
    ``is_encrypted = True`` even though no password is required to read them.
    We attempt to authenticate with an empty password first and only treat the
    file as encrypted when that attempt fails.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        fitz = None

    if fitz is not None:
        try:
            with fitz.open(str(path)) as doc:
                if not doc.needs_pass:
                    return False
                return not doc.authenticate("")
        except Exception:
            return False

    try:
        from pypdf import PdfReader
    except ImportError:
        return False
    try:
        reader = PdfReader(str(path))
        if not reader.is_encrypted:
            return False
        try:
            result = reader.decrypt("")
        except Exception:
            return True
        return not bool(result)
    except Exception:
        return False
