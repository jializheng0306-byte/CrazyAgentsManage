#!/usr/bin/env python3
"""
晚间趋势分析脚本 v2 - repo-tracked source-of-truth
每日 20:00 执行
主链：
1. 运行 repo-tracked evening-intel-collector.sh
2. 读取 ai-builders-digest 摘要
3. 上传报告到飞书云盘 + 发群消息
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
import subprocess


SCRIPT_DIR = Path(__file__).resolve().parent
COLLECTOR_SCRIPT = SCRIPT_DIR / "evening-intel-collector.sh"
REPO_DIR = "/root/ai-builders-digest"
CHAT_ID = "oc_bbde428675a7c267d55c3f0663ca701d"
CLOUD_FOLDER_TOKEN = "SipPfr9lvlymYzdH0KUcPG0dnle"
TREND_DIR = os.path.expanduser("~/.hermes/trends")
INTEL_DIR = os.path.expanduser("~/.hermes/intel")
LOG_DIR = os.path.expanduser("~/.hermes/logs")

FOLDER_COLLABORATORS = [
    {"member_type": "openid", "member_id": "ou_b5f83af09aff327edda33a83f5f87700", "perm": "full_access"},
    {"member_type": "openid", "member_id": "ou_306fb8d5c89c5eae54434630bd57a96e", "perm": "full_access"},
]


def run_cmd(cmd: str, timeout: int = 60) -> tuple[str, int]:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return result.stdout.strip(), result.returncode


def ensure_folder_permissions():
    for collab in FOLDER_COLLABORATORS:
        data = json.dumps(collab, ensure_ascii=False)
        cmd = (
            f"lark-cli drive permission.members create "
            f"--params '{{\"type\":\"folder\",\"token\":\"{CLOUD_FOLDER_TOKEN}\"}}' "
            f"--data '{data}'"
        )
        run_cmd(cmd)


def pull_repo() -> bool:
    try:
        cmd = f"cd {REPO_DIR} && timeout 15 git pull --ff-only 2>&1"
        output, code = run_cmd(cmd, timeout=20)
        return code == 0 or "Already up to date" in output
    except Exception:
        return False


def get_today_digest(today: str | None = None):
    today = today or datetime.now().strftime("%Y-%m-%d")
    try:
        day_name = datetime.strptime(today, "%Y-%m-%d").strftime("%a")
    except ValueError:
        day_name = datetime.now().strftime("%a")
    filename = f"ai-digest-{today}-{day_name}.md"
    filepath = os.path.join(REPO_DIR, "zh", "daily", filename)

    if os.path.exists(filepath):
        text = Path(filepath).read_text(encoding="utf-8")
        if text.strip():
            return text, filepath

    zh_daily = Path(REPO_DIR) / "zh" / "daily"
    files = sorted(zh_daily.glob("ai-digest-*.md"), reverse=True)
    if files:
        filepath = files[0]
        text = filepath.read_text(encoding="utf-8")
        if text.strip():
            return text, str(filepath)
    return None, None


def resolve_report_source(today: str, collector_stdout: str = "") -> tuple[str | None, str | None]:
    content, filepath = get_today_digest(today)
    if content:
        return content, filepath

    collector_report = Path(INTEL_DIR) / f"evening-intel-{today}.md"
    if collector_report.exists():
        text = collector_report.read_text(encoding="utf-8")
        if text.strip():
            return text, str(collector_report)

    stdout_text = collector_stdout.strip()
    if stdout_text:
        return stdout_text, f"collector-stdout-{today}"

    return None, None


def extract_digest_date(filepath: str | None, default_date: str) -> str:
    if not filepath:
        return default_date

    match = re.match(r"ai-digest-(\d{4}-\d{2}-\d{2})(?:-[^.]+)?\.md$", Path(filepath).name)
    if match:
        return match.group(1)
    return default_date


def extract_summary(content: str, max_chars: int = 1500) -> str:
    lines = content.split("\n")
    summary_lines = []
    in_intro = False

    for line in lines:
        if "## 导读" in line:
            in_intro = True
            continue
        if in_intro and line.startswith("## "):
            break
        if in_intro and line.strip():
            summary_lines.append(line.strip("- ").strip())
            if sum(len(item) for item in summary_lines) > max_chars:
                break
    if summary_lines:
        return "\n".join(summary_lines)

    fallback_lines = []
    in_section = False
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("## "):
            if in_section and fallback_lines:
                break
            in_section = True
            continue
        if not in_section:
            continue
        if line.startswith("# ") or line.startswith("===") or line.startswith("REPORT_FILE=") or line.startswith("采集时间:"):
            continue
        if len(line) >= 3 and line[0].isdigit() and line[1:3] == ". ":
            continue
        if line.startswith("### "):
            line = line[4:].strip()
        elif line.startswith("- "):
            line = line[2:].strip()
        if line:
            fallback_lines.append(line)
        if sum(len(item) for item in fallback_lines) > max_chars:
            break

    if fallback_lines:
        return "\n".join(fallback_lines)

    return "\n".join(
        line.strip()
        for line in lines
        if line.strip()
        and not line.strip().startswith("# ")
        and not line.strip().startswith("===")
        and not line.strip().startswith("REPORT_FILE=")
    )[:max_chars]


def extract_topics(content: str) -> list[tuple[str, str]]:
    lines = content.split("\n")
    topics = []
    current_person = None
    current_summary = []

    for line in lines:
        if line.startswith("**") and line.endswith("**"):
            if current_person and current_summary:
                topics.append((current_person, " ".join(current_summary)[:120]))
            current_person = line.strip("*").strip()
            current_summary = []
        elif current_person and line.strip() and not line.startswith("https://"):
            current_summary.append(line.strip())

    if current_person and current_summary:
        topics.append((current_person, " ".join(current_summary)[:120]))
    if topics:
        return topics[:6]

    topics = []
    current_title = None
    current_summary = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("### "):
            if current_title and current_summary:
                topics.append((current_title, " ".join(current_summary)[:120]))
            current_title = stripped[4:].strip()
            current_summary = []
            continue
        if not current_title:
            continue
        if (
            stripped.startswith("## ")
            or stripped.startswith("===")
            or stripped.startswith("REPORT_FILE=")
            or stripped.startswith("http://")
            or stripped.startswith("https://")
            or (len(stripped) >= 3 and stripped[0].isdigit() and stripped[1:3] == ". ")
        ):
            continue
        if stripped.startswith("- "):
            current_summary.append(stripped[2:].strip())
        else:
            current_summary.append(stripped)

    if current_title and current_summary:
        topics.append((current_title, " ".join(current_summary)[:120]))
    return topics[:6]


def upload_to_feishu(local_file: str, date_str: str):
    filename = f"趋势分析-{date_str}.md"
    cmd = (
        f'cd {os.path.dirname(local_file)} && '
        f'lark-cli drive +upload --file "{os.path.basename(local_file)}" '
        f'--folder-token "{CLOUD_FOLDER_TOKEN}" --name "{filename}"'
    )
    output, code = run_cmd(cmd)

    file_token = None
    try:
        result = json.loads(output)
        if result.get("ok"):
            file_token = result["data"].get("file_token")
    except Exception:
        file_token = None

    if file_token:
        perm_cmd = (
            f"lark-cli api PATCH \"/open-apis/drive/v1/permissions/{file_token}/public\" "
            f"--params '{{\"type\":\"file\"}}' "
            f"--data '{{\"external_access_entity\":\"open\",\"link_share_entity\":\"anyone_readable\",\"comment_entity\":\"anyone_can_view\"}}'"
        )
        run_cmd(perm_cmd)

    return file_token


def send_to_feishu(summary: str, topics: list[tuple[str, str]], digest_date: str) -> bool:
    topic_text = ""
    for i, (person, view) in enumerate(topics[:5], 1):
        topic_text += f"{i}. {person}: {view}...\n"

    message = f"""📈 晚间趋势分析 ({digest_date})

