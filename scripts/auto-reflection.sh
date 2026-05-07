#!/bin/bash
# auto-reflection.sh - 基于跨日滚动窗口的自动反思脚本
# 默认在 23:30 执行，采集“上一日 23:30 之后到本次运行时刻”的真实活动

set -e

LOG_DIR="$HOME/.hermes/logs"
LOG_FILE="$LOG_DIR/auto-reflection-$(date +%Y%m%d).log"
LEARNINGS_DIR="$HOME/.hermes/learnings"
CRAZY_ROOT="${CRAZY_ROOT:-$HOME/CrazyAgentsManage}"
FLOWMIND_ROOT="${FLOWMIND_ROOT:-$HOME/FlowMindDeploy}"
REPORT_DAY=$(date +%Y-%m-%d)
WINDOW_START=$(date -d 'yesterday 23:30:00' '+%Y-%m-%d %H:%M:%S')
WINDOW_END=$(date '+%Y-%m-%d %H:%M:%S')
WINDOW_POLICY="固定采集窗口：上一日 23:30:00（不含）到本次运行时刻（含）；23:30 之后的新活动自动并入下一次反思。"
TMP_DIR="${TMPDIR:-/tmp}/auto-reflection-$(date +%Y%m%d)-$$"
FLOWMIND_COMMITS_FILE="$TMP_DIR/flowmind-commits.txt"
CRAZY_COMMITS_FILE="$TMP_DIR/crazy-commits.txt"
CRON_LOGS_FILE="$TMP_DIR/cron-logs.txt"
CHANGED_DOCS_FILE="$TMP_DIR/changed-docs.txt"
LEARNINGS_AUDIT_FILE="$TMP_DIR/learnings-audit.txt"
PROMOTE_LOG_FILE="$TMP_DIR/promote.log"
PROMOTE_JSON_FILE="$TMP_DIR/promote.json"

mkdir -p "$LOG_DIR" "$LEARNINGS_DIR" "$TMP_DIR"
trap 'rm -rf "$TMP_DIR"' EXIT

echo "=== 自动反思循环开始 $(date) ===" | tee -a "$LOG_FILE"

# 1. 采集窗口内实际活动
echo "1. 采集窗口内实际活动..." | tee -a "$LOG_FILE"
echo "  采集窗口: $WINDOW_START -> $WINDOW_END" | tee -a "$LOG_FILE"

ACTIVITIES_FILE="$LEARNINGS_DIR/activities-$REPORT_DAY.md"
cat > "$ACTIVITIES_FILE" << 'HEADER'
# 反思活动采集
HEADER

{
    echo ""
    echo "## 采集窗口"
    echo ""
    echo "- 起始: $WINDOW_START"
    echo "- 结束: $WINDOW_END"
    echo "- 规则: $WINDOW_POLICY"
    echo ""
} >> "$ACTIVITIES_FILE"

# 1a. 采集窗口内的 session 历史（通过 hermes session search）
echo "  采集 session 历史..." | tee -a "$LOG_FILE"
# 这部分由 cron agent 完成（见下方 prompt）

# 1b. 采集窗口内的 git 提交记录
echo "  采集 git 提交记录..." | tee -a "$LOG_FILE"
FLOWMIND_COMMIT_COUNT=0
CRAZY_COMMIT_COUNT=0

{
    echo ""
    echo "## Git 提交记录"
    echo ""
    
    # FlowMindDeploy
    if [ -d "$FLOWMIND_ROOT/.git" ]; then
        echo "### FlowMindDeploy"
        cd "$FLOWMIND_ROOT"
        git log --since="$WINDOW_START" --until="$WINDOW_END" --oneline --all 2>/dev/null | tee "$FLOWMIND_COMMITS_FILE" || true
        FLOWMIND_COMMIT_COUNT=$(grep -cve '^\s*$' "$FLOWMIND_COMMITS_FILE" 2>/dev/null || true)
        if [ "${FLOWMIND_COMMIT_COUNT:-0}" -eq 0 ]; then
            echo "（无提交）"
        fi
        echo ""
    fi
    
    # CrazyAgentsManage
    if [ -d "$CRAZY_ROOT/.git" ]; then
        echo "### CrazyAgentsManage"
        cd "$CRAZY_ROOT"
        git log --since="$WINDOW_START" --until="$WINDOW_END" --oneline --all 2>/dev/null | tee "$CRAZY_COMMITS_FILE" || true
        CRAZY_COMMIT_COUNT=$(grep -cve '^\s*$' "$CRAZY_COMMITS_FILE" 2>/dev/null || true)
        if [ "${CRAZY_COMMIT_COUNT:-0}" -eq 0 ]; then
            echo "（无提交）"
        fi
        echo ""
    fi
    
    cd "$HOME"
} >> "$ACTIVITIES_FILE" 2>&1

