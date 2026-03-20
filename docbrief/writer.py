"""
writer.py - Assemble and write the final briefing packet plus metadata outputs.

Produces three artifacts in the output directory:
  brief.txt     - the full assembled text (written only when extract_text=True)
  summary.json  - run metadata and per-file status
  sources.csv   - tabular per-file extraction results
"""

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


SEPARATOR = "\n\n" + "=" * 72 + "\n\n"


@dataclass
class DocResult:
    """Result record for a single processed file."""
    path: str        # relative path from input_dir
    filename: str
    extension: str
    status: str      # "ok" | "error" | "skipped"
    char_count: int  # raw chars extracted (0 on error/skipped)
    error: str       # error message, or "" on success


def assemble(documents: list[str], tag: str = "") -> str:
    """Join processed document strings into a single briefing packet string.

    Prepends a packet header with tag, timestamp, and document count.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header_lines = [
        "DOCBRIEF BRIEFING PACKET",
        f"Generated : {now}",
        f"Documents : {len(documents)}",
    ]
    if tag:
        header_lines.insert(1, f"Tag       : {tag}")

    packet_header = "\n".join(header_lines)
    parts = [packet_header] + documents
    return SEPARATOR.join(parts)


def write_output(content: str, output_path: Path, overwrite: bool = False) -> None:
    """Write the assembled briefing packet to output_path.

    Raises FileExistsError if the file already exists and overwrite is False.
    Creates parent directories as needed.
    """
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"Output file already exists: {output_path}  (use --overwrite to replace it)"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def write_summary(
    results: list[DocResult],
    output_path: Path,
    tag: str,
    input_dir: Path,
) -> None:
    """Write a summary.json describing the run and every file's outcome."""
    ok = [r for r in results if r.status == "ok"]
    skipped = [r for r in results if r.status == "skipped"]
    errors = [r for r in results if r.status == "error"]

    summary = {
        "tag": tag,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_dir": str(input_dir.resolve()),
        "total_files_found": len(results),
        "files_ok": len(ok),
        "files_skipped": len(skipped),
        "files_error": len(errors),
        "total_chars_extracted": sum(r.char_count for r in ok),
        "files": [asdict(r) for r in results],
    }

    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def write_sources_csv(results: list[DocResult], output_path: Path) -> None:
    """Write a sources.csv with one row per processed file."""
    fieldnames = ["path", "filename", "extension", "status", "char_count", "error"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))
