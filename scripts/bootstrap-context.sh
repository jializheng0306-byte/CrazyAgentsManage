#!/bin/bash
# bootstrap-context.sh - 为新 session 准备上下文注入文件
# 生成 prefill_messages_file 内容，包含 MEMORY.md 和 .learnings/ 摘要
# 
# 用法：在 cron 中运行，或手动运行生成上下文文件
# 输出：~/.hermes/prefill-context.md

set -e

MEMORY_FILE="$HOME/CrazyAgentsManage/soul/MEMORY.md"
LEARNINGS_DIR="$HOME/CrazyAgentsManage/harness/learnings"
OUTPUT="$HOME/.hermes/prefill-context.md"

echo "# 自动注入上下文" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "> 由 bootstrap-context.sh 生成于 $(date)" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# 1. 注入 MEMORY.md 核心内容
echo "## 长期记忆 (MEMORY.md)" >> "$OUTPUT"
echo "" >> "$OUTPUT"
if [ -f "$MEMORY_FILE" ]; then
    # 只注入最近的部分（避免过长）
    head -50 "$MEMORY_FILE" >> "$OUTPUT"
    TOTAL_LINES=$(wc -l < "$MEMORY_FILE")
    if [ "$TOTAL_LINES" -gt 50 ]; then
        echo "" >> "$OUTPUT"
        echo "... (共 $TOTAL_LINES 行，仅显示前 50 行)" >> "$OUTPUT"
    fi
fi
echo "" >> "$OUTPUT"

# 2. 注入 .learnings/ 中的 pending 摘要
echo "## 待处理学习记录" >> "$OUTPUT"
echo "" >> "$OUTPUT"
for f in ERRORS.md LEARNINGS.md FEATURE_REQUESTS.md; do
    filepath="$LEARNINGS_DIR/$f"
    if [ -f "$filepath" ]; then
        PENDING_COUNT=$(grep -c "status: pending" "$filepath" 2>/dev/null || echo 0)
        if [ "$PENDING_COUNT" -gt 0 ]; then
            echo "### $f ($PENDING_COUNT 条 pending)" >> "$OUTPUT"
            grep -B2 -A3 "status: pending" "$filepath" >> "$OUTPUT" 2>/dev/null || true
            echo "" >> "$OUTPUT"
        fi
    fi
done

# 3. 注入最近的 Tech Radar 条目
TECH_RADAR="$HOME/CrazyAgentsManage/shared-context/tech-radar.json"
if [ -f "$TECH_RADAR" ]; then
    echo "## Tech Radar 最新状态" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    python3 -c "
import json
with open('$TECH_RADAR') as f:
    radar = json.load(f)
entries = radar.get('entries', [])
if entries:
    for cat in ['adopt', 'trial', 'assess']:
        items = [e for e in entries if e.get('status') == cat]
        if items:
            print(f'### {cat.upper()} ({len(items)}条)')
            for e in items[-3:]:  # 只显示最近3条
                print(f'- {e[\"name\"]}: {e.get(\"action_suggested\", \"无\")}')
            print()
else:
    print('(Tech Radar 暂无条目)')
" >> "$OUTPUT" 2>/dev/null || echo "(Tech Radar 解析失败)" >> "$OUTPUT"
fi

echo "" >> "$OUTPUT"
echo "---" >> "$OUTPUT"
echo "上下文注入完成: $(date)" >> "$OUTPUT"

echo "Bootstrap context 生成完成: $OUTPUT"
echo "文件大小: $(wc -c < "$OUTPUT") 字符"
