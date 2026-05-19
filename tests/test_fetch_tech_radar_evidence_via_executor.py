import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "fetch-tech-radar-evidence-via-executor.py"
SPEC = importlib.util.spec_from_file_location("fetch_tech_radar_evidence_via_executor", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_filter_entries_limits_to_supported_sources_and_priority():
    entries = [
        {"name": "A", "source": "arxiv", "priority": "P0", "status": "pending"},
        {"name": "B", "source": "hn", "priority": "P1", "status": "pending"},
        {"name": "C", "source": "github", "priority": "P1", "status": "pending"},
        {"name": "D", "source": "arxiv", "priority": "P2", "status": "pending"},
    ]

    filtered = MODULE.filter_entries(entries, {"P0", "P1"}, {"pending"}, 10)

    assert [entry["name"] for entry in filtered] == ["A", "B", "C"]


def test_render_entry_includes_executor_source_and_items():
    entry = {
        "name": "Memanto",
        "source": "arxiv",
        "priority": "P0",
        "action_suggested": "Deep read",
    }
    evidence = {
        "executorSource": "crossref-readonly",
        "items": [
            {
                "kind": "crossref",
                "title": "Memanto Published Version",
                "url": "https://doi.org/example",
                "container": "Journal",
            }
        ],
    }

    lines = MODULE.render_entry(entry, evidence)

    assert any("Executor evidence source: crossref-readonly" in line for line in lines)
    assert any("[Crossref] Memanto Published Version" in line for line in lines)


def test_filter_entries_can_fallback_to_ring_statuses():
    entries = [
        {"name": "A", "source": "arxiv", "priority": "P0", "status": "trial"},
        {"name": "B", "source": "hn", "priority": "P1", "status": "adopt"},
        {"name": "C", "source": "github", "priority": "P1", "status": "trial"},
    ]

    primary = MODULE.filter_entries(entries, {"P0", "P1"}, {"pending"}, 10)
    fallback = MODULE.filter_entries(entries, {"P0", "P1"}, {"adopt", "trial", "assess"}, 10)

    assert primary == []
    assert [entry["name"] for entry in fallback] == ["A", "B", "C"]


def test_parse_github_repo_extracts_owner_and_repo():
    owner, repo = MODULE.parse_github_repo("https://github.com/FrankHui/paragents")
    assert (owner, repo) == ("FrankHui", "paragents")


def test_render_entry_formats_github_evidence():
    entry = {
        "name": "paragents",
        "source": "github",
        "priority": "P1",
        "action_suggested": "Review source",
    }
    evidence = {
        "executorSource": "github-repo-readonly",
        "items": [
            {
                "kind": "github",
                "full_name": "FrankHui/paragents",
                "url": "https://github.com/FrankHui/paragents",
                "stars": 87,
                "forks": 3,
                "issues": 1,
                "language": "Python",
                "updated_at": "2026-05-18",
                "pushed_at": "2026-05-19",
                "default_branch": "main",
                "archived": False,
                "recent_commits": [
                    {
                        "sha": "abc1234",
                        "date": "2026-05-19",
                        "message": "Tighten runtime conflict checks",
                        "url": "https://github.com/FrankHui/paragents/commit/abc1234",
                    }
                ],
            }
        ],
    }

    lines = MODULE.render_entry(entry, evidence)

    assert any("Executor evidence source: github-repo-readonly" in line for line in lines)
    assert any("[GitHub] FrankHui/paragents" in line for line in lines)
    assert any("recent commit abc1234" in line for line in lines)


def test_filter_entries_keeps_source_coverage_for_priority_matches():
    entries = [
        {"name": "Arxiv A", "source": "arxiv", "priority": "P0", "status": "pending"},
        {"name": "Arxiv B", "source": "arxiv", "priority": "P1", "status": "pending"},
        {"name": "GitHub A", "source": "github", "priority": "P1", "status": "pending"},
        {"name": "HN A", "source": "hn", "priority": "P1", "status": "pending"},
    ]

    filtered = MODULE.filter_entries(entries, {"P0", "P1"}, {"pending"}, 3)

    assert [entry["name"] for entry in filtered] == ["Arxiv A", "GitHub A", "HN A"]


def test_filter_entries_exhausts_compact_sources_before_dense_arxiv_pool():
    entries = [
        {"name": "Tweet A", "source": "x/twitter", "priority": "P1", "status": "pending"},
        {"name": "Arxiv P0 A", "source": "arxiv", "priority": "P0", "status": "pending"},
        {"name": "Arxiv P0 B", "source": "arxiv", "priority": "P0", "status": "pending"},
        {"name": "Arxiv P0 C", "source": "arxiv", "priority": "P0", "status": "pending"},
        {"name": "GitHub P0", "source": "github", "priority": "P0", "status": "pending"},
        {"name": "GitHub P1", "source": "github", "priority": "P1", "status": "pending"},
    ]

    filtered = MODULE.filter_entries(entries, {"P0", "P1"}, {"pending"}, 6)

    assert [entry["name"] for entry in filtered] == [
        "Arxiv P0 A",
        "Arxiv P0 B",
        "Arxiv P0 C",
        "GitHub P0",
        "Tweet A",
        "GitHub P1",
    ]


def test_build_arxiv_queries_prioritizes_prefix_and_normalized_variants():
    queries = MODULE.build_arxiv_queries("Safe Bilevel Delegation (SBD): Runtime Delegation Safety")

    assert queries[0] == "Safe Bilevel Delegation (SBD): Runtime Delegation Safety"
    assert "Safe Bilevel Delegation (SBD)" in queries
    assert "Safe Bilevel Delegation" in queries


def test_score_crossref_candidate_rejects_keyword_only_false_positive():
    score = MODULE.score_crossref_candidate(
        "Memanto: Typed Semantic Memory with Information-Theoretic Retrieval",
        "Information-theoretic semantic multimedia indexing",
    )

    assert score < 0.5


def test_score_crossref_candidate_penalizes_missing_unique_prefix_anchor():
    score = MODULE.score_crossref_candidate(
        "RecursiveMAS: Recursive Multi-Agent Systems",
        "Towards the Specification of Recursive Multi-agent Systems Using Type Theory",
    )

    assert score < 0.5


def test_select_crossref_items_filters_low_confidence_hits_and_keeps_close_match():
    payloads = [
        {
            "message": {
                "items": [
                    {
                        "DOI": "10.1000/bad",
                        "title": ["Information-theoretic semantic multimedia indexing"],
                        "URL": "https://doi.org/10.1000/bad",
                        "container-title": ["Conference"],
                    },
                    {
                        "DOI": "10.1000/good",
                        "title": ["Memanto: Typed Semantic Memory with Information-Theoretic Retrieval"],
                        "URL": "https://doi.org/10.1000/good",
                        "container-title": ["arXiv"],
                    },
                ]
            }
        }
    ]

    items = MODULE.select_crossref_items(
        "Memanto: Typed Semantic Memory with Information-Theoretic Retrieval",
        payloads,
        max_results=3,
    )

    assert [item["doi"] for item in items] == ["10.1000/good"]


def test_select_crossref_items_dedupes_and_prefers_higher_score():
    payloads = [
        {
            "message": {
                "items": [
                    {
                        "DOI": "10.1000/demo",
                        "title": ["Safe Bilevel Delegation: Runtime Delegation Safety"],
                        "URL": "https://doi.org/10.1000/demo",
                        "container-title": ["Journal A"],
                    }
                ]
            }
        },
        {
            "message": {
                "items": [
                    {
                        "DOI": "10.1000/demo",
                        "title": ["Safe Bilevel Delegation (SBD): Runtime Delegation Safety"],
                        "URL": "https://doi.org/10.1000/demo",
                        "container-title": ["Journal B"],
                    }
                ]
            }
        },
    ]

    items = MODULE.select_crossref_items(
        "Safe Bilevel Delegation (SBD): Runtime Delegation Safety",
        payloads,
        max_results=3,
    )

    assert len(items) == 1
    assert items[0]["title"] == "Safe Bilevel Delegation (SBD): Runtime Delegation Safety"


def test_fetch_entry_evidence_tolerates_single_crossref_query_failure(monkeypatch):
    calls = []

    def fake_call_executor_tool(*, source, group, tool, payload):
        calls.append(payload["query"])
        if payload["query"] == "Memanto":
            raise RuntimeError("invalid executor JSON output")
        return {
            "message": {
                "items": [
                    {
                        "DOI": "10.1000/good",
                        "title": ["Memanto: Typed Semantic Memory with Information-Theoretic Retrieval"],
                        "URL": "https://doi.org/10.1000/good",
                        "container-title": ["arXiv"],
                    }
                ]
            }
        }

    monkeypatch.setattr(MODULE, "call_executor_tool", fake_call_executor_tool)

    evidence = MODULE.fetch_entry_evidence(
        {
            "name": "Memanto: Typed Semantic Memory with Information-Theoretic Retrieval",
            "source": "arxiv",
        },
        max_results=3,
    )

    assert calls == [
        "Memanto: Typed Semantic Memory with Information-Theoretic Retrieval",
        "Memanto",
    ]
    assert [item["doi"] for item in evidence["items"]] == ["10.1000/good"]


def test_fetch_entry_evidence_adds_recent_github_commit_activity(monkeypatch, tmp_path):
    monkeypatch.setenv("TECH_RADAR_EXECUTOR_CACHE_DIR", str(tmp_path / "cache"))
    def fake_call_executor_tool(*, source, group, tool, payload):
        assert source == "github-repo-readonly"
        assert group == "repos"
        if tool == "getRepo":
            return {
                "full_name": "dmae97/oh-my-kimichan",
                "html_url": "https://github.com/dmae97/oh-my-kimichan",
                "description": "multi-agent harness",
                "stargazers_count": 20,
                "forks_count": 2,
                "open_issues_count": 4,
                "language": "TypeScript",
                "updated_at": "2026-05-18T12:00:00Z",
                "pushed_at": "2026-05-19T08:00:00Z",
                "default_branch": "main",
                "archived": False,
            }
        if tool == "listRepoCommits":
            assert payload["per_page"] == 3
            return [
                {
                    "sha": "abc1234567",
                    "html_url": "https://github.com/dmae97/oh-my-kimichan/commit/abc1234",
                    "commit": {
                        "message": "Stabilize DAG planning checks\n\nMore detail",
                        "author": {"date": "2026-05-19T08:00:00Z"},
                    },
                }
            ]
        raise AssertionError(f"unexpected tool {tool}")

    monkeypatch.setattr(MODULE, "call_executor_tool", fake_call_executor_tool)

    evidence = MODULE.fetch_entry_evidence(
        {
            "name": "oh-my-kimichan",
            "source": "github",
            "url": "https://github.com/dmae97/oh-my-kimichan",
        },
        max_results=3,
    )

    item = evidence["items"][0]
    assert item["full_name"] == "dmae97/oh-my-kimichan"
    assert item["default_branch"] == "main"
    assert evidence["cacheStatus"] == "miss"
    assert item["recent_commits"] == [
        {
            "sha": "abc1234",
            "date": "2026-05-19",
            "message": "Stabilize DAG planning checks",
            "url": "https://github.com/dmae97/oh-my-kimichan/commit/abc1234",
        }
    ]


def test_fetch_entry_evidence_tolerates_github_commit_lookup_failure(monkeypatch, tmp_path):
    monkeypatch.setenv("TECH_RADAR_EXECUTOR_CACHE_DIR", str(tmp_path / "cache"))
    def fake_call_executor_tool(*, source, group, tool, payload):
        if tool == "getRepo":
            return {
                "full_name": "FrankHui/paragents",
                "html_url": "https://github.com/FrankHui/paragents",
                "stargazers_count": 87,
                "forks_count": 3,
                "open_issues_count": 1,
                "language": "Python",
                "updated_at": "2026-05-18T12:00:00Z",
                "pushed_at": "2026-05-19T08:00:00Z",
                "default_branch": "main",
                "archived": False,
            }
        if tool == "listRepoCommits":
            raise RuntimeError("executor call failed")
        raise AssertionError(f"unexpected tool {tool}")

    monkeypatch.setattr(MODULE, "call_executor_tool", fake_call_executor_tool)

    evidence = MODULE.fetch_entry_evidence(
        {
            "name": "paragents",
            "source": "github",
            "url": "https://github.com/FrankHui/paragents",
        },
        max_results=3,
    )

    assert evidence["items"][0]["recent_commits"] == []


def test_fetch_entry_evidence_uses_fresh_github_cache(monkeypatch, tmp_path):
    cache_root = tmp_path / "cache"
    monkeypatch.setenv("TECH_RADAR_EXECUTOR_CACHE_DIR", str(cache_root))
    monkeypatch.setenv("TECH_RADAR_GITHUB_CACHE_TTL_SECONDS", "3600")

    cached_item = {
        "kind": "github",
        "full_name": "FrankHui/paragents",
        "url": "https://github.com/FrankHui/paragents",
        "stars": 87,
        "forks": 3,
        "issues": 1,
        "language": "Python",
        "updated_at": "2026-05-18",
        "pushed_at": "2026-05-19",
        "default_branch": "main",
        "archived": False,
        "recent_commits": [],
    }
    cache_path = MODULE.github_cache_path("FrankHui", "paragents")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(
            {
                "owner": "FrankHui",
                "repo": "paragents",
                "fetchedAtEpoch": MODULE.time.time(),
                "item": cached_item,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    def fail_call_executor_tool(*, source, group, tool, payload):
        raise AssertionError("fresh cache should avoid executor calls")

    monkeypatch.setattr(MODULE, "call_executor_tool", fail_call_executor_tool)

    evidence = MODULE.fetch_entry_evidence(
        {
            "name": "paragents",
            "source": "github",
            "url": "https://github.com/FrankHui/paragents",
        },
        max_results=3,
    )

    assert evidence["cacheStatus"] == "hit"
    assert evidence["items"][0]["full_name"] == "FrankHui/paragents"


def test_fetch_entry_evidence_falls_back_to_stale_github_cache_on_error(monkeypatch, tmp_path):
    cache_root = tmp_path / "cache"
    monkeypatch.setenv("TECH_RADAR_EXECUTOR_CACHE_DIR", str(cache_root))
    monkeypatch.setenv("TECH_RADAR_GITHUB_CACHE_TTL_SECONDS", "1")

    cached_item = {
        "kind": "github",
        "full_name": "FrankHui/paragents",
        "url": "https://github.com/FrankHui/paragents",
        "stars": 87,
        "forks": 3,
        "issues": 1,
        "language": "Python",
        "updated_at": "2026-05-18",
        "pushed_at": "2026-05-19",
        "default_branch": "main",
        "archived": False,
        "recent_commits": [{"sha": "abc1234", "date": "2026-05-19", "message": "cached", "url": "https://example.com"}],
    }
    cache_path = MODULE.github_cache_path("FrankHui", "paragents")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(
            {
                "owner": "FrankHui",
                "repo": "paragents",
                "fetchedAtEpoch": MODULE.time.time() - 300,
                "item": cached_item,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    def fail_call_executor_tool(*, source, group, tool, payload):
        raise RuntimeError("rate limit")

    monkeypatch.setattr(MODULE, "call_executor_tool", fail_call_executor_tool)

    evidence = MODULE.fetch_entry_evidence(
        {
            "name": "paragents",
            "source": "github",
            "url": "https://github.com/FrankHui/paragents",
        },
        max_results=3,
    )

    assert evidence["cacheStatus"] == "fallback"
    assert evidence["items"][0]["recent_commits"][0]["message"] == "cached"


def test_fetch_entry_evidence_supports_x_syndication(monkeypatch):
    def fake_call_executor_tool(*, source, group, tool, payload):
        assert source == "x-syndication-readonly"
        assert group == "tweets"
        assert tool == "getTweetResult"
        assert payload["id"] == "2048669695344046090"
        return {
            "id_str": "2048669695344046090",
            "created_at": "2026-04-27T07:44:52.000Z",
            "lang": "en",
            "favorite_count": 1904,
            "text": "SOUL.md matters.",
            "user": {
                "name": "Garry Tan",
                "screen_name": "garrytan",
            },
        }

    monkeypatch.setattr(MODULE, "call_executor_tool", fake_call_executor_tool)

    evidence = MODULE.fetch_entry_evidence(
        {
            "name": "Agent Constitution Pattern",
            "source": "x/twitter",
            "url": "https://x.com/garrytan/status/2048669695344046090",
        },
        max_results=3,
    )

    item = evidence["items"][0]
    assert evidence["executorSource"] == "x-syndication-readonly"
    assert item["kind"] == "x"
    assert item["author_name"] == "Garry Tan"
    assert item["handle"] == "garrytan"
    assert item["text"] == "SOUL.md matters."
    assert item["posted_at"] == "2026-04-27"


def test_render_entry_formats_x_evidence():
    entry = {
        "name": "Agent Constitution Pattern",
        "source": "x/twitter",
        "priority": "P1",
        "action_suggested": "Review signal",
    }
    evidence = {
        "executorSource": "x-syndication-readonly",
        "items": [
            {
                "kind": "x",
                "author_name": "Garry Tan",
                "handle": "garrytan",
                "posted_at": "2026-04-27",
                "text": "SOUL.md matters.",
                "url": "https://twitter.com/garrytan/status/2048669695344046090",
                "favorite_count": 1904,
                "lang": "en",
            }
        ],
    }

    lines = MODULE.render_entry(entry, evidence)

    assert any("Executor evidence source: x-syndication-readonly" in line for line in lines)
    assert any("[X] Garry Tan @garrytan | 2026-04-27 | SOUL.md matters. | likes=1904 | lang=en" in line for line in lines)
