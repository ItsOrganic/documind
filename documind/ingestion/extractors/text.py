import re
from pathlib import Path

from documind.ingestion.errors import ExtractionError
from documind.ingestion.types import Block

# a blank line = newline, optional spaces/tabs, newline
_PARAGRAPH_BREAK = re.compile(r"\n[ \t]*\n")


class TextExtractor:
    def extract(self, path: Path) -> list[Block]:
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError as e:
            raise ExtractionError(f"file is not valid UTF-8 at byte {e.start}") from e

        text = text.replace("\r\n", "\n").replace("\r", "\n")

        blocks = [
            Block(text=p.strip())
            for p in _PARAGRAPH_BREAK.split(text)
            if p.strip()
        ]

        if not blocks:
            raise ExtractionError("text file is empty")
        return blocks