# 1c. 采集窗口内的 cron job 执行记录
echo "  采集 cron job 记录..." | tee -a "$LOG_FILE"
CRON_LOG_COUNT=0
{
    echo "## Cron Job 执行"
    echo ""
    # 列出采集窗口内更新过的日志文件
    if [ -d "$LOG_DIR" ]; then
        find "$LOG_DIR" -type f -name "*.log" -newermt "$WINDOW_START" ! -newermt "$WINDOW_END" 2>/dev/null | sort | head -20 > "$CRON_LOGS_FILE" || true
        CRON_LOG_COUNT=$(grep -cve '^\s*$' "$CRON_LOGS_FILE" 2>/dev/null || true)
        if [ "${CRON_LOG_COUNT:-0}" -gt 0 ]; then
            while read -r f; do
                [ -n "$f" ] && echo "- $(basename "$f")"
            done < "$CRON_LOGS_FILE"
        else
            echo "（无）"
        fi
    fi
    echo ""
} >> "$ACTIVITIES_FILE" 2>&1

# 1d. 采集窗口内的文件变更（学习记录、计划文件等）
echo "  采集窗口内文件变更..." | tee -a "$LOG_FILE"
CHANGED_DOC_COUNT=0
{
    echo "## 采集窗口内变更的配置/文档文件"
    echo ""
    find "$HOME/.hermes" -type f \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" \) -newermt "$WINDOW_START" ! -newermt "$WINDOW_END" 2>/dev/null | sort | head -20 > "$CHANGED_DOCS_FILE" || true
    CHANGED_DOC_COUNT=$(grep -cve '^\s*$' "$CHANGED_DOCS_FILE" 2>/dev/null || true)
    if [ "${CHANGED_DOC_COUNT:-0}" -gt 0 ]; then
        while read -r f; do
            [ -n "$f" ] && echo "- $f"
        done < "$CHANGED_DOCS_FILE"
    else
        echo "（无）"
    fi
    echo ""
} >> "$ACTIVITIES_FILE" 2>&1

# 1e. 审查 .learnings/ 待处理项
echo "  审查 .learnings/ 待处理项..." | tee -a "$LOG_FILE"
PENDING_LEARNINGS=0
{
    : > "$LEARNINGS_AUDIT_FILE"
    for f in ERRORS.md LEARNINGS.md FEATURE_REQUESTS.md; do
        path="$CRAZY_ROOT/harness/learnings/$f"
        if [ -f "$path" ]; then
            count=$(grep -Ec '^- \[LRN-[0-9]{8}-[0-9]+\].*status: pending' "$path" 2>/dev/null || true)
            echo "$f:$count" >> "$LEARNINGS_AUDIT_FILE"
            PENDING_LEARNINGS=$((PENDING_LEARNINGS + count))
        fi
    done
} 2>/dev/null

echo "  活动采集完成: $ACTIVITIES_FILE" | tee -a "$LOG_FILE"

# 2. 执行 .learnings/ promote 检查
echo "2. 执行 .learnings/ promote 检查..." | tee -a "$LOG_FILE"
PROMOTE_SCANNED=0
PROMOTE_PENDING=0
PROMOTE_DONE=0
PROMOTE_SKIPPED=0
PROMOTE_FAILED=0
PENDING_LEARNINGS_REMAINING=0
PROMOTE_DETAIL_LINES="  - 无"

if [ -f "$CRAZY_ROOT/scripts/memory_promote.py" ]; then
    CRAZY_ROOT="$CRAZY_ROOT" python3 "$CRAZY_ROOT/scripts/memory_promote.py" --json-out "$PROMOTE_JSON_FILE" > "$PROMOTE_LOG_FILE" 2>&1 || true
    if [ -f "$PROMOTE_JSON_FILE" ]; then
        PROMOTE_SCANNED=$(python3 -c "import json; print(json.load(open('$PROMOTE_JSON_FILE')).get('scanned', 0))")
        PROMOTE_PENDING=$(python3 -c "import json; print(json.load(open('$PROMOTE_JSON_FILE')).get('pending', 0))")
        PROMOTE_DONE=$(python3 -c "import json; print(json.load(open('$PROMOTE_JSON_FILE')).get('promoted', 0))")
        PROMOTE_SKIPPED=$(python3 -c "import json; print(json.load(open('$PROMOTE_JSON_FILE')).get('skipped', 0))")
        PROMOTE_FAILED=$(python3 -c "import json; print(json.load(open('$PROMOTE_JSON_FILE')).get('failed', 0))")
        PENDING_LEARNINGS_REMAINING=$((PROMOTE_PENDING - PROMOTE_DONE))
        PROMOTE_DETAIL_LINES=$(python3 - <<PY
import json
from pathlib import Path
data = json.load(open("$PROMOTE_JSON_FILE"))
details = data.get("details", [])
selected = []
for item in details:
    result = item.get("result", "")
    if result in {"promoted", "failed (capacity)"}:
        selected.append(f"  - {item['id']}: {item['result']} | {item['reason']}")
if not selected:
    selected = ["  - 无 promote 或失败条目"]
print("\n".join(selected))
PY
)
    fi
    echo "  promote 检查完成: promoted=$PROMOTE_DONE, skipped=$PROMOTE_SKIPPED, failed=$PROMOTE_FAILED" | tee -a "$LOG_FILE"
