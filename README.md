# docbrief

Convert a folder of raw documents into an AI-optimized briefing packet for use with Claude, Gemini, and NotebookLM.

## Supported formats

`.txt` `.md` `.pdf` `.docx` `.csv`

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
docbrief --input ./docs --output brief.md
docbrief --input ./docs --output brief.md --recursive --overwrite
```

### Options

| Flag | Default | Description |
|---|---|---|
| `--input / -i` | required | Directory containing source documents |
| `--output / -o` | required | Output file path |
| `--recursive / -r` | off | Walk subdirectories |
| `--overwrite` | off | Overwrite output if it exists |
| `--char-limit` | 50000 | Max characters retained per document |

## Development

```bash
pytest tests/
```

## Project structure

```
docbrief/
├── docbrief/
│   ├── __init__.py
│   ├── cli.py        # entry point, arg parsing
│   ├── reader.py     # per-format file reading
│   ├── processor.py  # normalization, cleaning, truncation
│   └── writer.py     # output assembly and file writing
├── tests/
│   └── test_reader.py
├── pyproject.toml
└── README.md
```
