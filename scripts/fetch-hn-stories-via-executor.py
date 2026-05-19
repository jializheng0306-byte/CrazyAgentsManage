#!/usr/bin/env python3
"""Fetch Hacker News stories through executor and render a markdown section."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from executor_readonly_helper import call_executor_tool, render_markdown_section


def normalize_items(payload: dict, max_desc_chars: int) -> list[dict]:
    items = []
    for item in payload.get("hits") or []:
        title = (item.get("title") or "Untitled").strip()
        url = (item.get("url") or "").strip()
        author = (item.get("author") or "未知作者").strip()
        created_at = str(item.get("created_at") or "")[:10] or "未知日期"
        summary = (item.get("story_text") or "").strip()
        if len(summary) > max_desc_chars:
            summary = summary[: max_desc_chars - 3] + "..."
        items.append(
            {
                "title": title,
                "url": url,
                "author": author,
                "date": created_at,
                "summary": summary,
                "points": item.get("points"),
                "comments": item.get("num_comments"),
            }
        )
    return items


def render_item(item: dict) -> list[str]:
    lines = [
        f"### {item['title'][:100]}",
        f"- 作者: {item['author']}",
        f"- 日期: {item['date']}",
    ]
    if item.get("points") is not None:
        lines.append(f"- Points: {item['points']}")
    if item.get("comments") is not None:
        lines.append(f"- 评论数: {item['comments']}")
    if item.get("summary"):
        lines.append(f"- 简介: {item['summary']}")
    lines.append(f"- 链接: {item['url'] or 'N/A'}")
    return lines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="hn-readonly")
    parser.add_argument("--heading", default="Hacker News AI / Agent Stories（via executor）")
    parser.add_argument("--query", default="AI agent")
    parser.add_argument("--rows", type=int, default=5)
    parser.add_argument("--tags", default="story")
    parser.add_argument("--max-desc-chars", type=int, default=180)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = call_executor_tool(
        source=args.source,
        group="stories",
        tool="searchStoriesByDate",
        payload={
            "query": args.query,
            "tags": args.tags,
            "hitsPerPage": args.rows,
        },
    )
    items = normalize_items(payload, args.max_desc_chars)
    if args.json:
        print(json.dumps({"query": args.query, "items": items}, ensure_ascii=False, indent=2))
    else:
        print(
            render_markdown_section(
                heading=args.heading,
                items=items,
                render_item=render_item,
                empty_text="（未返回 HN 条目）",
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
