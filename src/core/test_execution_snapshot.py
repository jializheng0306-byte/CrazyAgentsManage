"""
CAM-P0/P1 tests: 执行时配置快照 + Operations façade 只读投影

边界守卫：
- R13: 快照不含 owner 字段，不转移承诺 ownership
- append-only: 不可变
- CAM-P1: 只读投影，无写操作

@see CR-20260723-002
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.execution_snapshot import (
    capture_execution_snapshot,
    append_snapshot,
    load_snapshots,
    verify_snapshot,
)


class TestCaptureExecutionSnapshot(unittest.TestCase):
    """CAM-P0: 执行时配置快照"""

    def test_capture_returns_checksum_and_frozen_at(self):
        snap = capture_execution_snapshot(
            task_id="task-001",
            task_config={"action": "write", "target": "truth"},
            automation_state="approved-for-automation",
        )
        self.assertIn("checksum", snap)
        self.assertIn("frozen_at", snap)
        self.assertEqual(snap["task_id"], "task-001")
        self.assertEqual(snap["automation_state"], "approved-for-automation")

    def test_checksum_is_64_char_hex(self):
        snap = capture_execution_snapshot("t1", {}, "prototype")
        self.assertRegex(snap["checksum"], r"^[0-9a-f]{64}$")

    def test_same_config_produces_same_checksum_deterministic(self):
        cfg = {"action": "write"}
        s1 = capture_execution_snapshot("t1", cfg, "automated")
        s2 = capture_execution_snapshot("t1", cfg, "automated")
        self.assertEqual(s1["checksum"], s2["checksum"])

    def test_different_config_produces_different_checksum(self):
        s1 = capture_execution_snapshot("t1", {"a": 1}, "automated")
        s2 = capture_execution_snapshot("t1", {"a": 2}, "automated")
        self.assertNotEqual(s1["checksum"], s2["checksum"])

    def test_snapshot_does_not_contain_owner_r13(self):
        """R13: 不转移承诺 ownership — 快照不含 owner 字段"""
        snap = capture_execution_snapshot("t1", {}, "automated")
        self.assertNotIn("owner", snap)
        self.assertNotIn("commitment_owner", snap)

    def test_permission_and_duplicate_hooks_default_empty(self):
        snap = capture_execution_snapshot("t1", {}, "prototype")
        self.assertEqual(snap["permission_hooks"], [])
        self.assertEqual(snap["duplicate_hooks"], [])


class TestAppendSnapshot(unittest.TestCase):
    """CAM-P0: append-only 不可变存储"""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        )
        self.tmp.close()
        os.unlink(self.tmp.name)
        self.storage = self.tmp.name

    def tearDown(self):
        if os.path.exists(self.storage):
            os.unlink(self.storage)

    def test_append_and_load_roundtrip(self):
        snap = capture_execution_snapshot("t1", {"a": 1}, "automated")
        append_snapshot(snap, self.storage)
        loaded = load_snapshots(self.storage)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["task_id"], "t1")
        self.assertEqual(loaded[0]["checksum"], snap["checksum"])

    def test_append_only_multiple_snapshots(self):
        for i in range(3):
            snap = capture_execution_snapshot(f"t{i}", {"i": i}, "automated")
            append_snapshot(snap, self.storage)
        loaded = load_snapshots(self.storage)
        self.assertEqual(len(loaded), 3)
        self.assertEqual([s["task_id"] for s in loaded], ["t0", "t1", "t2"])

    def test_load_nonexistent_returns_empty(self):
        self.assertEqual(load_snapshots("/nonexistent/path.jsonl"), [])


class TestVerifySnapshot(unittest.TestCase):
    """CAM-P0: checksum 不变性校验"""

    def test_verify_unmodified_snapshot(self):
        snap = capture_execution_snapshot("t1", {"a": 1}, "automated")
        self.assertTrue(verify_snapshot(snap))

    def test_verify_detects_tampering(self):
        snap = capture_execution_snapshot("t1", {"a": 1}, "automated")
        snap["task_config"] = {"a": 999}  # 篡改
        self.assertFalse(verify_snapshot(snap))

    def test_verify_after_load_unchanged(self):
        snap = capture_execution_snapshot("t1", {"a": 1}, "automated")
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            storage = f.name
        os.unlink(storage)
        try:
            append_snapshot(snap, storage)
            loaded = load_snapshots(storage)
            self.assertTrue(verify_snapshot(loaded[0]))
        finally:
            if os.path.exists(storage):
                os.unlink(storage)


if __name__ == "__main__":
    unittest.main()
