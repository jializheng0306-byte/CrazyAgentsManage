#!/bin/bash
# tech-radar-review.sh - Tech Radar 周审查数据准备
# 由 cron agent 调用，汇总本周 Tech Radar 变更供审查

set -e

TODAY=$(date +%Y-%m-%d)
RADAR_FILE="$HOME/CrazyAgentsManage/shared-context/tech-radar.json"
INTEL_DIR="$HOME/.hermes/intel"
LOG_DIR="$HOME/.hermes/logs"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$INTEL_DIR" "$LOG_DIR"

LOG_FILE="$LOG_DIR/tech-radar-review-$(date +%Y%m%d).log"
REPORT_FILE="$INTEL_DIR/tech-radar-review-$TODAY.md"

echo "=== Tech Radar 周审查 $(date) ===" | tee "$LOG_FILE"

cat > "$REPORT_FILE" << EOF
# Tech Radar 周审查 $TODAY

审查时间: $(date)
EOF

# 1. 读取当前 Tech Radar 状态
echo "1. 读取 Tech Radar..." | tee -a "$LOG_FILE"
{
    echo ""
    echo "## 当前 Tech Radar 状态"
    echo ""
    if [ -f "$RADAR_FILE" ]; then
        python3 -c "
import json
with open('$RADAR_FILE') as f:
    radar = json.load(f)
entries = radar.get('entries', [])
print(f'总条目: {len(entries)}')
print()
for cat in ['adopt', 'trial', 'assess']:
    items = [e for e in entries if e.get('status') == cat]
    print(f'### {cat.upper()} ({len(items)}条)')
    if items:
        for e in items:
            print(f'- {e[\"name\"]} | 优先级: {e.get(\"priority\", \"N/A\")} | 发现: {e.get(\"discovered_date\", \"N/A\")}')
            if e.get('action_suggested'):
                print(f'  建议行动: {e[\"action_suggested\"]}')
            if e.get('impact_assessment'):
                print(f'  影响评估: {e[\"impact_assessment\"]}')
    else:
        print('(暂无)')
    print()
" 2>/dev/null || echo "(Tech Radar 解析失败)"
    else
        echo "Tech Radar 文件不存在"
    fi
} >> "$REPORT_FILE" 2>&1

# 2. 本周情报摘要中的高星发现
echo "2. 汇总本周高星发现..." | tee -a "$LOG_FILE"
{
    echo ""
    echo "## 本周情报中的高星发现（⭐⭐⭐⭐ 以上）"
    echo ""
    # 扫描最近 7 天的情报文件
    for f in $(find "$INTEL_DIR" -name "*-intel-*.md" -mtime -7 2>/dev/null | sort -r); do
        fname=$(basename "$f")
        echo "### $fname"
        grep -A2 "⭐⭐⭐⭐\|5星\|4星\|P0\|P1" "$f" 2>/dev/null | head -10 || echo "（无高星条目）"
        echo ""
    done
} >> "$REPORT_FILE" 2>&1

# 3. P0/P1 pending 条目补证据
echo "3. 通过 executor 为 P0/P1 pending 条目补证据..." | tee -a "$LOG_FILE"
{
    echo ""
    python3 /root/CrazyAgentsManage/scripts/runtime/ensure_crossref_readonly_source.py >/dev/null 2>&1 || true
    python3 /root/CrazyAgentsManage/scripts/runtime/ensure_github_repo_readonly_source.py --required-tool listRepoCommits >/dev/null 2>&1 || true
    python3 /root/CrazyAgentsManage/scripts/runtime/ensure_hn_readonly_source.py >/dev/null 2>&1 || true
    python3 "$SCRIPT_DIR/fetch-tech-radar-evidence-via-executor.py" \
        --radar-file "$RADAR_FILE" \
        --priorities "P0,P1" \
        --statuses "pending" \
        --max-entries 5 \
        --max-results 3
} >> "$REPORT_FILE" 2>&1 || {
    echo "" >> "$REPORT_FILE"
    echo "## P0/P1 Pending Radar 条目只读补证据（via executor）" >> "$REPORT_FILE"
    echo "（补证据失败）" >> "$REPORT_FILE"
}

echo "=== Tech Radar 周审查完成 ===" | tee -a "$LOG_FILE"
echo "REPORT_FILE=$REPORT_FILE"
cat "$REPORT_FILE"
