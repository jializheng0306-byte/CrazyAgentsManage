#!/bin/bash
# noon-paper-review.sh - 午间论文解读脚本
# 每日12:00执行

set -e

LOG_DIR="$HOME/.hermes/logs"
LOG_FILE="$LOG_DIR/noon-paper-$(date +%Y%m%d).log"
PAPER_DIR="$HOME/.hermes/papers"

mkdir -p "$LOG_DIR" "$PAPER_DIR"

echo "=== 午间论文解读开始 $(date) ===" | tee -a "$LOG_FILE"

# 1. 搜索最新论文
echo "1. 搜索arxiv最新论文..." | tee -a "$LOG_FILE"
PAPER_FILE="$PAPER_DIR/papers-$(date +%Y%m%d).json"

if command -v arxiv &> /dev/null; then
    arxiv search --query "AI agent OR LLM OR multi-agent" --max-results 3 --output json > "$PAPER_FILE" 2>&1
    echo "  找到 $(jq length "$PAPER_FILE" 2>/dev/null || echo 0) 篇论文" | tee -a "$LOG_FILE"
else
    echo "  arxiv未安装，使用模拟数据" | tee -a "$LOG_FILE"
    echo '[]' > "$PAPER_FILE"
fi

# 2. 生成论文解读
echo "2. 生成论文解读..." | tee -a "$LOG_FILE"
REVIEW_FILE="$PAPER_DIR/review-$(date +%Y%m%d).md"

cat > "$REVIEW_FILE" << EOF
# 午间论文解读 $(date +%Y-%m-%d)

## 今日论文
[待更新]

## 关键发现
- [待分析]

## 应用场景
- [待评估]

## 学习笔记
- [待整理]

---
解读时间: $(date)
EOF

echo "  解读已生成: $REVIEW_FILE" | tee -a "$LOG_FILE"

# 3. 更新知识库
echo "3. 更新知识库..." | tee -a "$LOG_FILE"
KNOWLEDGE_DIR="$HOME/.hermes/knowledge"
mkdir -p "$KNOWLEDGE_DIR"

if [ -f "$REVIEW_FILE" ]; then
    cp "$REVIEW_FILE" "$KNOWLEDGE_DIR/paper-$(date +%Y%m%d).md"
    echo "  知识库已更新" | tee -a "$LOG_FILE"
fi

# 4. 发送到飞书群
echo "4. 发送论文解读到飞书群..." | tee -a "$LOG_FILE"
CHAT_ID="oc_bbde428675a7c267d55c3f0663ca701d"

lark-cli im +messages-send --chat-id "$CHAT_ID" --text "📚 午间论文解读 ($(date +%Y-%m-%d))

今日论文:
- [待更新]

关键发现:
- [待分析]

---
📁 报告目录: https://bcn7uazoofu0.feishu.cn/drive/folder/Y60WfJXg7l0TXodK75Dc0azXnrc" 2>&1 | tee -a "$LOG_FILE"

echo "=== 午间论文解读完成 $(date) ===" | tee -a "$LOG_FILE"
