#!/usr/bin/env python3
"""Write a CrazyAgentsManage runtime snapshot into .omx."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / ".omx" / "crazyagents" / "runtime-state.json"


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--actor", default="codex")
    parser.add_argument("--counterpart", default="HermesAgent")
    parser.add_argument("--summary", required=True)
    parser.add_argument("--goal", default="")
    parser.add_argument("--thread", default="")
    parser.add_argument("--artifacts", nargs="*", default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": iso_now(),
        "phase": args.phase,
        "status": args.status,
        "actor": args.actor,
        "counterpart": args.counterpart,
        "summary": args.summary,
        "goal": args.goal,
        "thread": args.thread,
        "artifacts": args.artifacts,
        "repository_root": str(ROOT),
    }
    STATE_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(str(STATE_PATH))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
