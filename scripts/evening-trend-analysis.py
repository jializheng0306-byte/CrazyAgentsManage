#!/usr/bin/env python3
"""
晚间趋势分析脚本 v2 - 基于 ai-builders-digest
每日20:00执行
数据源：https://github.com/AkashiSensei/ai-builders-digest
输出：上传飞书云盘 + 设开放权限 + 群消息推送
"""

import os
import subprocess
import json
from datetime import datetime
from pathlib import Path

# 配置
REPO_DIR = "/root/ai-builders-digest"
CHAT_ID = "oc_bbde428675a7c267d55c3f0663ca701d"
CLOUD_FOLDER_TOKEN = "SipPfr9lvlymYzdH0KUcPG0dnle"  # 晚间趋势分析文件夹
TREND_DIR = os.path.expanduser("~/.hermes/trends")
LOG_DIR = os.path.expanduser("~/.hermes/logs")

# 文件夹协作者
FOLDER_COLLABORATORS = [
    {"member_type": "openid", "member_id": "ou_b5f83af09aff327edda33a83f5f87700", "perm": "full_access"},
    {"member_type": "openid", "member_id": "ou_306fb8d5c89c5eae54434630bd57a96e", "perm": "full_access"},
]


def run_cmd(cmd, timeout=60):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return result.stdout.strip(), result.returncode


def ensure_folder_permissions():
    for collab in FOLDER_COLLABORATORS:
        data = json.dumps(collab, ensure_ascii=False)
        cmd = f'''lark-cli drive permission.members create --params '{{"type":"folder","token":"{CLOUD_FOLDER_TOKEN}"}}' --data '{data}' '''
        run_cmd(cmd)


def pull_repo():
    try:
        cmd = f"cd {REPO_DIR} && timeout 15 git pull --ff-only 2>&1"
        output, code = run_cmd(cmd, timeout=20)
        return code == 0 or "Already up to date" in output
    except Exception:
        return False


def get_today_digest():
    today = datetime.now().strftime("%Y-%m-%d")
    day_name = datetime.now().strftime("%a")
    filename = f"ai-digest-{today}-{day_name}.md"
    filepath = os.path.join(REPO_DIR, "zh", "daily", filename)

    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read(), filepath

    # 找最近的日报
    zh_daily = Path(REPO_DIR) / "zh" / "daily"
    files = sorted(zh_daily.glob("ai-digest-*.md"), reverse=True)
    if files:
        filepath = files[0]
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read(), filepath
    return None, None


def extract_summary(content, max_chars=1500):
    lines = content.split('\n')
    summary_lines = []
    in_intro = False

    for line in lines:
        if '## 导读' in line:
            in_intro = True
            continue
        if in_intro and line.startswith('## '):
            break
        if in_intro and line.strip():
            summary_lines.append(line.strip('- ').strip())
            if sum(len(l) for l in summary_lines) > max_chars:
                break

    return '\n'.join(summary_lines)


def extract_topics(content):
    lines = content.split('\n')
    topics = []
    current_person = None
    current_summary = []

    for line in lines:
        if line.startswith('**') and line.endswith('**'):
            if current_person and current_summary:
                topics.append((current_person, ' '.join(current_summary)[:120]))
            current_person = line.strip('*').strip()
            current_summary = []
        elif current_person and line.strip() and not line.startswith('https://'):
            current_summary.append(line.strip())

    if current_person and current_summary:
        topics.append((current_person, ' '.join(current_summary)[:120]))

    return topics[:6]


def upload_to_feishu(local_file, date_str):
    """上传到飞书云盘并设开放权限"""
    filename = f"趋势分析-{date_str}.md"
    cmd = f'cd {os.path.dirname(local_file)} && lark-cli drive +upload --file "{os.path.basename(local_file)}" --folder-token "{CLOUD_FOLDER_TOKEN}" --name "{filename}"'
    output, code = run_cmd(cmd)

    file_token = None
    try:
        result = json.loads(output)
        if result.get("ok"):
            file_token = result["data"].get("file_token")
    except Exception:
        pass

    if file_token:
        perm_cmd = f'''lark-cli api PATCH "/open-apis/drive/v1/permissions/{file_token}/public" --params '{{"type":"file"}}' --data '{{"external_access_entity":"open","link_share_entity":"anyone_readable","comment_entity":"anyone_can_view"}}' '''
        run_cmd(perm_cmd)

    return file_token


def send_to_feishu(summary, topics, digest_date):
    topic_text = ""
    for i, (person, view) in enumerate(topics[:5], 1):
        topic_text += f"{i}. {person}: {view}...\n"

    message = f"""📈 晚间趋势分析 ({digest_date})

📊 今日AI Builder动态:
{summary[:600]}

🔥 关键人物观点:
{topic_text}
---
数据源: ai-builders-digest
📁 完整报告: https://bcn7uazoofu0.feishu.cn/drive/folder/SipPfr9lvlymYzdH0KUcPG0dnle"""

    cmd = f'lark-cli im +messages-send --chat-id {CHAT_ID} --text "{message}"'
    output, code = run_cmd(cmd)
    return code == 0


def main():
    os.makedirs(TREND_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")

    print("📈 晚间趋势分析 v2 (ai-builders-digest)")

    # 0. 确保文件夹权限
    print("0. 检查文件夹权限...")
    ensure_folder_permissions()

    # 1. 拉取最新内容
    print("1. 拉取最新数据...")
    if not pull_repo():
        print("  ⚠️ git pull 失败，使用本地缓存")

    # 2. 读取日报
    print("2. 读取日报...")
    content, filepath = get_today_digest()
    if not content:
        print("  ❌ 无可用日报")
        return
    print(f"  📄 {os.path.basename(filepath)}")

    # 3. 提取信息
    print("3. 提取关键信息...")
    summary = extract_summary(content)
    topics = extract_topics(content)
    digest_date = Path(filepath).stem.replace("ai-digest-", "").rsplit("-", 1)[0]

    # 4. 保存本地
    report_file = os.path.join(TREND_DIR, f"trend-{today}.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  📄 本地: {report_file}")

    # 5. 上传飞书云盘
    print("5. 上传飞书云盘...")
    file_token = upload_to_feishu(report_file, today)
    print(f"  {'✅' if file_token else '❌'} 上传{'成功' if file_token else '失败'}")

    # 6. 发送群消息
    print("6. 发送到飞书群...")
    if send_to_feishu(summary, topics, digest_date):
        print("  ✅ 群消息推送成功")
    else:
        print("  ❌ 群消息推送失败")

    print("\n✅ 晚间趋势分析完成！")


if __name__ == "__main__":
    main()
