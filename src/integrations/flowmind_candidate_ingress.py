#!/usr/bin/env python3
"""
FlowMind Candidate Ingress API 调用模块
用于将承诺候选数据提交到FlowMind系统
"""

import json
import requests
import os
from datetime import datetime

# FlowMind配置
FLOWMIND_URL = os.getenv("FLOWMIND_URL", "https://exclusive-harrison-mixed-dat.trycloudflare.com")
FLOWMIND_TOKEN = os.getenv("FLOWMIND_TOKEN", "flowmind-dev-token")

def submit_candidate(
    title: str,
    description: str,
    raw_data: dict,
    confidence: int = 80,
    source_context: dict = None
) -> dict:
    """
    提交承诺候选到FlowMind
    
    Args:
        title: 承诺标题
        description: 承诺描述
        raw_data: 原始数据字典
        confidence: 置信度(0-100)
        source_context: 来源上下文
    
    Returns:
        API响应字典
    """
    url = f"{FLOWMIND_URL}/api/integrations/candidate-ingress"
    
    headers = {
        "Authorization": f"Bearer {FLOWMIND_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "instanceId": "hermes-agent",
        "title": title,
        "description": description,
        "rawText": json.dumps(raw_data, ensure_ascii=False),
        "confidence": confidence,
        "sourceContext": source_context or {
            "route_id": "promise-governance",
            "action": "created",
            "timestamp": datetime.now().isoformat()
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "status": "failed"}

def submit_promise_candidate(promise_id: str, promise_data: dict) -> dict:
    """
    提交承诺候选到FlowMind
    
    Args:
        promise_id: 承诺ID
        promise_data: 承诺数据
    
    Returns:
        API响应字典
    """
    return submit_candidate(
        title=promise_data.get("title", ""),
        description=promise_data.get("description", ""),
        raw_data={
            "promise_id": promise_id,
            "deliverables": promise_data.get("deliverables", []),
            "deadline": promise_data.get("deadline", ""),
            "acceptance_criteria": promise_data.get("acceptance_criteria", [])
        },
        confidence=85,
        source_context={
            "route_id": "promise-governance",
            "action": "created",
            "promise_id": promise_id
        }
    )

def submit_task_candidate(task_name: str, task_data: dict) -> dict:
    """
    提交任务候选到FlowMind
    
    Args:
        task_name: 任务名称
        task_data: 任务数据
    
    Returns:
        API响应字典
    """
    return submit_candidate(
        title=task_name,
        description=task_data.get("description", ""),
        raw_data={
            "task_name": task_name,
            "priority": task_data.get("priority", ""),
            "category": task_data.get("category", ""),
            "status": task_data.get("status", "")
        },
        confidence=90,
        source_context={
            "route_id": "task-management",
            "action": "created",
            "task_name": task_name
        }
    )

# 测试函数
if __name__ == "__main__":
    # 测试提交承诺候选
    test_promise = {
        "title": "测试承诺",
        "description": "这是一个测试承诺",
        "deliverables": ["交付物1", "交付物2"],
        "deadline": "2026-04-30",
        "acceptance_criteria": ["验收标准1", "验收标准2"]
    }
    
    result = submit_promise_candidate("promise-test-001", test_promise)
    print(json.dumps(result, indent=2, ensure_ascii=False))
