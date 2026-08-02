#!/usr/bin/env python3
"""Ensure the X syndication readonly executor source exists via Crazy's façade."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from urllib.parse import quote
from urllib import error as urlerror
from urllib import request as urlrequest


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SPEC_PATH = ROOT / "shared-context" / "executor-sources" / "x-publish-readonly-openapi.v1.json"


def http_json(url: str, method: str = "GET", data: dict | None = None, timeout: int = 30, attempts: int = 4):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            payload = json.dumps(data).encode("utf-8") if data is not None else None
            req = urlrequest.Request(
                url,
                method=method,
                data=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
            )
            with urlrequest.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                return resp.status, json.loads(body) if body else None
        except (urlerror.URLError, urlerror.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt == attempts:
                raise
            time.sleep(min(1.5 * attempt, 4))
    raise last_error  # pragma: no cover


def find_existing(base_url: str, namespace: str):
    _, sources = http_json(base_url.rstrip("/") + "/api/operations/integrations/sources")
    for item in sources or []:
        if item.get("id") == namespace:
            return item
    return None


def list_tools(base_url: str, namespace: str):
    _, tools = http_json(
        base_url.rstrip("/") + f"/api/operations/integrations/tools?sourceId={quote(namespace, safe='')}"
    )
    return tools or []


def has_required_tool(base_url: str, namespace: str, required_tool: str) -> bool:
    if not required_tool:
        return True
    suffix = "." + required_tool
    for item in list_tools(base_url, namespace):
        tool_id = str(item.get("id") or "")
        tool_name = str(item.get("name") or "")
        if tool_name == required_tool or tool_id == required_tool or tool_id.endswith(suffix):
            return True
    return False


def delete_existing(base_url: str, namespace: str) -> None:
    http_json(
        base_url.rstrip("/") + f"/api/operations/integrations/sources/{quote(namespace, safe='')}",
        method="DELETE",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://111.229.194.203/manage")
    parser.add_argument("--namespace", default="x-syndication-readonly")
    parser.add_argument("--name", default="X Syndication Readonly")
    parser.add_argument("--spec-path", default=str(DEFAULT_SPEC_PATH))
    parser.add_argument("--base-api-url", default="https://cdn.syndication.twimg.com")
    parser.add_argument("--required-tool", default="getTweetResult")
    args = parser.parse_args()

    recreated = False
    existing = find_existing(args.base_url, args.namespace)
    if existing is not None and not has_required_tool(args.base_url, args.namespace, args.required_tool):
        delete_existing(args.base_url, args.namespace)
        existing = None
        recreated = True

    if existing is not None:
        print(
            json.dumps(
                {
                    "created": False,
                    "recreated": False,
                    "requiredTool": args.required_tool,
                    "source": existing,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    spec_text = Path(args.spec_path).read_text(encoding="utf-8")
    payload = {
        "type": "openapi",
        "name": args.name,
        "namespace": args.namespace,
        "baseUrl": args.base_api_url,
        "spec": spec_text,
    }
    _, created = http_json(
        args.base_url.rstrip("/") + "/api/operations/integrations/sources",
        method="POST",
        data=payload,
        timeout=60,
    )
    print(
        json.dumps(
            {
                "created": True,
                "recreated": recreated,
                "requiredTool": args.required_tool,
                "source": created,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
