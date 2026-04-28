#!/bin/bash
# evening-intel-collector.sh - 晚间趋势数据采集
# 由 cron agent 调用，采集 ai-builders-digest 日报供 agent 评估

set -e

TODAY=$(date +%Y-%m-%d)
INTEL_DIR="$HOME/.hermes/intel"
LOG_DIR="$HOME/.hermes/logs"
DIGEST_DIR="/root/ai-builders-digest"
mkdir -p "$INTEL_DIR" "$LOG_DIR"

LOG_FILE="$LOG_DIR/evening-intel-$(date +%Y%m%d).log"
REPORT_FILE="$INTEL_DIR/evening-intel-$TODAY.md"

echo "=== 晚间趋势采集 $(date) ===" | tee "$LOG_FILE"

# 1. 拉取 ai-builders-digest 最新
echo "1. 拉取 ai-builders-digest..." | tee -a "$LOG_FILE"
if [ -d "$DIGEST_DIR" ]; then
    cd "$DIGEST_DIR"
    git pull --ff-only 2>/dev/null || echo "  git pull 失败，使用本地缓存"
    cd "$HOME"
fi

# 2. 读取今日或最近日报
echo "2. 读取日报..." | tee -a "$LOG_FILE"
DAY_NAME=$(date +%a)
DIGEST_FILE="$DIGEST_DIR/zh/daily/ai-digest-$TODAY-$DAY_NAME.md"

if [ ! -f "$DIGEST_FILE" ]; then
    # 找最近的
    DIGEST_FILE=$(find "$DIGEST_DIR/zh/daily/" -name "ai-digest-*.md" 2>/dev/null | sort -r | head -1)
fi

cat > "$REPORT_FILE" << EOF
# 晚间趋势原始数据 $TODAY

采集时间: $(date)
EOF

if [ -f "$DIGEST_FILE" ]; then
    echo "3. 读取: $(basename "$DIGEST_FILE")" | tee -a "$LOG_FILE"
    {
        echo ""
        echo "## ai-builders-digest 日报"
        echo ""
        head -100 "$DIGEST_FILE"
    } >> "$REPORT_FILE"
else
    echo "  无可用日报" | tee -a "$LOG_FILE"
    echo "" >> "$REPORT_FILE"
    echo "## ai-builders-digest 日报" >> "$REPORT_FILE"
    echo "（无可用日报）" >> "$REPORT_FILE"
fi

# 3. 补充 RSS 采集
echo "4. 补充 RSS 采集..." | tee -a "$LOG_FILE"
{
    echo ""
    echo "## TechCrunch AI"
    echo ""
    curl -s --max-time 30 "https://techcrunch.com/category/artificial-intelligence/feed/" \
        | python3 -c "
import sys, xml.etree.ElementTree as ET, re
root = ET.fromstring(sys.stdin.read())
items = root.findall('.//item')[:5]
for item in items:
    title = item.find('title').text if item.find('title') is not None else 'N/A'
    link = item.find('link').text if item.find('link') is not None else ''
    desc = item.find('description')
    desc_text = re.sub(r'<[^>]+>', '', desc.text)[:200] if desc is not None and desc.text else ''
    print(f'### {title[:80]}')
    print(f'- 链接: {link}')
    if desc_text:
        print(f'- 简介: {desc_text[:150]}...')
    print()
" 2>/dev/null || echo "（TechCrunch 采集失败）"
} >> "$REPORT_FILE" 2>&1

echo "=== 晚间趋势采集完成 ===" | tee -a "$LOG_FILE"
echo "REPORT_FILE=$REPORT_FILE"
cat "$REPORT_FILE"
