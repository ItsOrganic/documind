import pytest

from documind.ingestion.errors import ExtractionError
from documind.ingestion.extractors.markdown import MarkdownExtractor


def test_sections_get_heading_paths(tmp_path):
    f = tmp_path / "a.md"
    f.write_text(
        "Intro before any heading.\n\n"
        "# Setup\n\nInstall it.\n\n"
        "## Docker\n\nRun the container.\n\n"
        "### Volumes\n\nMount a volume.\n\n"
        "## Kubernetes\n\nUse helm.\n"
    )

    blocks = MarkdownExtractor().extract(f)

    assert [(b.heading_path, b.text) for b in blocks] == [
        ([], "Intro before any heading."),
        (["Setup"], "Install it."),
        (["Setup", "Docker"], "Run the container."),
        (["Setup", "Docker", "Volumes"], "Mount a volume."),
        (["Setup", "Kubernetes"], "Use helm."),
    ]
    assert all(b.page is None for b in blocks)


def test_hash_inside_code_block_is_not_a_heading(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("# Usage\n\n```bash\n# not a heading\nls\n```\n")

    blocks = MarkdownExtractor().extract(f)

    assert len(blocks) == 1
    assert blocks[0].heading_path == ["Usage"]
    assert "# not a heading" in blocks[0].text


def test_setext_headings_and_inline_markup(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("Run `docker` **now**\n====================\n\nBody.\n")

    blocks = MarkdownExtractor().extract(f)

    assert blocks[0].heading_path == ["Run docker now"]
    assert blocks[0].text == "Body."


def test_heading_without_body_is_skipped(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("# Title\n## Section\n\nText.\n")

    assert [b.heading_path for b in MarkdownExtractor().extract(f)] == [["Title", "Section"]]


def test_only_headings_raises(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("# Title\n\n## Empty\n")
    with pytest.raises(ExtractionError):
        MarkdownExtractor().extract(f)
