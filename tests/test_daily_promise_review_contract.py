import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "daily-promise-review.py"


def load_module():
    spec = importlib.util.spec_from_file_location("daily_promise_review", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DailyPromiseReviewContractTests(unittest.TestCase):
    def test_bitable_api_forces_explicit_lark_identity(self):
        module = load_module()
        calls = []

        def fake_run_json_cmd(args, timeout=30):
            calls.append((args, timeout))
            return {"ok": True}

        with patch.object(module, "run_json_cmd", side_effect=fake_run_json_cmd):
            result = module._bitable_api(
                "/open-apis/bitable/v1/apps/app/tables/tbl/records",
                method="GET",
                params={"page_size": 1},
            )

        self.assertEqual(result, {"ok": True})
        self.assertEqual(len(calls), 1)
        args, timeout = calls[0]
        self.assertEqual(timeout, 20)
        self.assertEqual(args[:4], [module.LARK_CLI, "api", "GET", "/open-apis/bitable/v1/apps/app/tables/tbl/records"])
        self.assertIn("--as", args)
        self.assertEqual(args[args.index("--as") + 1], module.LARK_IDENTITY)
        self.assertIn("--params", args)

    def test_send_to_feishu_forces_explicit_lark_identity(self):
        module = load_module()
        commands = []

        def fake_run_cmd(cmd, timeout=30):
            commands.append((cmd, timeout))
            return "{}", 0

        classified = {
            "total": 3,
            "in_progress": [],
            "completed": [],
            "overdue": [],
            "due_today": [],
            "due_soon": [],
            "blocked": [],
            "pending_count": 1,
        }
        sync_result = {"main_sync_count": 2, "trace_sync_count": 4}
        config = {
            "chat_id": "oc_test_chat",
            "bitable_url": "https://example.com/base",
            "bitable_main_table_id": "tbl_main",
        }

        with patch.object(module, "run_cmd", side_effect=fake_run_cmd):
            ok = module.send_to_feishu(classified, sync_result, config)

        self.assertTrue(ok)
        self.assertEqual(len(commands), 1)
        cmd, timeout = commands[0]
        self.assertEqual(timeout, 30)
        self.assertIn("im +messages-send", cmd)
        self.assertIn(f"--as {module.LARK_IDENTITY}", cmd)
        self.assertIn("--chat-id oc_test_chat", cmd)

    def test_review_state_skip_detects_same_digest(self):
        module = load_module()
        state_dir = Path(tempfile.mkdtemp(prefix="cam-review-state-"))
        state_path = state_dir / "state.json"
        payload = {
            "digest": "abc123",
            "checked_at": "2026-05-16T09:00:00+08:00",
            "snapshot": {"promise_count": 1},
        }
        module.persist_review_state(state_path, payload)
        self.assertTrue(module.should_skip_review(state_path, "abc123"))
        self.assertFalse(module.should_skip_review(state_path, "def456"))

    def test_build_review_state_changes_when_feedback_changes(self):
        module = load_module()
        promises = [
            {
                "id": "promise-1",
                "title": "Test promise",
                "status": "pending",
                "priority": "P1",
                "due_date": "2026-05-20",
            }
        ]
        classified = {
            "total": 1,
            "overdue": [],
            "due_today": [],
            "due_soon": [],
            "in_progress": [],
            "completed": [],
            "blocked": [],
            "pending_count": 1,
        }
        base_state = {
            "promise-1": {
                "truth_payload": {},
                "trace_events": [],
                "feedback_events": [],
                "feedback_summary": {
                    "latest_feedback_type": "",
                    "latest_feedback_summary": "",
                    "notes_text": "",
                },
                "trace_summary": {
                    "flowmind_status": "approved",
                    "trace_event_count": 1,
                    "last_trace_at": 123,
                    "last_trace_summary": "summary-a",
                },
                "operational_follow_up": {
                    "follow_up_kind": "",
                    "next_actor": "",
                    "needs_follow_up": "",
                    "last_governance_feedback": "",
                },
                "flowmind_candidate_id": "cand-1",
                "instance_id": "inst-1",
            }
        }
        changed_state = json.loads(json.dumps(base_state))
        changed_state["promise-1"]["feedback_summary"]["latest_feedback_type"] = "clarified"
        changed_state["promise-1"]["feedback_summary"]["latest_feedback_summary"] = "Need more detail"

        digest_a = module.build_review_state(promises, classified, base_state)["digest"]
        digest_b = module.build_review_state(promises, classified, changed_state)["digest"]
        self.assertNotEqual(digest_a, digest_b)

    def test_build_review_state_changes_when_operational_follow_up_changes(self):
        module = load_module()
        promises = [
            {
                "id": "promise-1",
                "title": "Test promise",
                "status": "pending",
                "priority": "P1",
                "due_date": "2026-05-20",
            }
        ]
        classified = {
            "total": 1,
            "overdue": [],
            "due_today": [],
            "due_soon": [],
            "in_progress": [],
            "completed": [],
            "blocked": [],
            "pending_count": 1,
        }
        base_state = {
            "promise-1": {
                "truth_payload": {},
                "trace_events": [],
                "feedback_events": [],
                "feedback_summary": {
                    "latest_feedback_type": "",
                    "latest_feedback_summary": "",
                    "notes_text": "",
                },
                "trace_summary": {
                    "flowmind_status": "approved",
                    "trace_event_count": 1,
                    "last_trace_at": 123,
                    "last_trace_summary": "summary-a",
                },
                "operational_follow_up": {
                    "follow_up_kind": "",
                    "next_actor": "",
                    "needs_follow_up": "",
                    "last_governance_feedback": "",
                },
                "flowmind_candidate_id": "cand-1",
                "instance_id": "inst-1",
            }
        }
        changed_state = json.loads(json.dumps(base_state))
        changed_state["promise-1"]["operational_follow_up"]["follow_up_kind"] = "blocked"
        changed_state["promise-1"]["operational_follow_up"]["next_actor"] = "local_operator"
        changed_state["promise-1"]["operational_follow_up"]["needs_follow_up"] = "true"
        changed_state["promise-1"]["operational_follow_up"]["last_governance_feedback"] = "blocked"

        digest_a = module.build_review_state(promises, classified, base_state)["digest"]
        digest_b = module.build_review_state(promises, classified, changed_state)["digest"]
        self.assertNotEqual(digest_a, digest_b)

    def test_normalize_operational_follow_up_reads_projection(self):
        module = load_module()
        result = module.normalize_operational_follow_up(
            {
                "success": True,
                "data": {
                    "operationalFollowUp": {
                        "projectionState": "resolved",
                        "flowmindStatus": "approved",
                        "lastGovernanceStatus": "approved",
                        "lastGovernanceFeedback": "blocked",
                        "localStatus": "blocked",
                        "needsFollowUp": True,
                        "followUpKind": "blocked",
                        "nextActor": "local_operator",
                        "isTerminalLocal": False,
                        "reason": "Ready replay sample with complete blocked follow-up context.",
                        "note": "Use upstream projection directly.",
                        "evidenceRefs": ["review:1", "candidate:1"],
                        "missingFields": [],
                    }
                },
            }
        )
        self.assertEqual(result["projection_state"], "resolved")
        self.assertEqual(result["follow_up_kind"], "blocked")
        self.assertEqual(result["next_actor"], "local_operator")
        self.assertEqual(result["needs_follow_up"], "true")
        self.assertEqual(result["last_governance_feedback"], "blocked")
        self.assertEqual(result["evidence_refs_text"], "review:1 | candidate:1")


if __name__ == "__main__":
    unittest.main()
