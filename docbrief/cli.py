"""
cli.py - Command-line entry point for docbrief.

Usage:
    docbrief --input <dir> --output <dir> [options]

Output directory will contain:
    brief.txt     assembled briefing packet  (requires --extract-text)
    summary.json  run metadata and per-file status
    sources.csv   tabular per-file extraction results
"""

import argparse
import sys
from pathlib import Path

from docbrief.processor import DEFAULT_CHAR_LIMIT, process
from docbrief.reader import SUPPORTED_EXTENSIONS, read_file
from docbrief.writer import (
    DocResult,
    assemble,
    write_output,
    write_sources_csv,
    write_summary,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="docbrief",
        description="Convert a folder of documents into an AI-optimized briefing packet.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        metavar="DIR",
        help="Directory containing source documents (scanned recursively).",
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        metavar="DIR",
        help="Output directory for brief.txt, summary.json, and sources.csv.",
    )
    parser.add_argument(
        "--extract-text",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Write the assembled brief.txt to the output directory.",
    )
    parser.add_argument(
        "--max-chars-per-doc",
        type=int,
        default=DEFAULT_CHAR_LIMIT,
        metavar="N",
        help="Maximum characters to retain per document before truncating.",
    )
    parser.add_argument(
        "--tag",
        default="",
        metavar="LABEL",
        help="Optional label embedded in the packet header and summary.json.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing output files without prompting.",
    )
    return parser


def scan_files(input_dir: Path) -> list[Path]:
    """Recursively collect all files with supported extensions."""
    found = []
    for path in sorted(input_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            found.append(path)
    return found


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_dir = Path(args.input).resolve()
    output_dir = Path(args.output).resolve()

    # --- Validate input ---
    if not input_dir.is_dir():
        print(f"Error: input path '{input_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    files = scan_files(input_dir)
    if not files:
        print(
            f"Error: no supported files found in '{input_dir}'.\n"
            f"Supported extensions: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
            file=sys.stderr,
        )
        sys.exit(1)

    # --- Prepare output directory ---
    output_dir.mkdir(parents=True, exist_ok=True)

    brief_path = output_dir / "brief.txt"
    summary_path = output_dir / "summary.json"
    sources_path = output_dir / "sources.csv"

    if args.extract_text and brief_path.exists() and not args.overwrite:
        print(
            f"Error: '{brief_path}' already exists. Use --overwrite to replace it.",
            file=sys.stderr,
        )
        sys.exit(1)

    # --- Process each file ---
    results: list[DocResult] = []
    processed_blocks: list[str] = []

    print(f"Scanning {len(files)} file(s) in '{input_dir}' ...")

    for path in files:
        rel = str(path.relative_to(input_dir))
        ext = path.suffix.lower()

        try:
            raw = read_file(path)
            block = process(raw, path, char_limit=args.max_chars_per_doc)
            processed_blocks.append(block)
            results.append(DocResult(
                path=rel,
                filename=path.name,
                extension=ext,
                status="ok",
                char_count=len(raw),
                error="",
            ))
            print(f"  [ok]      {rel}  ({len(raw):,} chars)")

        except NotImplementedError:
            results.append(DocResult(
                path=rel,
                filename=path.name,
                extension=ext,
                status="skipped",
                char_count=0,
                error="extraction not yet implemented for this format",
            ))
            print(f"  [skipped] {rel}")

        except Exception as exc:
            results.append(DocResult(
                path=rel,
                filename=path.name,
                extension=ext,
                status="error",
                char_count=0,
                error=str(exc),
            ))
            print(f"  [error]   {rel}  — {exc}")

    # --- Write outputs ---
    if args.extract_text:
        if processed_blocks:
            content = assemble(processed_blocks, tag=args.tag)
            write_output(content, brief_path, overwrite=args.overwrite)
            print(f"\nBrief written   : {brief_path}")
        else:
            print("\nNo text was extracted — brief.txt not written.", file=sys.stderr)

    write_summary(results, summary_path, tag=args.tag, input_dir=input_dir)
    write_sources_csv(results, sources_path)

    print(f"Summary written : {summary_path}")
    print(f"Sources written : {sources_path}")

    # --- Final summary line ---
    ok_count = sum(1 for r in results if r.status == "ok")
    skipped_count = sum(1 for r in results if r.status == "skipped")
    error_count = sum(1 for r in results if r.status == "error")
    total_chars = sum(r.char_count for r in results if r.status == "ok")

    print(
        f"\nDone. processed={ok_count}  skipped={skipped_count}  "
        f"errors={error_count}  total_chars={total_chars:,}"
    )

    if error_count > 0:
        sys.exit(2)  # partial failure — outputs were still written


if __name__ == "__main__":
    main()
