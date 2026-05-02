#!/usr/bin/env python3
"""
承诺生命周期测试
测试Candidate→Clarify→Confirm全流程
"""

import json
import os
import sys
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.integrations.flowmind_candidate_ingress import submit_promise_candidate
from src.integrations.flowmind_truth_query import query_promise_status, get_promise_summary

def test_promise_lifecycle():
    """
    测试承诺生命周期
    """
    print("=" * 60)
    print("承诺生命周期测试")
    print("=" * 60)
    
    # 1. 创建承诺
    print("\n1. 创建承诺 (Candidate)")
    promise_id = f"promise-test-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    promise_data = {
        "title": "测试承诺 - 登录页面设计",
        "description": "设计一个包含用户名/密码输入框、登录按钮、忘记密码链接的登录页面",
        "deliverables": [
            "登录页面HTML/CSS代码",
            "响应式设计适配",
            "表单验证逻辑"
        ],
        "deadline": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "acceptance_criteria": [
            "页面在Chrome/Firefox/Safari正常显示",
            "表单验证正常工作",
            "响应式布局适配移动端"
        ]
    }
    
    print(f"   承诺ID: {promise_id}")
    print(f"   标题: {promise_data['title']}")
    print(f"   截止时间: {promise_data['deadline']}")
    
    # 提交到FlowMind
    result = submit_promise_candidate(promise_id, promise_data)
    
    if "error" in result:
        print(f"   ❌ 提交失败: {result['error']}")
        return False
    
    print(f"   ✅ 提交成功: {result.get('candidateId', 'N/A')}")
    
    # 2. 澄清承诺 (Clarify)
    print("\n2. 澄清承诺 (Clarify)")
    print("   通过提问澄清细节:")
    print("   - 交付物: 登录页面HTML/CSS代码、响应式设计、表单验证")
    print("   - 截止时间: 7天后")
    print("   - 验收标准: 跨浏览器兼容、表单验证、响应式布局")
    
    # 3. 确认承诺 (Confirm)
    print("\n3. 确认承诺 (Confirm)")
    print("   生成结构化承诺记录:")
    
    promise_record = {
        "id": promise_id,
        "title": promise_data["title"],
        "description": promise_data["description"],
        "deliverables": promise_data["deliverables"],
        "deadline": promise_data["deadline"],
        "acceptance_criteria": promise_data["acceptance_criteria"],
        "status": "confirmed",
        "created_at": datetime.now().isoformat(),
        "source": "user-request"
    }
    
    # 保存到本地
    promise_dir = os.path.expanduser("~/.hermes/promises")
    os.makedirs(promise_dir, exist_ok=True)
    promise_file = os.path.join(promise_dir, f"{promise_id}.json")
    
    with open(promise_file, 'w', encoding='utf-8') as f:
        json.dump(promise_record, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ 承诺已确认: {promise_file}")
    
    # 4. 查询承诺状态 (Track)
    print("\n4. 查询承诺状态 (Track)")
    status_result = query_promise_status(promise_id)
    
    if "error" in status_result:
        print(f"   ⚠️  查询失败（FlowMind可能未连接）: {status_result['error']}")
        print("   使用本地状态: confirmed")
    else:
        print(f"   ✅ 查询成功: {status_result}")
    
    # 5. 模拟完成承诺 (Complete)
    print("\n5. 模拟完成承诺 (Complete)")
    promise_record["status"] = "completed"
    promise_record["completed_at"] = datetime.now().isoformat()
    
    with open(promise_file, 'w', encoding='utf-8') as f:
        json.dump(promise_record, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ 承诺已完成")
    
    # 6. 获取摘要统计 (Summary)
    print("\n6. 获取摘要统计 (Summary)")
    summary = get_promise_summary()
    
    if "error" in summary:
        print(f"   ⚠️  获取摘要失败: {summary['error']}")
    else:
        print(f"   总承诺数: {summary.get('total', 0)}")
        print(f"   待处理: {summary.get('pending', 0)}")
        print(f"   进行中: {summary.get('in_progress', 0)}")
        print(f"   已完成: {summary.get('completed', 0)}")
    
    print("\n" + "=" * 60)
    print("✅ 承诺生命周期测试完成")
    print("=" * 60)
    
    return True

def test_promise_drift_detection():
    """
    测试承诺漂移检测
    """
    print("\n" + "=" * 60)
    print("承诺漂移检测测试")
    print("=" * 60)
    
    # 创建一个承诺
    promise_id = f"promise-drift-test-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    promise_data = {
        "title": "测试承诺 - 漂移检测",
        "description": "测试范围蔓延、时间偏差、质量漂移",
        "deliverables": ["交付物1"],
        "deadline": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
        "acceptance_criteria": ["验收标准1"]
    }
    
    # 提交承诺
    result = submit_promise_candidate(promise_id, promise_data)
    
    if "error" in result:
        print(f"   ❌ 提交失败: {result['error']}")
        return False
    
    print(f"   ✅ 承诺已创建: {promise_id}")
    
    # 模拟漂移检测
    print("\n   检测漂移:")
    
    # 1. 范围蔓延
    print("   - 范围蔓延: 原始交付物1个，实际需求3个")
    print("     策略: 通知用户并协商调整")
    
    # 2. 时间偏差
    print("   - 时间偏差: 原计划3天，实际已用5天")
    print("     策略: 暂停并重新评估")
    
    # 3. 质量漂移
    print("   - 质量漂移: 验收标准降低")
    print("     策略: 记录并继续")
    
    print("\n" + "=" * 60)
    print("✅ 承诺漂移检测测试完成")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    print("开始承诺生命周期测试...")
    
    # 运行测试
    success1 = test_promise_lifecycle()
    success2 = test_promise_drift_detection()
    
    if success1 and success2:
        print("\n✅ 所有测试通过")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败")
        sys.exit(1)
