#!/usr/bin/env python3
"""
HermesAgent 自动情报捕获与痕迹留存 — 产出 2: 自动捕获脚本

在外部任务完成后作为后处理步骤调用。
自动化边界：Bitable value item。不自动进入 FlowMind candidate-ingress。
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# === 配置 ===
RULES_PATH = os.path.expanduser("~/.hermes/rules/intent-analysis-rules.json")
LOG_PATH = os.path.expanduser("~/.hermes/logs/auto-capture-trace.log")
SCRIPT_DIR = Path(__file__).resolve().parent
TRACE_SCRIPT = SCRIPT_DIR / "send-capture-trace-to-feishu.py"

# === 日志设置 ===
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stderr),
    ],
)
logger = logging.getLogger("auto-capture-trace")


def load_rules(path: str) -> list[dict]:
    """加载规则文件。返回规则列表，规则文件损坏时返回空列表。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        rules = data.get("rules", [])
        logger.info(f"已加载 {len(rules)} 条规则 (version={data.get('version','unknown')})")
        return rules
    except Exception as e:
        logger.warning(f"规则文件加载失败 ({path}): {e}，跳过规则匹配")
        return []


def match_rules(content: str, rules: list[dict]) -> tuple[float, str]:
    """
    对 content 执行规则匹配。
    返回 (最高置信度, 匹配规则id) 或 (0, None)。
    """
    if not rules or not content:
        return 0.0, None

    max_confidence = 0.0
    best_rule_id = None
    content_lower = content.lower()

    for rule in rules:
        rule_id = rule.get("id", "unknown")
        rule_type = rule.get("type", "keyword")
        keywords = rule.get("keywords", [])
        min_conf = rule.get("min_confidence", 40)

        if rule_type == "keyword":
            conf = rule.get("confidence_if_match", 50)
            for kw in keywords:
                if kw.lower() in content_lower:
                    if conf > max_confidence:
                        max_confidence = conf
                        best_rule_id = rule_id
                    break

        elif rule_type == "mixed":
            # mixed 模式：关键词匹配 + 简单语义判断
            matched_kw = any(kw.lower() in content_lower for kw in keywords)
            if not matched_kw:
                continue

            # 语义判断：看 content 长度是否足以产生有效分析
            word_count = len(content.split())
            has_substance = word_count > 10

            if has_substance:
                conf = min(90, 50 + word_count // 10)
            else:
                conf = min_conf

            if conf > max_confidence:
                max_confidence = conf
                best_rule_id = rule_id

    if max_confidence > 0:
        logger.info(f"规则匹配结果: rule={best_rule_id}, confidence={max_confidence}")
    else:
        logger.info("无规则命中")

    return max_confidence, best_rule_id


def extract_title(content: str, max_len: int = 60) -> str:
    """从内容中提取标题：取第一段有意义的文本。"""
    lines = [l.strip() for l in content.strip().split("\n") if l.strip()]
    if not lines:
        return "无标题"
    title = lines[0]
    if len(title) > max_len:
        title = title[:max_len] + "..."
    return title


def extract_summary(content: str, max_len: int = 100) -> str:
    """从内容中提取摘要。"""
    cleaned = content.strip().replace("\n", " ").replace("\r", "")
    parts = [p.strip() for p in cleaned.split("。") if p.strip()]
    if parts:
        summary = parts[0]
    else:
        summary = cleaned[:100]
    if len(summary) > max_len:
        summary = summary[:max_len] + "..."
    return summary


def extract_raw_text(content: str, max_len: int = 2000) -> str:
    """提取原文（截断）。"""
    if len(content) > max_len:
        return content[:max_len] + "\n...[截断]"
    return content


def run_trace_script(source_task: str, title: str, summary: str, raw_text: str,
                     confidence: float, rule_id: str | None) -> dict:
    """调用产出 3 留痕脚本发送通知。"""
    payload = json.dumps({
        "source_task": source_task,
        "title": title,
        "summary": summary,
        "raw_text": raw_text,
        "confidence": round(confidence),
        "rule_id": rule_id or "none",
        "captured_at": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S"),
    })

    try:
        result = subprocess.run(
            [sys.executable, str(TRACE_SCRIPT)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            logger.info(f"留痕脚本调用成功")
            return {"ok": True, "output": result.stdout.strip()}
        else:
            logger.warning(f"留痕脚本返回非零: {result.stderr.strip()}")
            return {"ok": False, "stderr": result.stderr.strip()}
    except Exception as e:
        logger.warning(f"留痕脚本调用失败: {e}")
        return {"ok": False, "error": str(e)}


def main():
    """主入口。从 stdin 或 sys.argv[1] 读取 JSON 输入。"""
    if len(sys.argv) > 1:
        input_raw = sys.argv[1]
    else:
        input_raw = sys.stdin.read()

    try:
        data = json.loads(input_raw)
    except json.JSONDecodeError as e:
        logger.error(f"输入 JSON 解析失败: {e}")
        sys.exit(1)

    source_task = data.get("source_task", "unknown")
    raw_content = data.get("raw_content", "")

    if not raw_content:
        logger.warning(f"source_task={source_task}: raw_content 为空，跳过")
        sys.exit(0)

    logger.info(f"开始处理: source_task={source_task}, content_length={len(raw_content)}")

    # Step 1: 加载规则
    rules = load_rules(RULES_PATH)

    # Step 2: 规则匹配
    confidence, rule_id = match_rules(raw_content, rules)

    # Step 3: 判断是否触发
    if confidence < 40:
        logger.info(f"置信度 {confidence} < 40，跳过捕获。rule_id={rule_id}")
        sys.exit(0)

    logger.info(f"触发捕获: confidence={confidence}, rule_id={rule_id}")

    # Step 4: 提取信息
    title = extract_title(raw_content)
    summary = extract_summary(raw_content)
    raw_text = extract_raw_text(raw_content)

    # Step 5: 调用留痕脚本（并发写入三个通道）
    trace_result = run_trace_script(source_task, title, summary, raw_text, confidence, rule_id)

    if trace_result.get("ok"):
        logger.info(f"捕获完成: title={title}, confidence={confidence}, rule_id={rule_id}")
    else:
        logger.warning(f"捕获完成但留痕失败: title={title}, error={trace_result}")

    logger.info(f"处理完成: source_task={source_task}, matched={rule_id}, confidence={confidence}")


if __name__ == "__main__":
    main()
