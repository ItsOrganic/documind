from pathlib import Path

from documind.ingestion.types import Block


class TextExtractor:
    def extract(self, path: Path) -> list[Block]:
        try:
            return []
        except KeyError:
            raise NotImplementedError("This feature is not implemented")