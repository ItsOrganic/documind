from pathlib import Path
from typing import Protocol

from documind.ingestion.errors import UnsupportedFileType
from documind.ingestion.extractors.html import HtmlExtractor
from documind.ingestion.extractors.markdown import MarkdownExtractor
from documind.ingestion.extractors.pdf import PdfExtractor
from documind.ingestion.extractors.text import TextExtractor
from documind.ingestion.types import Block


class Extractor(Protocol):
    def extract(self, path: Path) -> list[Block]: ...


EXTRACTORS: dict[str, Extractor] = {
    "pdf": PdfExtractor(),          # one Block per page        (pymupdf or pypdf)
    "markdown": MarkdownExtractor(),# one Block per section     (markdown-it-py)
    "html": HtmlExtractor(),        # one Block per section     (beautifulsoup4)
    "text": TextExtractor(),        # one Block per paragraph
}

def get_extractor(source_type: str) -> Extractor:
    try:
        return EXTRACTORS[source_type]
    except KeyError:
        raise UnsupportedFileType(source_type)

