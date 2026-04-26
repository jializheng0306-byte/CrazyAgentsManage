#!/usr/bin/env python3
"""Generate a structured handoff packet for @HermesAgent group collaboration."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / ".omx" / "crazyagents" / "runtime-state.json"
OUTBOX_DIR = ROOT / ".omx" / "crazyagents" / "outbox"


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--questions", required=True)
    parser.add_argument("--artifacts", nargs="*", default=[])
    parser.add_argument("--output", default="")
    return parser.parse_args()


def read_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def render_packet(args: argparse.Namespace, state: dict) -> str:
    artifacts = args.artifacts or state.get("artifacts", [])
    artifact_lines = "\n".join(f"- {item}" for item in artifacts) if artifacts else "- (none)"
    phase = state.get("phase", "unknown")
    status = state.get("status", "unknown")
    summary = state.get("summary", "")
    return f"""@HermesAgent

## Handoff
- Title: {args.title}
- Goal: {args.goal}
- Runtime phase: {phase}
- Runtime status: {status}
- Current summary: {summary or "(none)"}

## Artifacts To Review
{artifact_lines}

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
    packet = render_packet(args, state)

    output = Path(args.output) if args.output else OUTBOX_DIR / f"handoff-{iso_now()}.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(packet + "\n", encoding="utf-8")
    print(packet)
    print(f"\n[written] {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
