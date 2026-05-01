#!/usr/bin/env python3
"""
承诺审查脚本 - 每日09:00执行
功能：扫描承诺文件、生成审查报告、上传飞书云盘、发送群消息
"""

import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# 配置
PROMISE_DIR = os.path.expanduser("~/.hermes/promises")
REPORT_DIR = os.path.expanduser("~/.hermes/promises/reviews")
CLOUD_FOLDER_TOKEN = "KnUNfAvLGlgYgwdwGjPcgkPonTc"  # 承诺审查报告文件夹
CHAT_ID = "oc_bbde428675a7c267d55c3f0663ca701d"  # CrazyAgentsManage群

# 文件夹协作者列表（新成员加入时在此添加）
FOLDER_COLLABORATORS = [
    {"member_type": "openid", "member_id": "ou_b5f83af09aff327edda33a83f5f87700", "perm": "full_access"},  # 贾利铮
    {"member_type": "openid", "member_id": "ou_306fb8d5c89c5eae54434630bd57a96e", "perm": "full_access"},  # 李瑆
]


def run_cmd(cmd, timeout=30):
    """执行命令并返回结果"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return result.stdout.strip(), result.returncode


def ensure_folder_permissions():
    """确保文件夹协作者权限正确（幂等操作）"""
    for collab in FOLDER_COLLABORATORS:
        data = json.dumps(collab, ensure_ascii=False)
        cmd = f'''lark-cli drive permission.members create \
            --params '{{"type":"folder","token":"{CLOUD_FOLDER_TOKEN}"}}' \
            --data '{data}' '''
        output, code = run_cmd(cmd)
        # 1061041 = already has permission, 0 = success
        if code == 0 or "1061041" in output:
            print(f"  ✅ {collab['member_id'][:12]}... 权限正常")
        else:
            print(f"  ❌ {collab['member_id'][:12]}... 设置失败")


def scan_promises():
    """扫描所有承诺文件"""
    promises = []
    promise_dir = Path(PROMISE_DIR)

    if not promise_dir.exists():
        return promises

    for json_file in promise_dir.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for p in data:
                        p["_source_file"] = json_file.name
                    promises.extend(data)
                elif isinstance(data, dict):
                    data["_source_file"] = json_file.name
                    promises.append(data)
        except Exception:
            continue

    return promises


def classify_promises(promises):
    """分类承诺状态"""
    today = datetime.now().strftime("%Y-%m-%d")
    next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    result = {
        "total": len(promises),
        "overdue": [],       # 已过期
        "due_today": [],     # 今日到期
        "due_soon": [],      # 7天内到期
        "in_progress": [],   # 进行中
        "completed": [],     # 已完成
        "blocked": [],       # 阻塞
    }

    for p in promises:
        status = p.get("status", "pending").lower()
        due = p.get("due_date", p.get("deadline", ""))

        if status in ("done", "completed", "已完成"):
            result["completed"].append(p)
        elif status in ("blocked", "阻塞"):
            result["blocked"].append(p)
        elif due:
            if due < today:
                result["overdue"].append(p)
            elif due == today:
                result["due_today"].append(p)
            elif due <= next_week:
                result["due_soon"].append(p)
            else:
                result["in_progress"].append(p)
        else:
            if status in ("in_progress", "进行中"):
                result["in_progress"].append(p)
            else:
                result["pending_count"] = result.get("pending_count", 0) + 1

    return result


def generate_report(classified):
    """生成审查报告Markdown"""
    today = datetime.now().strftime("%Y-%m-%d")

    report = f"""# 承诺审查报告 {today}

## 📊 统计摘要
| 状态 | 数量 |
|------|------|
| 总承诺数 | {classified['total']} |
| 已过期 | {len(classified['overdue'])} |
| 今日到期 | {len(classified['due_today'])} |
| 7天内到期 | {len(classified['due_soon'])} |
| 进行中 | {len(classified['in_progress'])} |
| 已完成 | {len(classified['completed'])} |
| 阻塞 | {len(classified['blocked'])} |
| 待处理 | {classified.get('pending_count', 0)} |