else
    echo "  未找到 memory_promote.py，跳过 promote 检查" | tee -a "$LOG_FILE"
fi

# 3. 生成真实反思报告
echo "3. 生成反思报告..." | tee -a "$LOG_FILE"
REPORT_FILE="$LEARNINGS_DIR/reflection-report-$REPORT_DAY.md"

TOTAL_COMMITS=$((FLOWMIND_COMMIT_COUNT + CRAZY_COMMIT_COUNT))

SUMMARY="本次采集窗口内产出了 ${TOTAL_COMMITS} 条代码提交，记录到 ${CRON_LOG_COUNT} 个运行日志文件，沉淀了 ${CHANGED_DOC_COUNT} 个文档/配置变更。"
if [ "$TOTAL_COMMITS" -eq 0 ] && [ "$CRON_LOG_COUNT" -eq 0 ]; then
    SUMMARY="本次采集窗口内没有明显代码提交，也没有采集到足够的运行日志，反思链本身需要重点关注零产出风险。"
fi

GOOD_1="- Git 侧有可审计产出：FlowMindDeploy ${FLOWMIND_COMMIT_COUNT} 条，CrazyAgentsManage ${CRAZY_COMMIT_COUNT} 条。"
GOOD_2="- 窗口内活动已被结构化采集到 activities-$REPORT_DAY.md，后续可追溯。"
GOOD_3="- .learnings/ promote 检查已执行：扫描 ${PROMOTE_SCANNED} 条，自动 promote ${PROMOTE_DONE} 条。"

IMPROVE_1="- 当前 auto-reflection 仍依赖本地采集结果，session 历史与真正的 AI 复盘链还没有稳定接实。"
IMPROVE_2="- 如果日志或提交偏少，说明本次窗口存在零产出或记录缺失风险，需要人工复核。"
if [ "$CRON_LOG_COUNT" -gt 0 ]; then
    IMPROVE_2="- 仍需把这些运行日志进一步归并成可读的运行事件，而不只是文件名列表。"
fi

TOMORROW_1="- 优先处理本次窗口里最明显的阻塞项，并把仍处于 pending 的 learnings 条目转成可执行改进。"
TOMORROW_2="- 23:30 之后的新活动会自动进入下一次反思；若仍出现遗漏，应优先修补采集源，而不是手工补写总结。"

TOP_FLOWMIND=$(head -n 3 "$FLOWMIND_COMMITS_FILE" 2>/dev/null || true)
TOP_CRAZY=$(head -n 3 "$CRAZY_COMMITS_FILE" 2>/dev/null || true)
TOP_CRON=$(head -n 5 "$CRON_LOGS_FILE" 2>/dev/null | xargs -I{} basename "{}" 2>/dev/null || true)

cat > "$REPORT_FILE" << EOF
# 反思报告 $REPORT_DAY

> 基于跨日滚动窗口的自动反思初稿
> 原始采集数据见: activities-$REPORT_DAY.md

## 采集窗口

- 起始: $WINDOW_START
- 结束: $WINDOW_END
- 规则: $WINDOW_POLICY

## 今日概要

$SUMMARY

## 做得好的

$GOOD_1
$GOOD_2
$GOOD_3

## 需改进的

$IMPROVE_1
$IMPROVE_2

## .learnings/ 审查

- 初始识别到待处理条目: $PENDING_LEARNINGS
- 当前剩余待处理条目: $PENDING_LEARNINGS_REMAINING
- 详细统计:
$(sed 's/^/- /' "$LEARNINGS_AUDIT_FILE" 2>/dev/null || echo "- 无可审计 learnings 文件")

## .learnings/ promote 结果

- 扫描条目: $PROMOTE_SCANNED
- pending 条目: $PROMOTE_PENDING
- 已自动 promote: $PROMOTE_DONE
- 跳过: $PROMOTE_SKIPPED
- 失败: $PROMOTE_FAILED
- 关键结果:
$PROMOTE_DETAIL_LINES

## 关键证据

- FlowMindDeploy 提交（前 3 条）:
$(if [ -n "$TOP_FLOWMIND" ]; then printf '%s\n' "$TOP_FLOWMIND" | sed 's/^/  - /'; else echo "  - 无"; fi)
- CrazyAgentsManage 提交（前 3 条）:
$(if [ -n "$TOP_CRAZY" ]; then printf '%s\n' "$TOP_CRAZY" | sed 's/^/  - /'; else echo "  - 无"; fi)
- 窗口内 cron / 运行日志（前 5 条）:
$(if [ -n "$TOP_CRON" ]; then printf '%s\n' "$TOP_CRON" | sed 's/^/  - /'; else echo "  - 无"; fi)

## 明日建议

$TOMORROW_1
$TOMORROW_2

---
生成时间: $(date)
EOF

echo "  真实反思报告已生成: $REPORT_FILE" | tee -a "$LOG_FILE"

# 4. 上传到飞书云盘
echo "4. 上传到飞书云盘..." | tee -a "$LOG_FILE"
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
