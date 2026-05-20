import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "flowmind-health-check.py"
SPEC = importlib.util.spec_from_file_location("flowmind_health_check", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_parse_latest_json_block_prefers_last_complete_block():
    text = """
=== 2026-05-19T20:00:00Z ===
{"passed": true, "runId": "old"}
=== 2026-05-19T21:00:00Z ===
{"passed": false, "runId": "new"}
""".strip()

    result = MODULE.parse_latest_json_block(text)

    assert result == {"passed": False, "runId": "new"}


def test_build_status_payload_reports_ok_only_when_operational_queue_is_clear():
    report = {
        "passed": True,
        "checkedAt": "2026-05-19T12:00:00Z",
        "runId": "run-1",
        "checks": [{"url": "/healthz", "ok": True, "elapsedMs": 50}],
        "reviewQueue": {
            "ok": True,
            "pendingCount": 2,
            "pendingOperationalCount": 0,
            "pendingValidationCount": 2,
        },
    }

    payload = MODULE.build_status_payload(report)

    assert payload["status"] == "OK"
    assert payload["reviewQueue"]["pendingValidationCount"] == 2


def test_build_status_payload_reports_abnormal_on_failed_checks():
    report = {
        "passed": False,
        "checkedAt": "2026-05-19T12:00:00Z",
        "runId": "run-2",
        "checks": [{"url": "/healthz", "ok": False, "status": 500, "elapsedMs": 120}],
        "reviewQueue": {
            "ok": False,
            "pendingCount": 1,
            "pendingOperationalCount": 1,
            "pendingValidationCount": 0,
            "groups": [{"sourceAgent": "hermes", "pendingCount": 1, "pendingOperationalCount": 1, "pendingValidationCount": 0}],
        },
    }

    payload = MODULE.build_status_payload(report)
    lines = MODULE.render_status_lines(payload)

    assert payload["status"] == "ABNORMAL"
    assert any("失败的检查项 (1):" in line for line in lines)
    assert any("Review Queue: ok=False, pending=1, pending_operational=1, pending_validation=0" in line for line in lines)
    assert any("Review Queue [hermes]" in line for line in lines)


def test_probe_executor_health_reports_ok(monkeypatch):
    def fake_call_executor_tool(*, source, group, tool, payload):
        assert source == "flowmind-health-readonly"
        if tool == "getHealthz":
            return {"status": "ok"}
        if tool == "getReadyz":
            return {"status": "ready", "checks": {"server": "ok", "database": "ok"}}
        raise AssertionError(f"unexpected tool {tool}")

    monkeypatch.setattr(MODULE, "call_executor_tool", fake_call_executor_tool)

    probe = MODULE.probe_executor_health("flowmind-health-readonly")

    assert probe["status"] == "ok"
    assert probe["healthz"]["status"] == "ok"
    assert probe["readyz"]["status"] == "ready"


def test_probe_executor_health_reports_unavailable(monkeypatch):
    def fail_call_executor_tool(*, source, group, tool, payload):
        raise RuntimeError("executor unavailable")

    monkeypatch.setattr(MODULE, "call_executor_tool", fail_call_executor_tool)

    probe = MODULE.probe_executor_health("flowmind-health-readonly")

    assert probe["status"] == "unavailable"
    assert "executor unavailable" in probe["error"]


def test_render_status_lines_includes_executor_probe_summary():
    payload = {
        "status": "OK",
        "checkedAt": "2026-05-20T00:00:00Z",
        "reviewQueue": {
            "pendingCount": 0,
            "pendingValidationCount": 0,
        },
    }

    lines = MODULE.render_status_lines(
        payload,
        {
            "source": "flowmind-health-readonly",
            "status": "ok",
            "healthz": {"status": "ok"},
            "readyz": {"status": "ready"},
        },
    )

    assert any("Executor probe: flowmind-health-readonly healthz=ok readyz=ready" in line for line in lines)


def test_write_snapshot_persists_json_payload(tmp_path):
    target = tmp_path / "state" / "flowmind-health-check-latest.json"
    payload = {"status": "ABNORMAL", "checkedAt": "2026-05-20T00:00:00Z"}

    MODULE.write_snapshot(str(target), payload)

    assert target.exists()
    assert target.read_text(encoding="utf-8").strip().startswith("{")
