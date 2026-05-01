#!/usr/bin/env python3
"""
FlowMind handshake smoke for CrazyAgentsManage.

目标：
1. 注册 Crazy 侧 instance
2. 发送 1 条 synthetic candidate 到 FlowMind
3. 验证 review queue 能看到该 candidate
4. 执行 1 次 reject 清理
5. 验证 feedback pull、context-pack、truth read 至少成功 1 次
"""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone

from flowmind_capture import build_runtime_config, flowmind_json_request, register_instance


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the first Crazy ↔ FlowMind handshake smoke")
    parser.add_argument("--control-plane-url", default="http://111.229.194.203:3301")
    parser.add_argument("--public-url", default="https://www.uncentury.cn")
    parser.add_argument("--base-url", dest="control_plane_url_legacy", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--api-key", default="flowmind-dev-token")
    parser.add_argument("--instance-id", default="crazyagentsmanage-intel-sentinel")
    parser.add_argument("--source-agent", default="hermes")
    parser.add_argument("--server-id", default="ali-hermes")
    parser.add_argument("--plugin-version", default="crazyagentsmanage-link-v1")
    parser.add_argument("--route-id", default="crazyagentsmanage-handshake-smoke")
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> int:
    args = parse_args()
    if args.control_plane_url_legacy:
        args.control_plane_url = args.control_plane_url_legacy
    runtime = build_runtime_config(args)

    registration = register_instance(runtime)
    instance = registration.get("data", {})
    instance_token = instance.get("apiKey")
    if not instance_token:
        raise RuntimeError(f"register instance returned no apiKey: {registration}")

    synthetic_title = f"Crazy↔FlowMind handshake smoke {uuid.uuid4().hex[:8]}"
    ingress = flowmind_json_request(
        base_url=runtime["control_plane_url"],
        api_key=runtime["api_key"],
        method="POST",
        path="/api/integrations/candidate-ingress",
        body={
            "instanceId": runtime["instance_id"],
            "sourceAgent": runtime["source_agent"],
            "title": synthetic_title,
            "description": "Synthetic candidate created by handshake smoke",
            "rawText": json.dumps(
                {
                    "runType": "handshake-smoke",
                    "title": synthetic_title,
                    "originSystem": "CrazyAgentsManage",
                    "routeId": runtime["route_id"],
                },
                ensure_ascii=False,
            ),
            "confidence": 77,
            "sourceContext": {
                "route_id": runtime["route_id"],
                "origin_system": "CrazyAgentsManage",
                "validation": True,
            },
            "timestamp": now_iso(),
        },
    )

    candidate = ingress.get("data", {}) if isinstance(ingress.get("data"), dict) else ingress
    candidate_id = candidate.get("candidateId")
    if not candidate_id:
        raise RuntimeError(f"candidate ingress failed: {ingress}")

    queue = flowmind_json_request(
        base_url=runtime["control_plane_url"],
        api_key=runtime["api_key"],
        method="GET",
        path="/api/integrations/review-queue",
    )

    queue_seen = False
    for group in queue.get("data", []):
        for item in group.get("candidates", []):
            if item.get("id") == candidate_id:
                queue_seen = True
                break
        if queue_seen:
            break
    if not queue_seen:
        raise RuntimeError(f"candidate {candidate_id} not visible in review queue")

    reject = flowmind_json_request(
        base_url=runtime["control_plane_url"],
        api_key=runtime["api_key"],
        method="POST",
        path=f"/api/integrations/candidates/{candidate_id}/reject",
        body={
            "confirmedBy": "codex-cli",
            "rejectedReason": "handshake smoke cleanup",
            "notes": "Synthetic candidate cleanup after handshake smoke",
        },
    )

    feedback_pull = flowmind_json_request(
        base_url=runtime["control_plane_url"],
        api_key=runtime["api_key"],
        method="GET",
        path=f"/api/bridge/feedback/{runtime['instance_id']}",
        instance_token=instance_token,
    )

    context_pack = flowmind_json_request(
        base_url=runtime["control_plane_url"],
        api_key=runtime["api_key"],
        method="POST",
        path="/api/bridge/context-pack",
        instance_token=instance_token,
        body={
            "instanceId": runtime["instance_id"],
            "sourceAgent": runtime["source_agent"],
            "scope": "recent",
            "maxItems": 5,
        },
    )

    truth = flowmind_json_request(
        base_url=runtime["control_plane_url"],
        api_key=runtime["api_key"],
        method="GET",
        path="/api/bridge/truth?limit=5",
    )

    report = {
        "ok": True,
        "runtime": runtime,
        "registration": registration,
        "candidateIngress": ingress,
        "reviewQueueSeen": queue_seen,
        "reject": reject,
        "feedbackPullCount": len(feedback_pull.get("data", [])),
        "contextPackSummary": context_pack.get("data", {}).get("summary", {}),
        "truthCount": truth.get("totalCount", truth.get("data", {}).get("totalCount")),
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
