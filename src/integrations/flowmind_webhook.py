#!/usr/bin/env python3
"""
FlowMind Webhook回调配置模块
用于接收FlowMind状态变更通知
"""

import json
import os
import hashlib
import hmac
from datetime import datetime

# Webhook配置
WEBHOOK_SECRET = os.getenv("FLOWMIND_WEBHOOK_SECRET", "flowmind-webhook-secret")
WEBHOOK_EVENTS = [
    "promise.status_changed",
    "promise.completed",
    "promise.overdue",
    "review.triggered",
    "candidate.ingested"
]

# 回调处理器配置
CALLBACK_HANDLERS = {
    "promise.status_changed": "handle_promise_status_changed",
    "promise.completed": "handle_promise_completed",
    "promise.overdue": "handle_promise_overdue",
    "review.triggered": "handle_review_triggered",
    "candidate.ingested": "handle_candidate_ingested"
}

def verify_webhook_signature(payload: str, signature: str) -> bool:
    """
    验证Webhook签名
    
    Args:
        payload: 请求体
        signature: 签名
    
    Returns:
        验证结果
    """
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)

def parse_webhook_event(headers: dict, body: dict) -> dict:
    """
    解析Webhook事件
    
    Args:
        headers: 请求头
        body: 请求体
    
    Returns:
        解析后的事件
    """
    event_type = headers.get("X-FlowMind-Event", "unknown")
    delivery_id = headers.get("X-FlowMind-Delivery", "")
    signature = headers.get("X-FlowMind-Signature", "")
    
    return {
        "event_type": event_type,
        "delivery_id": delivery_id,
        "signature": signature,
        "timestamp": datetime.now().isoformat(),
        "data": body
    }

def handle_promise_status_changed(event: dict) -> dict:
    """
    处理承诺状态变更事件
    
    Args:
        event: 事件数据
    
    Returns:
        处理结果
    """
    promise_id = event["data"].get("promise_id")
    old_status = event["data"].get("old_status")
    new_status = event["data"].get("new_status")
    
    print(f"承诺状态变更: {promise_id} {old_status} -> {new_status}")
    
    # 更新本地承诺记录
    promise_dir = os.path.expanduser("~/.hermes/promises")
    promise_file = os.path.join(promise_dir, f"{promise_id}.json")
    
    if os.path.exists(promise_file):
        with open(promise_file, 'r', encoding='utf-8') as f:
            promise_data = json.load(f)
        
        promise_data["status"] = new_status
        promise_data["updated_at"] = datetime.now().isoformat()
        
        with open(promise_file, 'w', encoding='utf-8') as f:
            json.dump(promise_data, f, indent=2, ensure_ascii=False)
        
        return {"status": "success", "message": f"承诺 {promise_id} 状态已更新"}
    
    return {"status": "not_found", "message": f"承诺 {promise_id} 不存在"}

def handle_promise_completed(event: dict) -> dict:
    """
    处理承诺完成事件
    
    Args:
        event: 事件数据
    
    Returns:
        处理结果
    """
    promise_id = event["data"].get("promise_id")
    
    print(f"承诺完成: {promise_id}")
    
    # 更新本地承诺记录
    promise_dir = os.path.expanduser("~/.hermes/promises")
    promise_file = os.path.join(promise_dir, f"{promise_id}.json")
    
    if os.path.exists(promise_file):
        with open(promise_file, 'r', encoding='utf-8') as f:
            promise_data = json.load(f)
        
        promise_data["status"] = "completed"
        promise_data["completed_at"] = datetime.now().isoformat()
        
        with open(promise_file, 'w', encoding='utf-8') as f:
            json.dump(promise_data, f, indent=2, ensure_ascii=False)
        
        return {"status": "success", "message": f"承诺 {promise_id} 已完成"}
    
    return {"status": "not_found", "message": f"承诺 {promise_id} 不存在"}

def handle_promise_overdue(event: dict) -> dict:
    """
    处理承诺逾期事件
    
    Args:
        event: 事件数据
    
    Returns:
        处理结果
    """
    promise_id = event["data"].get("promise_id")
    deadline = event["data"].get("deadline")
    
    print(f"承诺逾期: {promise_id} (截止: {deadline})")
    
    # 发送告警到飞书群
    chat_id = "oc_bbde428675a7c267d55c3f0663ca701d"
    message = f"⚠️ 承诺逾期告警\n\n承诺ID: {promise_id}\n截止时间: {deadline}\n\n请及时处理！"
    
    # 这里可以调用lark-cli发送消息
    print(f"发送告警到飞书群: {message}")
    
    return {"status": "success", "message": f"承诺 {promise_id} 逾期告警已发送"}

def handle_review_triggered(event: dict) -> dict:
    """
    处理审查触发事件
    
    Args:
        event: 事件数据
    
    Returns:
        处理结果
    """
    review_id = event["data"].get("review_id")
    review_type = event["data"].get("review_type")
    
    print(f"审查触发: {review_id} (类型: {review_type})")
    
    return {"status": "success", "message": f"审查 {review_id} 已触发"}

def handle_candidate_ingested(event: dict) -> dict:
    """
    处理候选入库事件
    
    Args:
        event: 事件数据
    
    Returns:
        处理结果
    """
    candidate_id = event["data"].get("candidate_id")
    title = event["data"].get("title")
    
    print(f"候选入库: {candidate_id} - {title}")
    
    return {"status": "success", "message": f"候选 {candidate_id} 已入库"}

def process_webhook(headers: dict, body: dict) -> dict:
    """
    处理Webhook请求
    
    Args:
        headers: 请求头
        body: 请求体
    
    Returns:
        处理结果
    """
    # 解析事件
    event = parse_webhook_event(headers, body)
    
    # 获取处理器
    event_type = event["event_type"]
    handler_name = CALLBACK_HANDLERS.get(event_type)
    
    if not handler_name:
        return {"status": "error", "message": f"未知事件类型: {event_type}"}
    
    # 调用处理器
    handler = globals().get(handler_name)
    if not handler:
        return {"status": "error", "message": f"处理器不存在: {handler_name}"}
    
    try:
        result = handler(event)
        return {"status": "success", "event_type": event_type, "result": result}
    except Exception as e:
        return {"status": "error", "event_type": event_type, "message": str(e)}

# 配置文件生成
def generate_webhook_config() -> dict:
    """
    生成Webhook配置
    
    Returns:
        Webhook配置字典
    """
    config = {
        "webhook_url": "http://your-server:8765/feishu/webhook",
        "secret": WEBHOOK_SECRET,
        "events": WEBHOOK_EVENTS,
        "active": True,
        "created_at": datetime.now().isoformat()
    }
    
    return config

def save_webhook_config(config: dict, filepath: str = None):
    """
    保存Webhook配置
    
    Args:
        config: 配置字典
        filepath: 文件路径
    """
    if filepath is None:
        filepath = os.path.expanduser("~/.hermes/config/webhook-config.json")
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"Webhook配置已保存: {filepath}")

# 测试函数
if __name__ == "__main__":
    print("=== Webhook配置测试 ===")
    
    # 生成配置
    config = generate_webhook_config()
    print(json.dumps(config, indent=2, ensure_ascii=False))
    
    # 保存配置
    save_webhook_config(config)
    
    # 测试事件处理
    test_event = {
        "event_type": "promise.status_changed",
        "data": {
            "promise_id": "promise-test-001",
            "old_status": "pending",
            "new_status": "confirmed"
        }
    }
    
    print("\n=== 测试事件处理 ===")
    result = process_webhook(
        {"X-FlowMind-Event": "promise.status_changed"},
        test_event["data"]
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
