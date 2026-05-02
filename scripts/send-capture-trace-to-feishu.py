#!/usr/bin/env python3
"""
HermesAgent 自动情报捕获与痕迹留存 — 产出 3: 留痕函数

被 auto-trace-to-bitable.py 调用，并发写入三个通道：
1. 飞书群聊（FlowMind 群 @codex cli）
2. HermesAgent 私聊（与用户的 1v1 飞书对话）
3. Bitable value item 新增记录
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# === 配置 ===
LARK_CLI = os.environ.get("LARK_CLI", "lark-cli")
LOG_PATH = os.path.expanduser("~/.hermes/logs/auto-capture-trace.log")
LARK_NO_PROXY = os.environ.get("LARK_CLI_NO_PROXY", "1")

# FlowMind 群 chat_id (CrazyAgentsManage 群)
GROUP_CHAT_ID = os.environ.get("CAPTURE_GROUP_CHAT_ID", "oc_bbde428675a7c267d55c3f0663ca701d")
# HermesAgent 与用户的私聊 — 用 app admin open_id
USER_OPEN_ID = os.environ.get("CAPTURE_USER_OPEN_ID", "ou_0")
# Bitable 配置
BITABLE_APP_TOKEN = os.environ.get("BITABLE_APP_TOKEN", "")
BITABLE_TABLE_ID = os.environ.get("BITABLE_TABLE_ID", "")

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
logger = logging.getLogger("send-capture-trace")


def _lark(args: list[str]) -> dict:
    """执行 lark-cli 命令并返回解析后的 JSON。"""
    env = os.environ.copy()
    if LARK_NO_PROXY:
        env["LARK_CLI_NO_PROXY"] = LARK_NO_PROXY
    try:
        result = subprocess.run(
            [LARK_CLI, *args],
            capture_output=True, text=True, timeout=30, env=env
        )
        stdout = result.stdout.strip()
        if stdout:
            return json.loads(stdout)
        return {"ok": False, "error": "empty_response", "stderr": result.stderr.strip()}
    except json.JSONDecodeError:
        return {"ok": False, "error": "json_parse", "raw": stdout}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def ensure_bitable_fields(token: str, table_id: str) -> bool:
    """
    确保 Bitable 表包含所需字段。
    返回 True 表示字段已就绪（已存在或已创建）。
    """
    # 先获取现有字段列表
    result = _lark([
        "base", "+field-list",
        "--as", "bot",
        "--base-token", token,
        f"--table-id={table_id}",
        "--limit", "50",
    ])
    if not result.get("ok"):
        logger.warning(f"获取 Bitable 字段列表失败: {result.get('error')}")
        return False

    fields = result.get("data", {}).get("items", []) if result.get("data") else []
    existing_names = {f.get("field_name", "") for f in fields}

    required_fields = {
        "title": {"field_name": "title", "type": 1},    # text
        "summary": {"field_name": "summary", "type": 1},  # text
        "raw_text": {"field_name": "raw_text", "type": 1}, # text
        "source_task": {"field_name": "source_task", "type": 1}, # text
        "captured_at": {"field_name": "captured_at", "type": 5}, # datetime
        "status": {"field_name": "status", "type": 3},    # select
        "confidence": {"field_name": "confidence", "type": 2}, # number
    }

    all_ready = True
    for fname, fdef in required_fields.items():
        if fname not in existing_names:
            logger.info(f"Bitable 缺少字段 '{fname}'，尝试创建...")
            cr = _lark([
                "base", "+field-create",
                "--as", "bot",
                "--base-token", token,
                f"--table-id={table_id}",
                "--name", fdef["field_name"],
                "--type", str(fdef["type"]),
            ])
            if cr.get("ok"):
                logger.info(f"字段 '{fname}' 创建成功")
            else:
                logger.warning(f"字段 '{fname}' 创建失败: {cr.get('error')}")
                all_ready = False

    # 确保 status 字段有 Select 选项
    if "status" not in existing_names:
        # 创建选项：待确认、已确认、已忽略
        for opt_val in ["待确认", "已确认", "已忽略"]:
            _lark([
                "base", "+field-create",
                "--as", "bot",
                "--base-token", token,
                f"--table-id={table_id}",
                "--name", f"opt_{opt_val}",
                "--type", "3",
            ])

    return all_ready


def send_group_notification(source_task: str, title: str, summary: str,
                            confidence: float, captured_at: str) -> dict:
    """通道 1: 飞书群聊 FlowMind 群 @codex cli 发送摘要通知。"""
    msg = f"""📥 自动捕获通知
