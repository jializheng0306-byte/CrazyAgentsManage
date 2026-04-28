# -*- coding: utf-8 -*-
"""
Unit tests for the Agent Factory and related modules.

Tests cover:
- AgentRole enum and role resolution
- Role toolset mapping
- Role prompt generation
- build_role_config output
- Delegate Tool delegation flow
- Shared Context Manager operations
- Task Orchestrator DAG execution
- Memory Loader layer loading
- Team Memory Manager CRUD
- Cron Jobs with team binding
"""

import json
import os
import tempfile
import time
import unittest
from pathlib import Path


class TestAgentRole(unittest.TestCase):
    """Tests for AgentRole enum and resolve_role function."""

    def test_role_values(self):
        from src.agent.agent_factory import AgentRole
        self.assertEqual(AgentRole.EXPERT.value, "expert")
        self.assertEqual(AgentRole.RESEARCH.value, "research")
        self.assertEqual(AgentRole.CODE.value, "code")
        self.assertEqual(AgentRole.OPS.value, "ops")
        self.assertEqual(AgentRole.CRON.value, "cron")
        self.assertEqual(AgentRole.TEAM.value, "team")
        self.assertEqual(AgentRole.COORDINATOR.value, "coordinator")

    def test_resolve_role_exact(self):
        from src.agent.agent_factory import AgentRole, resolve_role
        self.assertEqual(resolve_role("expert"), AgentRole.EXPERT)
        self.assertEqual(resolve_role("research"), AgentRole.RESEARCH)
        self.assertEqual(resolve_role("code"), AgentRole.CODE)
        self.assertEqual(resolve_role("ops"), AgentRole.OPS)
        self.assertEqual(resolve_role("cron"), AgentRole.CRON)
        self.assertEqual(resolve_role("team"), AgentRole.TEAM)

    def test_resolve_role_aliases(self):
        from src.agent.agent_factory import AgentRole, resolve_role
        self.assertEqual(resolve_role("researcher"), AgentRole.RESEARCH)
        self.assertEqual(resolve_role("developer"), AgentRole.CODE)
        self.assertEqual(resolve_role("dev"), AgentRole.CODE)
        self.assertEqual(resolve_role("operations"), AgentRole.OPS)

    def test_resolve_role_chinese_aliases(self):
        from src.agent.agent_factory import AgentRole, resolve_role
        self.assertEqual(resolve_role("运维"), AgentRole.OPS)
        self.assertEqual(resolve_role("定时"), AgentRole.CRON)
        self.assertEqual(resolve_role("专家"), AgentRole.EXPERT)
        self.assertEqual(resolve_role("研究"), AgentRole.RESEARCH)
        self.assertEqual(resolve_role("编程"), AgentRole.CODE)
        self.assertEqual(resolve_role("团队"), AgentRole.TEAM)

    def test_resolve_role_case_insensitive(self):
        from src.agent.agent_factory import AgentRole, resolve_role
        self.assertEqual(resolve_role("EXPERT"), AgentRole.EXPERT)
        self.assertEqual(resolve_role("Research"), AgentRole.RESEARCH)

    def test_resolve_role_unknown_defaults_to_expert(self):
        from src.agent.agent_factory import AgentRole, resolve_role
        self.assertEqual(resolve_role("unknown_role"), AgentRole.EXPERT)


class TestRoleToolsets(unittest.TestCase):
    """Tests for role toolset mapping."""

    def test_expert_toolsets(self):
        from src.agent.agent_factory import AgentRole, get_role_toolsets
        toolsets = get_role_toolsets(AgentRole.EXPERT)
        self.assertIn("terminal", toolsets)
        self.assertIn("file", toolsets)
        self.assertIn("web", toolsets)

    def test_research_toolsets(self):
        from src.agent.agent_factory import AgentRole, get_role_toolsets
        toolsets = get_role_toolsets(AgentRole.RESEARCH)
        self.assertIn("web", toolsets)
        self.assertIn("file", toolsets)
        self.assertNotIn("terminal", toolsets)

    def test_cron_toolsets(self):
        from src.agent.agent_factory import AgentRole, get_role_toolsets
        toolsets = get_role_toolsets(AgentRole.CRON)
        self.assertIn("terminal", toolsets)
        self.assertIn("file", toolsets)
        self.assertIn("web", toolsets)
        self.assertIn("memory", toolsets)

    def test_team_toolsets(self):
        from src.agent.agent_factory import AgentRole, get_role_toolsets
        toolsets = get_role_toolsets(AgentRole.TEAM)
        self.assertIn("file", toolsets)
        self.assertIn("memory", toolsets)


