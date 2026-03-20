"""Tests for docbrief.processor."""

from pathlib import Path

from docbrief.processor import process, DEFAULT_CHAR_LIMIT


FAKE_PATH = Path("docs/sample.txt")


class TestProcessHeaders:
    def test_header_and_footer_present(self):
        result = process("Hello", FAKE_PATH)
        assert "--- BEGIN: sample.txt ---" in result
        assert "--- END: sample.txt ---" in result

    def test_body_between_header_and_footer(self):
        result = process("body text", FAKE_PATH)
        begin = result.index("--- BEGIN:")
        end = result.index("--- END:")
        assert begin < end
        assert "body text" in result[begin:end]


class TestProcessWhitespace:
    def test_strips_trailing_spaces(self):
        result = process("line one   \nline two  ", FAKE_PATH)
        for line in result.splitlines():
            assert line == line.rstrip()

    def test_collapses_excess_blank_lines(self):
        text = "a\n\n\n\n\nb"
        result = process(text, FAKE_PATH)
        # Should never have more than 2 consecutive blank lines
        assert "\n\n\n\n" not in result

    def test_preserves_up_to_two_blank_lines(self):
        text = "a\n\n\nb"  # 2 blank lines
        result = process(text, FAKE_PATH)
        assert "a\n\n\nb" in result


class TestProcessTruncation:
    def test_truncates_long_document(self):
        long_text = "x" * 200
        result = process(long_text, FAKE_PATH, char_limit=100)
        assert "TRUNCATED" in result
        assert "x" * 101 not in result

    def test_no_truncation_notice_when_within_limit(self):
        result = process("short", FAKE_PATH, char_limit=100)
        assert "TRUNCATED" not in result

    def test_truncation_notice_mentions_limit(self):
        result = process("y" * 200, FAKE_PATH, char_limit=50)
        assert "50" in result


class TestProcessEmpty:
    def test_empty_string(self):
        result = process("", FAKE_PATH)
        assert "--- BEGIN: sample.txt ---" in result
        assert "--- END: sample.txt ---" in result
