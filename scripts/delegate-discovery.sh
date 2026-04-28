#!/bin/bash
# delegate-discovery.sh - 情报→委派编码的评估脚本
# 由 cron agent 调用，读取 Tech Radar 中 Assess/Trial 条目，生成评估报告

set -e

TODAY=$(date +%Y-%m-%d)
RADAR_FILE="$HOME/CrazyAgentsManage/shared-context/tech-radar.json"
REPORT_DIR="$HOME/.hermes/intel/delegate-discoveries"
mkdir -p "$REPORT_DIR"

REPORT_FILE="$REPORT_DIR/discovery-$TODAY.md"

echo "=== 委派编码评估 $(date) ==="

cat > "$REPORT_FILE" << EOF
# 委派编码评估 $TODAY

评估时间: $(date)
EOF

# 读取 Tech Radar 中 status=pending 且 priority=P0/P1 的条目
{
    echo ""
    echo "## 待评估发现"
    echo ""
    if [ -f "$RADAR_FILE" ]; then
        python3 -c "
import json
with open('$RADAR_FILE') as f:
    radar = json.load(f)
entries = radar.get('entries', [])
pending = [e for e in entries if e.get('status') == 'pending' and e.get('priority') in ['P0', 'P1']]
if pending:
    print(f'共 {len(pending)} 条待评估')
    print()
    for i, e in enumerate(pending, 1):
        print(f'### {i}. {e[\"name\"]}')
        print(f'- 链接: {e.get(\"url\", \"无\")}')
        print(f'- 来源: {e.get(\"source\", \"N/A\")}')
        print(f'- 优先级: {e.get(\"priority\", \"N/A\")}')
        print(f'- 影响评估: {e.get(\"impact_assessment\", \"待评估\")}')
        print(f'- 建议行动: {e.get(\"action_suggested\", \"待评估\")}')
        print(f'- 发现日期: {e.get(\"discovered_date\", \"N/A\")}')
        print()
        print(f'**评估清单**:')
        print(f'- [ ] 源码可用性检查')
        print(f'- [ ] 与现有系统的兼容性评估')
        print(f'- [ ] 接入成本估算')
        print(f'- [ ] 风险评估')
        print(f'- [ ] 建议：直接接入 / 参考设计自研 / 暂不行动')
        print()
else:
    print('暂无待评估条目')
" 2>/dev/null || echo "(解析失败)"
    else
        echo "Tech Radar 文件不存在"
    fi
} >> "$REPORT_FILE"

echo "REPORT_FILE=$REPORT_FILE"
cat "$REPORT_FILE"
