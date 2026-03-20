# docbrief — Next Steps

_Last updated: 2026-03-19_

---

## Next Milestone: Hardening and Verified Output

The extraction pipeline is in place. The next milestone is to close the known
gaps in correctness, add an end-to-end test, and make the tool trustworthy on
real document folders before adding any new features.

---

## Task Sequence

### 1. Fix the overwrite inconsistency (small, ~15 min)

`summary.json` and `sources.csv` are always overwritten; `brief.txt` is not.
Either apply the `--overwrite` check to all three, or document that metadata
files are always refreshed (and remove the check from `brief.txt`).
Recommendation: always refresh all three — they are derived outputs, not user
files. Remove the `brief.txt` existence check from `cli.py` and rely solely on
`write_output(overwrite=...)`.

### 2. Fix silent empty output for scanned PDFs (~20 min)

In `reader.py`, after extracting all pages, check whether the joined result
is empty or all-whitespace. If so, raise `ValueError("PDF appears to be
image-only — no text layer found")` so the CLI records it as `status=error`
rather than `status=ok` with 0 chars.

### 3. Fix silent data loss for DOCX tables (~30 min)

In `read_docx()`, after paragraph extraction, also extract table cell text.
Iterate `doc.tables`, then each `table.rows`, then `cell.text`. Append the
collected table text below the paragraphs with a light separator. This keeps
the function simple while capturing the most common missing content.

### 4. Add an end-to-end CLI integration test (~45 min)

Create `tests/test_cli.py`. Use `pytest` with `tmp_path` to write a small set
of fixture files (one `.txt`, one `.csv`, one `.md`), call `main()` with
controlled `sys.argv`, and assert:
- `brief.txt` exists and contains the expected filenames
- `summary.json` is valid JSON with `files_ok == 3`
- `sources.csv` has 3 data rows
- exit code is 0

This is the most important gap — nothing currently tests the pipeline as a whole.

### 5. Remove the unused `import sys` from `reader.py` (trivial)

Dead import. Delete it.

### 6. Add `--version` flag to `cli.py` (~10 min)

```python
parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
```

---

## Suggested Testing Steps

After each task above, run:

```bash
pytest tests/ -v
```

After task 4 (integration test), do a manual smoke test against real files:

```bash
# Create a small test fixture folder
mkdir -p /tmp/doctest
echo "Hello from text" > /tmp/doctest/a.txt
echo "# Markdown doc" > /tmp/doctest/b.md
printf "name,age\nAlice,30\n" > /tmp/doctest/c.csv

docbrief --input /tmp/doctest --output /tmp/doctest-out --tag smoke-test

# Inspect outputs
cat /tmp/doctest-out/brief.txt
cat /tmp/doctest-out/summary.json
cat /tmp/doctest-out/sources.csv
```

Expected: 3 files processed, `files_ok: 3`, brief.txt contains all three document
blocks with `--- BEGIN/END ---` headers.

---

## Resume Instructions

```bash
cd ~/projects/docbrief
source .venv/bin/activate        # or: python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # install package + dev deps
pytest tests/ -v                 # confirm current test state
```

Key files to orient:
- `docbrief/cli.py` — the pipeline orchestrator; start here to understand flow
- `docbrief/reader.py` — one function per format; most fixes will land here
- `tests/test_reader.py` — existing format tests to extend
- `STATUS.md` — current implementation state

The tool is invoked as:
```bash
docbrief --input <dir> --output <dir> [--tag LABEL] [--max-chars-per-doc N]
```

---

## Known Blockers and Open Questions

| Item | Status | Notes |
|---|---|---|
| `pymupdf` / `python-docx` not yet installed in the venv | Unknown | Run `pip install -e ".[dev]"` to confirm; PDF and DOCX tests will skip cleanly if absent |
| No real-file smoke test has been run yet | Blocker | The pipeline is untested against actual documents; run one before marking MVP done |
| DOCX table extraction approach | Open | The simple cell-text approach covers most cases but drops table structure; acceptable for V1 |
| Token counting for AI context planning | Deferred | Not in scope until extraction is verified correct; easy to add with `tiktoken` or character-based estimation |
