import pymupdf
import pytest

from documind.ingestion.errors import ExtractionError
from documind.ingestion.extractors.pdf import PdfExtractor


def make_pdf(path, pages: list[str], password: str | None = None) -> None:
    """Build a PDF with one page per string; an empty string makes a blank page."""
    doc = pymupdf.open()
    for text in pages:
        page = doc.new_page()
        if text:
            page.insert_text((72, 72), text)
    if password:
        doc.save(path, encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw=password, owner_pw=password)
    else:
        doc.save(path)


def test_one_block_per_page_with_1_based_numbers(tmp_path):
    pdf = tmp_path / "a.pdf"
    make_pdf(pdf, ["first page", "", "third page"])   # page 2 is blank

    blocks = PdfExtractor().extract(pdf)

    assert [(b.page, b.text) for b in blocks] == [(1, "first page"), (3, "third page")]
    assert all(b.heading_path == [] for b in blocks)


def test_multiline_page_text(tmp_path):
    pdf = tmp_path / "a.pdf"
    make_pdf(pdf, ["line one\nline two"])

    assert PdfExtractor().extract(pdf)[0].text == "line one\nline two"


def test_pdf_without_text_raises(tmp_path):
    pdf = tmp_path / "empty.pdf"
    make_pdf(pdf, ["", ""])

    with pytest.raises(ExtractionError, match="no"):
        PdfExtractor().extract(pdf)


def test_password_protected_raises(tmp_path):
    pdf = tmp_path / "locked.pdf"
    make_pdf(pdf, ["secret"], password="pw")

    with pytest.raises(ExtractionError, match="password"):
        PdfExtractor().extract(pdf)


def test_corrupt_file_raises(tmp_path):
    pdf = tmp_path / "broken.pdf"
    pdf.write_bytes(b"%PDF-1.7\nthis is not really a pdf")

    with pytest.raises(ExtractionError, match="cannot open PDF"):
        PdfExtractor().extract(pdf)