class TestRolePrompt(unittest.TestCase):
    """Tests for role prompt generation."""

    def test_prompt_contains_goal(self):
        from src.agent.agent_factory import AgentRole, get_role_prompt
        prompt = get_role_prompt(AgentRole.EXPERT, "Analyze the codebase")
        self.assertIn("Analyze the codebase", prompt)

    def test_prompt_contains_context(self):
        from src.agent.agent_factory import AgentRole, get_role_prompt
        prompt = get_role_prompt(AgentRole.RESEARCH, "Find docs", context="Python project")
        self.assertIn("Python project", prompt)

    def test_prompt_without_context(self):
        from src.agent.agent_factory import AgentRole, get_role_prompt
        prompt = get_role_prompt(AgentRole.CODE, "Write tests")
        self.assertIn("Write tests", prompt)
        self.assertNotIn("CONTEXT:", prompt)


class TestBuildRoleConfig(unittest.TestCase):
    """Tests for build_role_config function."""

    def test_basic_config(self):
        from src.agent.agent_factory import AgentRole, build_role_config
        config = build_role_config(AgentRole.EXPERT, "Debug issue")
        self.assertEqual(config["role"], "expert")
        self.assertEqual(config["goal"], "Debug issue")
        self.assertIn("toolsets", config)
        self.assertIn("system_prompt", config)

    def test_blocked_toolsets_stripped(self):
        from src.agent.agent_factory import AgentRole, build_role_config
        config = build_role_config(
            AgentRole.EXPERT,
            "Test",
            override_toolsets=["terminal", "file", "delegation", "memory"],
        )
        self.assertNotIn("delegation", config["toolsets"])
        self.assertNotIn("memory", config["toolsets"])
        self.assertIn("terminal", config["toolsets"])

    def test_override_model(self):
        from src.agent.agent_factory import AgentRole, build_role_config
        config = build_role_config(
            AgentRole.CODE, "Code", override_model="gpt-4"
        )
        self.assertEqual(config["model"], "gpt-4")


class TestAvailableRoles(unittest.TestCase):
    """Tests for available_roles function."""

    def test_coordinator_excluded(self):
        from src.agent.agent_factory import available_roles
        roles = available_roles()
        role_names = [r["name"] for r in roles]
        self.assertNotIn("coordinator", role_names)

    def test_all_roles_have_description(self):
        from src.agent.agent_factory import available_roles
        roles = available_roles()
        for role in roles:
            self.assertTrue(role["description"])
            self.assertTrue(role["toolsets"])


