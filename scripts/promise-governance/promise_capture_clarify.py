#!/usr/bin/env python3
"""
承诺捕获澄清脚本 (Promise Capture-Clarify)
每日 08:30 执行，在 daily-promise-review (09:00) 之前

功能：
1. 读取昨日/今日的 intel 数据（晨间情报采集输出）
2. 评估每条情报的承诺价值（自动打分）
3. 对有价值项创建承诺 JSON 到 ~/.hermes/promises/active/
4. 记录 trace 到 ~/.hermes/promises/traces/
5. 可选：调用 FlowMind candidate-ingress 提交候选
"""

import json
import os
import hashlib
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# 配置
INTEL_DIR = os.path.expanduser("~/.hermes/intel")
PROMISE_ACTIVE_DIR = os.path.expanduser("~/.hermes/promises/active")
PROMISE_TRACE_DIR = os.path.expanduser("~/.hermes/promises/traces")
PROMISE_ROOT = os.path.expanduser("~/.hermes/promises")

# 优先级评分阈值
PRIORITY_THRESHOLDS = {
    "P0": 85,   # 关键：直接影响当前项目
    "P1": 70,   # 高价值：重要研究发现
    "P2": 55,   # 中等：有潜力的发展
    "P3": 40,   # 低：一般了解
}

# 关键词评分表（关键词 → 分值加成）
KEYWORD_SCORES = {
    # 高价值关键词（与项目直接相关）
    "agent": 15, "ai agent": 20, "multi-agent": 20, "agentic": 18,
    "automation": 12, "workflow": 10, "orchestration": 15,
    "llm": 12, "large language model": 15, "gpt": 10,
    "hermes": 25, "flowmind": 25, "promise": 15, "governance": 15,
    "cron": 10, "scheduling": 10, "task management": 12,
    "mcp": 18, "model context protocol": 20,
    "feishu": 15, "lark": 15, "bitable": 12,
    "code review": 12, "ci/cd": 10, "devops": 10,
    "fine-tuning": 12, "rlhf": 15, "dpo": 12, "grpo": 15,
    "rag": 12, "retrieval augmented": 12,
    "security": 10, "vulnerability": 12,
    # 中等价值关键词
    "open source": 8, "github": 6, "api": 8,
    "benchmark": 8, "evaluation": 8,
    "transformer": 8, "attention": 6,
    "deployment": 8, "inference": 8, "serving": 8,
}

# 低价值排除词（命中则大幅降分）
EXCLUDE_KEYWORDS = [
    "game", "gaming", "esports", "crypto", "nft", "web3",
    "celebrity", "entertainment", "sports", "weather",
]


def load_intel_data(date_str):
    """加载指定日期的 intel 数据"""
    patterns = [
        f"intel-data-{date_str}-v2.json",
        f"intel-data-{date_str}.json",
    ]
    for pattern in patterns:
        path = os.path.join(INTEL_DIR, pattern)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    return None


