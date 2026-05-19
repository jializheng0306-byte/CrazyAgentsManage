import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "fetch-hn-stories-via-executor.py"
SPEC = importlib.util.spec_from_file_location("fetch_hn_stories_via_executor", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_normalize_items_limits_summary_and_preserves_fields():
    payload = {
        "hits": [
            {
                "title": "A Story About Agents",
                "url": "https://example.com/story",
                "author": "alice",
                "created_at": "2026-05-19T01:07:43Z",
                "story_text": "x" * 50,
                "points": 42,
                "num_comments": 7,
            }
        ]
    }

    items = MODULE.normalize_items(payload, max_desc_chars=20)

    assert items == [
        {
            "title": "A Story About Agents",
            "url": "https://example.com/story",
            "author": "alice",
            "date": "2026-05-19",
            "summary": "xxxxxxxxxxxxxxxxx...",
            "points": 42,
            "comments": 7,
        }
    ]


def test_render_item_contains_hn_fields():
    lines = MODULE.render_item(
        {
            "title": "A Story About Agents",
            "url": "https://example.com/story",
            "author": "alice",
            "date": "2026-05-19",
            "summary": "Short summary",
            "points": 42,
            "comments": 7,
        }
    )

    assert any("作者: alice" in line for line in lines)
    assert any("Points: 42" in line for line in lines)
    assert any("评论数: 7" in line for line in lines)
