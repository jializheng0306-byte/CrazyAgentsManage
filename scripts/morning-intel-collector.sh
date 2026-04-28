#!/bin/bash
# morning-intel-collector.sh - 晨间情报数据采集
# 由 cron agent 调用，采集原始数据供 agent 评估

set -e

TODAY=$(date +%Y-%m-%d)
INTEL_DIR="$HOME/.hermes/intel"
LOG_DIR="$HOME/.hermes/logs"
mkdir -p "$INTEL_DIR" "$LOG_DIR"

LOG_FILE="$LOG_DIR/morning-intel-$(date +%Y%m%d).log"
REPORT_FILE="$INTEL_DIR/morning-intel-$TODAY.md"

echo "=== 晨间情报采集 $(date) ===" | tee "$LOG_FILE"

cat > "$REPORT_FILE" << EOF
# 晨间情报原始数据 $TODAY

采集时间: $(date)
EOF

# 1. arxiv 论文
echo "1. 采集 arxiv 论文..." | tee -a "$LOG_FILE"
{
    echo ""
    echo "## arxiv 论文 (AI Agent 相关)"
    echo ""
    curl -s --max-time 30 \
        "https://export.arxiv.org/api/query?search_query=all:AI+agent+OR+multi-agent+OR+LLM+agent&max_results=5&sortBy=submittedDate&sortOrder=descending" \
        | python3 -c "
import sys, xml.etree.ElementTree as ET
ns = {'a': 'http://www.w3.org/2005/Atom'}
root = ET.fromstring(sys.stdin.read())
for entry in root.findall('a:entry', ns):
    title = entry.find('a:title', ns).text.strip().replace('\n', ' ')
    arxiv_id = entry.find('a:id', ns).text.strip().split('/abs/')[-1]
    published = entry.find('a:published', ns).text[:10]
    authors = ', '.join(a.find('a:name', ns).text for a in entry.findall('a:author', ns)[:3])
    summary = entry.find('a:summary', ns).text.strip()[:300]
    print(f'### {title[:80]}')
    print(f'- ID: {arxiv_id}')
    print(f'- 作者: {authors}')
    print(f'- 日期: {published}')
    print(f'- 摘要: {summary}...')
    print(f'- 链接: https://arxiv.org/abs/{arxiv_id}')
    print()
" 2>/dev/null || echo "（arxiv 采集失败）"
} >> "$REPORT_FILE" 2>&1

# 2. Hacker News
echo "2. 采集 Hacker News..." | tee -a "$LOG_FILE"
{
    echo ""
    echo "## Hacker News 前页"
    echo ""
    curl -s --max-time 30 "https://hnrss.org/frontpage" \
        | python3 -c "
import sys, xml.etree.ElementTree as ET
import re
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
" 2>/dev/null || echo "（HN 采集失败）"
} >> "$REPORT_FILE" 2>&1

# 3. GitHub Trending (简化版)
echo "3. 采集 GitHub Trending..." | tee -a "$LOG_FILE"
{
    echo ""
    echo "## GitHub Trending"
    echo ""
    curl -s --max-time 30 "https://api.github.com/search/repositories?q=created:>$(date -d '7 days ago' +%Y-%m-%d)+topic:ai-agent+OR+topic:llm-agent&sort=stars&order=desc&per_page=5" \
        | python3 -c "
import sys, json
data = json.load(sys.stdin)
for repo in data.get('items', [])[:5]:
    print(f'### {repo[\"full_name\"]} ⭐{repo[\"stargazers_count\"]}')
    print(f'- 描述: {(repo.get(\"description\") or \"无\")[:150]}')
    print(f'- 链接: {repo[\"html_url\"]}')
    print(f'- 语言: {repo.get(\"language\", \"N/A\")}')
    print()
" 2>/dev/null || echo "（GitHub 采集失败）"
} >> "$REPORT_FILE" 2>&1

echo "=== 晨间情报采集完成 ===" | tee -a "$LOG_FILE"
echo "REPORT_FILE=$REPORT_FILE"
cat "$REPORT_FILE"
