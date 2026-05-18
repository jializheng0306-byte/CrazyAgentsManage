import argparse
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parent.parent / "scripts" / "runtime" / "generate_hermes_handoff.py"
SPEC = importlib.util.spec_from_file_location("generate_hermes_handoff", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def make_args(**overrides):
    defaults = {
        "title": "Need operations review",
        "goal": "Review runtime and operations impact",
        "questions": "What operator view is still missing?",
        "artifacts": ["docs/codex-hermes-role-design.md"],
        "output": "",
        "candidate_id": "",
        "instance_id": "",
        "truth_limit": 3,
        "flowmind_base_url": "http://111.229.194.203:3301",
        "flowmind_api_key": "flowmind-dev-token",
        "skip_truth_read": False,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class GenerateHermesHandoffTests(unittest.TestCase):
    def test_fetch_truth_snapshot_prefers_candidate_endpoint(self):
        args = make_args(candidate_id="cand-123", instance_id="hermes-agent")
        calls = []

        def fake_request(base_url, api_key, path):
            calls.append((base_url, api_key, path))
            return {
                "success": True,
                "data": {
                    "candidateId": "cand-123",
                    "status": "approved",
                },
            }

        with patch.object(MODULE, "flowmind_json_request", side_effect=fake_request):
            snapshot = MODULE.fetch_truth_snapshot(args, {"candidate_id": "state-candidate"})

        self.assertEqual(snapshot["mode"], "candidate")
        self.assertEqual(snapshot["path"], "/api/bridge/truth/cand-123")
        self.assertEqual(
            calls,
            [("http://111.229.194.203:3301", "flowmind-dev-token", "/api/bridge/truth/cand-123")],
        )

    def test_render_packet_includes_semantic_context_and_latest_evidence(self):
        args = make_args(candidate_id="cand-123")
        state = {
            "phase": "closeout",
            "status": "in_progress",
            "summary": "C-1 implemented",
        }
        truth_snapshot = {
            "mode": "candidate",
            "path": "/api/bridge/truth/cand-123",
            "payload": {
                "candidateId": "cand-123",
                "status": "approved",
                "decisionMetadata": {
                    "confirmedAt": "2026-05-03T01:18:38.308Z",
                },
                "latestEvidence": {
                    "summary": "Crazy 验收已确认 Bitable 主表与时序图页面可用",
                    "evidenceClass": "EXTRACTED",
                    "evidenceSourceType": "OPERATOR_ACCEPTANCE",
                    "refs": [
                        "bitable:EpeXbhpF9a0s0wsh6axce9PknFg",
                        "timeline:http://47.99.217.1/timeline/",
                    ],
                },
                "semanticContext": {
                    "entries": [
                        {
                            "id": "flowmind.candidate",
                            "summary": "Candidate 是进入 FlowMind 治理链的候选对象。",
                        },
                        {
                            "id": "truth.read_surface",
                            "summary": "`approved` 与 `committed` 都属于当前 truth read surface。",
                        },
                    ],
                    "fieldMappings": [
                        {
                            "dslField": "evidence_class",
                            "runtimeField": "latestEvidence.evidenceClass",
                        },
                        {
                            "dslField": "evidence_source_type",
                            "runtimeField": "latestEvidence.evidenceSourceType",
                        },
                    ],
                    "consumerHints": [
                        "Treat approved and committed as readable truth on the current public read surface.",
                    ],
                },
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
                    "note": "Use the upstream projection directly.",
                    "evidenceRefs": [
                        "review:blocked-strong-001",
                        "candidate:blocked-strong-001",
                    ],
                    "missingFields": [],
                },
            },
        }

        packet = MODULE.render_packet(args, state, truth_snapshot)

        self.assertIn("## FlowMind Truth Read", packet)
        self.assertIn("Latest evidence: EXTRACTED / OPERATOR_ACCEPTANCE", packet)
        self.assertIn("flowmind.candidate: Candidate 是进入 FlowMind 治理链的候选对象。", packet)
        self.assertIn("evidence_class -> latestEvidence.evidenceClass", packet)
        self.assertIn(
            "Treat approved and committed as readable truth on the current public read surface.",
            packet,
        )
        self.assertIn("- Operational follow-up:", packet)
        self.assertIn("  - Follow-up kind: blocked", packet)
        self.assertIn("  - Next actor: local_operator", packet)
        self.assertIn("  - Note: Use the upstream projection directly.", packet)
        self.assertIn("  - Missing fields: (none)", packet)


if __name__ == "__main__":
    unittest.main()
