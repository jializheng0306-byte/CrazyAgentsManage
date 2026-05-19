#!/bin/bash
# noon-paper-review.sh - 午间论文解读脚本（repo-tracked source-of-truth）
# 每日12:00执行，调用 noon-paper-collector.sh 形成原始只读采集结果，
# 再生成本地 review copy 和简短飞书摘要。

set -euo pipefail

TODAY=$(date +%Y-%m-%d)
TODAY_COMPACT=$(date +%Y%m%d)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$HOME/.hermes/logs"
INTEL_DIR="$HOME/.hermes/intel"
PAPER_DIR="$HOME/.hermes/papers"
KNOWLEDGE_DIR="$HOME/.hermes/knowledge"
LOG_FILE="$LOG_DIR/noon-paper-${TODAY_COMPACT}.log"
COLLECTOR_SCRIPT="$SCRIPT_DIR/noon-paper-collector.sh"
SOURCE_REPORT="$INTEL_DIR/noon-paper-$TODAY.md"
REVIEW_FILE="$PAPER_DIR/review-${TODAY_COMPACT}.md"
CHAT_ID="${NOON_PAPER_CHAT_ID:-oc_bbde428675a7c267d55c3f0663ca701d}"
REPORT_FOLDER_URL="${NOON_PAPER_REPORT_URL:-https://bcn7uazoofu0.feishu.cn/drive/folder/Y60WfJXg7l0TXodK75Dc0azXnrc}"

mkdir -p "$LOG_DIR" "$INTEL_DIR" "$PAPER_DIR" "$KNOWLEDGE_DIR"

echo "=== 午间论文解读开始 $(date) ===" | tee -a "$LOG_FILE"

echo "1. 运行 repo-tracked collector..." | tee -a "$LOG_FILE"
if "$COLLECTOR_SCRIPT" >>"$LOG_FILE" 2>&1; then
  echo "  ✅ collector 完成" | tee -a "$LOG_FILE"
else
  echo "  ⚠️ collector 失败，保留已生成的部分结果" | tee -a "$LOG_FILE"
fi

if [ ! -f "$SOURCE_REPORT" ]; then
  echo "  ❌ 未生成 $SOURCE_REPORT" | tee -a "$LOG_FILE"
  exit 1
fi

cp "$SOURCE_REPORT" "$REVIEW_FILE"
cp "$SOURCE_REPORT" "$KNOWLEDGE_DIR/paper-${TODAY_COMPACT}.md"
echo "2. 已复制 review / knowledge 副本" | tee -a "$LOG_FILE"

SUMMARY_TEXT="$(python3 - "$SOURCE_REPORT" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
lines = path.read_text(encoding="utf-8").splitlines()
headings = [line[4:].strip() for line in lines if line.startswith("### ")]
sections = [line[3:].strip() for line in lines if line.startswith("## ")]

print(f"📚 午间论文解读 ({path.stem.split('-')[-1]})")
print()
if sections:
    print("已完成采集分区:")
    for section in sections[:4]:
        print(f"- {section}")
    print()
if headings:
    print("今日重点论文:")
    for heading in headings[:3]:
        print(f"- {heading[:90]}")
else:
    print("今日重点论文: （待人工复核）")
print()
print("完整报告目录: REPORT_URL_PLACEHOLDER")
PY
)"
SUMMARY_TEXT="${SUMMARY_TEXT/REPORT_URL_PLACEHOLDER/$REPORT_FOLDER_URL}"

echo "3. 发送飞书摘要（best-effort）..." | tee -a "$LOG_FILE"
if lark-cli im +messages-send --chat-id "$CHAT_ID" --text "$SUMMARY_TEXT" >>"$LOG_FILE" 2>&1; then
  echo "  ✅ 飞书摘要发送成功" | tee -a "$LOG_FILE"
else
  echo "  ⚠️ 飞书摘要发送失败（不阻塞主链）" | tee -a "$LOG_FILE"
fi

echo "=== 午间论文解读完成 $(date) ===" | tee -a "$LOG_FILE"
echo "REVIEW_FILE=$REVIEW_FILE"
