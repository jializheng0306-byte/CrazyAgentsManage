#!/usr/bin/env python3
"""Check Crazy harness governance docs for local contradiction patterns."""

from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
HARNESS_DIR = ROOT / "docs" / "02-engineering" / "harness"
MATRIX_PATH = HARNESS_DIR / "hermes-flowmind-compatibility-matrix-2026-04-30.md"
SMOKE_PATH = HARNESS_DIR / "handshake-smoke-status-2026-05-03.md"
CONSUMPTION_PATH = HARNESS_DIR / "feedback-context-consumption-status-2026-05-03.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def repo_has(pattern: str) -> bool:
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts or "node_modules" in path.parts or "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if re.search(pattern, text):
            return True
    return False


def main() -> int:
    errors: list[str] = []

    for path in (MATRIX_PATH, SMOKE_PATH, CONSUMPTION_PATH):
        if not path.exists():
            errors.append(f"missing required evidence file: {path.relative_to(ROOT)}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    matrix = read(MATRIX_PATH)
    smoke = read(SMOKE_PATH)
    consumption = read(CONSUMPTION_PATH)

    if SMOKE_PATH.exists():
        banned_matrix_phrases = [
            "`pending_evidence`",
            "(待固化到仓库)",
            "缺少仓库内固化记录",
            "handshake smoke 记录未固化到仓库",
        ]
        for phrase in banned_matrix_phrases:
            if phrase in matrix:
                errors.append(
                    f"compatibility matrix still contains stale handshake phrase after smoke evidence exists: {phrase}"
                )

    banned_consumption_phrases = [
        "无任何文件引用 `bridge/feedback`",
        "无任何文件引用 `bridge/context-pack`",
    ]
    for phrase in banned_consumption_phrases:
        if phrase in consumption:
            errors.append(f"consumption status uses over-strong wording: {phrase}")

    if "scripts/flowmind_handshake_smoke.py" not in consumption:
        errors.append("consumption status should acknowledge handshake smoke probe references")

    if "疑似缺少正确的 x-instance-token 或 session context，待进一步定位" not in smoke:
        errors.append("handshake smoke should keep decision failure root cause as an unconfirmed hypothesis")

    if "需要正确的 x-instance-token 或 session context，裸调不通过" in smoke:
        errors.append("handshake smoke still states an unverified decision failure cause too strongly")

    if not repo_has(r"bridge/feedback") or not repo_has(r"bridge/context-pack"):
        errors.append("repository scan unexpectedly found no feedback/context-pack references; update checker assumptions")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("OK: harness governance docs are locally consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
