import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "fetch-crossref-papers-via-executor.py"
SPEC = importlib.util.spec_from_file_location("fetch_crossref_papers_via_executor", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_strip_jats_and_normalize_items():
    payload = {
        "message": {
            "items": [
                {
                    "DOI": "10.1000/demo",
                    "title": ["A Demo Paper"],
                    "URL": "https://doi.org/10.1000/demo",
                    "abstract": "<jats:p>  A <b>demo</b> abstract. </jats:p>",
                    "container-title": ["Journal of Demos"],
                    "author": [
                        {"given": "Ada", "family": "Lovelace"},
                        {"given": "Alan", "family": "Turing"}
                    ],
                    "published-online": {"date-parts": [[2026, 5, 19]]}
                }
            ]
        }
    }

    items = MODULE.normalize_items(payload, max_abstract_chars=80)

    assert items == [
        {
            "title": "A Demo Paper",
            "doi": "10.1000/demo",
            "url": "https://doi.org/10.1000/demo",
            "authors": "Ada Lovelace, Alan Turing",
            "date": "2026-05-19",
            "container": "Journal of Demos",
            "abstract": "A demo abstract."
        }
    ]


def test_format_markdown_contains_core_fields():
    markdown = MODULE.render_markdown_section(
        heading="Crossref 测试",
        items=[
            {
                "title": "A Demo Paper",
                "doi": "10.1000/demo",
                "url": "https://doi.org/10.1000/demo",
                "authors": "Ada Lovelace",
                "date": "2026-05-19",
                "container": "Journal of Demos",
                "abstract": "A concise abstract."
            }
        ],
        render_item=MODULE.render_item,
        empty_text="（未返回论文结果）"
    )

    assert "## Crossref 测试" in markdown
    assert "### A Demo Paper" in markdown
    assert "- DOI: 10.1000/demo" in markdown
    assert "- 作者: Ada Lovelace" in markdown
