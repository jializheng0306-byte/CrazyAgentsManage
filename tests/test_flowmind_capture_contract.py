import importlib.util
import json
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


def test_build_record_from_radar_name_uses_real_radar_shape(tmp_path, monkeypatch):
    radar_file = tmp_path / "tech-radar.json"
    radar_file.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "name": "Sample",
                        "priority": "P1",
                        "impact_assessment": "impact",
                        "action_suggested": "action",
                        "source": "arxiv",
                        "url": "https://example.com",
                        "notes": "note",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(MODULE, "RADAR_FILE", radar_file)

    record = MODULE.build_record_from_radar_name("Sample")

    assert record["name"] == "Sample"
    assert record["priority"] == "P1"
    assert record["impact"] == "impact"
    assert record["action"] == "action"


def test_build_trace_check_url_uses_manage_proxy_for_ali_hermes_runtime():
    runtime = {
        "base_url": "http://111.229.194.203:3301",
        "server_id": "ali-hermes",
        "watcher_trace_base_url": "",
    }

    url = MODULE.build_trace_check_url(runtime, "candidate-123")

    assert url == "http://127.0.0.1/manage/api/promise-review/trace/candidate-123"


def test_build_trace_check_url_uses_bridge_trace_endpoint_outside_manage_proxy():
    runtime = {
        "base_url": "http://111.229.194.203:3301",
        "server_id": "tx-newhost",
        "watcher_trace_base_url": "",
    }

    url = MODULE.build_trace_check_url(runtime, "candidate-123")

    assert url == "http://111.229.194.203:3301/api/bridge/trace/candidate-123"


def test_build_trace_check_url_honors_explicit_watcher_base_url():
    runtime = {
        "base_url": "http://111.229.194.203:3301",
        "server_id": "ali-hermes",
        "watcher_trace_base_url": "http://47.99.217.1/manage",
    }

    url = MODULE.build_trace_check_url(runtime, "candidate-123")

    assert url == "http://47.99.217.1/manage/api/promise-review/trace/candidate-123"