📊 今日AI Builder动态:
{summary[:600]}

🔥 关键人物观点:
{topic_text}
---
数据源: ai-builders-digest + executor readonly supplement
📁 完整报告: https://bcn7uazoofu0.feishu.cn/drive/folder/SipPfr9lvlymYzdH0KUcPG0dnle"""

    cmd = f'lark-cli im +messages-send --chat-id {CHAT_ID} --text "{message}"'
    output, code = run_cmd(cmd)
    return code == 0


def main():
    os.makedirs(TREND_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(INTEL_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")

    print("📈 晚间趋势分析 v2 (repo-tracked)")

    print("0. 检查文件夹权限...")
    ensure_folder_permissions()

    print("1. 运行 repo-tracked collector...")
    collector_result = subprocess.run(
        ["bash", str(COLLECTOR_SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    if collector_result.returncode == 0:
        print("  ✅ collector 完成")
    else:
        print("  ⚠️ collector 失败，继续使用可用 digest 路径")

    print("2. 拉取最新 digest...")
    if not pull_repo():
        print("  ⚠️ git pull 失败，使用本地缓存")

    print("3. 读取 digest...")
    content, filepath = resolve_report_source(today, collector_result.stdout)
    if not content:
        print("  ❌ 无可用日报")
        return
    if filepath and filepath.endswith(".md"):
        print(f"  📄 {os.path.basename(filepath)}")
    else:
        print("  📄 collector stdout fallback")

    print("4. 提取关键信息...")
    summary = extract_summary(content)
    topics = extract_topics(content)
    digest_date = extract_digest_date(filepath, today)

    report_file = os.path.join(TREND_DIR, f"trend-{today}.md")
    collector_report = os.path.join(INTEL_DIR, f"evening-intel-{today}.md")
    if os.path.exists(collector_report):
        Path(report_file).write_text(Path(collector_report).read_text(encoding="utf-8"), encoding="utf-8")
    else:
        Path(report_file).write_text(content, encoding="utf-8")
    print(f"  📄 本地: {report_file}")

    print("5. 上传飞书云盘...")
    file_token = upload_to_feishu(report_file, today)
    print(f"  {'✅' if file_token else '❌'} 上传{'成功' if file_token else '失败'}")

    print("6. 发送到飞书群...")
    if send_to_feishu(summary, topics, digest_date):
        print("  ✅ 群消息推送成功")
    else:
        print("  ❌ 群消息推送失败")

    print("\n✅ 晚间趋势分析完成！")


if __name__ == "__main__":
    main()
