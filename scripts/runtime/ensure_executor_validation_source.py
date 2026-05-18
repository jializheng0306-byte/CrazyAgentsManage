#!/usr/bin/env python3
"""Ensure a long-lived read-only validation source exists in Crazy/executor."""

from __future__ import annotations

import argparse
import json
import time
from urllib import request as urlrequest
from urllib import error as urlerror


PETSTORE_SPEC_URL = "https://petstore3.swagger.io/api/v3/openapi.json"
PETSTORE_BASE_URL = "https://petstore3.swagger.io/api/v3"


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


def fetch_text(url: str, timeout: int = 30, attempts: int = 4) -> str:
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            req = urlrequest.Request(url, method="GET")
            with urlrequest.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (urlerror.URLError, urlerror.HTTPError, TimeoutError) as exc:
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://47.99.217.1/manage")
    parser.add_argument("--namespace", default="petstore-readonly-validation")
    parser.add_argument("--name", default="Petstore Readonly Validation")
    args = parser.parse_args()

    existing = find_existing(args.base_url, args.namespace)
    if existing is not None:
        print(json.dumps({"created": False, "source": existing}, ensure_ascii=False, indent=2))
        return 0

    spec_text = fetch_text(PETSTORE_SPEC_URL)
    payload = {
        "type": "openapi",
        "name": args.name,
        "namespace": args.namespace,
        "baseUrl": PETSTORE_BASE_URL,
        "spec": spec_text,
    }
    _, created = http_json(
        args.base_url.rstrip("/") + "/api/operations/integrations/sources",
        method="POST",
        data=payload,
        timeout=60,
    )
    print(json.dumps({"created": True, "source": created}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
