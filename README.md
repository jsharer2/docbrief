# docbrief

A Python CLI tool that recursively scans a folder of documents and produces
an AI-optimized briefing packet for use with Claude, Gemini, and NotebookLM.

> **Status: early development (MVP).** The core pipeline works end-to-end on
> `.txt`, `.md`, `.csv`, `.pdf`, and `.docx` files. See `STATUS.md` for a full
> account of what is and isn't implemented yet.

---

## What it does

Given an input directory, docbrief:

1. Scans recursively for supported document types
2. Extracts plain text from each file
3. Normalizes whitespace and applies a per-document character limit
4. Assembles all documents into a single annotated briefing packet
5. Writes three output files to an output directory:
   - `brief.txt` — the assembled text packet
   - `summary.json` — run metadata and per-file status
   - `sources.csv` — tabular extraction results

---

## Supported formats

| Format | Extension | Notes |
|---|---|---|
| Plain text | `.txt` | UTF-8 with latin-1 fallback |
| Markdown | `.md` | Treated as plain text; Markdown syntax is preserved |
| CSV | `.csv` | Rendered as a pipe-delimited plain-text table |
| PDF | `.pdf` | Text layer only — scanned/image PDFs will produce empty output |
| Word document | `.docx` | Paragraph text only — tables are not extracted yet |

---

## Installation

Requires Python 3.10+.

```bash
git clone <repo>
cd docbrief
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

---

## Usage

```bash
docbrief --input ./docs --output ./output
```

The output directory is created if it does not exist.

### Options

| Flag | Default | Description |
|---|---|---|
| `--input / -i` | required | Directory to scan (always recursive) |
| `--output / -o` | required | Directory for output files |
| `--extract-text` / `--no-extract-text` | on | Write `brief.txt` to the output directory |
| `--max-chars-per-doc N` | 50000 | Truncate each document at N characters |
| `--tag LABEL` | _(none)_ | Label embedded in the packet header and `summary.json` |
| `--overwrite` | off | Overwrite `brief.txt` if it already exists |

### Example

```bash
docbrief --input ./project-docs --output ./briefing --tag q1-review
```

Output:
```
Scanning 12 file(s) in '/path/to/project-docs' ...
  [ok]      contracts/agreement.pdf  (18,432 chars)
  [ok]      notes/meeting.md  (2,105 chars)
  [error]   archive/scan.pdf  — PDF appears to be image-only
  ...

Brief written   : /path/to/briefing/brief.txt
Summary written : /path/to/briefing/summary.json
Sources written : /path/to/briefing/sources.csv

Done. processed=11  skipped=0  errors=1  total_chars=94,210
```

Exit code is `0` on full success, `2` if any files produced errors (outputs are
still written).

---

## Development

```bash
pytest tests/ -v
```

Three test modules cover the reader, processor, and writer independently.
There is no end-to-end CLI integration test yet (see `NEXT-STEPS.md`).

---

## Project structure

```
docbrief/
├── docbrief/
│   ├── __init__.py       package and version
│   ├── cli.py            entry point, argument parsing, pipeline orchestration
│   ├── reader.py         per-format text extraction
│   ├── processor.py      whitespace normalization, truncation, header/footer wrapping
│   └── writer.py         DocResult dataclass, output assembly, JSON/CSV writers
├── tests/
│   ├── test_reader.py
│   ├── test_processor.py
│   └── test_writer.py
├── pyproject.toml
├── STATUS.md             current implementation state
├── NEXT-STEPS.md         next milestone and task breakdown
└── README.md
```

---

## Known limitations

- Scanned (image-only) PDFs have no text layer and will produce empty output.
- DOCX table content is not extracted — paragraphs only.
- `summary.json` and `sources.csv` are always overwritten on re-runs.
- No token counting for context-window planning.
