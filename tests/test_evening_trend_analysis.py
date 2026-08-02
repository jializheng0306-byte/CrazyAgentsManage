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


def test_resolve_report_source_falls_back_to_collector_report(tmp_path, monkeypatch):
    repo_dir = tmp_path / "digest-repo"
    intel_dir = tmp_path / "intel"
    (repo_dir / "zh" / "daily").mkdir(parents=True)
    intel_dir.mkdir(parents=True)

    report_file = intel_dir / "evening-intel-2026-06-29.md"
    report_file.write_text(
        """# 晚间趋势原始数据 2026-06-29

采集时间: 2026-06-29 20:00:00

## Hacker News Agent / Builder Trends（via executor）

### Agents hit a new quality bar
- 作者: Alice
- 日期: 2026-06-29
- 简介: The collector produced a meaningful fallback report.
- 链接: https://example.com/story
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(MODULE, "REPO_DIR", str(repo_dir))
    monkeypatch.setattr(MODULE, "INTEL_DIR", str(intel_dir))

    content, filepath = MODULE.resolve_report_source("2026-06-29")

    assert content == report_file.read_text(encoding="utf-8")
    assert filepath == str(report_file)
    assert MODULE.extract_digest_date(filepath, "2026-06-29") == "2026-06-29"

    summary = MODULE.extract_summary(content)
    topics = MODULE.extract_topics(content)

    assert "Agents hit a new quality bar" in summary
    assert topics[0][0] == "Agents hit a new quality bar"
    assert "collector produced a meaningful fallback report" in topics[0][1]
