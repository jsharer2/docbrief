"""
reader.py - Per-format file reading.

Each public function accepts a file path and returns extracted plain text as a
string. On unrecoverable failure, raises ValueError so the caller can record
the error and continue. NotImplementedError is never raised in this module.
"""

import csv
import sys
import warnings
from pathlib import Path


SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".csv"}


def read_file(path: Path) -> str:
    """Dispatch to the appropriate reader based on file extension.

    Raises ValueError for unsupported extensions or unrecoverable parse errors.
    """
    ext = path.suffix.lower()
    if ext in (".txt", ".md"):
        return read_text(path)
    elif ext == ".pdf":
        return read_pdf(path)
    elif ext == ".docx":
        return read_docx(path)
    elif ext == ".csv":
        return read_csv(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def read_text(path: Path) -> str:
    """Read a plain text or Markdown file.

    Tries UTF-8 first; falls back to latin-1 on decode error and emits a
    warning to stderr.
    """
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        warnings.warn(
            f"{path.name}: UTF-8 decode failed, retrying with latin-1",
            stacklevel=2,
        )
        return path.read_text(encoding="latin-1")


def read_pdf(path: Path) -> str:
    """Extract text from a PDF using pymupdf (fitz).

    Raises ValueError for password-protected or corrupt files.
    """
    try:
        import fitz  # pymupdf
    except ImportError as exc:
        raise ValueError("pymupdf is not installed — run: pip install pymupdf") from exc

    try:
        doc = fitz.open(str(path))
    except Exception as exc:
        raise ValueError(f"Cannot open PDF: {exc}") from exc

    if doc.is_encrypted:
        raise ValueError("PDF is password-protected and cannot be read")

    pages: list[str] = []
    for page in doc:
        text = page.get_text()
        if text.strip():
            pages.append(text)

    doc.close()
    return "\n\n".join(pages)


def read_docx(path: Path) -> str:
    """Extract paragraph text from a .docx file using python-docx.

    Raises ValueError for corrupt or unreadable files.
    """
    try:
        from docx import Document
    except ImportError as exc:
        raise ValueError("python-docx is not installed — run: pip install python-docx") from exc

    try:
        doc = Document(str(path))
    except Exception as exc:
        raise ValueError(f"Cannot open DOCX: {exc}") from exc

    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def read_csv(path: Path) -> str:
    """Render a CSV file as a pipe-delimited plain-text table.

    Tries UTF-8, falls back to latin-1. Returns an empty string for empty files.
    """
    def _load(encoding: str) -> list[list[str]]:
        with open(path, newline="", encoding=encoding) as f:
            return list(csv.reader(f))

    try:
        rows = _load("utf-8")
    except UnicodeDecodeError:
        warnings.warn(
            f"{path.name}: UTF-8 decode failed, retrying with latin-1",
            stacklevel=2,
        )
        rows = _load("latin-1")

    if not rows:
        return ""

    lines = [" | ".join(cell.strip() for cell in row) for row in rows]

    # Insert a separator line after the header row if there are multiple rows.
    if len(lines) > 1:
        header_width = len(lines[0])
        lines.insert(1, "-" * header_width)

    return "\n".join(lines)
