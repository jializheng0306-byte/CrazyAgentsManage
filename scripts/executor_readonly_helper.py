#!/usr/bin/env python3
"""Shared helper for readonly executor-backed fetch scripts."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable


_EXECUTOR_ENV_VARS = ("EXECUTOR_BIN", "CRAZY_EXECUTOR_BIN")


def _is_executable(candidate: str) -> bool:
    path = Path(candidate).expanduser()
    return path.is_file() and os.access(path, os.X_OK)


def _resolve_npm_global_executor() -> str | None:
    npm_bin = shutil.which("npm")
    if not npm_bin:
        return None

    result = subprocess.run(
        [npm_bin, "prefix", "-g"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None

    prefix = (result.stdout or "").strip()
    if not prefix:
        return None

    candidate = str(Path(prefix).expanduser() / "bin" / "executor")
    return candidate if _is_executable(candidate) else None


def resolve_executor_binary() -> str:
    candidates: list[str] = []

    for env_var in _EXECUTOR_ENV_VARS:
        value = os.environ.get(env_var, "").strip()
        if value:
            candidates.append(value)

    path = shutil.which("executor")
    if path:
        candidates.append(path)

    npm_candidate = _resolve_npm_global_executor()
    if npm_candidate:
        candidates.append(npm_candidate)

    candidates.extend(
        [
            "/usr/local/bin/executor",
            "/usr/bin/executor",
            "/opt/homebrew/bin/executor",
        ]
    )

    home_nvm = Path.home() / ".nvm" / "versions" / "node"
    if home_nvm.exists():
        candidates.extend(str(path) for path in sorted(home_nvm.glob("*/bin/executor")))

    seen: set[str] = set()
    for candidate in candidates:
        normalized = str(Path(candidate).expanduser())
        if normalized in seen:
            continue
        seen.add(normalized)
        if _is_executable(normalized):
            return normalized

    raise FileNotFoundError(
        "executor CLI not found. Set EXECUTOR_BIN or install executor so the binary is available on PATH."
    )


def call_executor_tool(source: str, group: str, tool: str, payload: dict) -> dict:
    try:
        executor_bin = resolve_executor_binary()
    except FileNotFoundError as exc:
        raise RuntimeError(str(exc)) from exc

    result = subprocess.run(
        [
            executor_bin,
            "call",
            source,
            group,
            tool,
            json.dumps(payload, ensure_ascii=False),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "executor call failed").strip())
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid executor JSON output: {exc}") from exc


def render_markdown_section(
    heading: str,
    items: list[dict],
    render_item: Callable[[dict], list[str]],
    empty_text: str,
) -> str:
    lines = ["", f"## {heading}", ""]
    if not items:
        lines.append(empty_text)
        lines.append("")
        return "\n".join(lines)
    for item in items:
        lines.extend(render_item(item))
        lines.append("")
    return "\n".join(lines)
