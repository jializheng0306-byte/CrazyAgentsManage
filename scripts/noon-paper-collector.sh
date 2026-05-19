#!/bin/bash
# noon-paper-collector.sh - 午间论文数据采集
# 由 cron agent 调用，搜索最新 AI/Agent 学术论文

set -e

TODAY=$(date +%Y-%m-%d)
INTEL_DIR="$HOME/.hermes/intel"
LOG_DIR="$HOME/.hermes/logs"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$INTEL_DIR" "$LOG_DIR"

LOG_FILE="$LOG_DIR/noon-paper-$(date +%Y%m%d).log"
REPORT_FILE="$INTEL_DIR/noon-paper-$TODAY.md"

echo "=== 午间论文采集 $(date) ===" | tee "$LOG_FILE"

cat > "$REPORT_FILE" << EOF
# 午间论文摘要 $TODAY

采集时间: $(date)
EOF

# 0. Crossref via executor
echo "0. 通过 executor 读取 Crossref..." | tee -a "$LOG_FILE"
{
    python3 "$SCRIPT_DIR/fetch-crossref-papers-via-executor.py" \
        --heading "Crossref 最新 AI Agent / Multi-Agent 论文（via executor）" \
        --query "AI agent multi-agent LLM agent" \
        --rows 5 \
        --sort published \
        --order desc
} >> "$REPORT_FILE" 2>&1 || {
    echo "" >> "$REPORT_FILE"
    echo "## Crossref 最新 AI Agent / Multi-Agent 论文（via executor）" >> "$REPORT_FILE"
    echo "（Crossref via executor 采集失败）" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

# 通用解析函数
parse_arxiv() {
    python3 -c "
import sys, xml.etree.ElementTree as ET
ns = {'a': 'http://www.w3.org/2005/Atom'}
try:
    root = ET.fromstring(sys.stdin.read())
except:
    print('（解析失败）')
    sys.exit(0)
for entry in root.findall('a:entry', ns):
    title = entry.find('a:title', ns).text.strip().replace('\n', ' ')
    arxiv_id = entry.find('a:id', ns).text.strip().split('/abs/')[-1]
    published = entry.find('a:published', ns).text[:10]
    authors = ', '.join(a.find('a:name', ns).text for a in entry.findall('a:author', ns)[:3])
    summary = entry.find('a:summary', ns).text.strip()[:400]
    cats = [c.get('term') for c in entry.findall('a:category', ns)]
    print(f'### {title[:100]}')
    print(f'- ID: {arxiv_id}')
    print(f'- 作者: {authors}')
    print(f'- 日期: {published}')
    print(f'- 分类: {\", \".join(cats[:3])}')
    print(f'- 摘要: {summary}...')
    print(f'- 链接: https://arxiv.org/abs/{arxiv_id}')
    print()
"
}

# 1. AI Agent 论文
echo "1. 搜索 AI Agent 论文..." | tee -a "$LOG_FILE"
{
    echo ""
    echo "## AI Agent 论文"
    echo ""
    curl -s --max-time 60 \
        "https://export.arxiv.org/api/query?search_query=cat:cs.AI+AND+ti:agent&max_results=8&sortBy=submittedDate&sortOrder=descending" \
        | parse_arxiv 2>/dev/null || echo "（AI Agent 论文采集失败）"
} >> "$REPORT_FILE" 2>&1

# 2. Multi-Agent / 协作 论文
echo "2. 搜索 Multi-Agent 论文..." | tee -a "$LOG_FILE"
{
    echo ""
    echo "## Multi-Agent 协作论文"
    echo ""
    curl -s --max-time 60 \
        "https://export.arxiv.org/api/query?search_query=cat:cs.AI+AND+ti:multi-agent&max_results=5&sortBy=submittedDate&sortOrder=descending" \
        | parse_arxiv 2>/dev/null || echo "（Multi-Agent 论文采集失败）"
} >> "$REPORT_FILE" 2>&1

# 3. RAG 论文
echo "3. 搜索 RAG 论文..." | tee -a "$LOG_FILE"
{
    echo ""
    echo "## RAG 论文"
    echo ""
    curl -s --max-time 60 \
        "https://export.arxiv.org/api/query?search_query=cat:cs.AI+AND+ti:RAG&max_results=5&sortBy=submittedDate&sortOrder=descending" \
        | parse_arxiv 2>/dev/null || echo "（RAG 论文采集失败）"
} >> "$REPORT_FILE" 2>&1

# 4. Agent Memory / Context 论文
echo "4. 搜索 Agent Memory 论文..." | tee -a "$LOG_FILE"
{
    echo ""
    echo "## Agent Memory / Context Engineering 论文"
    echo ""
    curl -s --max-time 60 \
        "https://export.arxiv.org/api/query?search_query=cat:cs.AI+AND+ti:memory+AND+ti:agent&max_results=5&sortBy=submittedDate&sortOrder=descending" \
        | parse_arxiv 2>/dev/null || echo "（Agent Memory 论文采集失败）"
} >> "$REPORT_FILE" 2>&1

echo "=== 午间论文采集完成 ===" | tee -a "$LOG_FILE"
echo "REPORT_FILE=$REPORT_FILE"
cat "$REPORT_FILE"
