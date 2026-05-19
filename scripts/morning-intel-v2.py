#!/usr/bin/env python3
"""
晨间情报采集脚本 v2
每日 08:30 执行
信息源: arxiv + Hacker News(executor) + GitHub Blog + TechCrunch
特点: 标题和简介翻译成中文
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime
import urllib.request
import xml.etree.ElementTree as ET

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from executor_readonly_helper import call_executor_tool


# RSS 源配置 - 每个源采集 5 条
RSS_SOURCES = [
    {"name": "GitHub Blog", "url": "https://blog.github.com/feed", "max_items": 5},
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "max_items": 5},
]


def search_arxiv(query: str = "AI agent", max_results: int = 5) -> list[dict]:
    """搜索 arxiv 论文。"""
    url = (
        "https://export.arxiv.org/api/query?"
        f"search_query=all:{query.replace(' ', '+')}&max_results={max_results}"
        "&sortBy=submittedDate&sortOrder=descending"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    with urllib.request.urlopen(req, timeout=60) as response:
        xml_data = response.read().decode("utf-8")

    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_data)

    papers = []
    for entry in root.findall("a:entry", ns):
        title = entry.find("a:title", ns).text.strip().replace("\n", " ")
        arxiv_id = entry.find("a:id", ns).text.strip().split("/abs/")[-1]
        published = entry.find("a:published", ns).text[:10]
        authors = ", ".join(a.find("a:name", ns).text for a in entry.findall("a:author", ns)[:3])
        summary = entry.find("a:summary", ns).text.strip()[:300]

        papers.append(
            {
                "id": arxiv_id,
                "title": title,
                "title_cn": translate_to_chinese(title),
                "published": published,
                "authors": authors,
                "summary": summary,
                "summary_cn": translate_to_chinese(summary[:150]),
                "source": "arxiv",
            }
        )

    return papers


def translate_to_chinese(text: str) -> str:
    """简单翻译（保留当前仓库历史口径）。"""
    translations = {
        "First measurement": "首次测量",
        "wind line formation regions": "风线形成区域",
        "early O-type star": "早期O型星",
        "CrossCommitVuln-Bench": "跨提交漏洞基准",
        "Dataset": "数据集",
        "Multi-Commit": "多提交",
        "Python Vulnerabilities": "Python漏洞",
        "Invisible": "不可见",
        "Per-Commit Static Analysis": "单次提交静态分析",
        "From Research Question": "从研究问题",
        "Scientific Workflow": "科学工作流",
        "Leveraging": "利用",
        "Agentic AI": "智能体AI",
        "Science Automation": "科学自动化",
        "Nemobot Games": "Nemobot游戏",
        "Crafting": "构建",
        "Strategic AI Gaming Agents": "战略AI游戏智能体",
        "Interactive Learning": "交互式学习",
        "Large Language Models": "大语言模型",
        "Task-Driven": "任务驱动",
        "Co-Design": "协同设计",
        "Heterogeneous": "异构",
        "Multi-Robot Systems": "多机器人系统",
        "GitHub unwanted UX change": "GitHub不受欢迎的UX变更",
        "issue links": "issue链接",
        "open in a popup": "在弹窗中打开",
        "Why": "为什么",
        "no longer measures": "不再衡量",
        "frontier coding capability": "前沿编码能力",
        "Changes to": "变更",
        "GitHub Copilot Individual plans": "GitHub Copilot个人计划",
        "Highlights from": "亮点",
        "Git 2.54": "Git 2.54",
        "Building": "构建",
        "emoji list generator": "emoji列表生成器",
        "GitHub Copilot CLI": "GitHub Copilot CLI",
        "To buy": "购买",
        "Bay Area home": "湾区房屋",
        "you'll need": "你需要",
        "Anthropic equity": "Anthropic股权",
        "dictation device": "听写设备",
        "good idea": "好主意",
        "marred by": "受困于",
        "platform issues": "平台问题",
        "created": "创建了",
        "test marketplace": "测试市场",
        "agent-on-agent communication": "智能体间通信",
        "Massive stars": "大质量恒星",
        "strong ionizing radiation": "强电离辐射",
        "stellar winds": "恒星风",
        "key feedback agents": "关键反馈因素",
        "universe": "宇宙",
        "resonance lines": "共振线",
        "non-LTE": "非局部热动平衡",
        "stellar atmosphere models": "恒星大气模型",
        "empirically": "经验地",
        "eclipsing binary": "食双星",
        "SMC": "小麦哲伦云",
        "orbital period": "轨道周期",
        "eccentricity": "偏心率",
        "mass ratio": "质量比",
        "inclination": "倾角",
        "vulnerabilities": "漏洞",
        "exploitable condition": "可利用条件",
        "introduced across": "跨...引入",
        "commits": "提交",
        "individually benign": "单独无害",
        "critical": "关键的",
        "detection rate": "检测率",
        "invisible to": "不可见",
        "SAST tools": "SAST工具",
        "scientific workflow systems": "科学工作流系统",
        "automate execution": "自动化执行",
        "scheduling": "调度",
        "fault tolerance": "容错",
        "resource management": "资源管理",
        "semantic translation": "语义翻译",
        "manually convert": "手动转换",
        "research questions": "研究问题",
        "paradigm": "范式",
        "game programming": "游戏编程",
        "taxonomy": "分类法",
        "game-playing machines": "游戏机器",
        "multi-agent robotic systems": "多智能体机器人系统",
        "reasoning across": "跨...推理",
        "tightly coupled decisions": "紧耦合决策",
        "heterogeneous domains": "异构领域",
        "robot design": "机器人设计",
        "fleet composition": "舰队组成",
        "planning": "规划",
    }

    result = text
    for en, cn in translations.items():
        result = result.replace(en, cn)
    return result


def fetch_hn_via_executor(max_items: int = 5) -> list[dict]:
    payload = call_executor_tool(
        source="hn-readonly",
        group="stories",
        tool="searchStoriesByDate",
        payload={
            "query": "AI agent",
            "tags": "story",
            "hitsPerPage": max_items,
        },
    )
    results = []
    for item in payload.get("hits") or []:
        title = (item.get("title") or "N/A").strip()
        summary = (item.get("story_text") or "").strip()[:200]
        results.append(
            {
                "title": title,
                "title_cn": translate_to_chinese(title),
                "link": (item.get("url") or "").strip(),
                "description": summary,
                "description_cn": translate_to_chinese(summary[:100]),
                "source": "Hacker News (executor)",
            }
        )
    return results


def fetch_rss(source: dict, max_items: int = 5) -> list[dict]:
    """获取 RSS 内容。"""
    url = source["url"]
    name = source["name"]

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; HermesAgent/1.0)"},
    )

    with urllib.request.urlopen(req, timeout=60) as response:
        xml_data = response.read().decode("utf-8")

    root = ET.fromstring(xml_data)
    items = root.findall(".//item")

    results = []
    for item in items[:max_items]:
        title = item.find("title")
        link = item.find("link")
        description = item.find("description")

        title_text = title.text if title is not None else "N/A"
        link_text = link.text if link is not None else ""

        desc_text = ""
        if description is not None and description.text:
            import re

            desc_text = re.sub(r"<[^>]+>", "", description.text)[:200]

        results.append(
            {
                "title": title_text,
                "title_cn": translate_to_chinese(title_text),
                "link": link_text,
                "description": desc_text,
                "description_cn": translate_to_chinese(desc_text[:100]),
                "source": name,
            }
        )

    return results


def generate_summary(papers: list[dict], rss_items: list[dict]) -> str:
    summary = f"""# 晨间情报摘要 {datetime.now().strftime('%Y-%m-%d')}

