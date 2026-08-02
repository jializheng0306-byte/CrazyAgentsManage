import importlib.util
import json
import subprocess
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "executor_readonly_helper.py"
SPEC = importlib.util.spec_from_file_location("executor_readonly_helper", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_resolve_executor_binary_prefers_env_override(tmp_path, monkeypatch):
    executor_bin = tmp_path / "executor"
    executor_bin.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executor_bin.chmod(0o755)

    monkeypatch.setenv("EXECUTOR_BIN", str(executor_bin))
    monkeypatch.delenv("CRAZY_EXECUTOR_BIN", raising=False)
    monkeypatch.setattr(MODULE.shutil, "which", lambda name: None)

    assert MODULE.resolve_executor_binary() == str(executor_bin)


def test_resolve_executor_binary_uses_npm_prefix(tmp_path, monkeypatch):
    prefix = tmp_path / "npm-prefix"
    executor_bin = prefix / "bin" / "executor"
    executor_bin.parent.mkdir(parents=True)
    executor_bin.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executor_bin.chmod(0o755)

    monkeypatch.delenv("EXECUTOR_BIN", raising=False)
    monkeypatch.delenv("CRAZY_EXECUTOR_BIN", raising=False)
    monkeypatch.setattr(MODULE.shutil, "which", lambda name: "/usr/bin/npm" if name == "npm" else None)

    def fake_run(cmd, capture_output=True, text=True, check=False):
        assert cmd == ["/usr/bin/npm", "prefix", "-g"]
        return subprocess.CompletedProcess(cmd, 0, stdout=f"{prefix}\n", stderr="")

    monkeypatch.setattr(MODULE.subprocess, "run", fake_run)

    assert MODULE.resolve_executor_binary() == str(executor_bin)


def test_call_executor_tool_uses_resolved_executor_binary(monkeypatch):
    calls = []

    monkeypatch.setattr(MODULE, "resolve_executor_binary", lambda: "/opt/executor/bin/executor")

    def fake_run(cmd, capture_output=True, text=True, check=False, timeout=None):
        calls.append(
            {
                "cmd": cmd,
                "capture_output": capture_output,
                "text": text,
                "check": check,
                "timeout": timeout,
            }
        )
        return subprocess.CompletedProcess(cmd, 0, stdout='{"status":"ok"}', stderr="")

    monkeypatch.setattr(MODULE.subprocess, "run", fake_run)

    result = MODULE.call_executor_tool(
        source="flowmind-health-readonly",
        group="health",
        tool="getReadyz",
        payload={"probe": True},
    )

    assert result == {"status": "ok"}
    assert calls == [
        {
            "cmd": [
                "/opt/executor/bin/executor",
                "call",
                "flowmind-health-readonly",
                "health",
                "getReadyz",
                json.dumps({"probe": True}, ensure_ascii=False),
            ],
            "capture_output": True,
            "text": True,
            "check": False,
            "timeout": 60,
        }
    ]