━━━━━━━━━━━━━━━━━━━
来源: {source_task}
捕获时间: {captured_at}
━━━━━━━━━━━━━━━━━━━
🔹 {title}
🔹 {summary}
🔹 置信度: {int(confidence)}/100
━━━━━━━━━━━━━━━━━━━
⏳ 状态：待确认（Bitable 中已记录）
操作提示：
- 确认有价值 → Bitable 标记「已确认」后手动运行 flowmind_capture.py
- 标记无价值 → Bitable 标记「已忽略」"""

    result = _lark([
        "im", "send",
        "--as", "bot",
        "--chat-id", GROUP_CHAT_ID,
        "--msg-type", "text",
        "--content", msg,
    ])
    if result.get("ok"):
        msg_id = result.get("data", {}).get("message_id", "unknown")
        logger.info(f"群聊通知发送成功, msg_id={msg_id}")
    else:
        logger.warning(f"群聊通知发送失败: {result.get('error')}")
    return result


def send_private_notification(source_task: str, title: str, summary: str,
                              raw_text: str, confidence: float,
                              captured_at: str) -> dict:
    """通道 2: HermesAgent 私聊发送详细内容。"""
    msg = f"""📥 自动捕获详情
━━━━━━━━━━━━━━━━━━━
{title}
[来源任务] {source_task}
[置信度] {int(confidence)}/100
[捕获时间] {captured_at}
━━━━━━━━━━━━━━━━━━━
[摘要]
{summary}
[原文]
{raw_text}
━━━━━━━━━━━━━━━━━━━
当前状态: 待确认（已在 Bitable 中记录）
如确认有价值，请在 Bitable 中标记「已确认」后运行 capture 脚本"""

    result = _lark([
        "im", "send",
        "--as", "bot",
        "--user-id", USER_OPEN_ID,
        "--msg-type", "text",
        "--content", msg,
    ])
    if result.get("ok"):
        msg_id = result.get("data", {}).get("message_id", "unknown")
        logger.info(f"私聊通知发送成功, msg_id={msg_id}")
    else:
        logger.warning(f"私聊通知发送失败: {result.get('error')}")
    return result


def write_bitable_record(token: str, table_id: str, fields: dict) -> dict:
    """通道 3: Bitable value item 新增记录。"""
    # 构建记录字段
    record_fields = {"title": fields["title"]}
    if fields.get("summary"):
        record_fields["summary"] = fields["summary"]
    if fields.get("raw_text"):
        record_fields["raw_text"] = fields["raw_text"]
    if fields.get("source_task"):
        record_fields["source_task"] = fields["source_task"]
    if fields.get("captured_at"):
        record_fields["captured_at"] = fields["captured_at"]
    if fields.get("confidence") is not None:
        record_fields["confidence"] = int(fields["confidence"])
    # status 默认 "待确认" — 通过 data 传入

    payload = json.dumps({"fields": record_fields})
    result = _lark([
        "base", "+record-create",
        "--as", "bot",
        "--base-token", token,
        f"--table-id={table_id}",
        "--data", payload,
    ])
    if result.get("ok"):
        record_id = result.get("data", {}).get("record_id", "unknown")
        logger.info(f"Bitable 记录创建成功, record_id={record_id}")
    else:
        logger.warning(f"Bitable 记录创建失败: {result.get('error')}")
    return result


def main():
    """从 stdin 读取 JSON 输入，并发写入三个通道。"""
    input_raw = sys.stdin.read()
    try:
        data = json.loads(input_raw)
    except json.JSONDecodeError as e:
        logger.error(f"输入 JSON 解析失败: {e}")
        sys.exit(1)

    source_task = data.get("source_task", "unknown")
    title = data.get("title", "无标题")
    summary = data.get("summary", "")
    raw_text = data.get("raw_text", "")
    confidence = data.get("confidence", 0)
    captured_at = data.get("captured_at",
                           datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S"))

    results = {}

    # 通道 1: 群聊通知
    logger.info("=== 通道 1: 群聊通知 ===")
    results["group"] = send_group_notification(source_task, title, summary, confidence, captured_at)

    # 通道 2: 私聊通知
    logger.info("=== 通道 2: 私聊通知 ===")
    if USER_OPEN_ID and USER_OPEN_ID != "ou_0":
        results["private"] = send_private_notification(
            source_task, title, summary, raw_text, confidence, captured_at)
    else:
        logger.info("未配置 USER_OPEN_ID，跳过私聊通知")

    # 通道 3: Bitable 记录
    logger.info("=== 通道 3: Bitable 记录 ===")
    if BITABLE_APP_TOKEN and BITABLE_TABLE_ID:
        # 先确保字段存在
        ensure_bitable_fields(BITABLE_APP_TOKEN, BITABLE_TABLE_ID)
        fields = {
            "title": title,
            "summary": summary,
            "raw_text": raw_text,
            "source_task": source_task,
            "captured_at": captured_at,
            "confidence": round(confidence) if confidence else 0,
        }
        results["bitable"] = write_bitable_record(BITABLE_APP_TOKEN, BITABLE_TABLE_ID, fields)
    else:
        logger.info("未配置 BITABLE_APP_TOKEN/TABLE_ID，跳过 Bitable 记录")

    # 输出结果摘要
    status = "ok" if all(r.get("ok", False) for r in results.values() if r) else "partial"
    output = {
        "ok": status == "ok",
        "status": status,
        "channels": {k: v.get("ok", False) for k, v in results.items() if v},
    }
    print(json.dumps(output, ensure_ascii=False))
    logger.info(f"留痕完成: status={status}")

    if status != "ok":
        sys.exit(0 if results else 1)


if __name__ == "__main__":
    main()
