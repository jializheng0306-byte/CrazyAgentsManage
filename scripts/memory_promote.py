#!/usr/bin/env python3
"""
记忆自主迭代 promote 验证脚本

扫描 .learnings/ 中的 pending 条目，评估复现频率，≥3次 promote 到 MEMORY.md。

这是《OpenClaw 实战》文章描述的 6 步循环中第 3-4 步的实现：
  触发事件 → .learnings/ 即时记录 → [本脚本] → promote 到 MEMORY.md → bootstrap 注入 → 行为改进
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

# 路径配置
CRAZY_ROOT = Path(os.environ.get(
    "CRAZY_ROOT", os.path.expanduser("~/CrazyAgentsManage")
))
LEARNINGS_DIR = CRAZY_ROOT / "harness" / "learnings"
AGENT_LEARNINGS_DIR = CRAZY_ROOT / "soul" / "agents"
MEMORY_FILE = CRAZY_ROOT / "soul" / "MEMORY.md"
MEMORY_CHAR_LIMIT = 2200  # 对应 config.yaml memory.memory_char_limit


def parse_learnings(filepath: Path) -> List[Dict]:
    """解析 .learnings/ 文件中的条目"""
    if not filepath.exists():
        return []

    entries = []
    content = filepath.read_text()
    current = None

    for line in content.split("\n"):
        # 匹配条目头: - [LRN-YYYYMMDD-NNN] TYPE | priority: X | status: Y
        match = re.match(
            r'- \[(LRN-\d{8}-\d+)\] (\w+) \| priority: (\w+) \| status: (\w+)',
            line.strip()
        )
        if match:
            if current:
                entries.append(current)
            current = {
                "id": match.group(1),
                "type": match.group(2),
                "priority": match.group(3),
                "status": match.group(4),
                "content": [],
                "source": str(filepath),
                "reproduce_count": 1,
            }
        elif current and (line.startswith("  ") or line.startswith("\t")):
            current["content"].append(line.strip())

    if current:
        entries.append(current)

    return entries


def count_reproductions(entry: Dict) -> int:
    """计算条目的复现次数（从内容中提取或默认为1）"""
    for line in entry["content"]:
        match = re.search(r'复现次数[：:]\s*(\d+)', line)
        if match:
            return int(match.group(1))
    return 1


def has_explicit_user_correction(entry: Dict) -> bool:
    """检测条目是否包含“用户明确纠正”信号。"""
    joined = "\n".join(entry["content"])
    markers = [
        "用户明确纠正",
        "用户纠正",
        "明确纠正",
    ]
    return any(marker in joined for marker in markers)


def should_promote(entry: Dict) -> Tuple[bool, str]:
    """判断条目是否应该 promote"""
    if entry["status"] != "pending":
        return False, f"状态是 {entry['status']}，跳过"

    reproduce_count = count_reproductions(entry)
    if has_explicit_user_correction(entry):
        return True, "命中用户明确纠正信号，立即 promote"

    if reproduce_count >= 3:
        return True, f"复现 {reproduce_count} 次 ≥ 3，promote"

    return False, f"复现 {reproduce_count} 次 < 3，继续观察"


def get_memory_tokens() -> int:
    """估算 MEMORY.md 的 token 数"""
    if not MEMORY_FILE.exists():
        return 0
    chars = len(MEMORY_FILE.read_text())
    return int(chars * 2 / 3)  # 粗略估算


def promote_to_memory(entry: Dict) -> bool:
    """将条目 promote 到 MEMORY.md"""
    current_tokens = get_memory_tokens()
    if MEMORY_FILE.exists() and entry["id"] in MEMORY_FILE.read_text():
        print(f"  ℹ️ MEMORY.md 已存在该条目，跳过重复 promote: {entry['id']}")
        return True

    # 构造要追加的内容
    type_emoji = {"ERR": "❌", "LRN": "💡", "FEAT": "📌"}.get(entry["type"], "📝")
    content_lines = "\n".join(
        f"  {line}" if line else line for line in entry["content"]
    )
    promoted_at = datetime.now().strftime("%Y-%m-%d")
    new_entry = (
        f"\n### {promoted_at} promote\n"
        f"- id: {entry['id']}\n"
        f"- type: {entry['type']}\n"
        f"- priority: {entry['priority']}\n"
        f"- source: {entry['source']}\n"
        f"{type_emoji} 记录内容:\n"
        f"{content_lines}\n"
    )

    new_tokens = int(len(new_entry) * 2 / 3)

    if current_tokens + new_tokens > MEMORY_CHAR_LIMIT:
        print(f"  ⚠️ MEMORY.md 容量警告: {current_tokens} + {new_tokens} > {MEMORY_CHAR_LIMIT}")
        print(f"  需要先精简 MEMORY.md 才能 promote")
        return False

    # 追加到 MEMORY.md
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MEMORY_FILE, "a") as f:
        f.write(new_entry)

    print(f"  ✅ 已 promote 到 MEMORY.md: {entry['id']}")
    return True


def update_status(filepath: Path, entry_id: str, new_status: str):
    """更新条目状态"""
    content = filepath.read_text()
    content = content.replace(
        f"[{entry_id}]",
        f"[{entry_id}]"
    )
    # 更精确的状态更新
    lines = content.split("\n")
    updated = []
    for line in lines:
        if entry_id in line and "status:" in line:
            line = re.sub(r'status: \w+', f'status: {new_status}', line)
        updated.append(line)
    filepath.write_text("\n".join(updated))


def run_promote_check() -> Dict:
    """运行一次完整的 promote 检查"""
    results = {
        "scanned": 0,
        "pending": 0,
        "promoted": 0,
        "skipped": 0,
        "failed": 0,
        "details": []
    }

    # 扫描所有 .learnings/ 文件
    learnings_files = []
    if LEARNINGS_DIR.exists():
        learnings_files.extend(LEARNINGS_DIR.glob("*.md"))

    # 也扫描 agent 专属 .learnings/
    if AGENT_LEARNINGS_DIR.exists():
        for agent_dir in AGENT_LEARNINGS_DIR.iterdir():
            if agent_dir.is_dir():
                agent_learnings = agent_dir / "learnings"
                if agent_learnings.exists():
                    learnings_files.extend(agent_learnings.glob("*.md"))

    for filepath in learnings_files:
        entries = parse_learnings(filepath)
        for entry in entries:
            results["scanned"] += 1

            if entry["status"] != "pending":
                continue

            results["pending"] += 1
            should, reason = should_promote(entry)

            detail = {
                "id": entry["id"],
                "file": str(filepath),
                "type": entry["type"],
                "priority": entry["priority"],
                "decision": "promote" if should else "skip",
                "reason": reason,
            }

            if should:
                success = promote_to_memory(entry)
                if success:
                    update_status(filepath, entry["id"], "promoted")
                    results["promoted"] += 1
                    detail["result"] = "promoted"
                else:
                    results["failed"] += 1
                    detail["result"] = "failed (capacity)"
            else:
                results["skipped"] += 1
                detail["result"] = "skipped"

            results["details"].append(detail)

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Promote pending learnings to MEMORY.md")
    parser.add_argument("--json-out", help="Write JSON result to this path")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    print(f"=== 记忆 promote 检查 {datetime.now().isoformat()} ===")
    print(f"MEMORY.md: {MEMORY_FILE} ({get_memory_tokens()} tokens / {MEMORY_CHAR_LIMIT} limit)")
    print(f"learnings: {LEARNINGS_DIR}")
    print()

    results = run_promote_check()

    print(f"扫描: {results['scanned']} 条")
    print(f"待处理: {results['pending']} 条")
    print(f"已 promote: {results['promoted']} 条")
    print(f"跳过: {results['skipped']} 条")
    print(f"失败: {results['failed']} 条")
    print()

    if results["details"]:
        print("详情:")
        for d in results["details"]:
            emoji = "✅" if d["result"] == "promoted" else "⏭️" if d["result"] == "skipped" else "❌"
            print(f"  {emoji} {d['id']}: {d['reason']}")

    # 输出 JSON 供 cron agent 读取
    print()
    payload = json.dumps(results, ensure_ascii=False, indent=2)
    print(payload)
    if args.json_out:
        Path(args.json_out).write_text(payload)
