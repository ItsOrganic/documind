import pytest

from documind.ingestion.errors import ExtractionError
from documind.ingestion.extractors.html import HtmlExtractor


def test_sections_get_heading_paths(tmp_path):
    f = tmp_path / "a.html"
    f.write_text(
        "<html><body>"
        "<h1>Setup</h1><p>Install   it.</p>"
        "<h2>Docker</h2><p>Run the <b>container</b>.</p><ul><li>one</li><li>two</li></ul>"
        "<h2>Kubernetes</h2><p>Use helm.</p>"
        "</body></html>"
    )

    blocks = HtmlExtractor().extract(f)

    assert [(b.heading_path, b.text) for b in blocks] == [
        (["Setup"], "Install it."),
        (["Setup", "Docker"], "Run the container.\none\ntwo"),
        (["Setup", "Kubernetes"], "Use helm."),
    ]


def test_skips_scripts_nav_and_comments(tmp_path):
    f = tmp_path / "a.html"
    f.write_text(
        "<!DOCTYPE html><html><head><title>T</title><style>p{}</style></head><body>"
        "<nav>Home | About</nav><script>var x = 1;</script>"
        "<!-- hidden --><p>Real content.</p>"
        "<footer>Copyright</footer></body></html>"
    )

    assert [b.text for b in HtmlExtractor().extract(f)] == ["Real content."]


def test_pre_keeps_line_breaks(tmp_path):
    f = tmp_path / "a.html"
    f.write_text("<h1>Run</h1><p>Use:</p><pre><code>uv sync\nuv run main.py</code></pre>")

    assert HtmlExtractor().extract(f)[0].text == "Use:\nuv sync\nuv run main.py"


def test_prefers_main_element(tmp_path):
    f = tmp_path / "a.html"
    f.write_text("<body><div>Sidebar junk</div><main><h1>Doc</h1><p>Body.</p></main></body>")

    blocks = HtmlExtractor().extract(f)

    assert [(b.heading_path, b.text) for b in blocks] == [(["Doc"], "Body.")]


def test_no_text_raises(tmp_path):
    f = tmp_path / "a.html"
    f.write_text("<html><body><script>x()</script></body></html>")
    with pytest.raises(ExtractionError):
        HtmlExtractor().extract(f)
