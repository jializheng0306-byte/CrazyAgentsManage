#!/usr/bin/env python3
"""Write CrazyAgentsManage harness closeout records."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HARNESS_ROOT = ROOT / "harness"


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", choices=["success", "failed"], required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument("--agent", default="codex")
    parser.add_argument("--counterpart", default="HermesAgent")
    parser.add_argument("--stage", default="closeout")
    parser.add_argument("--artifacts", nargs="*", default=[])
    parser.add_argument("--verification", default="")
    parser.add_argument("--next-action", default="")
    parser.add_argument("--update-procedural", action="store_true")
    parser.add_argument("--update-failure-patterns", action="store_true")
    return parser.parse_args()


def append_line(path: Path, heading: str, body: str) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    addition = f"\n## {heading}\n\n{body}\n"
    path.write_text(existing.rstrip() + addition, encoding="utf-8")


def main() -> int:
    args = parse_args()
    target_dir = HARNESS_ROOT / "trace" / ("successes" if args.status == "success" else "failures")
    target_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": args.status,
        "timestamp": iso_now(),
        "agent": args.agent,
        "counterpart": args.counterpart,
        "stage": args.stage,
        "message": args.message,
        "artifacts": args.artifacts,
    }
    if args.verification:
        payload["verification"] = args.verification
    if args.next_action:
        payload["next_action"] = args.next_action

    output = target_dir / f"{stamp()}-{args.stage}.json"
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.update_procedural and args.status == "success":
        append_line(
            HARNESS_ROOT / "memory" / "procedural.md",
            f"{stamp()} — validated round",
            f"- Stage: {args.stage}\n- Message: {args.message}\n- Artifacts: {', '.join(args.artifacts) or '(none)'}",
        )

    if args.update_failure_patterns and args.status == "failed":
        append_line(
            HARNESS_ROOT / "memory" / "failure-patterns.md",
            f"{stamp()} — observed failure",
            f"- Stage: {args.stage}\n- Message: {args.message}\n- Next action: {args.next_action or '(unspecified)'}",
        )

    print(str(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