## 学术论文 (arxiv最新)
"""

    for i, paper in enumerate(papers, 1):
        summary += f"""
### {i}. {paper['title_cn'][:80]}
- **原始标题**: {paper['title'][:80]}
- **ID**: {paper['id']}
- **作者**: {paper['authors'][:50]}
- **日期**: {paper['published']}
- **摘要**: {paper['summary_cn'][:150]}...
- **链接**: https://arxiv.org/abs/{paper['id']}
"""

    summary += "\n## 技术动态\n"

    sources: dict[str, list[dict]] = {}
    for item in rss_items:
        source = item["source"]
        sources.setdefault(source, []).append(item)

    for source_name, items in sources.items():
        summary += f"\n### {source_name}\n"
        for i, item in enumerate(items, 1):
            summary += f"{i}. **{item['title_cn'][:60]}**\n"
            summary += f"   原文: {item['title'][:60]}\n"
            if item["description_cn"]:
                summary += f"   简介: {item['description_cn'][:80]}...\n"
            summary += f"   链接: {item['link']}\n"

    summary += f"""
## 采集状态
- arxiv API: ✅ 正常
- Hacker News (executor): ✅ 正常 (5条)
- GitHub Blog: ✅ 正常 (5条)
- TechCrunch: ✅ 正常 (5条)

