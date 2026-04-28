#!/bin/bash
# memory-maintenance.sh - MEMORY.md 容量管理 + .learnings/ 清理
# 每周日 10:00 执行

set -e

MEMORY_FILE="$HOME/CrazyAgentsManage/soul/MEMORY.md"
LEARNINGS_DIR="$HOME/CrazyAgentsManage/harness/learnings"
LOG_DIR="$HOME/.hermes/logs"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/memory-maintenance-$(date +%Y%m%d).log"
echo "=== 记忆维护开始 $(date) ===" | tee "$LOG_FILE"

# 1. 检查 MEMORY.md 大小
echo "1. 检查 MEMORY.md 容量..." | tee -a "$LOG_FILE"
if [ -f "$MEMORY_FILE" ]; then
    CHARS=$(wc -c < "$MEMORY_FILE")
    LINES=$(wc -l < "$MEMORY_FILE")
    # 粗略估算 tokens (中文约 1.5 char/token, 英文约 4 char/token)
    ESTIMATED_TOKENS=$((CHARS * 2 / 3))
    echo "  字符数: $CHARS, 行数: $LINES, 估算tokens: $ESTIMATED_TOKENS" | tee -a "$LOG_FILE"
    
    if [ "$ESTIMATED_TOKENS" -gt 3000 ]; then
        echo "  ⚠️ MEMORY.md 超过 3000 tokens 上限！需要精简。" | tee -a "$LOG_FILE"
        echo "  ACTION_NEEDED=memory_compress" >> "$LOG_FILE"
    else
        echo "  ✅ 容量正常 ($ESTIMATED_TOKENS / 3000 tokens)" | tee -a "$LOG_FILE"
    fi
else
    echo "  ❌ MEMORY.md 不存在" | tee -a "$LOG_FILE"
fi

# 2. 检查 .learnings/ 统计
echo "2. 检查 .learnings/ 状态..." | tee -a "$LOG_FILE"
for f in ERRORS.md LEARNINGS.md FEATURE_REQUESTS.md; do
    filepath="$LEARNINGS_DIR/$f"
    if [ -f "$filepath" ]; then
        PENDING=$(grep -c "status: pending" "$filepath" 2>/dev/null || echo 0)
        PROMOTED=$(grep -c "status: promoted" "$filepath" 2>/dev/null || echo 0)
        DISMISSED=$(grep -c "status: dismissed" "$filepath" 2>/dev/null || echo 0)
        echo "  $f: pending=$PENDING, promoted=$PROMOTED, dismissed=$DISMISSED" | tee -a "$LOG_FILE"
    else
        echo "  $f: 不存在" | tee -a "$LOG_FILE"
    fi
done

# 3. 清理已 promoted/dismissed 超过 30 天的条目
echo "3. 清理旧条目..." | tee -a "$LOG_FILE"
for f in ERRORS.md LEARNINGS.md FEATURE_REQUESTS.md; do
    filepath="$LEARNINGS_DIR/$f"
    if [ -f "$filepath" ]; then
        BEFORE_LINES=$(wc -l < "$filepath")
        # 不自动删除，只统计（人工决定是否清理）
        AFTER_LINES=$BEFORE_LINES
        if [ "$BEFORE_LINES" -ne "$AFTER_LINES" ]; then
            echo "  $f: 清理了 $((BEFORE_LINES - AFTER_LINES)) 行" | tee -a "$LOG_FILE"
        fi
    fi
done

# 4. 生成维护报告
echo "4. 生成维护报告..." | tee -a "$LOG_FILE"
REPORT=$(cat << EOF
📊 记忆系统维护报告 $(date +%Y-%m-%d)

MEMORY.md: $(wc -c < "$MEMORY_FILE" 2>/dev/null || echo 0) 字符, ~$(( $(wc -c < "$MEMORY_FILE" 2>/dev/null || echo 0) * 2 / 3 )) tokens

.learnings/ 统计:
$(for f in ERRORS.md LEARNINGS.md FEATURE_REQUESTS.md; do
    fp="$LEARNINGS_DIR/$f"
    if [ -f "$fp" ]; then
        echo "- $f: pending=$(grep -c 'status: pending' "$fp" 2>/dev/null || echo 0), promoted=$(grep -c 'status: promoted' "$fp" 2>/dev/null || echo 0)"
    fi
done)

Hermes 配置:
- sessions.auto_prune: $(grep 'auto_prune' ~/.hermes/config.yaml | head -1 | awk '{print $2}')
- sessions.retention_days: $(grep 'retention_days' ~/.hermes/config.yaml | head -1 | awk '{print $2}')
- compression.threshold: $(grep 'threshold' ~/.hermes/config.yaml | head -1 | awk '{print $2}')
EOF
)

echo "$REPORT" | tee -a "$LOG_FILE"
echo "=== 记忆维护完成 $(date) ===" | tee -a "$LOG_FILE"
