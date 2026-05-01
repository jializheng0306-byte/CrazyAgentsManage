import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent.parent / "scripts" / "flowmind_capture.py"
SPEC = importlib.util.spec_from_file_location("flowmind_capture", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_build_candidate_payload_matches_current_contract():
    runtime = {
        "control_plane_url": "http://111.229.194.203:3301",
        "public_url": "https://www.uncentury.cn",
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


def test_parse_bitable_list_records_supports_current_matrix_shape():
    payload = {
        "data": {
            "data": [
                ["001", ["已确认"], ["P1"], ["高价值"], ["推进"], ["twitter"], ["https://x.com"], ["未同步"], ["备注A"]],
                ["002", ["待确认"], ["P2"], ["一般"], ["观察"], ["rss"], [""], ["不需要"], ["备注B"]],
            ],
            "fields": ["序号", "状态", "优先级", "影响评估", "建议行动", "来源", "关联任务", "FlowMind同步", "备注"],
            "record_id_list": ["recA", "recB"],
        }
    }

    records = MODULE.parse_bitable_list_records(payload)

    assert records[0]["record_id"] == "recA"
    assert records[0]["status"] == "已确认"
    assert records[0]["priority"] == "P1"
    assert records[0]["flowmind_sync"] == "未同步"
    assert records[1]["record_id"] == "recB"
    assert records[1]["status"] == "待确认"


def test_get_response_payload_supports_wrapped_and_flattened_contracts():
    wrapped = {
        "success": True,
        "data": {
            "candidateId": "cand-1",
            "status": "draft",
        },
    }
    flattened = {
        "success": True,
        "candidateId": "cand-2",
        "status": "draft",
    }

    assert MODULE.get_response_payload(wrapped)["candidateId"] == "cand-1"
    assert MODULE.get_response_payload(flattened)["candidateId"] == "cand-2"
