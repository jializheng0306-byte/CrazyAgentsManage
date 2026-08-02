#!/usr/bin/env python3
"""Fetch Crossref papers through executor and render a markdown section."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from executor_readonly_helper import call_executor_tool, render_markdown_section


def strip_jats(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def format_authors(item: dict) -> str:
    authors = []
    for author in (item.get("author") or [])[:3]:
        given = (author.get("given") or "").strip()
        family = (author.get("family") or "").strip()
        name = " ".join(part for part in (given, family) if part).strip()
        if name:
            authors.append(name)
    return ", ".join(authors) if authors else "未知作者"


def _date_from_parts(parts: list) -> str:
    values = parts[0] if parts else []
    if not values:
        return ""
    year = str(values[0])
    month = f"{int(values[1]):02d}" if len(values) > 1 else "01"
    day = f"{int(values[2]):02d}" if len(values) > 2 else "01"
    return f"{year}-{month}-{day}"


def format_date(item: dict) -> str:
    for key in ("published-print", "published-online", "issued"):
        date = _date_from_parts((item.get(key) or {}).get("date-parts") or [])
        if date:
            return date
    created = item.get("created") or {}
    date_time = created.get("date-time") or ""
    return str(date_time)[:10] if date_time else "未知日期"


def normalize_items(payload: dict, max_abstract_chars: int) -> list[dict]:
    items = []
    for item in ((payload.get("message") or {}).get("items") or []):
        title_values = item.get("title") or []
        container_values = item.get("container-title") or []
        abstract = strip_jats(item.get("abstract") or "")
        if len(abstract) > max_abstract_chars:
            abstract = abstract[: max_abstract_chars - 3] + "..."
        doi = item.get("DOI") or ""
        url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")
        items.append(
            {
                "title": title_values[0] if title_values else "Untitled",
                "doi": doi,
                "url": url,
                "authors": format_authors(item),
                "date": format_date(item),
                "container": container_values[0] if container_values else "",
                "abstract": abstract,
            }
        )
    return items


def render_item(item: dict) -> list[str]:
    return [
        f"### {item['title'][:100]}",
        f"- DOI: {item['doi'] or 'N/A'}",
        f"- 作者: {item['authors']}",
        f"- 日期: {item['date']}",
        f"- 来源: {item['container'] or 'N/A'}",
        f"- 摘要: {(item['abstract'] or '无摘要')[:400]}",
        f"- 链接: {item['url'] or 'N/A'}",
    ]


def fetch_crossref_items(args: argparse.Namespace) -> tuple[list[dict], str | None]:
    try:
        payload = call_executor_tool(
            source=args.source,
            group="works",
            tool="searchWorks",
            payload={
                "query": args.query,
                "rows": args.rows,
                "sort": args.sort,
                "order": args.order,
                **({"filter": args.filter} if args.filter else {}),
                **({"mailto": args.mailto} if args.mailto else {}),
            },
        )
    except RuntimeError as exc:
        return [], f"（Crossref via executor 不可用：{exc}）"
    return normalize_items(payload, args.max_abstract_chars), None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="crossref-readonly")
    parser.add_argument("--heading", required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--rows", type=int, default=5)
    parser.add_argument("--sort", default="published")
    parser.add_argument("--order", default="desc")
    parser.add_argument("--filter", default="")
    parser.add_argument("--mailto", default="")
    parser.add_argument("--max-abstract-chars", type=int, default=280)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    items, fallback_text = fetch_crossref_items(args)
    if args.json:
        print(json.dumps({"query": args.query, "items": items}, ensure_ascii=False, indent=2))
    else:
        print(
            render_markdown_section(
                heading=args.heading,
                items=items,
                render_item=render_item,
                empty_text=fallback_text or "（未返回论文结果）",
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
