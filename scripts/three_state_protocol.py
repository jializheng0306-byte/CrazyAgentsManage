#!/usr/bin/env python3
"""
三态通信协议实现 (Three-State Communication Protocol)

基于《OpenClaw 实战》文章的通信协议，防止 Agent 间 ACK 风暴。

状态机: request → confirmed → final → 静默
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, List, Dict

SHARED_CONTEXT = Path(os.environ.get(
    "SHARED_CONTEXT_DIR",
    os.path.expanduser("~/CrazyAgentsManage/shared-context")
))
REQUESTS_DIR = SHARED_CONTEXT / "agent-requests"
ROUND_TABLE_DIR = SHARED_CONTEXT / "roundtable"
EVENTS_FILE = REQUESTS_DIR / "events.jsonl"


class MessageState(str, Enum):
    REQUEST = "request"
    CONFIRMED = "confirmed"
    FINAL = "final"


class RequestStatus(str, Enum):
    ACCEPTED = "accepted"
    ROUTED = "routed"
    QUEUED = "queued"
    STARTED = "started"
    COMPLETED = "completed"
    DELIVERED = "delivered"
    TIMED_OUT = "timed_out"
    FAILED = "failed"


class AutomationState(str, Enum):
    PROTOTYPE = "prototype"
    REHEARSED = "rehearsed"
    APPROVED_FOR_AUTOMATION = "approved-for-automation"
    AUTOMATED = "automated"


@dataclass
class ThreeStateMessage:
    ack_id: str
    state: MessageState
    sender: str
    target: str
    content: str
    timestamp: str
    version: int = 1
    deadline: Optional[str] = None
    metadata: Optional[Dict] = None

    def to_line(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_line(cls, line: str) -> "ThreeStateMessage":
        data = json.loads(line)
        data["state"] = MessageState(data["state"])
        return cls(**data)


@dataclass
class AgentRequest:
    request_id: str
    ack_id: str
    sender: str
    target: str
    action: str
    status: RequestStatus
    created_at: str
    updated_at: str
    deadline: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    task_type: str = "task_request"
    owner: Optional[str] = None
    source_plane: str = "roundtable"
    automation_state: AutomationState = AutomationState.PROTOTYPE
    approval: Optional[str] = None
    rollback_rule: Optional[str] = None
    evidence_refs: Optional[List[str]] = None
    note: Optional[str] = None
    last_transition_by: Optional[str] = None
    last_transition_note: Optional[str] = None

    def to_line(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_line(cls, line: str) -> "AgentRequest":
        data = json.loads(line)
        data["status"] = RequestStatus(data["status"])
        if data.get("automation_state"):
            data["automation_state"] = AutomationState(data["automation_state"])
        return cls(**data)


class ThreeStateProtocol:
    """三态通信协议管理器"""

    def __init__(self, requests_dir: Optional[Path] = None,
                 roundtable_dir: Optional[Path] = None):
        self.requests_dir = requests_dir or REQUESTS_DIR
        self.roundtable_dir = roundtable_dir or ROUND_TABLE_DIR
        self.events_file = self.requests_dir / "events.jsonl"
        self.requests_dir.mkdir(parents=True, exist_ok=True)
        self.roundtable_dir.mkdir(parents=True, exist_ok=True)
        self.events_file.parent.mkdir(parents=True, exist_ok=True)

    def send_request(self, ack_id: str, sender: str, target: str,
                     content: str, deadline_minutes: int = 10) -> ThreeStateMessage:
        """发送 request 消息"""
        deadline = (datetime.now() + timedelta(minutes=deadline_minutes)).isoformat()
        msg = ThreeStateMessage(
            ack_id=ack_id,
            state=MessageState.REQUEST,
            sender=sender,
            target=target,
            content=content,
            timestamp=datetime.now().isoformat(),
            deadline=deadline
        )
        self._append_message(msg)
        self._create_request(msg)
        return msg

    def send_confirmed(self, ack_id: str, sender: str, target: str,
                       content: str, version: int = 1) -> ThreeStateMessage:
        """发送 confirmed 消息"""
        msg = ThreeStateMessage(
            ack_id=ack_id,
            state=MessageState.CONFIRMED,
            sender=sender,
            target=target,
            content=content,
            timestamp=datetime.now().isoformat(),
            version=version
        )
        self._append_message(msg)
        self._update_request(ack_id, RequestStatus.COMPLETED)
        return msg

    def send_final(self, ack_id: str, sender: str, target: str,
                   content: str) -> ThreeStateMessage:
        """发送 final 消息（终态，全员静默）"""
        msg = ThreeStateMessage(
            ack_id=ack_id,
            state=MessageState.FINAL,
            sender=sender,
            target=target,
            content=content,
            timestamp=datetime.now().isoformat()
        )
        self._append_message(msg)
        self._update_request(ack_id, RequestStatus.DELIVERED)
        return msg

    def transition_request(
        self,
        ack_id: str,
        status: RequestStatus,
        actor: str = "operator",
        note: str = "",
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Optional[AgentRequest]:
        req = self._get_request(ack_id)
        if not req:
            return None

        current = req.status
        if current != status and status not in self.allowed_status_transitions(current):
            raise ValueError(f"invalid transition: {current.value} -> {status.value}")

        req.status = status
        req.updated_at = datetime.now().isoformat()
        req.last_transition_by = actor
        req.last_transition_note = note or None
        if result is not None:
            req.result = result
        if error is not None:
            req.error = error
        self._save_request(req)
        self._append_event(
            ack_id=ack_id,
            event_type="status_transition",
            actor=actor,
            payload={
                "from_status": current.value,
                "to_status": status.value,
                "note": note,
                "result": result,
                "error": error,
            },
        )
        return req

    def set_automation_state(
        self,
        ack_id: str,
        automation_state: AutomationState,
        actor: str = "operator",
        approval: str = "",
        rollback_rule: str = "",
        evidence_refs: Optional[List[str]] = None,
        note: str = "",
    ) -> Optional[AgentRequest]:
        req = self._get_request(ack_id)
        if not req:
            return None

        current = req.automation_state
        req.automation_state = automation_state
        req.updated_at = datetime.now().isoformat()
        req.approval = approval or req.approval
        req.rollback_rule = rollback_rule or req.rollback_rule
        req.evidence_refs = evidence_refs or req.evidence_refs or []
        req.note = note or req.note
        req.last_transition_by = actor
        req.last_transition_note = note or None
        self._save_request(req)
        self._append_event(
            ack_id=ack_id,
            event_type="automation_promotion",
            actor=actor,
            payload={
                "from_state": current.value if current else "",
                "to_state": automation_state.value,
                "approval": approval,
                "rollback_rule": rollback_rule,
                "evidence_refs": evidence_refs or [],
                "note": note,
            },
        )
        return req

    def allowed_status_transitions(self, current_status: RequestStatus) -> set[RequestStatus]:
        transitions = {
            RequestStatus.ACCEPTED: {RequestStatus.ROUTED, RequestStatus.QUEUED, RequestStatus.STARTED, RequestStatus.FAILED, RequestStatus.TIMED_OUT},
            RequestStatus.ROUTED: {RequestStatus.QUEUED, RequestStatus.STARTED, RequestStatus.FAILED, RequestStatus.TIMED_OUT},
            RequestStatus.QUEUED: {RequestStatus.STARTED, RequestStatus.FAILED, RequestStatus.TIMED_OUT},
            RequestStatus.STARTED: {RequestStatus.COMPLETED, RequestStatus.FAILED, RequestStatus.TIMED_OUT},
            RequestStatus.COMPLETED: {RequestStatus.DELIVERED, RequestStatus.FAILED},
            RequestStatus.DELIVERED: set(),
            RequestStatus.TIMED_OUT: set(),
            RequestStatus.FAILED: set(),
        }
        return transitions.get(current_status, set())

    def check_timeouts(self) -> List[AgentRequest]:
        """检查超时的请求"""
        timed_out = []
        now = datetime.now()
        for req_file in self.requests_dir.glob("requests.jsonl"):
            for line in req_file.read_text().strip().split("\n"):
                if not line.strip():
                    continue
                req = AgentRequest.from_line(line)
                if req.status in (RequestStatus.DELIVERED, RequestStatus.FAILED,
                                  RequestStatus.TIMED_OUT):
                    continue
                if req.deadline:
                    deadline = datetime.fromisoformat(req.deadline)
                    if now > deadline:
                        req.status = RequestStatus.TIMED_OUT
                        req.updated_at = now.isoformat()
                        timed_out.append(req)
        return timed_out

    def get_pending_requests(self) -> List[AgentRequest]:
        """获取所有待处理的请求"""
        pending = []
        for req_file in self.requests_dir.glob("requests.jsonl"):
            for line in req_file.read_text().strip().split("\n"):
                if not line.strip():
                    continue
                req = AgentRequest.from_line(line)
                if req.status not in (RequestStatus.DELIVERED, RequestStatus.FAILED,
                                      RequestStatus.TIMED_OUT):
                    pending.append(req)
        return pending

    def get_conversation(self, ack_id: str) -> List[ThreeStateMessage]:
        """获取某个 ack_id 的完整对话"""
        messages = []
        for msg_file in self.roundtable_dir.glob("*.jsonl"):
            for line in msg_file.read_text().strip().split("\n"):
                if not line.strip():
                    continue
                msg = ThreeStateMessage.from_line(line)
                if msg.ack_id == ack_id:
                    messages.append(msg)
        return sorted(messages, key=lambda m: m.timestamp)

    def validate_transition(self, ack_id: str,
                            new_state: MessageState) -> bool:
        """验证状态转换是否合法"""
        conversation = self.get_conversation(ack_id)
        if not conversation:
            return new_state == MessageState.REQUEST

        last_msg = conversation[-1]
        transitions = {
            MessageState.REQUEST: {MessageState.CONFIRMED},
            MessageState.CONFIRMED: {MessageState.FINAL},
            MessageState.FINAL: set(),  # 终态，不可转换
        }
        return new_state in transitions.get(last_msg.state, set())

    def _append_message(self, msg: ThreeStateMessage):
        """追加消息到 roundtable 日志"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        msg_file = self.roundtable_dir / f"messages-{date_str}.jsonl"
        with open(msg_file, "a") as f:
            f.write(msg.to_line() + "\n")

    def _create_request(self, msg: ThreeStateMessage):
        """创建请求记录"""
        metadata = msg.metadata or {}
        req = AgentRequest(
            request_id=f"req-{msg.ack_id}",
            ack_id=msg.ack_id,
            sender=msg.sender,
            target=msg.target,
            action=msg.content,
            status=RequestStatus.ACCEPTED,
            created_at=msg.timestamp,
            updated_at=msg.timestamp,
            deadline=msg.deadline,
            task_type=str(metadata.get("task_type") or "task_request"),
            owner=str(metadata.get("owner") or msg.target or ""),
            source_plane=str(metadata.get("source_plane") or "roundtable"),
            evidence_refs=metadata.get("evidence_refs") or [],
            note=str(metadata.get("note") or ""),
        )
        self._append_request(req)
        self._append_event(
            ack_id=req.ack_id,
            event_type="request_created",
            actor=req.sender,
            payload={
                "status": req.status.value,
                "task_type": req.task_type,
                "owner": req.owner,
                "source_plane": req.source_plane,
            },
        )

    def _update_request(self, ack_id: str, status: RequestStatus):
        """更新请求状态"""
        req = self._get_request(ack_id)
        if not req:
            return
        old_status = req.status
        req.status = status
        req.updated_at = datetime.now().isoformat()
        self._save_request(req)
        self._append_event(
            ack_id=ack_id,
            event_type="status_transition",
            actor=req.target or "system",
            payload={
                "from_status": old_status.value,
                "to_status": status.value,
                "note": "protocol auto-update",
            },
        )

    def _append_request(self, req: AgentRequest):
        req_file = self.requests_dir / "requests.jsonl"
        with open(req_file, "a", encoding="utf-8") as f:
            f.write(req.to_line() + "\n")

    def _load_requests(self) -> List[AgentRequest]:
        req_file = self.requests_dir / "requests.jsonl"
        if not req_file.exists():
            return []
        lines = req_file.read_text(encoding="utf-8").splitlines()
        requests = []
        for line in lines:
            if not line.strip():
                continue
            requests.append(AgentRequest.from_line(line))
        return requests

    def _save_all_requests(self, requests: List[AgentRequest]):
        req_file = self.requests_dir / "requests.jsonl"
        content = "\n".join(req.to_line() for req in requests)
        if content:
            content += "\n"
        req_file.write_text(content, encoding="utf-8")

    def _get_request(self, ack_id: str) -> Optional[AgentRequest]:
        for req in self._load_requests():
            if req.ack_id == ack_id:
                return req
        return None

    def _save_request(self, request: AgentRequest):
        requests = self._load_requests()
        updated = False
        for idx, req in enumerate(requests):
            if req.ack_id == request.ack_id:
                requests[idx] = request
                updated = True
                break
        if not updated:
            requests.append(request)
        self._save_all_requests(requests)

    def _append_event(self, ack_id: str, event_type: str, actor: str, payload: Dict):
        row = {
            "ack_id": ack_id,
            "event_type": event_type,
            "actor": actor,
            "timestamp": datetime.now().isoformat(),
            "payload": payload,
        }
        with open(self.events_file, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def format_message(msg: ThreeStateMessage) -> str:
    """格式化消息为飞书群可读格式"""
    state_emoji = {
        MessageState.REQUEST: "🔵",
        MessageState.CONFIRMED: "🟢",
        MessageState.FINAL: "🔴",
    }
    emoji = state_emoji.get(msg.state, "⚪")
    return (
        f"{emoji} @{msg.target} [state={msg.state.value}] "
        f"[ack_id={msg.ack_id}]\n{msg.content}"
    )


if __name__ == "__main__":
    import sys

    protocol = ThreeStateProtocol()

    if len(sys.argv) < 2:
        print("用法:")
        print("  python three_state_protocol.py send <ack_id> <sender> <target> <content>")
        print("  python three_state_protocol.py confirm <ack_id> <sender> <target> <content>")
        print("  python three_state_protocol.py final <ack_id> <sender> <target> <content>")
        print("  python three_state_protocol.py status")
        print("  python three_state_protocol.py timeouts")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "send" and len(sys.argv) >= 6:
        msg = protocol.send_request(sys.argv[2], sys.argv[3], sys.argv[4], " ".join(sys.argv[5:]))
        print(format_message(msg))

    elif cmd == "confirm" and len(sys.argv) >= 6:
        msg = protocol.send_confirmed(sys.argv[2], sys.argv[3], sys.argv[4], " ".join(sys.argv[5:]))
        print(format_message(msg))

    elif cmd == "final" and len(sys.argv) >= 6:
        msg = protocol.send_final(sys.argv[2], sys.argv[3], sys.argv[4], " ".join(sys.argv[5:]))
        print(format_message(msg))

    elif cmd == "transition" and len(sys.argv) >= 5:
        req = protocol.transition_request(
            sys.argv[2],
            RequestStatus(sys.argv[3]),
            actor=sys.argv[4],
            note=" ".join(sys.argv[5:]),
        )
        if req:
            print(req.to_line())
        else:
            print("  未找到请求")

    elif cmd == "promote" and len(sys.argv) >= 5:
        req = protocol.set_automation_state(
            sys.argv[2],
            AutomationState(sys.argv[3]),
            actor=sys.argv[4],
            note=" ".join(sys.argv[5:]),
        )
        if req:
            print(req.to_line())
        else:
            print("  未找到请求")

    elif cmd == "status":
        pending = protocol.get_pending_requests()
        if pending:
            for req in pending:
                print(f"  {req.ack_id}: {req.sender}→{req.target} [{req.status.value}] deadline={req.deadline}")
        else:
            print("  无待处理请求")

    elif cmd == "timeouts":
        timed_out = protocol.check_timeouts()
        if timed_out:
            for req in timed_out:
                print(f"  ⏰ {req.ack_id}: 超时! {req.sender}→{req.target}")
        else:
            print("  无超时请求")
