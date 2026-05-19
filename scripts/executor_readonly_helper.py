#!/usr/bin/env python3
"""Shared helper for readonly executor-backed fetch scripts."""

from __future__ import annotations

import json
import subprocess
from typing import Callable


def call_executor_tool(source: str, group: str, tool: str, payload: dict) -> dict:
    result = subprocess.run(
        [
            "executor",
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
