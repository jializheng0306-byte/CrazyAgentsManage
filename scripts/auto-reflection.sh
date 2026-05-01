#!/bin/bash
# auto-reflection.sh - 基于当天实际活动的自动反思脚本
# 每日23:30执行，采集当天做了什么，然后生成真正的反思报告

set -e

LOG_DIR="$HOME/.hermes/logs"
LOG_FILE="$LOG_DIR/auto-reflection-$(date +%Y%m%d).log"
LEARNINGS_DIR="$HOME/.hermes/learnings"
TODAY=$(date +%Y-%m-%d)

mkdir -p "$LOG_DIR" "$LEARNINGS_DIR"

echo "=== 自动反思循环开始 $(date) ===" | tee -a "$LOG_FILE"

# 1. 采集当天实际活动
echo "1. 采集当天实际活动..." | tee -a "$LOG_FILE"

ACTIVITIES_FILE="$LEARNINGS_DIR/activities-$TODAY.md"
cat > "$ACTIVITIES_FILE" << 'HEADER'
# 当日活动采集
HEADER

# 1a. 采集今天的 session 历史（通过 hermes session search）
echo "  采集 session 历史..." | tee -a "$LOG_FILE"
# 这部分由 cron agent 完成（见下方 prompt）

# 1b. 采集今天的 git 提交记录
echo "  采集 git 提交记录..." | tee -a "$LOG_FILE"
{
    echo ""
    echo "## Git 提交记录"
    echo ""
    
    # FlowMindDeploy
    if [ -d "$HOME/FlowMindDeploy/.git" ]; then
        echo "### FlowMindDeploy"
        cd "$HOME/FlowMindDeploy"
        git log --since="$TODAY 00:00" --until="$TODAY 23:59" --oneline --all 2>/dev/null || echo "（无提交）"
        echo ""
    fi
    
    # CrazyAgentsManage
    if [ -d "$HOME/CrazyAgentsManage/.git" ]; then
        echo "### CrazyAgentsManage"
        cd "$HOME/CrazyAgentsManage"
        git log --since="$TODAY 00:00" --until="$TODAY 23:59" --oneline --all 2>/dev/null || echo "（无提交）"
        echo ""
    fi
    
    cd "$HOME"
} >> "$ACTIVITIES_FILE" 2>&1

# 1c. 采集今天的 cron job 执行记录
echo "  采集 cron job 记录..." | tee -a "$LOG_FILE"
{
    echo "## Cron Job 执行"
    echo ""
    # 列出今天的日志文件
    if [ -d "$LOG_DIR" ]; then
        find "$LOG_DIR" -name "*.log" -newer "$LOG_DIR/auto-reflection-$(date +%Y%m%d).log" -o -name "*-$(date +%Y%m%d).log" 2>/dev/null | head -10 | while read f; do
            echo "- $(basename "$f")"
        done || echo "（无）"
    fi
    echo ""
} >> "$ACTIVITIES_FILE" 2>&1

# 1d. 采集今天的文件变更（学习记录、计划文件等）
echo "  采集今日文件变更..." | tee -a "$LOG_FILE"
{
    echo "## 今日变更的配置/文档文件"
    echo ""
    find "$HOME/.hermes" -name "*.md" -mtime -1 2>/dev/null | head -20 | while read f; do
        echo "- $f"
    done || echo "（无）"
    echo ""
} >> "$ACTIVITIES_FILE" 2>&1

echo "  活动采集完成: $ACTIVITIES_FILE" | tee -a "$LOG_FILE"

# 2. 生成可直接上传的反思报告，避免把骨架文件提前推到飞书
echo "2. 生成反思报告..." | tee -a "$LOG_FILE"
REPORT_FILE="$LEARNINGS_DIR/reflection-report-$TODAY.md"

flowmind_commits=$(grep -cE '^[0-9a-f]{7,} ' "$ACTIVITIES_FILE" 2>/dev/null || true)
cron_logs=$(grep -c '^-' "$ACTIVITIES_FILE" 2>/dev/null || true)
changed_docs=$(grep -c '^-' "$ACTIVITIES_FILE" 2>/dev/null || true)

cat > "$REPORT_FILE" << EOF
# 反思报告 $TODAY

## 当日摘要

- Git 提交记录数（粗略）: ${flowmind_commits:-0}
- Cron/日志产物条目数（粗略）: ${cron_logs:-0}
- 今日变更文档/记忆文件数（粗略）: ${changed_docs:-0}

## 运行观察

- 本报告由自动采集脚本直接生成并上传，避免再上传空壳骨架
- 详细原始数据见：activities-$TODAY.md
- 如果稍后有 AI 二次分析，应覆盖写回此文件，而不是另起一个占位版本

## 原始活动摘录

EOF

sed -n '1,120p' "$ACTIVITIES_FILE" >> "$REPORT_FILE"

cat >> "$REPORT_FILE" << EOF

---
生成时间: $(date)
EOF

echo "  报告已生成: $REPORT_FILE" | tee -a "$LOG_FILE"

# 3. 上传到飞书云盘
echo "3. 上传到飞书云盘..." | tee -a "$LOG_FILE"
REFLECTION_CLOUD_FOLDER="YUfPftiTils0wedMGnvcBrr1nEg"

cd "$LEARNINGS_DIR"
for f in "$ACTIVITIES_FILE" "$REPORT_FILE"; do
    if [ -f "$f" ]; then
        fname=$(basename "$f")
        upload_result=$(lark-cli drive +upload --file "$fname" --folder-token "$REFLECTION_CLOUD_FOLDER" --name "$fname" 2>&1)
        echo "  📤 $fname: $upload_result" | tee -a "$LOG_FILE"
        
        ft=$(echo "$upload_result" | grep -o '"file_token": *"[^"]*"' | head -1 | sed 's/.*"file_token": *"//;s/"//')
        if [ -n "$ft" ]; then
            lark-cli api PATCH "/open-apis/drive/v1/permissions/$ft/public" \
                --params '{"type":"file"}' \
                --data '{"external_access_entity":"open","link_share_entity":"anyone_readable","comment_entity":"anyone_can_view"}' 2>/dev/null
        fi
    fi
done
cd "$HOME"

echo "=== 自动反思脚本完成 $(date) ===" | tee -a "$LOG_FILE"
echo ""
echo "--- 采集数据摘要 ---"
cat "$ACTIVITIES_FILE"
