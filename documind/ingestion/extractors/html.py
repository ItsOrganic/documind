import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

from documind.ingestion.errors import ExtractionError
from documind.ingestion.extractors.headings import HeadingStack
from documind.ingestion.types import Block

_HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
# page chrome and non-content elements; their text is never indexed
_SKIP = {"script", "style", "noscript", "template", "svg", "nav", "header", "footer", "aside", "form"}
# elements that start a new line in the extracted text
_BLOCK = {
    "p", "div", "section", "article", "main", "li", "ul", "ol", "pre", "blockquote",
    "table", "tr", "td", "th", "dl", "dt", "dd", "figure", "figcaption", "hr", "br",
}
_WHITESPACE = re.compile(r"\s+")


class HtmlExtractor:
    def extract(self, path: Path) -> list[Block]:
        try:
            html = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError as e:
            raise ExtractionError(f"file is not valid UTF-8 at byte {e.start}") from e

        soup = BeautifulSoup(html, "html.parser")
        # prefer the main content area when the page marks one
        root = soup.find("main") or soup.find("article") or soup.body or soup

        blocks: list[Block] = []
        headings = HeadingStack()
        buf: list[str] = []

        def flush() -> None:
            lines = (line.strip() for line in "".join(buf).split("\n"))
            body = "\n".join(line for line in lines if line)
            if body:
                blocks.append(Block(text=body, heading_path=headings.path()))
            buf.clear()

        def walk(node: Tag) -> None:
            for child in node.children:
                if isinstance(child, NavigableString):
                    # exact type check skips comments, doctype and CDATA (subclasses)
                    if type(child) is NavigableString:
                        buf.append(_WHITESPACE.sub(" ", str(child)))
                    continue
                if not isinstance(child, Tag) or child.name in _SKIP:
                    continue
                if child.name in _HEADINGS:
                    flush()
                    headings.push(int(child.name[1]), child.get_text(" ", strip=True))
                    continue
                if child.name == "pre":
                    # code keeps its line breaks; whitespace is only collapsed in normal text
                    buf.append(f"\n{child.get_text()}\n")
                    continue
                if child.name in _BLOCK:
                    buf.append("\n")
                walk(child)
                if child.name in _BLOCK:
                    buf.append("\n")

        if isinstance(root, Tag):
            walk(root)
        flush()

        if not blocks:
            raise ExtractionError("HTML file has no text")
        return blocks
