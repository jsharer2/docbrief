"""Tests for docbrief.writer."""

import csv
import json
from pathlib import Path

import pytest

from docbrief.writer import (
    DocResult,
    assemble,
    write_output,
    write_sources_csv,
    write_summary,
)


def make_result(status="ok", char_count=100, error="") -> DocResult:
    return DocResult(
        path="subdir/file.txt",
        filename="file.txt",
        extension=".txt",
        status=status,
        char_count=char_count,
        error=error,
    )


class TestAssemble:
    def test_single_document(self):
        result = assemble(["doc text"])
        assert "doc text" in result

    def test_multiple_documents_separated(self):
        result = assemble(["doc one", "doc two"])
        assert "doc one" in result
        assert "doc two" in result
        assert "=" * 10 in result  # separator present

    def test_packet_header_present(self):
        result = assemble(["anything"])
        assert "DOCBRIEF" in result

    def test_tag_in_header_when_provided(self):
        result = assemble(["x"], tag="my-project")
        assert "my-project" in result

    def test_no_tag_line_when_empty(self):
        result = assemble(["x"], tag="")
        assert "Tag" not in result

    def test_document_count_in_header(self):
        result = assemble(["a", "b", "c"])
        assert "3" in result


class TestWriteOutput:
    def test_writes_content(self, tmp_path):
        p = tmp_path / "brief.txt"
        write_output("hello", p)
        assert p.read_text() == "hello"

    def test_raises_if_exists_without_overwrite(self, tmp_path):
        p = tmp_path / "brief.txt"
        p.write_text("old")
        with pytest.raises(FileExistsError):
            write_output("new", p, overwrite=False)

    def test_overwrites_when_flag_set(self, tmp_path):
        p = tmp_path / "brief.txt"
        p.write_text("old")
        write_output("new", p, overwrite=True)
        assert p.read_text() == "new"

    def test_creates_parent_dirs(self, tmp_path):
        p = tmp_path / "a" / "b" / "brief.txt"
        write_output("content", p)
        assert p.exists()


class TestWriteSummary:
    def test_writes_valid_json(self, tmp_path):
        p = tmp_path / "summary.json"
        write_summary([make_result()], p, tag="test", input_dir=tmp_path)
        data = json.loads(p.read_text())
        assert isinstance(data, dict)

    def test_summary_counts(self, tmp_path):
        p = tmp_path / "summary.json"
        results = [
            make_result(status="ok", char_count=50),
            make_result(status="error", char_count=0, error="boom"),
            make_result(status="skipped", char_count=0),
        ]
        write_summary(results, p, tag="", input_dir=tmp_path)
        data = json.loads(p.read_text())
        assert data["files_ok"] == 1
        assert data["files_error"] == 1
        assert data["files_skipped"] == 1
        assert data["total_chars_extracted"] == 50

    def test_tag_in_summary(self, tmp_path):
        p = tmp_path / "summary.json"
        write_summary([], p, tag="my-tag", input_dir=tmp_path)
        data = json.loads(p.read_text())
        assert data["tag"] == "my-tag"

    def test_files_list_matches_results(self, tmp_path):
        p = tmp_path / "summary.json"
        write_summary([make_result(), make_result()], p, tag="", input_dir=tmp_path)
        data = json.loads(p.read_text())
        assert len(data["files"]) == 2


class TestWriteSourcesCsv:
    def test_writes_csv_with_header(self, tmp_path):
        p = tmp_path / "sources.csv"
        write_sources_csv([make_result()], p)
        rows = list(csv.DictReader(p.read_text().splitlines()))
        assert len(rows) == 1
        assert rows[0]["status"] == "ok"
        assert rows[0]["filename"] == "file.txt"

    def test_error_row_preserved(self, tmp_path):
        p = tmp_path / "sources.csv"
        write_sources_csv([make_result(status="error", error="bad file")], p)
        rows = list(csv.DictReader(p.read_text().splitlines()))
        assert rows[0]["error"] == "bad file"
