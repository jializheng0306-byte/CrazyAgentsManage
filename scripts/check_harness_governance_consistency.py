#!/usr/bin/env python3
"""Check Crazy harness governance docs for local contradiction patterns."""

from __future__ import annotations

from pathlib import Path
import json
import re
import sys
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
HARNESS_DIR = ROOT / "docs" / "02-engineering" / "harness"
MATRIX_PATH = HARNESS_DIR / "hermes-flowmind-compatibility-matrix-2026-04-30.md"
SMOKE_PATH = HARNESS_DIR / "handshake-smoke-status-2026-05-03.md"
CONSUMPTION_PATH = HARNESS_DIR / "feedback-context-consumption-status-2026-05-03.md"
ENTRYPOINT_MANIFEST = ROOT / "scripts" / "harness-doc-entrypoints.manifest.json"
REPORT_PATH = HARNESS_DIR / "harness-governance-report.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def extract_markdown_links(text: str) -> list[str]:
    return [match.group(1) for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text) if not match.group(1).startswith("http")]


def validate_entrypoint(spec: dict) -> tuple[bool, str]:
    rel_path = spec["path"]
    target = ROOT / rel_path
    if not target.exists():
        return False, f"{rel_path} 缺失"

    text = read(target)
    for token in spec.get("mustContain", []):
        if token not in text:
            return False, f"{rel_path} 缺少入口锚点: {token}"

    page_dir = target.parent
    raw_links = [unquote(href) for href in extract_markdown_links(text)]
    links = {str((page_dir / href).resolve()) for href in raw_links}
    for rel_link in spec.get("requiredLinks", []):
        abs_link = str((ROOT / rel_link).resolve())
        suffix_match = any(
            href.startswith("/")
            and Path(href).as_posix().endswith(rel_link.replace("\\", "/"))
            for href in raw_links
        )
        if not (ROOT / rel_link).exists() or (abs_link not in links and not suffix_match):
            return False, f"{rel_path} 的入口链接失效: {rel_link}"

    return True, f"{rel_path} 的入口锚点与链接有效"


def render_report(rows: list[tuple[str, bool, str]], errors: list[str]) -> str:
    status = "PASS" if not errors else "FAIL"
    lines = [
        "# Harness Governance Report",
        "",
        "- Date: 2026-05-03",
        f"- Status: {status}",
        "- Repo: CrazyAgentsManage",
        "",
        "## Results",
        "",
    ]
    for area, ok, message in rows:
        lines.append(f"- [{'PASS' if ok else 'FAIL'}] `{area}` — {message}")
    lines.extend(["", "## Findings", ""])
    if errors:
        for error in errors:
            lines.append(f"- {error}")
    else:
        lines.append("- No harness governance drift detected in the current minimal scan.")
    lines.append("")
    return "\n".join(lines)


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
    rows: list[tuple[str, bool, str]] = []

    for path in (MATRIX_PATH, SMOKE_PATH, CONSUMPTION_PATH, ENTRYPOINT_MANIFEST):
        if not path.exists():
            errors.append(f"missing required evidence file: {path.relative_to(ROOT)}")

    matrix = read(MATRIX_PATH) if MATRIX_PATH.exists() else ""
    smoke = read(SMOKE_PATH) if SMOKE_PATH.exists() else ""
    consumption = read(CONSUMPTION_PATH) if CONSUMPTION_PATH.exists() else ""

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
    rows.append(("compatibility-matrix", not any("compatibility matrix" in e for e in errors), "compatibility matrix 与 handshake evidence 未出现已知矛盾"))

    banned_consumption_phrases = [
        "无任何文件引用 `bridge/feedback`",
        "无任何文件引用 `bridge/context-pack`",
    ]
    for phrase in banned_consumption_phrases:
        if phrase in consumption:
            errors.append(f"consumption status uses over-strong wording: {phrase}")

    if "scripts/flowmind_handshake_smoke.py" not in consumption:
        errors.append("consumption status should acknowledge handshake smoke probe references")
    rows.append(("consumption-evidence", not any("consumption" in e for e in errors), "feedback/context-pack 消费证据口径未出现已知过强表述"))

    if "疑似缺少正确的 x-instance-token 或 session context，待进一步定位" not in smoke:
        errors.append("handshake smoke should keep decision failure root cause as an unconfirmed hypothesis")

    if "需要正确的 x-instance-token 或 session context，裸调不通过" in smoke:
        errors.append("handshake smoke still states an unverified decision failure cause too strongly")
    rows.append(("handshake-smoke", not any("handshake smoke" in e for e in errors), "handshake smoke 失败原因仍保持为待定位假设"))

    if not repo_has(r"bridge/feedback") or not repo_has(r"bridge/context-pack"):
        errors.append("repository scan unexpectedly found no feedback/context-pack references; update checker assumptions")
    rows.append(("repo-probe-references", not any("repository scan" in e for e in errors), "仓库中仍存在 feedback/context-pack 的探测性引用"))

    if ENTRYPOINT_MANIFEST.exists():
        manifest = json.loads(read(ENTRYPOINT_MANIFEST))
        entry_results: list[str] = []
        entry_errors: list[str] = []
        for spec in manifest.get("entrypoints", []):
            ok, message = validate_entrypoint(spec)
            entry_results.append(message)
            if not ok:
                entry_errors.append(message)
        if entry_errors:
            errors.extend(entry_errors)
        rows.append(("doc-entrypoint-manifest", not entry_errors, "；".join(entry_errors) if entry_errors else "固定入口文档清单存在且入口锚点有效"))

    write(REPORT_PATH, render_report(rows, errors))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("OK: harness governance docs are locally consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
