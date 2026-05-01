#!/usr/bin/env python3
"""
Task Watcher 实现

基于《OpenClaw 实战》文章的 Task Callback Event Bus。
解决"Agent 说了会做但实际没做"的问题。

核心组件：
- Registry: 任务注册 (tasks.jsonl)
- Watcher: 定时轮询
- Adapters: 检查具体任务状态
- Policy: 决策通知/升级/重试
"""

import json
import os
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, List, Dict, Callable

SHARED_CONTEXT = Path(os.environ.get(
    "SHARED_CONTEXT_DIR",
    os.path.expanduser("~/CrazyAgentsManage/shared-context")
))
MONITOR_DIR = SHARED_CONTEXT / "monitor-tasks"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class TaskPriority(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


@dataclass
class MonitoredTask:
    task_id: str
    name: str
    adapter: str
    check_target: str
    priority: TaskPriority
    status: TaskStatus
    created_at: str
    updated_at: str
    deadline: Optional[str] = None
    timeout_hours: int = 6
    retry_count: int = 0
    max_retries: int = 3
    last_check: Optional[str] = None
    last_result: Optional[str] = None
    notification_sent: bool = False

    def to_line(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_line(cls, line: str) -> "MonitoredTask":
        data = json.loads(line)
        data["status"] = TaskStatus(data["status"])
        data["priority"] = TaskPriority(data["priority"])
        return cls(**data)


class FileAdapter:
    """文件存在性检查适配器"""

    @staticmethod
    def check(target: str) -> tuple:
        """检查文件是否存在且非空"""
        path = Path(target).expanduser()
        if path.exists() and path.stat().st_size > 0:
            return True, f"文件存在 ({path.stat().st_size} bytes)"
        elif path.exists():
            return False, "文件存在但为空"
        else:
            return False, "文件不存在"


class CronAdapter:
    """Cron 任务状态检查适配器"""

    @staticmethod
    def check(target: str) -> tuple:
        """检查 cron 日志是否有产出"""
        log_path = Path(target).expanduser()
        if not log_path.exists():
            return False, "日志文件不存在"
        content = log_path.read_text()
        if len(content.strip()) < 50:
            return False, f"日志过短 ({len(content)} chars)，可能零产出"
        if "error" in content.lower() or "fail" in content.lower():
            return False, "日志中包含错误关键词"
        return True, f"日志正常 ({len(content)} chars)"


class HttpAdapter:
    """HTTP 端点健康检查适配器"""

    @staticmethod
    def check(target: str) -> tuple:
        """检查 HTTP 端点是否可达"""
        try:
            result = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                 "--max-time", "10", target],
                capture_output=True, text=True, timeout=15
            )
            code = result.stdout.strip()
            if code.startswith("2"):
                return True, f"HTTP {code}"
            else:
                return False, f"HTTP {code}"
        except Exception as e:
            return False, str(e)


class GitAdapter:
    """Git PR/Commit 状态检查适配器"""

    @staticmethod
    def check(target: str) -> tuple:
        """检查 git 仓库是否有新提交"""
        repo_path = Path(target).expanduser()
        if not (repo_path / ".git").exists():
            return False, "不是 git 仓库"
        try:
            result = subprocess.run(
                ["git", "-C", str(repo_path), "log", "--oneline", "--since=24 hours ago"],
                capture_output=True, text=True, timeout=10
            )
            commits = result.stdout.strip()
            if commits:
                count = len(commits.split("\n"))
                return True, f"最近24小时有 {count} 个提交"
            else:
                return False, "最近24小时无提交"
        except Exception as e:
            return False, str(e)


# 适配器注册表
ADAPTERS = {
    "file": FileAdapter,
    "cron": CronAdapter,
    "http": HttpAdapter,
    "git": GitAdapter,
}


