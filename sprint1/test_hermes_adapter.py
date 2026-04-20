"""
Tests for HermesAdapter -- Sprint 1 TDD.

Tests use a temporary directory with mock data files
to avoid depending on real hermes-agent state.
"""
import json
import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

from api.hermes_adapter import HermesAdapter


@pytest.fixture
def mock_hermes_home(tmp_path):
    home = tmp_path / "hermes"
    home.mkdir()
    (home / "cron").mkdir()
    (home / "memory").mkdir()
    (home / "skills").mkdir()
    return home


@pytest.fixture
def adapter_with_mock_db(mock_hermes_home):
    db_path = mock_hermes_home / "state.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE sessions (
            id TEXT PRIMARY KEY,
            source TEXT,
            user_id TEXT,
            model TEXT,
            title TEXT,
            system_prompt TEXT,
            parent_session_id TEXT,
            started_at REAL,
            ended_at REAL,
            end_reason TEXT,
            message_count INTEGER DEFAULT 0,
            tool_call_count INTEGER DEFAULT 0,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            cache_read_tokens INTEGER DEFAULT 0,
            cache_write_tokens INTEGER DEFAULT 0,
            reasoning_tokens INTEGER DEFAULT 0,
            billing_provider TEXT,
            billing_model TEXT,
            cost_usd REAL DEFAULT 0.0,
            estimated_cost_usd REAL DEFAULT 0.0
        )
    """)
    conn.execute("""
        CREATE TABLE messages (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            role TEXT,
            content TEXT,
            tool_call_id TEXT,
            tool_calls TEXT,
            tool_name TEXT,
            timestamp REAL,
            token_count INTEGER DEFAULT 0,
            finish_reason TEXT
        )
    """)
    conn.execute("""
        CREATE VIRTUAL TABLE messages_fts USING fts5(
            content, content=messages, content_rowid=rowid
        )
    """)
    conn.commit()
    conn.execute(
        "INSERT INTO sessions (id, source, model, title, started_at, message_count, input_tokens, output_tokens, cost_usd, billing_provider) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("s1", "cli", "gpt-4", "Test Session 1", 1000.0, 5, 100, 50, 0.01, "openai"),
    )
    conn.execute(
        "INSERT INTO sessions (id, source, model, title, started_at, parent_session_id, message_count, input_tokens, output_tokens, cost_usd, billing_provider) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("s2", "telegram", "claude-3", "Test Session 2", 2000.0, "s1", 3, 200, 100, 0.02, "anthropic"),
    )
    conn.execute(
        "INSERT INTO messages (id, session_id, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
        ("m1", "s1", "user", "Hello world", 1001.0),
    )
    conn.execute(
        "INSERT INTO messages (id, session_id, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
        ("m2", "s1", "assistant", "Hi there!", 1002.0),
    )
    conn.execute(
        "INSERT INTO messages (id, session_id, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
        ("m3", "s2", "user", "How are you?", 2001.0),
    )
    conn.commit()
    conn.close()
    return HermesAdapter(hermes_home=str(mock_hermes_home))


@pytest.fixture
def adapter_with_cron(mock_hermes_home):
    jobs_data = {
        "jobs": [
            {"id": "j1", "name": "Daily Summary", "enabled": True, "state": "scheduled"},
            {"id": "j2", "name": "Weekly Report", "enabled": False, "state": "paused"},
        ],
        "updated_at": "2026-04-21T09:00:00+08:00",
    }
    (mock_hermes_home / "cron" / "jobs.json").write_text(json.dumps(jobs_data), encoding="utf-8")
    return HermesAdapter(hermes_home=str(mock_hermes_home))


@pytest.fixture
def adapter_with_gateway(mock_hermes_home):
    gw_data = {
        "pid": 12345,
        "gateway_state": "running",
        "platforms": {
            "telegram": {"state": "connected", "updated_at": "2026-04-21T09:00:00+08:00"},
            "discord": {"state": "disconnected", "error_message": "Auth failed", "updated_at": "2026-04-21T08:00:00+08:00"},
        },
    }
    (mock_hermes_home / "gateway_state.json").write_text(json.dumps(gw_data), encoding="utf-8")
    return HermesAdapter(hermes_home=str(mock_hermes_home))


@pytest.fixture
def adapter_with_memory(mock_hermes_home):
    team_dir = mock_hermes_home / "memory" / "alpha-team"
    team_dir.mkdir(parents=True)
    shared_dir = team_dir / "shared"
    shared_dir.mkdir()
    (shared_dir / "guidelines.md").write_text("# Team Guidelines\nFollow these rules.", encoding="utf-8")
    role_dir = team_dir / "analyst"
    role_dir.mkdir()
    (role_dir / "notes.md").write_text("# Analyst Notes\nResearch findings.", encoding="utf-8")
    return HermesAdapter(hermes_home=str(mock_hermes_home))


@pytest.fixture
def adapter_with_skills(mock_hermes_home):
    skill_dir = mock_hermes_home / "skills" / "web-research"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Web Research\nSearch and analyze web content.", encoding="utf-8")
    skill_dir2 = mock_hermes_home / "skills" / "code-review"
    skill_dir2.mkdir(parents=True)
    (skill_dir2 / "SKILL.md").write_text("# Code Review\nReview code for quality.", encoding="utf-8")
    return HermesAdapter(hermes_home=str(mock_hermes_home))


# ── Session Stats Tests ─────────────────────────────────────────────────────

class TestSessionStats:
    def test_returns_zero_when_no_db(self, mock_hermes_home):
        a = HermesAdapter(hermes_home=str(mock_hermes_home))
        stats = a.get_session_stats()
        assert stats["total_sessions"] == 0
        assert stats["total_messages"] == 0
        assert stats["total_tokens"] == 0

    def test_returns_correct_counts(self, adapter_with_mock_db):
        stats = adapter_with_mock_db.get_session_stats()
        assert stats["total_sessions"] == 2
        assert stats["total_messages"] == 3
        assert stats["total_tokens"] == 450  # 100+50+200+100


class TestSessionsList:
    def test_returns_all_sessions(self, adapter_with_mock_db):
        sessions = adapter_with_mock_db.get_sessions_list()
        assert len(sessions) == 2

    def test_filters_by_source(self, adapter_with_mock_db):
        sessions = adapter_with_mock_db.get_sessions_list(source="cli")
        assert len(sessions) == 1
        assert sessions[0]["source"] == "cli"

    def test_respects_limit(self, adapter_with_mock_db):
        sessions = adapter_with_mock_db.get_sessions_list(limit=1)
        assert len(sessions) == 1


class TestSessionDetail:
    def test_returns_session_with_messages(self, adapter_with_mock_db):
        detail = adapter_with_mock_db.get_session_detail("s1")
        assert detail is not None
        assert detail["id"] == "s1"
        assert len(detail["messages"]) == 2

    def test_returns_none_for_unknown(self, adapter_with_mock_db):
        detail = adapter_with_mock_db.get_session_detail("nonexistent")
        assert detail is None


class TestSessionTree:
    def test_returns_tree_with_children(self, adapter_with_mock_db):
        tree = adapter_with_mock_db.get_session_tree("s1")
        assert "session" in tree
        assert "children" in tree
        assert len(tree["children"]) == 1
        assert tree["children"][0]["session"]["id"] == "s2"


class TestTokenStats:
    def test_returns_correct_totals(self, adapter_with_mock_db):
        stats = adapter_with_mock_db.get_token_stats()
        assert stats["total_input"] == 300
        assert stats["total_output"] == 150
        assert stats["total_cost"] == 0.03

    def test_returns_by_provider(self, adapter_with_mock_db):
        stats = adapter_with_mock_db.get_token_stats()
        assert len(stats["by_provider"]) == 2

    def test_returns_by_model(self, adapter_with_mock_db):
        stats = adapter_with_mock_db.get_token_stats()
        assert len(stats["by_model"]) == 2


# ── Cron Tests ───────────────────────────────────────────────────────────────

class TestCronJobs:
    def test_returns_empty_when_no_file(self, mock_hermes_home):
        a = HermesAdapter(hermes_home=str(mock_hermes_home))
        assert a.get_cron_jobs() == []

    def test_returns_jobs_list(self, adapter_with_cron):
        jobs = adapter_with_cron.get_cron_jobs()
        assert len(jobs) == 2
        assert jobs[0]["name"] == "Daily Summary"


# ── Gateway Tests ────────────────────────────────────────────────────────────

class TestGatewayStatus:
    def test_returns_unknown_when_no_file(self, mock_hermes_home):
        a = HermesAdapter(hermes_home=str(mock_hermes_home))
        status = a.get_gateway_status()
        assert status["gateway_state"] == "unknown"

    def test_returns_running_state(self, adapter_with_gateway):
        status = adapter_with_gateway.get_gateway_status()
        assert status["gateway_state"] == "running"
        assert "telegram" in status["platforms"]


# ── Memory Tests ─────────────────────────────────────────────────────────────

class TestMemoryTeams:
    def test_returns_empty_when_no_dir(self, mock_hermes_home):
        a = HermesAdapter(hermes_home=str(mock_hermes_home))
        assert a.get_teams() == []

    def test_returns_team_list(self, adapter_with_memory):
        teams = adapter_with_memory.get_teams()
        assert len(teams) == 1
        assert teams[0]["name"] == "alpha-team"
        assert "guidelines.md" in teams[0]["shared_files"]
        assert "analyst" in teams[0]["roles"]


class TestTeamMemory:
    def test_returns_team_content(self, adapter_with_memory):
        mem = adapter_with_memory.get_team_memory("alpha-team")
        assert mem is not None
        assert "guidelines.md" in mem["shared"]
        assert "analyst" in mem["roles"]
        assert "notes.md" in mem["roles"]["analyst"]

    def test_returns_none_for_unknown(self, adapter_with_memory):
        assert adapter_with_memory.get_team_memory("nonexistent") is None


# ── Skills Tests ─────────────────────────────────────────────────────────────

class TestSkillsList:
    def test_returns_empty_when_no_dir(self, mock_hermes_home):
        a = HermesAdapter(hermes_home=str(mock_hermes_home))
        assert a.get_skills_list() == []

    def test_returns_skills(self, adapter_with_skills):
        skills = adapter_with_skills.get_skills_list()
        assert len(skills) == 2
        names = [s["name"] for s in skills]
        assert "web-research" in names
        assert "code-review" in names


# ── Overview Stats Tests ─────────────────────────────────────────────────────

class TestOverviewStats:
    def test_aggregates_all_sources(self, mock_hermes_home):
        a = HermesAdapter(hermes_home=str(mock_hermes_home))
        stats = a.get_overview_stats()
        assert "sessions" in stats
        assert "cron_jobs" in stats
        assert "gateway" in stats
        assert "teams" in stats
        assert "skills" in stats
