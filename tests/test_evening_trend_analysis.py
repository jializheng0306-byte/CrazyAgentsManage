import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "evening-trend-analysis.py"
SPEC = importlib.util.spec_from_file_location("evening_trend_analysis", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_extract_summary_stops_at_next_section():
    content = """# Digest
## 导读
- 第一条摘要
- 第二条摘要
## 下一个分区
- 不应该进入摘要
"""

    summary = MODULE.extract_summary(content)

    assert "第一条摘要" in summary
    assert "第二条摘要" in summary
    assert "不应该进入摘要" not in summary


def test_extract_topics_returns_named_sections():
    content = """**Alice**
Build agent platforms with better evaluation.
https://example.com/alice
**Bob**
Focus on memory systems and workflow safety.
"""

    topics = MODULE.extract_topics(content)

    assert topics == [
        ("Alice", "Build agent platforms with better evaluation."),
        ("Bob", "Focus on memory systems and workflow safety."),
    ]
