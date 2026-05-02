#!/usr/bin/env python3
"""
FlowMind Truth Query API 调用模块
用于查询FlowMind系统中的承诺真相状态
"""

import json
import requests
import os
from datetime import datetime

# FlowMind配置
FLOWMIND_URL = os.getenv("FLOWMIND_URL", "https://exclusive-harrison-mixed-dat.trycloudflare.com")
FLOWMIND_TOKEN = os.getenv("FLOWMIND_TOKEN", "flowmind-dev-token")

def query_truth(promise_id: str = None, query_params: dict = None) -> dict:
    """
    查询FlowMind中的承诺真相
    
    Args:
        promise_id: 承诺ID（可选）
        query_params: 查询参数（可选）
    
    Returns:
        查询结果字典
    """
    url = f"{FLOWMIND_URL}/api/integrations/truth-query"
    
    headers = {
        "Authorization": f"Bearer {FLOWMIND_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {}
    
    if promise_id:
        payload["promise_id"] = promise_id
    
    if query_params:
        payload.update(query_params)
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "status": "failed"}

def query_promise_status(promise_id: str) -> dict:
    """
    查询承诺状态
    
    Args:
        promise_id: 承诺ID
    
    Returns:
        承诺状态字典
    """
    return query_truth(promise_id=promise_id)

def query_all_promises(status: str = None, limit: int = 100) -> dict:
    """
    查询所有承诺
    
    Args:
        status: 状态过滤（可选）
        limit: 返回数量限制
    
    Returns:
        承诺列表字典
    """
    query_params = {"limit": limit}
    
    if status:
        query_params["status"] = status
    
    return query_truth(query_params=query_params)

def query_promises_by_deadline(deadline: str) -> dict:
    """
    按截止日期查询承诺
    
    Args:
        deadline: 截止日期（YYYY-MM-DD格式）
    
    Returns:
        承诺列表字典
    """
    return query_truth(query_params={"deadline": deadline})

def query_promises_by_priority(priority: str) -> dict:
    """
    按优先级查询承诺
    
    Args:
        priority: 优先级（P0/P1/P2）
    
    Returns:
        承诺列表字典
    """
    return query_truth(query_params={"priority": priority})

def get_promise_summary() -> dict:
    """
    获取承诺摘要统计
    
    Returns:
        摘要统计字典
    """
    result = query_truth(query_params={"summary": True})
    
    if "error" in result:
        return result
    
    # 解析摘要数据
    summary = {
        "total": result.get("total", 0),
        "pending": result.get("pending", 0),
        "in_progress": result.get("in_progress", 0),
        "completed": result.get("completed", 0),
        "overdue": result.get("overdue", 0),
        "due_today": result.get("due_today", 0),
        "due_tomorrow": result.get("due_tomorrow", 0)
    }
    
    return summary

# 测试函数
if __name__ == "__main__":
    # 测试查询承诺状态
    print("=== 测试查询承诺状态 ===")
    result = query_promise_status("promise-test-001")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n=== 测试查询所有承诺 ===")
    result = query_all_promises(limit=10)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n=== 测试获取承诺摘要 ===")
    result = get_promise_summary()
    print(json.dumps(result, indent=2, ensure_ascii=False))
