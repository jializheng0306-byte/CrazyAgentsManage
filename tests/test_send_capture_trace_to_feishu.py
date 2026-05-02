import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "send-capture-trace-to-feishu.py"


def load_module():
    spec = importlib.util.spec_from_file_location("send_capture_trace_to_feishu", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SendCaptureTraceTests(unittest.TestCase):
    def test_ensure_bitable_fields_uses_json_shortcuts_and_repairs_status_options(self):
        module = load_module()
        calls = []

        def fake_lark(args):
            calls.append(args)
            if args[:2] == ["base", "+field-list"]:
                return {
                    "ok": True,
                    "data": {
                        "items": [
                            {"field_name": "title", "field_id": "fld_title"},
                            {"field_name": "status", "field_id": "fld_status"},
                        ]
                    },
                }
            if args[:2] == ["base", "+field-search-options"]:
                return {"ok": True, "data": {"options": [{"name": "待确认"}]}}
            return {"ok": True, "data": {}}

        with patch.object(module, "_lark", side_effect=fake_lark):
            self.assertTrue(module.ensure_bitable_fields("app_token", "tbl_token"))

        create_calls = [args for args in calls if args[:2] == ["base", "+field-create"]]
        update_calls = [args for args in calls if args[:2] == ["base", "+field-update"]]

        self.assertTrue(create_calls)
        self.assertTrue(update_calls)
        self.assertTrue(all("--json" in args for args in create_calls))
        self.assertTrue(all("--name" not in args and "--type" not in args for args in create_calls))

        create_specs = [json.loads(args[args.index("--json") + 1]) for args in create_calls]
        created_names = {spec["name"] for spec in create_specs}
        self.assertEqual(created_names, {"summary", "raw_text", "source_task", "captured_at", "confidence"})

        status_update = json.loads(update_calls[0][update_calls[0].index("--json") + 1])
        self.assertEqual(status_update["name"], "status")
        self.assertEqual(status_update["type"], "select")
        self.assertFalse(status_update["multiple"])
        self.assertEqual([option["name"] for option in status_update["options"]], ["待确认", "已确认", "已忽略"])

    def test_write_bitable_record_uses_record_upsert_and_sets_default_status(self):
        module = load_module()
        calls = []

        def fake_lark(args):
            calls.append(args)
            return {"ok": True, "data": {"record": {"record_id": "rec_123"}}}

        with patch.object(module, "_lark", side_effect=fake_lark):
            result = module.write_bitable_record(
                "app_token",
                "tbl_token",
                {
                    "title": "捕获标题",
                    "summary": "摘要",
                    "raw_text": "原文",
                    "source_task": "task-x",
                    "captured_at": "2026-05-02 10:00:00",
                    "confidence": 82.4,
                },
            )

        self.assertTrue(result["ok"])
        self.assertEqual(len(calls), 1)
        args = calls[0]
        self.assertEqual(args[:2], ["base", "+record-upsert"])
        self.assertIn("--json", args)
        self.assertNotIn("--data", args)

        payload = json.loads(args[args.index("--json") + 1])
        self.assertEqual(payload["title"], "捕获标题")
        self.assertEqual(payload["status"], "待确认")
        self.assertEqual(payload["summary"], "摘要")
        self.assertEqual(payload["raw_text"], "原文")
        self.assertEqual(payload["source_task"], "task-x")
        self.assertEqual(payload["captured_at"], "2026-05-02 10:00:00")
        self.assertEqual(payload["confidence"], 82)


if __name__ == "__main__":
    unittest.main()
