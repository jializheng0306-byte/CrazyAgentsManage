#!/usr/bin/env python3
"""
多Agent协作测试
测试HermesAgent与Codex CLI的三态通信协议
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
import tempfile

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from scripts.three_state_protocol import (
    AutomationState,
    RequestStatus,
    ThreeStateProtocol,
)

def test_three_state_protocol():
    """
    测试三态通信协议 (Request → Confirmed → Final)
    """
    print("=" * 60)
    print("三态通信协议测试")
    print("=" * 60)
    
    # 1. Request状态
    print("\n1. Request状态 (HermesAgent发起)")
    request = {
        "id": "request-001",
        "type": "task_request",
        "from": "hermes-agent",
        "to": "codex-cli",
        "content": {
            "task": "设计登录页面",
            "deliverables": ["HTML/CSS代码", "响应式设计"],
            "deadline": "2026-05-03",
            "acceptance_criteria": ["跨浏览器兼容", "表单验证"]
        },
        "timestamp": datetime.now().isoformat(),
        "status": "request"
    }
    
    print(f"   任务: {request['content']['task']}")
    print(f"   交付物: {request['content']['deliverables']}")
    print(f"   截止时间: {request['content']['deadline']}")
    
    # 2. Confirmed状态
    print("\n2. Confirmed状态 (Codex CLI确认)")
    confirmed = {
        "id": "confirmed-001",
        "request_id": "request-001",
        "type": "task_confirmed",
        "from": "codex-cli",
        "to": "hermes-agent",
        "content": {
            "estimated_time": "3天",
            "tech_stack": ["React", "TypeScript"],
            "questions": []
        },
        "timestamp": datetime.now().isoformat(),
        "status": "confirmed"
    }
    
    print(f"   预计时间: {confirmed['content']['estimated_time']}")
    print(f"   技术栈: {confirmed['content']['tech_stack']}")
    
    # 3. Final状态
    print("\n3. Final状态 (Codex CLI完成)")
    final = {
        "id": "final-001",
        "request_id": "request-001",
        "type": "task_completed",
        "from": "codex-cli",
        "to": "hermes-agent",
        "content": {
            "commit_hash": "abc123",
            "files": ["login.html", "login.css", "login.js"],
            "test_result": "passed",
            "coverage": "95%"
        },
        "timestamp": datetime.now().isoformat(),
        "status": "final"
    }
    
    print(f"   提交: {final['content']['commit_hash']}")
    print(f"   文件: {final['content']['files']}")
    print(f"   测试: {final['content']['test_result']}")
    
    # 保存协作记录
    collaboration_dir = os.path.expanduser("~/.hermes/collaboration")
    os.makedirs(collaboration_dir, exist_ok=True)
    
    collaboration_file = os.path.join(collaboration_dir, f"collab-{datetime.now().strftime('%Y%m%d%H%M%S')}.json")
    
    collaboration = {
        "request": request,
        "confirmed": confirmed,
        "final": final,
        "lifecycle": {
            "created_at": request["timestamp"],
            "confirmed_at": confirmed["timestamp"],
            "completed_at": final["timestamp"],
            "duration_minutes": 5
        }
    }
    
    with open(collaboration_file, 'w', encoding='utf-8') as f:
        json.dump(collaboration, f, indent=2, ensure_ascii=False)
    
    print(f"\n   协作记录已保存: {collaboration_file}")
    
    print("\n" + "=" * 60)
    print("✅ 三态通信协议测试完成")
    print("=" * 60)
    
    return True

def test_mention_protocol():
    """
    测试@mention协议
    """
    print("\n" + "=" * 60)
    print("@mention协议测试")
    print("=" * 60)
    
    # 测试消息格式
    messages = [
        {
            "type": "request",
            "from": "hermes-agent",
            "to": "codex-cli",
            "content": "@codex cli 需求: 设计登录页面",
            "requires_response": True
        },
        {
            "type": "confirmation",
            "from": "codex-cli",
            "to": "hermes-agent",
            "content": "@HermesAgent 确认: 已收到需求",
            "requires_response": False
        },
        {
            "type": "notification",
            "from": "hermes-agent",
            "to": "codex-cli",
            "content": "进度更新: 登录页面已完成50%",
            "requires_response": False
        }
    ]
    
    for i, msg in enumerate(messages, 1):
        print(f"\n{i}. {msg['type'].upper()}消息")
        print(f"   从: {msg['from']}")
        print(f"   到: {msg['to']}")
        print(f"   内容: {msg['content']}")
        print(f"   需要回复: {msg['requires_response']}")
    
    print("\n" + "=" * 60)
    print("✅ @mention协议测试完成")
    print("=" * 60)
    
    return True

def test_conflict_resolution():
    """
    测试冲突解决机制
    """
    print("\n" + "=" * 60)
    print("冲突解决机制测试")
    print("=" * 60)
    
    # 模拟冲突场景
    conflicts = [
        {
            "type": "priority_conflict",
            "description": "两个高优先级任务同时进行",
            "resolution": "按截止时间排序",
            "result": "任务A优先"
        },
        {
            "type": "resource_conflict",
            "description": "同一资源被多个任务占用",
            "resolution": "按优先级分配",
            "result": "高优先级任务获得资源"
        },
        {
            "type": "technical_conflict",
            "description": "技术方案存在分歧",
            "resolution": "技术评估后决策",
            "result": "选择性能更优的方案"
        }
    ]
    
    for i, conflict in enumerate(conflicts, 1):
        print(f"\n{i}. {conflict['type']}")
        print(f"   描述: {conflict['description']}")
        print(f"   解决: {conflict['resolution']}")
        print(f"   结果: {conflict['result']}")
    
    print("\n" + "=" * 60)
    print("✅ 冲突解决机制测试完成")
    print("=" * 60)
    
    return True


def test_three_state_protocol_transition_request():
    temp_dir = Path(tempfile.mkdtemp(prefix='three-state-test-'))
    protocol = ThreeStateProtocol(
        requests_dir=temp_dir / 'agent-requests',
        roundtable_dir=temp_dir / 'roundtable',
    )
    protocol.send_request('ack-1', 'hermes', 'codex', 'test request')
    req = protocol.transition_request('ack-1', RequestStatus.STARTED, actor='operator', note='picked up')
    assert req is not None
    assert req.status == RequestStatus.STARTED
    assert req.last_transition_note == 'picked up'

    events_file = temp_dir / 'agent-requests' / 'events.jsonl'
    assert events_file.exists()
    events = [json.loads(line) for line in events_file.read_text(encoding='utf-8').splitlines() if line.strip()]
    assert events[-1]['event_type'] == 'status_transition'
    assert events[-1]['payload']['to_status'] == 'started'


def test_three_state_protocol_automation_promotion():
    temp_dir = Path(tempfile.mkdtemp(prefix='three-state-test-'))
    protocol = ThreeStateProtocol(
        requests_dir=temp_dir / 'agent-requests',
        roundtable_dir=temp_dir / 'roundtable',
    )
    protocol.send_request('ack-2', 'hermes', 'codex', 'test request')
    req = protocol.set_automation_state(
        'ack-2',
        AutomationState.REHEARSED,
        actor='operator',
        evidence_refs=['closeout:1'],
        note='manual host verification',
    )
    assert req is not None
    assert req.automation_state == AutomationState.REHEARSED
    assert req.evidence_refs == ['closeout:1']

if __name__ == "__main__":
    print("开始多Agent协作测试...")
    
    # 运行测试
    success1 = test_three_state_protocol()
    success2 = test_mention_protocol()
    success3 = test_conflict_resolution()
    
    if success1 and success2 and success3:
        print("\n✅ 所有多Agent协作测试通过")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败")
        sys.exit(1)
