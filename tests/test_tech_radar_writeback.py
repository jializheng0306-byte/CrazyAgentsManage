import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent.parent / "scripts" / "tech_radar_writeback.py"
SPEC = importlib.util.spec_from_file_location("tech_radar_writeback", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_normalize_radar_status_maps_chinese_and_english_values():
    assert MODULE.normalize_radar_status("待确认") == "pending"
    assert MODULE.normalize_radar_status("已确认") == "confirmed"
    assert MODULE.normalize_radar_status("已拒绝") == "rejected"
    assert MODULE.normalize_radar_status("已实施") == "implemented"
    assert MODULE.normalize_radar_status("confirmed") == "confirmed"


def test_find_radar_entry_prefers_bitable_record_id():
    entries = [
        {"name": "A", "bitable_record_id": "rec_a"},
        {"name": "B"},
    ]
    record_lookup = {"B": "rec_b"}
    bitable_record = {"record_id": "rec_a", "name": "A"}

    matched = MODULE.find_radar_entry(entries, bitable_record, record_lookup)

    assert matched is entries[0]


def test_find_radar_entry_falls_back_to_record_map_then_name():
    entries = [
        {"name": "A"},
        {"name": "B"},
    ]
    bitable_record = {"record_id": "rec_b", "name": "B"}

    matched = MODULE.find_radar_entry(entries, bitable_record, {"B": "rec_b"})
    assert matched is entries[1]

    matched_by_name = MODULE.find_radar_entry(entries, {"record_id": "rec_c", "name": "A"}, {})
    assert matched_by_name is entries[0]


def test_apply_bitable_to_radar_updates_status_and_writeback_fields():
    entry = {
        "name": "A",
        "status": "pending",
        "priority": "P2",
        "impact_assessment": "",
        "action_suggested": "",
        "notes": "",
    }
    bitable_record = {
        "record_id": "rec_a",
        "name": "A",
        "status": "已确认",
        "priority": "P1",
        "impact_assessment": "impact",
        "action_suggested": "action",
        "notes": "note",
        "flowmind_sync": "已同步",
    }

    changed = MODULE.apply_bitable_to_radar(entry, bitable_record)

    assert changed is True
    assert entry["status"] == "confirmed"
    assert entry["priority"] == "P1"
    assert entry["bitable_record_id"] == "rec_a"
    assert entry["bitable_status"] == "已确认"
    assert entry["flowmind_sync_status"] == "已同步"
    assert "writeback_last_synced_at" in entry


def test_run_writeback_for_records_updates_matching_entry_without_bitable_read(tmp_path, monkeypatch):
    radar_file = tmp_path / "tech-radar.json"
    sync_state_file = tmp_path / "bitable-sync-state.json"
    radar_file.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "name": "A",
                        "status": "pending",
                        "priority": "P2",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    sync_state_file.write_text(
        json.dumps({"synced_ids": ["A"], "record_map": {"A": "rec_a"}}, ensure_ascii=False),
        encoding="utf-8",
    )

    monkeypatch.setattr(MODULE, "RADAR_FILE", radar_file)
    monkeypatch.setattr(MODULE, "SYNC_STATE_FILE", sync_state_file)

    result = MODULE.run_writeback_for_records(
        [
            {
                "record_id": "rec_a",
                "name": "A",
                "status": "已确认",
                "priority": "P1",
                "impact_assessment": "impact",
                "action_suggested": "action",
                "notes": "note",
                "flowmind_sync": "已同步",
            }
        ],
        dry_run=False,
    )

    saved = json.loads(radar_file.read_text(encoding="utf-8"))
    entry = saved["entries"][0]

    assert result["matched"] == 1
    assert result["updated"] == 1
    assert entry["status"] == "confirmed"
    assert entry["bitable_record_id"] == "rec_a"
    assert entry["flowmind_sync_status"] == "已同步"
