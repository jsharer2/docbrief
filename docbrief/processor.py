"""
processor.py - Text normalization and per-document preparation.

Takes raw extracted text from reader.py and returns a cleaned, bounded string
with a document header/footer, ready for assembly by writer.py.
"""

from pathlib import Path

DEFAULT_CHAR_LIMIT = 50_000


def process(text: str, source_path: Path, char_limit: int = DEFAULT_CHAR_LIMIT) -> str:
    """Normalize and bound a single document's text.

    Steps:
    1. Strip trailing whitespace from each line.
    2. Collapse runs of more than two consecutive blank lines down to two.
    3. Truncate to char_limit with a visible notice if the document exceeds it.
    4. Wrap in a document header/footer using the source filename.

    Returns the processed string ready for concatenation into the briefing packet.
    """
    # Step 1 & 2: per-line cleanup and blank-line collapsing.
    lines = text.splitlines()
    cleaned: list[str] = []
    consecutive_blanks = 0
    for line in lines:
        stripped = line.rstrip()
        if stripped == "":
            consecutive_blanks += 1
            if consecutive_blanks <= 2:
                cleaned.append("")
        else:
            consecutive_blanks = 0
            cleaned.append(stripped)

    body = "\n".join(cleaned).strip()

    # Step 3: truncation.
    truncated = False
    if len(body) > char_limit:
        body = body[:char_limit]
        truncated = True

    # Step 4: header/footer.
    name = source_path.name
    header = f"--- BEGIN: {name} ---"
    footer = f"--- END: {name} ---"
    if truncated:
        notice = f"[TRUNCATED: document exceeded {char_limit:,} character limit]"
        footer = f"{notice}\n{footer}"

    return f"{header}\n\n{body}\n\n{footer}"
