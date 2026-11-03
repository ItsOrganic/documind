import pytest

from documind.ingestion.errors import ExtractionError
from documind.ingestion.extractors.text import TextExtractor


def test_splits_on_blank_lines(tmp_path):
    f = tmp_path / "a.txt"
    f.write_bytes(b"First para\nstill first.\n\n  \t\nSecond para.\n\n\nThird.\n\n\n")

    blocks = TextExtractor().extract(f)

    assert [b.text for b in blocks] == ["First para\nstill first.", "Second para.", "Third."]
    assert all(b.page is None and b.heading_path == [] for b in blocks)


def test_windows_and_old_mac_line_endings(tmp_path):
    f = tmp_path / "a.txt"
    f.write_bytes(b"One\r\n\r\nTwo\r\rThree")

    assert [b.text for b in TextExtractor().extract(f)] == ["One", "Two", "Three"]


def test_strips_bom(tmp_path):
    f = tmp_path / "bom.txt"
    f.write_bytes("﻿Hello".encode())

    assert TextExtractor().extract(f)[0].text == "Hello"


def test_invalid_utf8_raises(tmp_path):
    f = tmp_path / "bad.txt"
    f.write_bytes(b"ok\n\n\xff\xfe")

    with pytest.raises(ExtractionError, match="not valid UTF-8"):
        TextExtractor().extract(f)


def test_empty_file_raises(tmp_path):
    f = tmp_path / "empty.txt"
    f.write_text("  \n\n  ")

    with pytest.raises(ExtractionError):
        TextExtractor().extract(f)
