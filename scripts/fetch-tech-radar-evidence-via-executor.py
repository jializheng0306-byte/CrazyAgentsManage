#!/usr/bin/env python3
"""Fetch readonly evidence for high-priority pending tech-radar entries via executor."""

from __future__ import annotations

import argparse
from difflib import SequenceMatcher
import json
import os
import re
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from executor_readonly_helper import call_executor_tool, render_markdown_section


SUPPORTED_SOURCES = {"arxiv", "hn", "github", "x/twitter"}
COMPACT_FULL_COVERAGE_SOURCES = {"github", "hn", "x/twitter"}
COMPACT_FULL_COVERAGE_LIMIT = 2
DEFAULT_GITHUB_CACHE_TTL_SECONDS = 3600
STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "via",
    "with",
}


def github_cache_ttl_seconds() -> int:
    raw_value = os.environ.get("TECH_RADAR_GITHUB_CACHE_TTL_SECONDS", str(DEFAULT_GITHUB_CACHE_TTL_SECONDS))
    try:
        value = int(raw_value)
    except ValueError:
        return DEFAULT_GITHUB_CACHE_TTL_SECONDS
    return max(0, value)


def github_cache_path(owner: str, repo: str) -> Path:
    root = os.environ.get("TECH_RADAR_EXECUTOR_CACHE_DIR")
    if root:
        base = Path(root)
    else:
        base = Path.home() / ".hermes" / "cache" / "tech-radar-evidence"
    safe_name = re.sub(r"[^a-z0-9._-]+", "-", f"{owner.lower()}-{repo.lower()}")
    return base / "github" / f"{safe_name}.json"


def load_github_cache(owner: str, repo: str) -> tuple[dict | None, bool]:
    path = github_cache_path(owner, repo)
    if not path.exists():
        return None, False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, False

    item = payload.get("item")
    fetched_at = payload.get("fetchedAtEpoch")
    if not isinstance(item, dict) or not isinstance(fetched_at, (int, float)):
        return None, False

    is_fresh = (time.time() - float(fetched_at)) <= github_cache_ttl_seconds()
    return item, is_fresh


