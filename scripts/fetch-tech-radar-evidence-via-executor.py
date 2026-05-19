#!/usr/bin/env python3
"""Fetch readonly evidence for high-priority pending tech-radar entries via executor."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from executor_readonly_helper import call_executor_tool, render_markdown_section


SUPPORTED_SOURCES = {"arxiv", "hn", "github"}


def priority_rank(priority: str) -> int:
    value = str(priority or "").upper()
    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    return order.get(value, 99)


def load_entries(radar_file: Path) -> list[dict]:
    data = json.loads(radar_file.read_text(encoding="utf-8"))
    return list(data.get("entries") or [])


def filter_entries(entries: list[dict], priorities: set[str], statuses: set[str], max_entries: int) -> list[dict]:
    filtered = [
        dict(entry, _source=str(entry.get("source", "")).lower(), _index=index)
        for index, entry in enumerate(entries)
        if str(entry.get("priority", "")).upper() in priorities
        and str(entry.get("status", "")).lower() in statuses
        and str(entry.get("source", "")).lower() in SUPPORTED_SOURCES
    ]
    if not filtered:
        return []

    by_source: dict[str, list[dict]] = {}
    for entry in filtered:
        by_source.setdefault(entry["_source"], []).append(entry)

    selected = []
    selected_ids = set()

    for items in by_source.values():
        ranked = sorted(items, key=lambda entry: (priority_rank(entry.get("priority")), entry["_index"]))
        chosen = ranked[0]
        selected.append(chosen)
        selected_ids.add(id(chosen))

    remainder = [
        entry for entry in sorted(
            filtered,
            key=lambda entry: (priority_rank(entry.get("priority")), entry["_index"]),
        )
        if id(entry) not in selected_ids
    ]

    combined = sorted(selected, key=lambda entry: (priority_rank(entry.get("priority")), entry["_index"]))
    for entry in remainder:
        if len(combined) >= max_entries:
            break
        combined.append(entry)

    cleaned = []
    for entry in combined[:max_entries]:
        copy = dict(entry)
        copy.pop("_source", None)
        copy.pop("_index", None)
        cleaned.append(copy)
    return cleaned


def fetch_entry_evidence(entry: dict, max_results: int) -> dict:
    source = str(entry.get("source", "")).lower()
    if source == "arxiv":
        payload = call_executor_tool(
            source="crossref-readonly",
            group="works",
            tool="searchWorks",
            payload={
                "query": entry.get("name", ""),
                "rows": max_results,
                "sort": "relevance",
                "order": "desc",
            },
        )
        items = []
        for item in ((payload.get("message") or {}).get("items") or [])[:max_results]:
            title_values = item.get("title") or []
            items.append(
                {
                    "kind": "crossref",
                    "title": title_values[0] if title_values else "Untitled",
                    "url": item.get("URL") or "",
                    "container": (item.get("container-title") or [""])[0],
                }
            )
        return {"executorSource": "crossref-readonly", "items": items}

    if source == "hn":
        payload = call_executor_tool(
            source="hn-readonly",
            group="stories",
            tool="searchStoriesByDate",
            payload={
                "query": entry.get("name", ""),
                "tags": "story",
                "hitsPerPage": max_results,
            },
        )
        items = []
        for item in (payload.get("hits") or [])[:max_results]:
            items.append(
                {
                    "kind": "hn",
                    "title": item.get("title") or "Untitled",
                    "url": item.get("url") or "",
                    "author": item.get("author") or "",
                }
            )
        return {"executorSource": "hn-readonly", "items": items}

    if source == "github":
        owner, repo = parse_github_repo(entry.get("url", ""))
        if not owner or not repo:
            return {"executorSource": "github-repo-readonly", "items": []}
        payload = call_executor_tool(
            source="github-repo-readonly",
            group="repos",
            tool="getRepo",
            payload={
                "owner": owner,
                "repo": repo,
            },
        )
        items = [
            {
                "kind": "github",
                "full_name": payload.get("full_name") or f"{owner}/{repo}",
                "url": payload.get("html_url") or entry.get("url", ""),
                "description": payload.get("description") or "",
                "stars": payload.get("stargazers_count"),
                "forks": payload.get("forks_count"),
                "issues": payload.get("open_issues_count"),
                "language": payload.get("language") or "",
                "updated_at": str(payload.get("updated_at") or "")[:10],
            }
        ]
        return {"executorSource": "github-repo-readonly", "items": items}

    return {"executorSource": "", "items": []}


def parse_github_repo(url: str) -> tuple[str, str]:
    value = (url or "").strip().rstrip("/")
    if not value.startswith("https://github.com/"):
        return "", ""
    parts = value.split("/")
    if len(parts) < 5:
        return "", ""
    return parts[3], parts[4]


def render_entry(entry: dict, evidence: dict) -> list[str]:
    lines = [
        f"### {entry.get('name', 'Untitled')}",
        f"- 当前来源: {entry.get('source', 'N/A')}",
        f"- 当前优先级: {entry.get('priority', 'N/A')}",
        f"- 当前建议行动: {entry.get('action_suggested', 'N/A')}",
        f"- Executor evidence source: {evidence.get('executorSource') or 'unsupported'}",
    ]

    items = evidence.get("items") or []
    if not items:
        lines.append("- 补证据结果: （无返回结果）")
        return lines

    lines.append("- 补证据结果:")
    for item in items:
        if item.get("kind") == "crossref":
            lines.append(f"  - [Crossref] {item['title'][:100]} | {item.get('container') or 'N/A'} | {item.get('url') or 'N/A'}")
        elif item.get("kind") == "github":
            lines.append(
                "  - [GitHub] "
                f"{item['full_name']} | ⭐{item.get('stars')} | forks={item.get('forks')} | "
                f"issues={item.get('issues')} | lang={item.get('language') or 'N/A'} | "
                f"updated={item.get('updated_at') or 'N/A'} | {item.get('url') or 'N/A'}"
            )
        else:
            lines.append(f"  - [HN] {item['title'][:100]} | {item.get('author') or 'N/A'} | {item.get('url') or 'N/A'}")
    return lines


def build_markdown(entries: list[dict], max_results: int) -> str:
    rendered = []
    for entry in entries:
        evidence = fetch_entry_evidence(entry, max_results=max_results)
        rendered.append({"entry": entry, "evidence": evidence})
    return render_markdown_section(
        heading="P0/P1 Pending Radar 条目只读补证据（via executor）",
        items=rendered,
        render_item=lambda item: render_entry(item["entry"], item["evidence"]),
        empty_text="（无符合条件的 radar 条目）",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--radar-file", default=str(Path(__file__).resolve().parents[1] / "shared-context" / "tech-radar.json"))
    parser.add_argument("--priorities", default="P0,P1")
    parser.add_argument("--statuses", default="pending")
    parser.add_argument("--fallback-statuses", default="adopt,trial,assess")
    parser.add_argument("--max-entries", type=int, default=5)
    parser.add_argument("--max-results", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    priorities = {value.strip().upper() for value in args.priorities.split(",") if value.strip()}
    statuses = {value.strip().lower() for value in args.statuses.split(",") if value.strip()}
    fallback_statuses = {value.strip().lower() for value in args.fallback_statuses.split(",") if value.strip()}
    all_entries = load_entries(Path(args.radar_file))
    entries = filter_entries(all_entries, priorities, statuses, args.max_entries)
    selection_mode = "primary"
    if not entries and fallback_statuses:
        entries = filter_entries(all_entries, priorities, fallback_statuses, args.max_entries)
        selection_mode = "fallback" if entries else "empty"

    if args.json:
        payload = []
        for entry in entries:
            payload.append(
                {
                    "entry": entry,
                    "evidence": fetch_entry_evidence(entry, max_results=args.max_results),
                }
            )
        print(json.dumps({"selectionMode": selection_mode, "items": payload}, ensure_ascii=False, indent=2))
    else:
        if selection_mode == "fallback":
            print("\n## Radar 条目选择说明\n")
            print("当前 `pending` + P0/P1 + 支持 source 的条目为空，已回退到 `adopt/trial/assess` 中的高优先级条目做只读补证据。\n")
        print(build_markdown(entries, max_results=args.max_results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
