import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent.parent / "scripts" / "flowmind_capture.py"
SPEC = importlib.util.spec_from_file_location("flowmind_capture", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_build_candidate_payload_matches_current_contract():
    runtime = {
        "base_url": "http://111.229.194.203:3301",
        "api_key": "flowmind-dev-token",
        "instance_id": "crazyagentsmanage-intel-sentinel",
        "source_agent": "hermes",
        "server_id": "ali-hermes",
        "plugin_version": "crazyagentsmanage-link-v1",
        "route_id": "crazyagentsmanage-bitable-capture",
    }
    record = {
        "record_id": "rec_123",
        "name": "Agent Constitution Pattern",
        "priority": "P1",
        "impact": "适用于 HermesAgent 记忆分层",
        "action": "评估并拆成可执行任务",
        "source": "twitter",
        "url": "https://example.com/post",
        "notes": "test",
    }

    payload = MODULE.build_candidate_payload(record, runtime)

    assert payload["instanceId"] == "crazyagentsmanage-intel-sentinel"
    assert payload["sourceAgent"] == "hermes"
    assert payload["title"] == "Agent Constitution Pattern"
    assert isinstance(payload["rawText"], str)
    assert payload["rawText"]
    assert payload["confidence"] == 70
    assert payload["sourceContext"]["bitable_record_id"] == "rec_123"
    assert payload["sourceContext"]["route_id"] == "crazyagentsmanage-bitable-capture"


def test_priority_confidence_uses_percentage_scale():
    assert MODULE.priority_confidence("P0") == 85
    assert MODULE.priority_confidence("P1") == 70
    assert MODULE.priority_confidence("P2") == 55