def save_github_cache(owner: str, repo: str, item: dict) -> None:
    path = github_cache_path(owner, repo)
    payload = {
        "owner": owner,
        "repo": repo,
        "fetchedAtEpoch": time.time(),
        "item": item,
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        return


def priority_rank(priority: str) -> int:
    value = str(priority or "").upper()
    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    return order.get(value, 99)


def normalize_title(value: str) -> str:
    text = str(value or "").lower()
    text = text.replace("≠", " not ")
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def title_tokens(value: str, *, drop_stopwords: bool = True) -> list[str]:
    tokens = normalize_title(value).split()
    if not drop_stopwords:
        return tokens
    return [token for token in tokens if token not in STOPWORDS]


def anchor_tokens(title: str) -> set[str]:
    full_tokens = title_tokens(title)
    if not full_tokens:
        return set()

    prefix = str(title or "").split(":", 1)[0].strip()
    prefix_tokens = title_tokens(prefix)
    if len(prefix_tokens) == 1:
        return set(prefix_tokens)
    if len(prefix_tokens) >= 3:
        return set(prefix_tokens)
    return set(full_tokens)


def unique_prefix_token(title: str) -> str:
    prefix = str(title or "").split(":", 1)[0].strip()
    prefix_tokens = title_tokens(prefix)
    if len(prefix_tokens) == 1 and len(prefix_tokens[0]) >= 5:
        return prefix_tokens[0]
    return ""


def build_arxiv_queries(title: str) -> list[str]:
    candidates = []
    seen = set()

    def add(value: str) -> None:
        cleaned = " ".join(str(value or "").split())
        if not cleaned:
            return
        marker = cleaned.lower()
        if marker in seen:
            return
        seen.add(marker)
        candidates.append(cleaned)

    raw_title = str(title or "").strip()
    add(raw_title)

    prefix = raw_title.split(":", 1)[0].strip()
    if prefix and prefix != raw_title:
        add(prefix)
        add(re.sub(r"\s*\([^)]*\)", "", prefix).strip())

    return candidates[:4]


def score_crossref_candidate(target_title: str, candidate_title: str) -> float:
    target_normalized = normalize_title(target_title)
    candidate_normalized = normalize_title(candidate_title)
    if not target_normalized or not candidate_normalized:
        return 0.0
    if target_normalized == candidate_normalized:
        return 1.0

    target_terms = set(title_tokens(target_title))
    candidate_terms = set(title_tokens(candidate_title))
    if not target_terms or not candidate_terms:
        return 0.0

    overlap = len(target_terms & candidate_terms) / len(target_terms)
    sequence = SequenceMatcher(None, target_normalized, candidate_normalized).ratio()

    anchors = anchor_tokens(target_title)
    anchor_overlap = 0.0
    if anchors:
        anchor_overlap = len(anchors & candidate_terms) / len(anchors)

    contains_bonus = 0.0
    if candidate_normalized in target_normalized or target_normalized in candidate_normalized:
        contains_bonus = 0.1

    score = min(1.0, overlap * 0.45 + sequence * 0.35 + anchor_overlap * 0.2 + contains_bonus)

    strict_prefix = unique_prefix_token(target_title)
    if strict_prefix and strict_prefix not in candidate_terms:
        score *= 0.35

    return score


def dedupe_crossref_candidates(candidates: list[dict]) -> list[dict]:
    best_by_key: dict[str, dict] = {}
    for candidate in candidates:
        title = candidate.get("title") or "Untitled"
        key = (
            str(candidate.get("doi") or "").lower()
            or str(candidate.get("url") or "").lower()
            or normalize_title(title)
        )
        previous = best_by_key.get(key)
        if previous is None or candidate.get("match_score", 0.0) > previous.get("match_score", 0.0):
            best_by_key[key] = candidate
    return list(best_by_key.values())


def select_crossref_items(entry_title: str, payloads: list[dict], max_results: int) -> list[dict]:
    scored = []
    for payload in payloads:
        for item in ((payload.get("message") or {}).get("items") or []):
            title_values = item.get("title") or []
            title = title_values[0] if title_values else "Untitled"
            score = score_crossref_candidate(entry_title, title)
            if score < 0.5:
                continue
            scored.append(
                {
                    "kind": "crossref",
                    "title": title,
                    "url": item.get("URL") or "",
                    "container": (item.get("container-title") or [""])[0],
                    "doi": item.get("DOI") or "",
                    "match_score": round(score, 3),
                }
            )

    ranked = sorted(
        dedupe_crossref_candidates(scored),
        key=lambda item: (-item.get("match_score", 0.0), item.get("title") or ""),
    )
    return ranked[:max_results]


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

    ranked_by_source = {
        source: sorted(items, key=lambda entry: (priority_rank(entry.get("priority")), entry["_index"]))
        for source, items in by_source.items()
    }

    combined: list[dict] = []
    selected_indexes: set[int] = set()

    def add_entry(entry: dict) -> None:
        if len(combined) >= max_entries:
            return
        index = entry["_index"]
        if index in selected_indexes:
            return
        combined.append(entry)
        selected_indexes.add(index)

    # Step 1: ensure at least one high-priority entry per supported source.
    leaders = [items[0] for items in ranked_by_source.values() if items]
    for entry in sorted(leaders, key=lambda item: (priority_rank(item.get("priority")), item["_index"])):
        add_entry(entry)

    # Step 2: fully cover compact non-paper sources before spending the rest on dense sources like arXiv.
    compact_remainder = []
    for source, items in ranked_by_source.items():
        if source not in COMPACT_FULL_COVERAGE_SOURCES or len(items) <= 1 or len(items) > COMPACT_FULL_COVERAGE_LIMIT:
            continue
        compact_remainder.extend(items[1:])
    for entry in sorted(compact_remainder, key=lambda item: (priority_rank(item.get("priority")), item["_index"])):
        add_entry(entry)

    # Step 3: fill remaining slots globally by priority and source order.
    for entry in sorted(filtered, key=lambda item: (priority_rank(item.get("priority")), item["_index"])):
        add_entry(entry)

    cleaned = []
    for entry in sorted(combined[:max_entries], key=lambda item: (priority_rank(item.get("priority")), item["_index"])):
        copy = dict(entry)
        copy.pop("_source", None)
        copy.pop("_index", None)
        cleaned.append(copy)
    return cleaned


def tweet_id_from_url(url: str) -> str:
    value = (url or "").strip().rstrip("/")
    match = re.search(r"/status/([0-9]+)", value)
    return match.group(1) if match else ""


def normalize_x_tweet(payload: dict, source_url: str) -> dict:
    user = payload.get("user") or {}
    return {
        "kind": "x",
        "author_name": str(user.get("name") or "").strip(),
        "handle": str(user.get("screen_name") or "").strip(),
        "posted_at": str(payload.get("created_at") or "")[:10],
        "text": " ".join(str(payload.get("text") or "").split()),
        "url": source_url,
        "favorite_count": payload.get("favorite_count"),
        "lang": str(payload.get("lang") or "").strip(),
    }


def fetch_entry_evidence(entry: dict, max_results: int) -> dict:
    source = str(entry.get("source", "")).lower()
    if source == "arxiv":
        payloads = []
        rows = min(max(max_results * 2, 4), 8)
        for query in build_arxiv_queries(entry.get("name", "")):
            try:
                payloads.append(
                    call_executor_tool(
                        source="crossref-readonly",
                        group="works",
                        tool="searchWorks",
                        payload={
                            "query": query,
                            "rows": rows,
                            "sort": "relevance",
                            "order": "desc",
                        },
                    )
                )
            except RuntimeError:
                continue
        return {
            "executorSource": "crossref-readonly",
            "items": select_crossref_items(entry.get("name", ""), payloads, max_results=max_results),
        }

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
        cached_item, cache_is_fresh = load_github_cache(owner, repo)
        if cached_item is not None and cache_is_fresh:
            return {
                "executorSource": "github-repo-readonly",
                "cacheStatus": "hit",
                "items": [cached_item],
            }
        try:
            payload = call_executor_tool(
                source="github-repo-readonly",
                group="repos",
                tool="getRepo",
                payload={
                    "owner": owner,
                    "repo": repo,
                },
            )
        except RuntimeError:
            if cached_item is not None:
                return {
                    "executorSource": "github-repo-readonly",
                    "cacheStatus": "fallback",
                    "items": [cached_item],
                }
            return {"executorSource": "github-repo-readonly", "items": []}

        recent_commits = []
        try:
            commit_payload = call_executor_tool(
                source="github-repo-readonly",
                group="repos",
                tool="listRepoCommits",
                payload={
                    "owner": owner,
                    "repo": repo,
                    "per_page": max(1, min(max_results, 3)),
                },
            )
        except RuntimeError:
            commit_payload = []

        for item in (commit_payload or [])[:max_results]:
            commit = item.get("commit") or {}
            author = commit.get("author") or {}
            recent_commits.append(
                {
                    "sha": str(item.get("sha") or "")[:7],
                    "message": str(commit.get("message") or "").splitlines()[0][:100],
                    "date": str(author.get("date") or "")[:10],
                    "url": item.get("html_url") or "",
                }
            )
        if not recent_commits and cached_item is not None:
            recent_commits = list(cached_item.get("recent_commits") or [])

        item = {
            "kind": "github",
            "full_name": payload.get("full_name") or f"{owner}/{repo}",
            "url": payload.get("html_url") or entry.get("url", ""),
            "description": payload.get("description") or "",
            "stars": payload.get("stargazers_count"),
            "forks": payload.get("forks_count"),
            "issues": payload.get("open_issues_count"),
            "language": payload.get("language") or "",
            "updated_at": str(payload.get("updated_at") or "")[:10],
            "pushed_at": str(payload.get("pushed_at") or "")[:10],
            "default_branch": payload.get("default_branch") or "",
            "archived": bool(payload.get("archived")),
            "recent_commits": recent_commits,
        }
        save_github_cache(owner, repo, item)
        return {"executorSource": "github-repo-readonly", "cacheStatus": "miss", "items": [item]}

    if source == "x/twitter":
        tweet_url = str(entry.get("url") or "").strip()
        tweet_id = tweet_id_from_url(tweet_url)
        if not tweet_id:
            return {"executorSource": "x-syndication-readonly", "items": []}
        try:
            payload = call_executor_tool(
                source="x-syndication-readonly",
                group="tweets",
                tool="getTweetResult",
                payload={
                    "id": tweet_id,
                    "token": 0,
                },
            )
        except RuntimeError:
            return {"executorSource": "x-syndication-readonly", "items": []}
        return {"executorSource": "x-syndication-readonly", "items": [normalize_x_tweet(payload, tweet_url)]}

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
    if evidence.get("cacheStatus"):
        lines.append(f"- Executor evidence cache: {evidence['cacheStatus']}")

    items = evidence.get("items") or []
    if not items:
        lines.append("- 补证据结果: （未找到可采纳结果）")
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
                f"updated={item.get('updated_at') or 'N/A'} | pushed={item.get('pushed_at') or 'N/A'} | "
                f"branch={item.get('default_branch') or 'N/A'} | archived={'yes' if item.get('archived') else 'no'} | "
                f"{item.get('url') or 'N/A'}"
            )
            for commit in item.get("recent_commits") or []:
                sha = commit.get("sha") or "unknown"
                date = commit.get("date") or "N/A"
                message = commit.get("message") or "No commit message"
                url = commit.get("url") or "N/A"
                lines.append(f"    - recent commit {sha} | {date} | {message} | {url}")
        elif item.get("kind") == "x":
            author_bits = []
            if item.get("author_name"):
                author_bits.append(item["author_name"])
            if item.get("handle"):
                author_bits.append(f"@{item['handle']}")
            author_label = " ".join(author_bits) or "N/A"
            lines.append(
                f"  - [X] {author_label} | {item.get('posted_at') or 'N/A'} | "
                f"{(item.get('text') or '无可解析正文')[:180]} | likes={item.get('favorite_count') if item.get('favorite_count') is not None else 'N/A'} | "
                f"lang={item.get('lang') or 'N/A'} | {item.get('url') or 'N/A'}"
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
    parser.add_argument("--max-entries", type=int, default=6)
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
