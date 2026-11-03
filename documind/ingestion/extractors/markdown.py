from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.token import Token

from documind.ingestion.errors import ExtractionError
from documind.ingestion.extractors.headings import HeadingStack
from documind.ingestion.types import Block

_md = MarkdownIt("commonmark").enable("table")


class MarkdownExtractor:
    def extract(self, path: Path) -> list[Block]:
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError as e:
            raise ExtractionError(f"file is not valid UTF-8 at byte {e.start}") from e

        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        tokens = _md.parse("\n".join(lines))

        # The parser only tells us where headings are (and skips "#" inside code
        # blocks); each section's text is the raw source between two headings.
        blocks: list[Block] = []
        headings = HeadingStack()
        section_start = 0

        def flush(end: int) -> None:
            body = "\n".join(lines[section_start:end]).strip()
            if body:
                blocks.append(Block(text=body, heading_path=headings.path()))

        for i, token in enumerate(tokens):
            if token.type != "heading_open" or token.map is None:
                continue
            start, end = token.map
            flush(start)
            headings.push(int(token.tag[1]), _inline_text(tokens[i + 1]))
            section_start = end
        flush(len(lines))

        if not blocks:
            raise ExtractionError("markdown file has no text")
        return blocks


def _inline_text(token: Token) -> str:
    """Heading text without markdown syntax: "Run `docker` **now**" -> "Run docker now"."""
    return "".join(
        child.content for child in token.children or [] if child.type in ("text", "code_inline")
    ).strip()
