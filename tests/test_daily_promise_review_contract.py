from importlib import util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "daily-promise-review.py"
SPEC = util.spec_from_file_location("daily_promise_review", SCRIPT_PATH)
MODULE = util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_build_trace_summary_keeps_truth_as_authority():
    trace_summary = MODULE.build_trace_summary(
        {
            "data": {
                "status": "approved",
                "latestEvidence": {"summary": "Truth approved by operator"},
            }
        },
        [
            {
                "timestamp": "2026-05-04T10:00:00Z",
                "summary": "feedback blocked should not override truth",
                "response_summary": "feedback blocked should not override truth",
            }
        ],
    )

    assert trace_summary["flowmind_status"] == "approved"
    assert trace_summary["latest_evidence_summary"] == "Truth approved by operator"
    assert trace_summary["last_trace_summary"] == "feedback blocked should not override truth"
    assert trace_summary["trace_summary"] == (
        "Truth approved by operator | feedback blocked should not override truth"
    )


def test_build_feedback_summary_uses_latest_feedback_without_touching_truth():
    feedback_summary = MODULE.build_feedback_summary(
        [
            {
                "event_type": "confirmed",
                "timestamp": "2026-05-04T10:00:00Z",
                "summary": "confirmed by operator",
            },
            {
                "event_type": "blocked",
                "timestamp": "2026-05-04T10:05:00Z",
                "summary": "waiting for human input",
            },
        ]
    )

    assert feedback_summary["latest_feedback_type"] == "blocked"
    assert feedback_summary["latest_feedback_summary"] == "waiting for human input"
    assert "confirmed: confirmed by operator" in feedback_summary["notes_text"]
    assert "blocked: waiting for human input" in feedback_summary["notes_text"]


def test_sync_to_bitable_separates_truth_status_from_feedback_status(monkeypatch):
    monkeypatch.setattr(MODULE, "DRY_RUN", False)
    monkeypatch.setattr(MODULE, "list_existing_records", lambda *args, **kwargs: {})
    monkeypatch.setattr(
        MODULE,
        "ensure_main_table_fields",
        lambda *args, **kwargs: {
            "timeline_url",
            "last_governance_status",
            "last_governance_feedback",
        },
    )
    monkeypatch.setattr(
        MODULE,
        "flowmind_truth_request",
        lambda *args, **kwargs: {
            "data": {
                "status": "approved",
                "latestEvidence": {"summary": "Truth approved"},
                "instanceId": "hermes-agent",
            }
        },
    )
    monkeypatch.setattr(
        MODULE,
        "flowmind_trace_request",
        lambda *args, **kwargs: {
            "data": {
                "traceEvents": [
                    {
                        "traceId": "trace-1",
                        "timestamp": "2026-05-04T10:00:00Z",
                        "module": "truth",
                        "action": "approve",
                        "summary": "Truth approved",
                        "toStatus": "approved",
                    }
                ]
            }
        },
    )
    monkeypatch.setattr(
        MODULE,
        "flowmind_feedback_request",
        lambda *args, **kwargs: {
            "data": {
                "feedbackEvents": [
                    {
                        "eventId": "fb-1",
                        "candidateId": "cand-1",
                        "eventType": "blocked",
                        "createdAt": "2026-05-04T10:05:00Z",
                        "payload": {
                            "candidateStatus": "approved",
                            "notes": "Need manual gate",
                        },
                    }
                ]
            }
        },
    )

    writes = []

    def fake_upsert(app_token, table_id, existing_records, key, fields):
        writes.append((table_id, key, fields))
        return True

    monkeypatch.setattr(MODULE, "upsert_record", fake_upsert)

    config = {
        "bitable_app_token": "app-token",
        "bitable_main_table_id": "main-table",
        "bitable_trace_table_id": "trace-table",
        "timeline_base_url": "http://example.com/timeline",
        "flowmind_trace_api_base_url": "http://example.com",
        "flowmind_trace_api_bearer_token": "token",
    }
    promises = [
        {
            "id": "promise-1",
            "title": "Promise title",
            "description": "Promise description",
            "status": "pending",
            "priority": "P1",
            "source": "user-request",
            "created_at": "2026-05-04T09:55:00Z",
            "flowmind_candidate_id": "cand-1",
        }
    ]

    result = MODULE.sync_to_bitable(promises, config)

    assert result["main_sync_count"] == 1
    assert result["trace_sync_count"] == 2

    main_write = next(fields for table_id, _, fields in writes if table_id == "main-table")
    assert main_write["flowmind_status"] == "approved"
    assert main_write["status"] == "blocked"
    assert main_write["last_governance_status"] == "approved"
    assert main_write["last_governance_feedback"] == "blocked"
    assert "FlowMind feedback: 2026-05-04T10:05:00Z blocked: Need manual gate" in main_write["备注"]


