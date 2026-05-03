#!/usr/bin/env python3
"""Generate a structured handoff packet for @HermesAgent group collaboration."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / ".omx" / "crazyagents" / "runtime-state.json"
OUTBOX_DIR = ROOT / ".omx" / "crazyagents" / "outbox"
MANIFEST_PATH = ROOT / "docs" / "02-engineering" / "harness" / "hermes-flowmind-link-manifest-v1.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def default_flowmind_base_url() -> str:
    manifest = load_json(MANIFEST_PATH)
    ip = (
        manifest.get("systems", {})
        .get("flowminddeploy", {})
        .get("primaryHost", {})
        .get("ip")
    )
    if ip:
        return f"http://{ip}:3301"
    return "http://111.229.194.203:3301"


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--questions", required=True)
    parser.add_argument("--artifacts", nargs="*", default=[])
    parser.add_argument("--output", default="")
    parser.add_argument("--candidate-id", default="")
    parser.add_argument("--instance-id", default="")
    parser.add_argument("--truth-limit", type=int, default=3)
    parser.add_argument("--flowmind-base-url", default=os.environ.get("FLOWMIND_BASE_URL", default_flowmind_base_url()))
    parser.add_argument("--flowmind-api-key", default=os.environ.get("FLOWMIND_API_KEY", "flowmind-dev-token"))
    parser.add_argument("--skip-truth-read", action="store_true")
    return parser.parse_args()


def read_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def flowmind_json_request(base_url: str, api_key: str, path: str) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}{path}"
    request = urlrequest.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
        method="GET",
    )
    with urlrequest.urlopen(request, timeout=20) as response:
        raw = response.read().decode("utf-8")
    return json.loads(raw)


def extract_payload(response: dict[str, Any]) -> dict[str, Any]:
    if response.get("success") is True and isinstance(response.get("data"), dict):
        return response["data"]
    return response


def fetch_truth_snapshot(args: argparse.Namespace, state: dict[str, Any]) -> dict[str, Any]:
    if args.skip_truth_read:
        return {}

    candidate_id = args.candidate_id or state.get("flowmind_candidate_id") or state.get("candidate_id") or ""
    instance_id = args.instance_id or state.get("flowmind_instance_id") or state.get("instance_id") or ""

    if not candidate_id and not instance_id:
        return {}

    if candidate_id:
        path = f"/api/bridge/truth/{urlparse.quote(candidate_id)}"
        mode = "candidate"
    else:
        query = urlparse.urlencode({"instanceId": instance_id, "limit": args.truth_limit})
        path = f"/api/bridge/truth?{query}"
        mode = "instance"

    try:
        response = flowmind_json_request(args.flowmind_base_url, args.flowmind_api_key, path)
        return {
            "mode": mode,
            "path": path,
            "payload": extract_payload(response),
        }
    except (urlerror.URLError, json.JSONDecodeError, RuntimeError, ValueError) as exc:
        return {
            "mode": mode,
            "path": path,
            "error": str(exc),
        }


def format_truth_section(snapshot: dict[str, Any]) -> str:
    if not snapshot:
        return "## FlowMind Truth Read\n- Truth read: skipped (no candidateId / instanceId provided)\n"

    if snapshot.get("error"):
        return (
            "## FlowMind Truth Read\n"
            f"- Truth read path: {snapshot.get('path', '(unknown)')}\n"
            f"- Truth read status: fallback to local runtime state\n"
            f"- Truth read error: {snapshot['error']}\n"
        )

    payload = snapshot.get("payload", {})
    semantic_context = payload.get("semanticContext", {}) if isinstance(payload, dict) else {}
    entries = semantic_context.get("entries", []) if isinstance(semantic_context, dict) else []
    field_mappings = semantic_context.get("fieldMappings", []) if isinstance(semantic_context, dict) else []
    consumer_hints = semantic_context.get("consumerHints", []) if isinstance(semantic_context, dict) else []

    lines = [
        "## FlowMind Truth Read",
        f"- Truth read path: {snapshot.get('path', '(unknown)')}",
    ]

    if snapshot.get("mode") == "candidate":
        latest_evidence = payload.get("latestEvidence", {}) if isinstance(payload, dict) else {}
        lines.extend(
            [
                f"- Candidate ID: {payload.get('candidateId', '(unknown)')}",
                f"- Truth status: {payload.get('status', '(unknown)')}",
                f"- Confirmed At: {payload.get('decisionMetadata', {}).get('confirmedAt', '(none)')}",
            ]
        )
        if latest_evidence:
            lines.extend(
                [
                    f"- Latest evidence: {latest_evidence.get('evidenceClass', '(none)')} / {latest_evidence.get('evidenceSourceType', '(none)')}",
                    f"- Evidence summary: {latest_evidence.get('summary', '(none)')}",
                    f"- Evidence refs: {', '.join(latest_evidence.get('refs', [])) or '(none)'}",
                ]
            )
    else:
        commitments = payload.get("commitments", []) if isinstance(payload, dict) else []
        lines.append(f"- Truth count: {payload.get('totalCount', len(commitments))}")
        if commitments:
            first = commitments[0]
            lines.extend(
                [
                    f"- Primary commitment: {first.get('title', '(untitled)')} [{first.get('status', 'unknown')}]",
                    f"- Primary commitment ID: {first.get('id', '(unknown)')}",
                ]
            )
            latest_evidence = first.get("latestEvidence", {})
            if latest_evidence:
                lines.extend(
                    [
                        f"- Latest evidence: {latest_evidence.get('evidenceClass', '(none)')} / {latest_evidence.get('evidenceSourceType', '(none)')}",
                        f"- Evidence summary: {latest_evidence.get('summary', '(none)')}",
                    ]
                )

    semantic_lines = []
    for entry in entries[:4]:
        semantic_lines.append(
            f"  - {entry.get('id', '(unknown)')}: {entry.get('summary', '(no summary)')}"
        )
    lines.append("- Semantic refs:")
    lines.extend(semantic_lines or ["  - (none)"])

    mapping_lines = []
    for mapping in field_mappings[:6]:
        mapping_lines.append(
            f"  - {mapping.get('dslField', '(unknown)')} -> {mapping.get('runtimeField', '(unknown)')}"
        )
    lines.append("- Semantic field mappings:")
    lines.extend(mapping_lines or ["  - (none)"])

    hint_lines = [f"  - {hint}" for hint in consumer_hints[:3]]
    lines.append("- Consumer hints:")
    lines.extend(hint_lines or ["  - (none)"])

    return "\n".join(lines) + "\n"


def render_packet(args: argparse.Namespace, state: dict, truth_snapshot: dict[str, Any]) -> str:
    artifacts = args.artifacts or state.get("artifacts", [])
    artifact_lines = "\n".join(f"- {item}" for item in artifacts) if artifacts else "- (none)"
    phase = state.get("phase", "unknown")
    status = state.get("status", "unknown")
    summary = state.get("summary", "")
    truth_section = format_truth_section(truth_snapshot)
    return f"""@HermesAgent

## Handoff
- Title: {args.title}
- Goal: {args.goal}
- Runtime phase: {phase}
- Runtime status: {status}
- Current summary: {summary or "(none)"}

## Artifacts To Review
{artifact_lines}

{truth_section}

## Questions
- {args.questions}

## Expected Output
- Runtime gap
- Operations gap
- Missing signal
- Missing action
- Accept / reject
"""


def main() -> int:
    args = parse_args()
    state = read_state()
    truth_snapshot = fetch_truth_snapshot(args, state)
    packet = render_packet(args, state, truth_snapshot)

    output = Path(args.output) if args.output else OUTBOX_DIR / f"handoff-{iso_now()}.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(packet + "\n", encoding="utf-8")
    print(packet)
    print(f"\n[written] {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