def get_intel_data():
    """获取 intel 数据（优先今日，回退昨日）"""
    today = datetime.now().strftime("%Y%m%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

    data = load_intel_data(today)
    if data:
        print(f"  使用今日 intel 数据: {today}")
        return data, today

    data = load_intel_data(yesterday)
    if data:
        print(f"  使用昨日 intel 数据: {yesterday}")
        return data, yesterday

    print("  ❌ 未找到 intel 数据")
    return None, None


def score_item(item, item_type="rss"):
    """评估单条情报的承诺价值"""
    text = " ".join([
        item.get("title", ""),
        item.get("title_cn", ""),
        item.get("description", ""),
        item.get("description_cn", ""),
        item.get("summary", ""),
        item.get("summary_cn", ""),
    ]).lower()

    score = 40  # 基础分

    # 关键词加分
    for keyword, bonus in KEYWORD_SCORES.items():
        if keyword.lower() in text:
            score += bonus

    # 排除词减分
    for exclude in EXCLUDE_KEYWORDS:
        if exclude.lower() in text:
            score -= 20

    # 来源类型调整
    if item_type == "arxiv":
        score += 10  # 学术论文基础价值更高

    # 限制在 0-100 范围
    score = max(0, min(100, score))

    # 确定优先级
    priority = "P3"
    for p, threshold in sorted(PRIORITY_THRESHOLDS.items(), reverse=True):
        if score >= threshold:
            priority = p
            break

    return score, priority


def generate_promise_id(title, date_str):
    """生成承诺 ID"""
    hash_input = f"{title}{date_str}".encode()
    short_hash = hashlib.md5(hash_input).hexdigest()[:8]
    return f"promise-auto-{date_str}-{short_hash}"


def create_promise(item, score, priority, date_str, item_type):
    """创建承诺 JSON"""
    promise_id = generate_promise_id(item.get("title", ""), date_str)

    title = item.get("title_cn") or item.get("title", "未命名情报")
    description = item.get("summary_cn") or item.get("description_cn") or item.get("summary") or item.get("description") or ""

    # 截断过长的描述
    if len(description) > 500:
        description = description[:497] + "..."

    source_url = item.get("link", "")
    if not source_url and item.get("id"):
        source_url = f"https://arxiv.org/abs/{item['id']}"

    promise = {
        "id": promise_id,
        "title": title[:200],
        "description": description,
        "status": "pending",
        "priority": priority,
        "score": score,
        "source": f"intel-auto-capture:{item_type}",
        "source_url": source_url,
        "source_date": date_str,
        "created_at": datetime.now().isoformat(),
        "deliverables": [],
        "acceptance_criteria": [],
        "deadline": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "flowmind_candidate_id": None,
    }

    return promise


def save_promise(promise):
    """保存承诺到 active 目录"""
    os.makedirs(PROMISE_ACTIVE_DIR, exist_ok=True)
    filepath = os.path.join(PROMISE_ACTIVE_DIR, f"{promise['id']}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(promise, f, ensure_ascii=False, indent=2)
    return filepath


def write_trace(promise, action="created"):
    """写入 trace 日志"""
    os.makedirs(PROMISE_TRACE_DIR, exist_ok=True)
    trace_file = os.path.join(PROMISE_TRACE_DIR, f"{promise['id']}.jsonl")

    trace_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "promise_id": promise["id"],
        "title": promise["title"][:100],
        "priority": promise["priority"],
        "score": promise["score"],
        "source": promise["source"],
    }

    with open(trace_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(trace_entry, ensure_ascii=False) + "\n")


def check_existing_promises():
    """检查已存在的承诺，避免重复创建"""
    existing = set()
    if os.path.exists(PROMISE_ACTIVE_DIR):
        for f in os.listdir(PROMISE_ACTIVE_DIR):
            if f.endswith(".json"):
                try:
                    with open(os.path.join(PROMISE_ACTIVE_DIR, f), "r") as fh:
                        data = json.load(fh)
                        existing.add(data.get("title", "")[:100])
                except Exception:
                    pass
    return existing


def main():
    print("🔍 开始承诺捕获澄清 (capture-clarify)...")
    print(f"  时间: {datetime.now().isoformat()}")

    # 1. 获取 intel 数据
    print("\n1. 加载 intel 数据...")
    intel_data, date_str = get_intel_data()
    if not intel_data:
        print("  ⚠️ 无 intel 数据可处理，退出")
        return

    # 2. 检查已有承诺（避免重复）
    existing_titles = check_existing_promises()
    print(f"  已有活跃承诺: {len(existing_titles)} 个")

    # 3. 评估并创建承诺
    print("\n2. 评估情报价值...")
    papers = intel_data.get("papers", [])
    rss_items = intel_data.get("rss_items", [])

    created_count = 0
    skipped_count = 0
    results = []

    # 处理论文
    for paper in papers:
        score, priority = score_item(paper, "arxiv")
        title = paper.get("title_cn") or paper.get("title", "")

        if title[:100] in existing_titles:
            skipped_count += 1
            continue

        # 只为 P2 及以上的项目创建承诺
        if score >= PRIORITY_THRESHOLDS["P2"]:
            promise = create_promise(paper, score, priority, date_str, "arxiv")
            filepath = save_promise(promise)
            write_trace(promise)
            created_count += 1
            results.append({"title": promise["title"][:60], "priority": priority, "score": score})
            print(f"  ✅ [{priority}] {promise['title'][:60]}... (score={score})")
        else:
            print(f"  ⏭️ [{priority}] {title[:60]}... (score={score}, 低于阈值)")

    # 处理 RSS 条目
    for item in rss_items:
        score, priority = score_item(item, "rss")
        title = item.get("title_cn") or item.get("title", "")

        if title[:100] in existing_titles:
            skipped_count += 1
            continue

        if score >= PRIORITY_THRESHOLDS["P2"]:
            promise = create_promise(item, score, priority, date_str, "rss")
            filepath = save_promise(promise)
            write_trace(promise)
            created_count += 1
            results.append({"title": promise["title"][:60], "priority": priority, "score": score})
            print(f"  ✅ [{priority}] {promise['title'][:60]}... (score={score})")
        else:
            print(f"  ⏭️ [{priority}] {title[:60]}... (score={score}, 低于阈值)")

    # 4. 输出汇总
    print(f"\n📊 汇总:")
    print(f"  论文: {len(papers)} 条")
    print(f"  RSS: {len(rss_items)} 条")
    print(f"  新建承诺: {created_count} 个")
    print(f"  跳过重复: {skipped_count} 个")

    if results:
        print("\n📋 新建承诺列表:")
        for r in results:
            print(f"  - [{r['priority']}] {r['title']} (score={r['score']})")

    print(f"\n✅ capture-clarify 完成 ({datetime.now().isoformat()})")


if __name__ == "__main__":
    main()
