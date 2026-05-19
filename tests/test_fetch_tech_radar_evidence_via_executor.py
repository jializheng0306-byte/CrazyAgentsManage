import importlib.util
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
            }
        ],
    }

    lines = MODULE.render_entry(entry, evidence)

    assert any("Executor evidence source: github-repo-readonly" in line for line in lines)
    assert any("[GitHub] FrankHui/paragents" in line for line in lines)


def test_filter_entries_keeps_source_coverage_for_priority_matches():
    entries = [
        {"name": "Arxiv A", "source": "arxiv", "priority": "P0", "status": "pending"},
        {"name": "Arxiv B", "source": "arxiv", "priority": "P1", "status": "pending"},
        {"name": "GitHub A", "source": "github", "priority": "P1", "status": "pending"},
        {"name": "HN A", "source": "hn", "priority": "P1", "status": "pending"},
    ]

    filtered = MODULE.filter_entries(entries, {"P0", "P1"}, {"pending"}, 3)

    assert [entry["name"] for entry in filtered] == ["Arxiv A", "GitHub A", "HN A"]


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
