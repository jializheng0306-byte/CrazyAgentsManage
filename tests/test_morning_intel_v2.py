import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "morning-intel-v2.py"
SPEC = importlib.util.spec_from_file_location("morning_intel_v2", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_executor_hn_items_are_mapped_to_rss_shape():
    payload = {
        "hits": [
            {
                "title": "Make products AI agents want",
                "url": "https://example.com/post",
                "story_text": "Short summary",
            }
        ]
    }

    original = MODULE.call_executor_tool
    MODULE.call_executor_tool = lambda source, group, tool, payload: payload and {
        "hits": [
            {
                "title": "Make products AI agents want",
                "url": "https://example.com/post",
                "story_text": "Short summary",
            }
        ]
    }
    try:
        items = MODULE.fetch_hn_via_executor(1)
    finally:
        MODULE.call_executor_tool = original

    assert items == [
        {
            "title": "Make products AI agents want",
            "title_cn": "Make products AI agents want",
            "link": "https://example.com/post",
            "description": "Short summary",
            "description_cn": "Short summary",
            "source": "Hacker News (executor)",
        }
    ]
