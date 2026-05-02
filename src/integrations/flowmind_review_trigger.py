#!/usr/bin/env python3
"""
FlowMind Review Trigger调用模块
用于触发FlowMind Review工作流
"""

import json
import requests
import os
from datetime import datetime

# FlowMind配置
FLOWMIND_URL = os.getenv("FLOWMIND_URL", "https://exclusive-harrison-mixed-dat.trycloudflare.com")
FLOWMIND_TOKEN = os.getenv("FLOWMIND_TOKEN", "flowmind-dev-token")

def trigger_review(
    promise_id: str,
    review_type: str = "daily",
    reviewer: str = "hermes-agent",
    context: dict = None
) -> dict:
    """
    触发Review工作流
    
    Args:
        promise_id: 承诺ID
        review_type: 审查类型 (daily/weekly/monthly/manual)
        reviewer: 审查者
        context: 上下文信息
    
    Returns:
        API响应字典
    """
    url = f"{FLOWMIND_URL}/api/integrations/review-trigger"
    
    headers = {
        "Authorization": f"Bearer {FLOWMIND_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "promise_id": promise_id,
        "review_type": review_type,
        "reviewer": reviewer,
        "triggered_at": datetime.now().isoformat(),
        "context": context or {
            "source": "hermes-agent",
            "reason": "scheduled_review"
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "status": "failed"}

def trigger_daily_review(promise_id: str) -> dict:
    """
    触发每日审查
    
    Args:
        promise_id: 承诺ID
    
    Returns:
        API响应字典
    """
    return trigger_review(
        promise_id=promise_id,
        review_type="daily",
        reviewer="hermes-agent",
        context={
            "source": "daily_review",
            "reason": "scheduled_daily_review",
            "schedule": "09:00"
        }
    )

def trigger_weekly_review(promise_id: str) -> dict:
    """
    触发每周审查
    
    Args:
        promise_id: 承诺ID
    
    Returns:
        API响应字典
    """
    return trigger_review(
        promise_id=promise_id,
        review_type="weekly",
        reviewer="hermes-agent",
        context={
            "source": "weekly_review",
            "reason": "scheduled_weekly_review",
            "schedule": "sunday_10:00"
        }
    )

def trigger_manual_review(promise_id: str, reason: str) -> dict:
    """
    触发手动审查
    
    Args:
        promise_id: 承诺ID
        reason: 审查原因
    
    Returns:
        API响应字典
    """
    return trigger_review(
        promise_id=promise_id,
        review_type="manual",
        reviewer="hermes-agent",
        context={
            "source": "manual_review",
            "reason": reason,
            "triggered_by": "user_request"
        }
    )

def trigger_overdue_review(promise_id: str) -> dict:
    """
    触发逾期审查
    
    Args:
        promise_id: 承诺ID
    
    Returns:
        API响应字典
    """
    return trigger_review(
        promise_id=promise_id,
        review_type="overdue",
        reviewer="hermes-agent",
        context={
            "source": "overdue_review",
            "reason": "promise_overdue",
            "alert_level": "P1"
        }
    )

def batch_trigger_reviews(promise_ids: list, review_type: str = "daily") -> dict:
    """
    批量触发审查
    
    Args:
        promise_ids: 承诺ID列表
        review_type: 审查类型
    
    Returns:
        批量处理结果
    """
    results = []
    
    for promise_id in promise_ids:
        result = trigger_review(
            promise_id=promise_id,
            review_type=review_type,
            reviewer="hermes-agent"
        )
        results.append({
            "promise_id": promise_id,
            "result": result
        })
    
    return {
        "total": len(promise_ids),
        "success": sum(1 for r in results if r["result"].get("status") != "failed"),
        "failed": sum(1 for r in results if r["result"].get("status") == "failed"),
        "results": results
    }

# 本地Review记录管理
def save_review_record(promise_id: str, review_type: str, result: dict):
    """
    保存审查记录
    
    Args:
        promise_id: 承诺ID
        review_type: 审查类型
        result: 审查结果
    """
    review_dir = os.path.expanduser("~/.hermes/promises/reviews")
    os.makedirs(review_dir, exist_ok=True)
    
    review_file = os.path.join(review_dir, f"{promise_id}-{review_type}-{datetime.now().strftime('%Y%m%d%H%M%S')}.json")
    
    review_record = {
        "promise_id": promise_id,
        "review_type": review_type,
        "reviewed_at": datetime.now().isoformat(),
        "result": result
    }
    
    with open(review_file, 'w', encoding='utf-8') as f:
        json.dump(review_record, f, indent=2, ensure_ascii=False)
    
    print(f"审查记录已保存: {review_file}")

# 测试函数
if __name__ == "__main__":
    print("=== Review Trigger测试 ===")
    
    # 测试触发每日审查
    print("\n1. 触发每日审查:")
    result = trigger_daily_review("promise-test-001")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 保存审查记录
    save_review_record("promise-test-001", "daily", result)
    
    print("\n=== 测试完成 ===")
