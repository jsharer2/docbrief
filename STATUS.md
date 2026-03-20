# docbrief — Project Status

_Last updated: 2026-03-19_

---

## Purpose

`docbrief` is a Python CLI tool that recursively scans a folder of raw documents
and produces an AI-optimized briefing packet for use with Claude, Gemini, and
NotebookLM. It extracts plain text from mixed-format document sets and writes a
single consolidated text file plus structured metadata.

---

## Current Milestone

**MVP slice complete.** The tool can be installed, run against a real document
folder, and will produce all three output artifacts. All five target formats are
handled. The core pipeline is wired end-to-end.

---

## Architecture

```
docbrief/
├── docbrief/
│   ├── __init__.py       version string only
│   ├── cli.py            entry point, arg parsing, scan+process pipeline
│   ├── reader.py         per-format extraction (txt/md/csv/pdf/docx)
│   ├── processor.py      normalization, truncation, header/footer wrapping
│   └── writer.py         DocResult dataclass, assembly, all three output writers
├── tests/
│   ├── __init__.py
│   ├── test_reader.py    unit tests for all five format readers
│   ├── test_processor.py unit tests for normalization and truncation
│   └── test_writer.py    unit tests for assembly and all three writers
├── pyproject.toml        setuptools, entry point, deps
├── README.md             usage docs and structure overview
└── .gitignore
```

**Data flow:**

```
scan_files() → read_file() → process() → assemble() → write_output()
                                       ↘ write_summary() + write_sources_csv()
```

**Output directory** (set via `--output`):
- `brief.txt` — assembled briefing packet (written when `--extract-text` is on)
- `summary.json` — run metadata and per-file status counts
- `sources.csv` — one row per file: path, status, char_count, error

---

## Implemented

- **CLI** (`cli.py`)
  - All five flags: `--input`, `--output`, `--extract-text` / `--no-extract-text`,
    `--max-chars-per-doc`, `--tag`, `--overwrite`
  - Recursive directory scan via `rglob`
  - Per-file progress lines (`[ok]` / `[skipped]` / `[error]`)
  - Final summary line with counts and total char count
  - Exit code 0 on full success, 2 on partial failure (outputs still written)
  - Input validation: non-existent directory, empty scan result

- **Reader** (`reader.py`)
  - `.txt` / `.md` — UTF-8 with latin-1 fallback and warning
  - `.csv` — pipe-delimited plain-text table, header separator line, encoding fallback
  - `.pdf` — `pymupdf` (fitz): page-by-page extraction, encrypted file detection,
    graceful error on corrupt files, missing-dependency message
  - `.docx` — `python-docx`: paragraph extraction, graceful error on corrupt files,
    missing-dependency message

- **Processor** (`processor.py`)
  - Per-line trailing whitespace strip
  - Collapse runs of 3+ blank lines to 2
  - Character-level truncation with visible `[TRUNCATED: ...]` notice
  - `--- BEGIN: filename ---` / `--- END: filename ---` wrapping

- **Writer** (`writer.py`)
  - `DocResult` dataclass (path, filename, extension, status, char_count, error)
  - `assemble()` — packet header (tag, timestamp, doc count) + `===` separators
  - `write_output()` — `FileExistsError` guard, parent dir creation
  - `write_summary()` — structured JSON with counts and full file list
  - `write_sources_csv()` — standard CSV via `DictWriter`

- **Tests**
  - `test_reader.py` — 13 tests across all five formats; PDF/DOCX tests use
    `pytest.importorskip` so they skip cleanly when deps are absent
  - `test_processor.py` — 8 tests covering headers, whitespace, truncation, empty input
  - `test_writer.py` — 13 tests covering assemble, write_output, summary, sources CSV
  - No end-to-end / CLI integration test yet

- **Packaging** — `pyproject.toml` with correct build backend, entry point wired

---

## Partially Implemented

- **DOCX extraction** — paragraphs only; tables, headers, footers, and text boxes
  in the DOCX body are not extracted. Most real-world DOCX files will still produce
  useful output, but documents that rely heavily on tables will be incomplete.
  _(inferred: no explicit skip logic for tables, just not implemented)_

- **PDF extraction** — text-layer only. Image-only (scanned) PDFs will silently
  return an empty string and be recorded as `status=ok` with `char_count=0` rather
  than `status=skipped` or a warning. No OCR.

- **Overwrite guard** — the `--overwrite` flag is checked for `brief.txt` in the
  CLI, but `summary.json` and `sources.csv` are always silently overwritten
  regardless of the flag.

---

## Not Yet Implemented

- Token counting (relevant for Claude/Gemini context window planning)
- Markdown formatting of the output brief (currently plain text only)
- Configurable output filename for the brief (hardcoded to `brief.txt`)
- Filtering by file extension or filename pattern
- End-to-end CLI integration tests (`test_cli.py`)
- A `--version` flag
- Any form of config file (`.docbriefrc` or similar)

---

## Technical Debt and Risks

| Item | Severity | Notes |
|---|---|---|
| `import sys` in `reader.py` is unused | Low | Dead import, no effect |
| `summary.json` / `sources.csv` always overwrite | Medium | Inconsistent with --overwrite behavior on `brief.txt` |
| Scanned PDFs silently produce empty-string output | Medium | Recorded as `ok` with 0 chars; misleading in sources.csv |
| DOCX tables not extracted | Medium | Silent data loss for table-heavy documents |
| CSV separator width based on header row only | Low | Separator can be shorter than wide data rows |
| No end-to-end test | Medium | Full pipeline correctness is untested against real files |
| Dependencies not pinned | Low | `pymupdf>=1.23` and `python-docx>=1.1` leave upper bounds open |
