import importlib.util
import sys
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "runtime"
    / "ensure_x_publish_readonly_source.py"
)
SPEC = importlib.util.spec_from_file_location("ensure_x_publish_readonly_source", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_main_recreates_source_when_required_tool_missing(monkeypatch, tmp_path, capsys):
    spec_path = tmp_path / "x-openapi.json"
    spec_path.write_text("{}", encoding="utf-8")
    calls = []

    def fake_http_json(url, method="GET", data=None, timeout=30, attempts=4):
        calls.append((method, url, data))
        if url.endswith("/api/operations/integrations/sources") and method == "GET":
            return 200, [{"id": "x-syndication-readonly", "name": "X Syndication Readonly"}]
        if "api/operations/integrations/tools?sourceId=x-syndication-readonly" in url and method == "GET":
            return 200, [{"id": "x-syndication-readonly.tweets.otherTool", "name": "otherTool"}]
        if url.endswith("/api/operations/integrations/sources/x-syndication-readonly") and method == "DELETE":
            return 200, {"success": True}
        if url.endswith("/api/operations/integrations/sources") and method == "POST":
            return 201, {"id": "x-syndication-readonly", "name": "X Syndication Readonly"}
        raise AssertionError(f"unexpected request: {method} {url}")

    monkeypatch.setattr(MODULE, "http_json", fake_http_json)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ensure_x_publish_readonly_source.py",
            "--base-url",
            "http://crazy.example/manage",
            "--spec-path",
            str(spec_path),
            "--required-tool",
            "getTweetResult",
        ],
    )

    assert MODULE.main() == 0

    stdout = capsys.readouterr().out
    assert '"created": true' in stdout.lower()
    assert '"recreated": true' in stdout.lower()
    assert any(method == "DELETE" for method, _, _ in calls)
    assert any(method == "POST" for method, _, _ in calls)