def test_sync_to_bitable_maps_deferred_and_cancelled_feedback(monkeypatch):
    monkeypatch.setattr(MODULE, "DRY_RUN", False)
    monkeypatch.setattr(MODULE, "list_existing_records", lambda *args, **kwargs: {})
    monkeypatch.setattr(
        MODULE,
        "ensure_main_table_fields",
        lambda *args, **kwargs: {"last_governance_status", "last_governance_feedback"},
    )
    monkeypatch.setattr(
        MODULE,
        "flowmind_truth_request",
        lambda *args, **kwargs: {"data": {"status": "draft", "instanceId": "hermes-agent"}},
    )
    monkeypatch.setattr(
        MODULE,
        "flowmind_trace_request",
        lambda *args, **kwargs: {"data": {"traceEvents": []}},
    )

    feedback_sequences = iter(
        [
            {
                "data": {
                    "feedbackEvents": [
                        {
                            "eventId": "fb-deferred",
                            "candidateId": "cand-deferred",
                            "eventType": "deferred",
                            "createdAt": "2026-05-04T11:00:00Z",
                            "payload": {"candidateStatus": "draft", "notes": "Wait for more info"},
                        }
                    ]
                }
            },
            {
                "data": {
                    "feedbackEvents": [
                        {
                            "eventId": "fb-cancelled",
                            "candidateId": "cand-cancelled",
                            "eventType": "cancelled",
                            "createdAt": "2026-05-04T11:05:00Z",
                            "payload": {"candidateStatus": "draft", "notes": "Stop this round"},
                        }
                    ]
                }
            },
        ]
    )
    monkeypatch.setattr(
        MODULE,
        "flowmind_feedback_request",
        lambda *args, **kwargs: next(feedback_sequences),
    )

    main_writes = []

    def fake_upsert(app_token, table_id, existing_records, key, fields):
        if table_id == "main-table":
            main_writes.append(fields)
        return True

    monkeypatch.setattr(MODULE, "upsert_record", fake_upsert)

    config = {
        "bitable_app_token": "app-token",
        "bitable_main_table_id": "main-table",
        "bitable_trace_table_id": "",
        "timeline_base_url": "http://example.com/timeline",
        "flowmind_trace_api_base_url": "http://example.com",
        "flowmind_trace_api_bearer_token": "token",
    }
    promises = [
        {
            "id": "promise-deferred",
            "title": "Deferred promise",
            "status": "pending",
            "priority": "P2",
            "flowmind_candidate_id": "cand-deferred",
        },
        {
            "id": "promise-cancelled",
            "title": "Cancelled promise",
            "status": "pending",
            "priority": "P2",
            "flowmind_candidate_id": "cand-cancelled",
        },
    ]

    MODULE.sync_to_bitable(promises, config)

    assert [fields["status"] for fields in main_writes] == ["deferred", "cancelled"]
    assert [fields["flowmind_status"] for fields in main_writes] == ["draft", "draft"]
    assert [fields["last_governance_feedback"] for fields in main_writes] == [
        "deferred",
        "cancelled",
    ]


def test_sync_to_bitable_maps_committed_truth_to_done(monkeypatch):
    monkeypatch.setattr(MODULE, "DRY_RUN", False)
    monkeypatch.setattr(MODULE, "list_existing_records", lambda *args, **kwargs: {})
    monkeypatch.setattr(
        MODULE,
        "ensure_main_table_fields",
        lambda *args, **kwargs: {"last_governance_status", "last_governance_feedback"},
    )
    monkeypatch.setattr(
        MODULE,
        "flowmind_truth_request",
        lambda *args, **kwargs: {
            "data": {
                "status": "committed",
                "instanceId": "hermes-agent",
            }
        },
    )
    monkeypatch.setattr(
        MODULE,
        "flowmind_trace_request",
        lambda *args, **kwargs: {
            "data": {
                "traceEvents": [
                    {
                        "traceId": "trace-committed",
                        "timestamp": "2026-05-05T01:00:00Z",
                        "module": "truth",
                        "action": "commit",
                        "summary": "Candidate committed",
                        "toStatus": "committed",
                    }
                ]
            }
        },
    )
    monkeypatch.setattr(
        MODULE,
        "flowmind_feedback_request",
        lambda *args, **kwargs: {"data": {"feedbackEvents": []}},
    )

    main_writes = []

    def fake_upsert(app_token, table_id, existing_records, key, fields):
        if table_id == "main-table":
            main_writes.append(fields)
        return True

    monkeypatch.setattr(MODULE, "upsert_record", fake_upsert)

    config = {
        "bitable_app_token": "app-token",
        "bitable_main_table_id": "main-table",
        "bitable_trace_table_id": "",
        "timeline_base_url": "http://example.com/timeline",
        "flowmind_trace_api_base_url": "http://example.com",
        "flowmind_trace_api_bearer_token": "token",
    }
    promises = [
        {
            "id": "promise-committed",
            "title": "Committed promise",
            "status": "in_progress",
            "priority": "P1",
            "flowmind_candidate_id": "cand-committed",
        }
    ]

    MODULE.sync_to_bitable(promises, config)

    assert len(main_writes) == 1
    assert main_writes[0]["flowmind_status"] == "committed"
    assert main_writes[0]["status"] == "已完成"
    assert main_writes[0]["last_governance_status"] == "committed"
    assert main_writes[0]["last_governance_feedback"] == ""
