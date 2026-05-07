import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent.parent / "scripts" / "task_watcher.py"
SPEC = importlib.util.spec_from_file_location("task_watcher", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_run_check_all_writes_status_and_heartbeat(tmp_path):
    target_file = tmp_path / "done.txt"
    target_file.write_text("ok", encoding="utf-8")

    watcher = MODULE.TaskWatcher(monitor_dir=tmp_path / "monitor")
    watcher.register_task(
        name="file-check",
        adapter="file",
        check_target=str(target_file),
        priority=MODULE.TaskPriority.P1,
        timeout_hours=1,
    )

    results = watcher.run_check_all()

    status = json.loads(watcher.status_file.read_text(encoding="utf-8"))
    heartbeat = json.loads(watcher.heartbeat_file.read_text(encoding="utf-8"))

    assert results["checked"] == 1
    assert results["completed"] == 1
    assert status["taskCounts"]["completed"] == 1
    assert status["tasks"][0]["status"] == "completed"
    assert heartbeat["ok"] is True
    assert heartbeat["completed"] == 1
