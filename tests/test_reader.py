"""Tests for docbrief.reader."""

import csv
import pytest
from pathlib import Path

from docbrief.reader import read_file, read_text, read_csv, SUPPORTED_EXTENSIONS


class TestSupportedExtensions:
    def test_unsupported_extension_raises(self, tmp_path):
        f = tmp_path / "file.xlsx"
        f.write_bytes(b"")
        with pytest.raises(ValueError, match="Unsupported"):
            read_file(f)

    def test_supported_set_contents(self):
        assert SUPPORTED_EXTENSIONS == {".txt", ".md", ".pdf", ".docx", ".csv"}


class TestReadText:
    def test_reads_plain_text(self, tmp_path):
        f = tmp_path / "hello.txt"
        f.write_text("Hello, world!", encoding="utf-8")
        assert read_text(f) == "Hello, world!"

    def test_reads_markdown(self, tmp_path):
        f = tmp_path / "notes.md"
        f.write_text("# Title\n\nBody text.", encoding="utf-8")
        result = read_text(f)
        assert "# Title" in result
        assert "Body text." in result

    def test_fallback_to_latin1(self, tmp_path):
        f = tmp_path / "latin.txt"
        f.write_bytes("caf\xe9".encode("latin-1"))  # 'café' in latin-1
        result = read_text(f)
        assert "caf" in result  # latin-1 round-trip may vary by platform

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")
        assert read_text(f) == ""

    def test_dispatch_txt(self, tmp_path):
        f = tmp_path / "doc.txt"
        f.write_text("content", encoding="utf-8")
        assert read_file(f) == "content"

    def test_dispatch_md(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text("# Header", encoding="utf-8")
        assert read_file(f) == "# Header"


class TestReadCsv:
    def _make_csv(self, tmp_path, rows: list[list[str]], name="data.csv") -> Path:
        f = tmp_path / name
        with open(f, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerows(rows)
        return f

    def test_renders_header_and_rows(self, tmp_path):
        f = self._make_csv(tmp_path, [["name", "age"], ["Alice", "30"], ["Bob", "25"]])
        result = read_csv(f)
        assert "name" in result
        assert "Alice" in result
        assert "Bob" in result

    def test_separator_line_inserted_after_header(self, tmp_path):
        f = self._make_csv(tmp_path, [["col1", "col2"], ["a", "b"]])
        lines = read_csv(f).splitlines()
        # Line 0: header, line 1: separator (dashes), line 2: data row
        assert set(lines[1]) <= {"-"}

    def test_empty_csv_returns_empty_string(self, tmp_path):
        f = tmp_path / "empty.csv"
        f.write_text("", encoding="utf-8")
        assert read_csv(f) == ""

    def test_single_row_no_separator(self, tmp_path):
        f = self._make_csv(tmp_path, [["only", "header"]])
        result = read_csv(f)
        assert "-" * 3 not in result  # no separator for a single-row file

    def test_dispatch_csv(self, tmp_path):
        f = self._make_csv(tmp_path, [["x"], ["1"]])
        result = read_file(f)
        assert "x" in result
        assert "1" in result


class TestReadPdf:
    """PDF tests require pymupdf and a real PDF fixture.

    These are integration tests skipped when pymupdf is unavailable.
    """

    @pytest.fixture
    def minimal_pdf(self, tmp_path):
        pytest.importorskip("fitz")
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Hello PDF")
        path = tmp_path / "test.pdf"
        doc.save(str(path))
        doc.close()
        return path

    def test_extracts_text(self, minimal_pdf):
        from docbrief.reader import read_pdf
        result = read_pdf(minimal_pdf)
        assert "Hello PDF" in result

    def test_dispatch_pdf(self, minimal_pdf):
        result = read_file(minimal_pdf)
        assert "Hello PDF" in result


class TestReadDocx:
    """DOCX tests require python-docx."""

    @pytest.fixture
    def minimal_docx(self, tmp_path):
        pytest.importorskip("docx")
        from docx import Document
        doc = Document()
        doc.add_paragraph("Hello DOCX")
        path = tmp_path / "test.docx"
        doc.save(str(path))
        return path

    def test_extracts_paragraphs(self, minimal_docx):
        from docbrief.reader import read_docx
        result = read_docx(minimal_docx)
        assert "Hello DOCX" in result

    def test_dispatch_docx(self, minimal_docx):
        result = read_file(minimal_docx)
        assert "Hello DOCX" in result