class TestSharedContextManager(unittest.TestCase):
    """Tests for SharedContextManager."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from src.agent.shared_context import SharedContextManager
        self.manager = SharedContextManager(base_dir=Path(self.tmpdir))

    def test_init_task_context(self):
        path = self.manager.init_task_context("task-001", "Initial context")
        self.assertTrue(path.exists())
        self.assertEqual(path.read_text(encoding="utf-8"), "Initial context")

    def test_write_task_output(self):
        path = self.manager.write_task_output("task-001", "Task completed")
        self.assertTrue(path.exists())
        self.assertEqual(path.read_text(encoding="utf-8"), "Task completed")

    def test_append_task_output(self):
        self.manager.write_task_output("task-001", "Line 1\n")
        self.manager.append_task_output("task-001", "Line 2\n")
        content = self.manager.read_task_output("task-001")
        self.assertIn("Line 1", content)
        self.assertIn("Line 2", content)

    def test_active_task(self):
        self.manager.set_active_task("task-001")
        active = self.manager.get_active_task()
        self.assertEqual(active, "task-001")
        self.manager.clear_active_task()
        self.assertIsNone(self.manager.get_active_task())

    def test_dependency_context(self):
        self.manager.write_task_output("task-001", "Research result A")
        self.manager.write_task_output("task-002", "Research result B")
        ctx = self.manager.get_context_for_dependent_task(
            "task-003", ["task-001", "task-002"]
        )
        self.assertIn("Research result A", ctx)
        self.assertIn("Research result B", ctx)


class TestTaskOrchestrator(unittest.TestCase):
    """Tests for TaskOrchestrator and TaskGraph."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from src.agent.task_orchestrator import TaskOrchestrator
        self.orchestrator = TaskOrchestrator(shared_context_dir=Path(self.tmpdir))

    def test_create_task(self):
        from src.agent.agent_factory import AgentRole
        task = self.orchestrator.create_task(
            goal="Research topic", role=AgentRole.RESEARCH
        )
        self.assertTrue(task.id.startswith("task-"))
        self.assertEqual(task.goal, "Research topic")
        self.assertEqual(task.role, AgentRole.RESEARCH)

    def test_task_graph_dag(self):
        from src.agent.agent_factory import AgentRole
        from src.agent.task_orchestrator import TaskState

        t1 = self.orchestrator.create_task("Research A", AgentRole.RESEARCH)
        t2 = self.orchestrator.create_task("Research B", AgentRole.RESEARCH)
        t3 = self.orchestrator.create_task("Code", AgentRole.CODE, dependencies=[t1.id, t2.id])

        self.orchestrator.graph.add_dependency(t1.id, t3.id)
        self.orchestrator.graph.add_dependency(t2.id, t3.id)

        ready = self.orchestrator.graph.get_ready_tasks()
        ready_ids = [t.id for t in ready]
        self.assertIn(t1.id, ready_ids)
        self.assertIn(t2.id, ready_ids)
        self.assertNotIn(t3.id, ready_ids)

    def test_execute_all(self):
        from src.agent.agent_factory import AgentRole
        from src.agent.task_orchestrator import TaskState

        results = {}

        def executor(task):
            results[task.id] = f"Result for {task.goal}"
            return results[task.id]

        self.orchestrator.set_executor(executor)
        self.orchestrator.create_task("Task 1", AgentRole.EXPERT)
        self.orchestrator.create_task("Task 2", AgentRole.RESEARCH)

        output = self.orchestrator.execute_all()
        self.assertTrue(self.orchestrator.graph.is_complete())


class TestTeamMemoryManager(unittest.TestCase):
    """Tests for TeamMemoryManager."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from src.memory.team_memory import TeamMemoryManager
        self.manager = TeamMemoryManager(base_dir=Path(self.tmpdir))

    def test_default_team_created(self):
        teams = self.manager.list_teams()
        team_names = [t["name"] for t in teams]
        self.assertIn("default", team_names)

    def test_create_and_get_team(self):
        self.manager._ensure_team("test-team")
        team = self.manager.get_team("test-team")
        self.assertIsNotNone(team)
        self.assertEqual(team["name"], "test-team")

    def test_role_memory(self):
        self.manager.create_role_memory("test-team", "pm", "PM experience")
        content = self.manager.get_role_memory("test-team", "pm")
        self.assertIsNotNone(content)
        self.assertIn("PM experience", content)

    def test_append_team_memory(self):
        self.manager._ensure_team("test-team")
        self.manager.append_to_team_memory("test-team", "New update")
        team = self.manager.get_team("test-team")
        self.assertIn("New update", team["memory"])

    def test_delete_team(self):
        self.manager._ensure_team("deletable-team")
        result = self.manager.delete_team("deletable-team")
        self.assertTrue(result)
        self.assertIsNone(self.manager.get_team("deletable-team"))

    def test_cannot_delete_default(self):
        result = self.manager.delete_team("default")
        self.assertFalse(result)


class TestMemoryLoader(unittest.TestCase):
    """Tests for MemoryLoader."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from src.memory.memory_loader import MemoryLoader
        self.loader = MemoryLoader(hermes_home=Path(self.tmpdir))

    def test_load_identity_empty(self):
        content = self.loader.load_identity()
        self.assertEqual(content, "")

    def test_load_identity_with_content(self):
        identity_file = Path(self.tmpdir) / "identity.md"
        identity_file.write_text("I am a helpful assistant", encoding="utf-8")
        content = self.loader.load_identity()
        self.assertIn("helpful assistant", content)

    def test_load_references(self):
        ref_dir = Path(self.tmpdir) / "references"
        ref_dir.mkdir(exist_ok=True)
        (ref_dir / "api.md").write_text("API documentation", encoding="utf-8")
        content = self.loader.load_references()
        self.assertIn("API documentation", content)

    def test_load_all_layers(self):
        identity_file = Path(self.tmpdir) / "identity.md"
        identity_file.write_text("Identity content", encoding="utf-8")
        result = self.loader.load_all()
        self.assertIn("L5_identity", result)
        self.assertIn("Identity content", result["L5_identity"])


