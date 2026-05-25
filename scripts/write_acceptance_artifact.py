#!/usr/bin/env python3
"""Write a repository-owned acceptance artifact for Crazy collaboration rounds."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE_ROOT = ROOT / "harness" / "acceptance"
STATE_PATH = ROOT / ".omx" / "crazyagents" / "runtime-state.json"


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def next_acceptance_id(now: datetime) -> str:
    day = now.strftime("%Y%m%d")
    ACCEPTANCE_ROOT.mkdir(parents=True, exist_ok=True)
    existing = []
    for path in ACCEPTANCE_ROOT.glob(f"A-{day}-*.json"):
        suffix = path.stem.split("-")[-1]
        try:
            existing.append(int(suffix))
        except ValueError:
            continue
    return f"A-{day}-{(max(existing) + 1) if existing else 1:03d}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", choices=["accepted", "rejected", "deferred"], required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--actor", default="HermesAgent")
    parser.add_argument("--counterpart", default="codex")
    parser.add_argument("--handoff-path", default="")
    parser.add_argument("--handoff-title", default="")
    parser.add_argument("--runtime-state-path", default=str(STATE_PATH.relative_to(ROOT)))
    parser.add_argument("--artifacts", nargs="*", default=[])
    parser.add_argument("--notes", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    now = datetime.now(timezone.utc)
    acceptance_id = next_acceptance_id(now)
    runtime_rel = str(args.runtime_state_path or ".omx/crazyagents/runtime-state.json").strip()
    runtime_path = ROOT / runtime_rel
    runtime_state = read_json(runtime_path)

    payload = {
        "id": acceptance_id,
        "timestamp": iso_now(),
        "decision": args.decision,
        "actor": args.actor,
        "counterpart": args.counterpart,
        "summary": args.summary,
        "handoff": {
            "path": str(args.handoff_path or "").strip(),
            "title": str(args.handoff_title or "").strip(),
        },
        "runtimeSnapshot": {
            "path": runtime_rel,
            "phase": runtime_state.get("phase"),
            "status": runtime_state.get("status"),
            "updated_at": runtime_state.get("updated_at"),
        },
        "artifacts": list(args.artifacts or []),
        "notes": args.notes,
        "repository_root": str(ROOT),
    }

    output = ACCEPTANCE_ROOT / f"{acceptance_id}.json"
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(str(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