class TaskWatcher:
    """Task Watcher 管理器"""

    def __init__(self, monitor_dir: Optional[Path] = None):
        self.monitor_dir = monitor_dir or MONITOR_DIR
        self.monitor_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_file = self.monitor_dir / "tasks.jsonl"
        self.watcher_log = self.monitor_dir / "watcher.log"
        self.audit_log = self.monitor_dir / "audit.log"
        self.dlq_file = self.monitor_dir / "dlq.jsonl"
        self.status_file = self.monitor_dir / "watcher-status.json"
        self.heartbeat_file = self.monitor_dir / "watcher-heartbeat.json"

    def register_task(self, name: str, adapter: str, check_target: str,
                      priority: TaskPriority = TaskPriority.P1,
                      timeout_hours: int = 6) -> MonitoredTask:
        """注册一个需要监控的任务"""
        task_id = f"task-{datetime.now().strftime('%Y%m%d%H%M%S')}-{name[:20]}"
        now = datetime.now().isoformat()
        deadline = (datetime.now() + timedelta(hours=timeout_hours)).isoformat()

        task = MonitoredTask(
            task_id=task_id,
            name=name,
            adapter=adapter,
            check_target=check_target,
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
            deadline=deadline,
            timeout_hours=timeout_hours
        )

        with open(self.tasks_file, "a") as f:
            f.write(task.to_line() + "\n")

        self._audit(f"REGISTER {task_id}: {name} [{adapter}] target={check_target}")
        return task

    def check_task(self, task: MonitoredTask) -> MonitoredTask:
        """检查单个任务的状态"""
        adapter_class = ADAPTERS.get(task.adapter)
        if not adapter_class:
            task.status = TaskStatus.FAILED
            task.last_result = f"未知适配器: {task.adapter}"
            return task

        try:
            success, message = adapter_class.check(task.check_target)
            task.last_check = datetime.now().isoformat()
            task.last_result = message

            if success:
                task.status = TaskStatus.COMPLETED
                self._audit(f"CHECK {task.task_id}: COMPLETED — {message}")
            else:
                task.retry_count += 1
                if task.retry_count >= task.max_retries:
                    task.status = TaskStatus.FAILED
                    self._audit(f"CHECK {task.task_id}: FAILED after {task.retry_count} retries — {message}")
                else:
                    self._audit(f"CHECK {task.task_id}: RETRY {task.retry_count}/{task.max_retries} — {message}")

        except Exception as e:
            task.last_result = str(e)
            task.status = TaskStatus.FAILED
            self._audit(f"CHECK {task.task_id}: ERROR — {e}")

        task.updated_at = datetime.now().isoformat()
        return task

    def check_timeouts(self) -> List[MonitoredTask]:
        """检查超时的任务"""
        timed_out = []
        now = datetime.now()
        for task in self._load_tasks():
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED,
                               TaskStatus.TIMED_OUT):
                continue
            if task.deadline:
                deadline = datetime.fromisoformat(task.deadline)
                if now > deadline:
                    task.status = TaskStatus.TIMED_OUT
                    task.updated_at = now.isoformat()
                    timed_out.append(task)
                    self._audit(f"TIMEOUT {task.task_id}: {task.name}")
        return timed_out

    def run_check_all(self) -> Dict:
        """运行一次完整的检查"""
        results = {"checked": 0, "completed": 0, "failed": 0, "timed_out": 0}
        tasks = self._load_tasks()
        updated_tasks = []

        for task in tasks:
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED,
                               TaskStatus.TIMED_OUT):
                updated_tasks.append(task)
                continue

            task = self.check_task(task)
            results["checked"] += 1

            if task.status == TaskStatus.COMPLETED:
                results["completed"] += 1
            elif task.status == TaskStatus.FAILED:
                results["failed"] += 1
                self._move_to_dlq(task)

            updated_tasks.append(task)

        # Check timeouts
        timed_out = self.check_timeouts()
        results["timed_out"] = len(timed_out)

        # Save updated tasks
        self._save_tasks(updated_tasks)
        self._write_runtime_state(results, updated_tasks)

        self._log(f"Check complete: {json.dumps(results)}")
        return results

    def _load_tasks(self) -> List[MonitoredTask]:
        """加载所有任务"""
        if not self.tasks_file.exists():
            return []
        tasks = []
        for line in self.tasks_file.read_text().strip().split("\n"):
            if line.strip():
                tasks.append(MonitoredTask.from_line(line))
        return tasks

    def _save_tasks(self, tasks: List[MonitoredTask]):
        """保存所有任务"""
        with open(self.tasks_file, "w") as f:
            for task in tasks:
                f.write(task.to_line() + "\n")

    def _move_to_dlq(self, task: MonitoredTask):
        """移动到死信队列"""
        with open(self.dlq_file, "a") as f:
            f.write(task.to_line() + "\n")
        self._audit(f"DLQ {task.task_id}: moved to dead letter queue")

    def _write_runtime_state(self, results: Dict[str, int], tasks: List[MonitoredTask]):
        """写出机器可读状态，便于外部巡检确认 watcher 真的跑过"""
        now = datetime.now().isoformat()
        status_payload = {
            "checkedAt": now,
            "results": results,
            "taskCounts": {
                "total": len(tasks),
                "pending": sum(1 for task in tasks if task.status == TaskStatus.PENDING),
                "in_progress": sum(1 for task in tasks if task.status == TaskStatus.IN_PROGRESS),
                "completed": sum(1 for task in tasks if task.status == TaskStatus.COMPLETED),
                "failed": sum(1 for task in tasks if task.status == TaskStatus.FAILED),
                "timed_out": sum(1 for task in tasks if task.status == TaskStatus.TIMED_OUT),
            },
            "tasks": [
                {
                    "task_id": task.task_id,
                    "name": task.name,
                    "adapter": task.adapter,
                    "status": task.status.value,
                    "retry_count": task.retry_count,
                    "last_check": task.last_check,
                    "last_result": task.last_result,
                    "deadline": task.deadline,
                }
                for task in tasks
            ],
        }
        heartbeat_payload = {
            "lastRunAt": now,
            "ok": results["failed"] == 0 and results["timed_out"] == 0,
            "checked": results["checked"],
            "completed": results["completed"],
            "failed": results["failed"],
            "timed_out": results["timed_out"],
        }
        self.status_file.write_text(
            json.dumps(status_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self.heartbeat_file.write_text(
            json.dumps(heartbeat_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _audit(self, message: str):
        """写审计日志"""
        timestamp = datetime.now().isoformat()
        with open(self.audit_log, "a") as f:
            f.write(f"[{timestamp}] {message}\n")

    def _log(self, message: str):
        """写 watcher 日志"""
        timestamp = datetime.now().isoformat()
        with open(self.watcher_log, "a") as f:
            f.write(f"[{timestamp}] {message}\n")


if __name__ == "__main__":
    import sys

    watcher = TaskWatcher()

    if len(sys.argv) < 2:
        print("用法:")
        print("  python task_watcher.py register <name> <adapter> <target> [priority] [timeout_hours]")
        print("  python task_watcher.py check-all")
        print("  python task_watcher.py list")
        print("  python task_watcher.py timeouts")
        print("  python task_watcher.py status")
        print()
        print("适配器: file, cron, http, git")
        print("优先级: P0, P1, P2")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "register" and len(sys.argv) >= 5:
        name = sys.argv[2]
        adapter = sys.argv[3]
        target = sys.argv[4]
        priority = TaskPriority(sys.argv[5]) if len(sys.argv) > 5 else TaskPriority.P1
        timeout = int(sys.argv[6]) if len(sys.argv) > 6 else 6
        task = watcher.register_task(name, adapter, target, priority, timeout)
        print(f"✅ 已注册: {task.task_id}")

    elif cmd == "check-all":
        results = watcher.run_check_all()
        print(f"检查完成: {json.dumps(results, indent=2)}")

    elif cmd == "list":
        tasks = watcher._load_tasks()
        if tasks:
            for t in tasks:
                emoji = {"pending": "⏳", "in_progress": "🔄", "completed": "✅",
                         "failed": "❌", "timed_out": "⏰"}.get(t.status.value, "❓")
                print(f"  {emoji} {t.task_id}: {t.name} [{t.adapter}] {t.status.value}")
        else:
            print("  无监控任务")

    elif cmd == "timeouts":
        timed_out = watcher.check_timeouts()
        if timed_out:
            for t in timed_out:
                print(f"  ⏰ {t.task_id}: 超时! {t.name}")
        else:
            print("  无超时任务")

    elif cmd == "status":
        if watcher.status_file.exists():
            print(watcher.status_file.read_text())
        else:
            print("  watcher 尚未产出状态文件")
