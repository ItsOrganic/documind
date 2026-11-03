from documind.ingestion.errors import ExtractionError
from pathlib import Path
import pymupdf
from documind.ingestion.types import Block


class PdfExtractor:
    def extract(self, path: Path) -> list[Block]:
        try:
            doc = pymupdf.open(path)
        except (pymupdf.FileDataError, RuntimeError) as e:
            raise ExtractionError(f"cannot open PDF: {e}") from e
        with doc:
            if doc.needs_pass:
                raise ExtractionError("PDF is password-protected")
            
            blocks: list[Block] = []
            for page in doc:
                text = page.get_text("text", sort=True).strip()
                if text:
                    blocks.append(Block(text=text, page=page.number + 1))
            if not blocks:
                raise ExtractionError("PDF has no aextractable text")
            return blocks