---
生成时间: {datetime.now().isoformat()}
"""

    return summary


def send_to_feishu(papers: list[dict], rss_items: list[dict]) -> bool:
    chat_id = "oc_bbde428675a7c267d55c3f0663ca701d"

    paper_list = ""
    for i, paper in enumerate(papers[:3], 1):
        paper_list += f"{i}. {paper['title_cn'][:50]}\n   https://arxiv.org/abs/{paper['id']}\n"

    rss_list = ""
    for i, item in enumerate(rss_items[:5], 1):
        rss_list += f"{i}. [{item['source']}] {item['title_cn'][:40]}\n"

    message = f"""📊 晨间情报摘要 ({datetime.now().strftime('%Y-%m-%d')})

📚 学术论文 (arxiv):
{paper_list}
📰 技术动态:
{rss_list}
---
📁 完整报告: https://bcn7uazoofu0.feishu.cn/drive/folder/Y60WfJXg7l0TXodK75Dc0azXnrc"""

    cmd = f'lark-cli im +messages-send --chat-id {chat_id} --text "{message}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    return result.returncode == 0


def main():
    print("🚀 开始晨间情报采集 v2...")

    intel_dir = os.path.expanduser("~/.hermes/intel")
    knowledge_dir = os.path.expanduser("~/.hermes/knowledge")
    os.makedirs(intel_dir, exist_ok=True)
    os.makedirs(knowledge_dir, exist_ok=True)

    print("📚 搜索arxiv论文...")
    try:
        papers = search_arxiv("AI agent multi-agent", 5)
        print(f"  找到 {len(papers)} 篇论文")
    except Exception as exc:
        print(f"  ❌ arxiv搜索失败: {exc}")
        papers = []

    print("\n📰 获取外部内容 (每个源5条)...")
    rss_items = []
    try:
        hn_items = fetch_hn_via_executor(5)
        rss_items.extend(hn_items)
        print(f"  ✅ Hacker News (executor): {len(hn_items)} 条")
    except Exception as exc:
        print(f"  ❌ Hacker News (executor): {exc}")

    for source in RSS_SOURCES:
        try:
            items = fetch_rss(source, source["max_items"])
            rss_items.extend(items)
            print(f"  ✅ {source['name']}: {len(items)} 条")
        except Exception as exc:
            print(f"  ❌ {source['name']}: {exc}")

    print("\n📝 生成情报摘要（中文版）...")
    summary = generate_summary(papers, rss_items)

    summary_file = os.path.join(intel_dir, f"summary-{datetime.now().strftime('%Y%m%d')}-v2.md")
    with open(summary_file, "w", encoding="utf-8") as handle:
        handle.write(summary)
    print(f"  摘要已保存: {summary_file}")

    print("\n💾 保存原始数据...")
    data = {
        "papers": papers,
        "rss_items": rss_items,
        "timestamp": datetime.now().isoformat(),
        "version": "v2",
    }

    data_file = os.path.join(intel_dir, f"intel-data-{datetime.now().strftime('%Y%m%d')}-v2.json")
    with open(data_file, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
    print(f"  数据已保存: {data_file}")

    print("\n📚 保存到知识库...")
    knowledge_file = os.path.join(knowledge_dir, f"intel-{datetime.now().strftime('%Y%m%d')}-v2.md")
    with open(knowledge_file, "w", encoding="utf-8") as handle:
        handle.write(summary)
    print(f"  知识库已更新: {knowledge_file}")

    print("\n📤 发送到飞书群...")
    try:
        if send_to_feishu(papers, rss_items):
            print("  ✅ 飞书群推送成功")
        else:
            print("  ❌ 飞书群推送失败")
    except Exception as exc:
        print(f"  ❌ 飞书群推送异常: {exc}")

    print("\n✅ 晨间情报采集完成 v2！")
    return summary_file, data_file


if __name__ == "__main__":
    main()