"""

    if classified["overdue"]:
        report += "## 🚨 已过期承诺\n"
        for p in classified["overdue"]:
            name = p.get("name", p.get("title", "未命名"))
            due = p.get("due_date", p.get("deadline", "未知"))
            owner = p.get("owner", p.get("assignee", "未指定"))
            report += f"- **{name}** (到期: {due}, 负责人: {owner})\n"
        report += "\n"

    if classified["due_today"]:
        report += "## ⚠️ 今日到期\n"
        for p in classified["due_today"]:
            name = p.get("name", p.get("title", "未命名"))
            owner = p.get("owner", p.get("assignee", "未指定"))
            report += f"- **{name}** (负责人: {owner})\n"
        report += "\n"

    if classified["due_soon"]:
        report += "## 📅 7天内到期\n"
        for p in classified["due_soon"]:
            name = p.get("name", p.get("title", "未命名"))
            due = p.get("due_date", p.get("deadline", "未知"))
            owner = p.get("owner", p.get("assignee", "未指定"))
            report += f"- **{name}** (到期: {due}, 负责人: {owner})\n"
        report += "\n"

    if classified["blocked"]:
        report += "## 🚧 阻塞问题\n"
        for p in classified["blocked"]:
            name = p.get("name", p.get("title", "未命名"))
            reason = p.get("block_reason", p.get("note", "未说明"))
            report += f"- **{name}**: {reason}\n"
        report += "\n"

    if classified["in_progress"]:
        report += "## 🔄 进行中\n"
        for p in classified["in_progress"]:
            name = p.get("name", p.get("title", "未命名"))
            due = p.get("due_date", p.get("deadline", "无"))
            report += f"- **{name}** (截止: {due})\n"
        report += "\n"

    report += f"""---
生成时间: {datetime.now().isoformat()}
"""
    return report


def upload_to_feishu(report_file, date_str):
    """上传报告到飞书云盘并设置开放权限"""
    filename = f"承诺审查报告-{date_str}.md"

    # 上传文件
    cmd = f'cd {os.path.dirname(report_file)} && lark-cli drive +upload --file "{os.path.basename(report_file)}" --folder-token "{CLOUD_FOLDER_TOKEN}" --name "{filename}"'
    output, code = run_cmd(cmd)
    print(f"  上传: {'✅' if code == 0 else '❌'} {filename}")

    # 从返回结果中提取 file_token
    file_token = None
    try:
        result = json.loads(output)
        if result.get("ok"):
            file_token = result["data"].get("file_token")
    except Exception:
        pass

    if file_token:
        # 设置文件权限为完全开放
        perm_cmd = f'''lark-cli api PATCH "/open-apis/drive/v1/permissions/{file_token}/public" \
            --params '{{"type":"file"}}' \
            --data '{{"external_access_entity":"open","link_share_entity":"anyone_readable","comment_entity":"anyone_can_view"}}' '''
        _, perm_code = run_cmd(perm_cmd)
        print(f"  权限设置: {'✅ 开放' if perm_code == 0 else '❌ 失败'}")

    return file_token


def send_to_feishu(classified, cloud_url=None):
    """发送审查摘要到飞书群"""
    today = datetime.now().strftime("%Y-%m-%d")

    overdue = len(classified["overdue"])
    due_today = len(classified["due_today"])
    due_soon = len(classified["due_soon"])
    blocked = len(classified["blocked"])

    # 构建告警部分
    alert = ""
    if overdue > 0:
        alert += f"🚨 已过期: {overdue} 项\n"
    if due_today > 0:
        alert += f"⚠️ 今日到期: {due_today} 项\n"
    if blocked > 0:
        alert += f"🚧 阻塞: {blocked} 项\n"

    message = f"""📋 承诺审查报告 ({today})

📊 统计:
- 总承诺: {classified['total']}
- 进行中: {len(classified['in_progress'])}
- 已完成: {len(classified['completed'])}
- 7天内到期: {due_soon}
{alert}
---
完整报告: 飞书云盘"""

    cmd = f'lark-cli im +messages-send --chat-id {CHAT_ID} --text "{message}"'
    output, code = run_cmd(cmd)
    print(f"  群消息: {'✅' if code == 0 else '❌'}")
    return code == 0


def main():
    print("📋 开始承诺审查...")

    os.makedirs(REPORT_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")

    # 0. 确保文件夹权限
    print("0. 检查文件夹权限...")
    ensure_folder_permissions()

    # 1. 扫描承诺
    print("1. 扫描承诺文件...")
    promises = scan_promises()
    print(f"  找到 {len(promises)} 条承诺")

    # 2. 分类统计
    print("2. 分类统计...")
    classified = classify_promises(promises)

    # 3. 生成报告
    print("3. 生成审查报告...")
    report = generate_report(classified)
    report_file = os.path.join(REPORT_DIR, f"review-{today}.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  报告已保存: {report_file}")

    # 4. 上传到飞书云盘
    print("4. 上传到飞书云盘...")
    date_str = datetime.now().strftime("%Y-%m-%d")
    upload_to_feishu(report_file, date_str)

    # 5. 发送到飞书群
    print("5. 发送审查摘要到飞书群...")
    send_to_feishu(classified)

    print("\n✅ 承诺审查完成！")
    return report_file


if __name__ == "__main__":
    main()