class TestSelfImprovementLoop(unittest.TestCase):
    """Tests for SelfImprovementLoop."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from src.memory.memory_improvement import SelfImprovementLoop, SessionResult
        self.loop = SelfImprovementLoop(hermes_home=Path(self.tmpdir))

    def test_extract_pattern(self):
        from src.memory.memory_improvement import SessionResult
        result = SessionResult(
            session_id="s-001",
            success=True,
            goal="Debug memory leak",
            role="expert",
            output="Found and fixed the leak",
            duration=120.0,
        )
        files = self.loop.on_session_end(result)
        self.assertTrue(len(files) > 0)
        self.assertTrue(files[0].exists())
        content = files[0].read_text(encoding="utf-8")
        self.assertIn("Success Pattern", content)

    def test_extract_lesson(self):
        from src.memory.memory_improvement import SessionResult
        result = SessionResult(
            session_id="s-002",
            success=False,
            goal="Deploy to production",
            role="ops",
            error="Connection timeout",
            duration=60.0,
        )
        files = self.loop.on_session_end(result)
        self.assertTrue(len(files) > 0)
        content = files[0].read_text(encoding="utf-8")
        self.assertIn("Failure Lesson", content)


class TestCronJobs(unittest.TestCase):
    """Tests for Cron Jobs with team binding."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        os.environ["HERMES_HOME"] = self.tmpdir

    def tearDown(self):
        if "HERMES_HOME" in os.environ:
            del os.environ["HERMES_HOME"]

    def test_create_job(self):
        from cron.jobs import create_job
        job = create_job(
            prompt="Daily report",
            schedule="0 9 * * *",
            name="daily-report",
            team="engineering",
        )
        self.assertEqual(job["name"], "daily-report")
        self.assertEqual(job["team"], "engineering")
        self.assertTrue(job["sediment_to_team"])

    def test_list_jobs(self):
        from cron.jobs import create_job, list_jobs
        create_job("Task 1", "0 * * * *", team="team-a")
        create_job("Task 2", "0 0 * * *", team="team-b")
        all_jobs = list_jobs()
        self.assertEqual(len(all_jobs), 2)
        team_a_jobs = list_jobs(team="team-a")
        self.assertEqual(len(team_a_jobs), 1)

    def test_pause_resume(self):
        from cron.jobs import create_job, pause_job, resume_job
        job = create_job("Test", "0 * * * *")
        paused = pause_job(job["id"])
        self.assertFalse(paused["enabled"])
        resumed = resume_job(job["id"])
        self.assertTrue(resumed["enabled"])

    def test_delete_job(self):
        from cron.jobs import create_job, remove_job
        job = create_job("Delete me", "0 * * * *")
        self.assertTrue(remove_job(job["id"]))
        self.assertFalse(remove_job(job["id"]))


class TestHermesStateDB(unittest.TestCase):
    """Tests for HermesStateDB tasks table."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from hermes_state import HermesStateDB
        self.db = HermesStateDB(db_path=Path(self.tmpdir) / "test_state.db")

    def test_create_and_get_task(self):
        task = self.db.create_task(
            task_id="task-001",
            goal="Test task",
            role="expert",
            team="default",
        )
        self.assertEqual(task["id"], "task-001")
        self.assertEqual(task["state"], "pending")
        self.assertEqual(task["goal"], "Test task")

    def test_update_task_state(self):
        self.db.create_task("task-002", "Running task", "code")
        self.db.update_task_state("task-002", "running")
        task = self.db.get_task("task-002")
        self.assertEqual(task["state"], "running")
        self.assertGreater(task["started_at"], 0)

    def test_list_tasks(self):
        self.db.create_task("task-003", "Task A", "expert")
        self.db.create_task("task-004", "Task B", "research")
        tasks = self.db.list_tasks()
        self.assertEqual(len(tasks), 2)

    def test_task_stats(self):
        self.db.create_task("task-005", "Task", "expert")
        self.db.create_task("task-006", "Task", "research")
        self.db.update_task_state("task-005", "running")
        stats = self.db.get_task_stats()
        self.assertEqual(stats["pending"], 1)
        self.assertEqual(stats["running"], 1)


if __name__ == "__main__":
    unittest.main()
