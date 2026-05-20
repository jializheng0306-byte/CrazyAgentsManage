import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "flowmind-health-notify.py"
SPEC = importlib.util.spec_from_file_location("flowmind_health_notify", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_summarize_snapshot_for_abnormal_state():
    snapshot = {
        "status": "ABNORMAL",
        "checkedAt": "2026-05-20T00:00:00Z",
        "runId": "run-1",
        "failedChecks": [{"url": "/healthz", "status": 500, "ok": False}],
        "reviewQueue": {"ok": False, "pendingCount": 1, "pendingOperationalCount": 1, "pendingValidationCount": 0},
        "executorProbe": {"source": "flowmind-health-readonly", "status": "ok"},
    }

    summary = MODULE.summarize_snapshot(snapshot)

    assert "状态: ABNORMAL" in summary
    assert "/healthz: status=500, ok=False" in summary
    assert "Executor probe: flowmind-health-readonly status=ok" in summary


def test_build_post_payload_wraps_summary_for_feishu():
    snapshot = {
        "status": "ERROR",
        "message": "SSH连接超时",
    }

    payload = MODULE.build_post_payload(
        snapshot,
        chat_id="oc_test",
        at_user_id="ou_test",
        title="⚠️ FlowMind巡检异常",
    )

    assert payload["receive_id"] == "oc_test"
    content = json.loads(payload["content"])
    text = content["zh_cn"]["content"][0][1]["text"]
    assert "SSH连接超时" in text


def test_main_skips_ok_snapshot_without_force(monkeypatch, tmp_path, capsys):
    snapshot_path = tmp_path / "ok.json"
    snapshot_path.write_text(json.dumps({"status": "OK"}, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(MODULE, "parse_args", lambda: type("Args", (), {
        "snapshot": str(snapshot_path),
        "chat_id": "oc_test",
        "at_user_id": "ou_test",
        "title": "title",
        "dry_run": False,
        "force": False,
    })())

    assert MODULE.main() == 0
    output = json.loads(capsys.readouterr().out)
    assert output["skipped"] is True


def test_main_dry_run_outputs_payload(monkeypatch, tmp_path, capsys):
    snapshot_path = tmp_path / "abnormal.json"
    snapshot_path.write_text(json.dumps({"status": "ABNORMAL", "checkedAt": "2026-05-20T00:00:00Z"}, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(MODULE, "parse_args", lambda: type("Args", (), {
        "snapshot": str(snapshot_path),
        "chat_id": "oc_test",
        "at_user_id": "ou_test",
        "title": "title",
        "dry_run": True,
        "force": False,
    })())

    assert MODULE.main() == 0
    output = json.loads(capsys.readouterr().out)
    assert output["dryRun"] is True
    assert output["payload"]["receive_id"] == "oc_test"
