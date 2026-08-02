#!/usr/bin/env python3
"""Validate Crazy live executor http mode by creating a real temporary source."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest


PETSTORE_SPEC_URL = "https://petstore3.swagger.io/api/v3/openapi.json"
PETSTORE_BASE_URL = "https://petstore3.swagger.io/api/v3"


def http_json(url: str, method: str = "GET", data: dict | None = None, timeout: int = 20):
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


def fetch_text(url: str, timeout: int = 20) -> str:
    req = urlrequest.Request(url, method="GET", headers={"Accept": "application/json"})
    with urlrequest.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def build_url(base_url: str, path: str, **query: str) -> str:
    url = base_url.rstrip("/") + path
    filtered = {key: value for key, value in query.items() if value}
    if filtered:
        url += "?" + urlparse.urlencode(filtered)
    return url


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://111.229.194.203/manage")
    parser.add_argument("--namespace-prefix", default="petstore-validation")
    parser.add_argument("--keep-source", action="store_true")
    args = parser.parse_args()

    report: dict[str, object] = {
        "ok": False,
        "baseUrl": args.base_url,
        "providerMode": None,
        "createdSourceId": None,
        "toolCount": 0,
        "cleanupRemoved": None,
        "checks": [],
    }

    namespace = f"{args.namespace_prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    created_source_id = None

    def add_check(name: str, ok: bool, detail: object) -> None:
        report["checks"].append({"name": name, "ok": ok, "detail": detail})

    try:
        _, provider_mode = http_json(build_url(args.base_url, "/api/operations/integrations/provider-mode"))
        mode = (provider_mode or {}).get("mode")
        report["providerMode"] = mode
        add_check("provider-mode", mode == "http", provider_mode)
        if mode != "http":
            raise RuntimeError(f"expected http mode, got {mode!r}")

        _, page_probe = http_json(build_url(args.base_url, "/api/operations/integrations/summary"))
        add_check("summary-endpoint", isinstance(page_probe, dict), page_probe)

        spec_text = fetch_text(PETSTORE_SPEC_URL)
        add_check("fetch-openapi-spec", bool(spec_text), {"url": PETSTORE_SPEC_URL, "bytes": len(spec_text)})

        create_payload = {
            "type": "openapi",
            "name": "Petstore Validation Source",
            "namespace": namespace,
            "baseUrl": PETSTORE_BASE_URL,
            "spec": spec_text,
        }
        _, created = http_json(
            build_url(args.base_url, "/api/operations/integrations/sources"),
            method="POST",
            data=create_payload,
        )
        created_source_id = (created or {}).get("id") or namespace
        report["createdSourceId"] = created_source_id
        add_check("create-source", bool(created_source_id), created)

        _, sources = http_json(build_url(args.base_url, "/api/operations/integrations/sources"))
        live_source = next((item for item in (sources or []) if item.get("id") == created_source_id), None)
        add_check("source-visible", live_source is not None, live_source or sources)
        if live_source is None:
            raise RuntimeError("created source did not appear in source list")

        _, tools = http_json(
            build_url(args.base_url, "/api/operations/integrations/tools", sourceId=created_source_id)
        )
        tool_count = len(tools or [])
        report["toolCount"] = tool_count
        add_check("tool-catalog", tool_count > 0, {"toolCount": tool_count, "sample": (tools or [])[:3]})
        if tool_count <= 0:
            raise RuntimeError("created source produced zero tools")

        _, providers = http_json(build_url(args.base_url, "/api/operations/integrations/providers"))
        provider = next((item for item in (providers or []) if item.get("provider") == "openapi"), None)
        add_check("provider-rollup", provider is not None, provider or providers)

        _, summary = http_json(build_url(args.base_url, "/api/operations/integrations/summary"))
        add_check("summary-rollup", isinstance(summary, dict) and summary.get("sourceCount", 0) >= 1, summary)

        if not args.keep_source and created_source_id:
            _, removed = http_json(
                build_url(args.base_url, f"/api/operations/integrations/sources/{created_source_id}"),
                method="DELETE",
            )
            report["cleanupRemoved"] = bool((removed or {}).get("success"))
            add_check("cleanup-source", report["cleanupRemoved"] is True, removed)

        report["ok"] = True
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (RuntimeError, urlerror.URLError, urlerror.HTTPError, TimeoutError, ValueError) as exc:
        report["error"] = str(exc)
        if created_source_id and not args.keep_source:
            try:
                _, removed = http_json(
                    build_url(args.base_url, f"/api/operations/integrations/sources/{created_source_id}"),
                    method="DELETE",
                )
                report["cleanupRemoved"] = bool((removed or {}).get("success"))
            except Exception:
                report["cleanupRemoved"] = False
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
