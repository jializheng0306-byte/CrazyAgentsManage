#!/bin/bash
# cron-health-check.sh - Cron 可观测性检查
# 检查所有 cron 任务的健康状态，识别失败/零产出/静默失联

set -e

LOG_DIR="$HOME/.hermes/logs"
REPORT_DIR="$HOME/.hermes/cron-health"
mkdir -p "$LOG_DIR" "$REPORT_DIR"

TODAY=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/cron-health-$TODAY.log"
REPORT_FILE="$REPORT_DIR/cron-health-$TODAY.md"
STATUS_FILE="$REPORT_DIR/cron-health-$TODAY.json"

echo "=== Cron 健康检查 $(date) ===" | tee "$LOG_FILE"

# 1. 检查今天的 cron 日志
echo "1. 扫描今日 cron 日志..." | tee -a "$LOG_FILE"

ISSUES=0
{
    echo "# Cron 健康报告 $TODAY"
    echo ""
    echo "检查时间: $(date)"
    echo ""
    echo "## 任务状态"
    echo ""

    # 检查每个 cron 日志文件
    for logfile in "$LOG_DIR"/*-$(date +%Y%m%d).log; do
        if [ -f "$logfile" ]; then
            fname=$(basename "$logfile")
            lines=$(wc -l < "$logfile")

            # 检查是否有错误
            errors=$(grep -ci "error\|fail\|exception\|traceback" "$logfile" 2>/dev/null || echo 0)

            # 检查是否零产出（日志行数太少）
            if [ "$lines" -lt 5 ]; then
                status="⚠️ 零产出（仅 $lines 行）"
                ISSUES=$((ISSUES + 1))
            elif [ "$errors" -gt 0 ]; then
                status="❌ 有 $errors 个错误"
                ISSUES=$((ISSUES + 1))
            else
                status="✅ 正常"
            fi

            echo "- $fname: $status ($lines 行, $errors 错误)"
        fi
    done

    echo ""
    echo "## 异常汇总"
    echo ""
    if [ "$ISSUES" -eq 0 ]; then
        echo "✅ 无异常"
    else
        echo "⚠️ 发现 $ISSUES 个问题，需要关注"
    fi

    echo ""
    echo "## Hermes 配置状态"
    echo ""
    echo "- sessions.auto_prune: $(grep 'auto_prune' ~/.hermes/config.yaml 2>/dev/null | head -1 | awk '{print $2}')"
    echo "- sessions.retention_days: $(grep 'retention_days' ~/.hermes/config.yaml 2>/dev/null | head -1 | awk '{print $2}')"
    echo "- compression.threshold: $(grep 'threshold' ~/.hermes/config.yaml 2>/dev/null | head -1 | awk '{print $2}')"
    echo "- compression.enabled: $(grep -A1 'compression:' ~/.hermes/config.yaml 2>/dev/null | grep 'enabled' | awk '{print $2}')"

    echo ""
    echo "---"
    echo "生成时间: $(date)"
} > "$REPORT_FILE"

python3 - <<PY > "$STATUS_FILE"
import json

payload = {
    "checked_at": "$(date --iso-8601=seconds)",
    "issues": int("${ISSUES}"),
    "report_file": "${REPORT_FILE}",
    "log_file": "${LOG_FILE}",
}
print(json.dumps(payload, ensure_ascii=False, indent=2))
PY

echo "=== Cron 健康检查完成 ===" | tee -a "$LOG_FILE"
echo "报告: $REPORT_FILE" | tee -a "$LOG_FILE"
echo "状态: $STATUS_FILE" | tee -a "$LOG_FILE"
echo "问题数: $ISSUES" | tee -a "$LOG_FILE"

# 输出摘要供 cron agent 读取
echo ""
echo "CRON_HEALTH_ISSUES=$ISSUES"
cat "$REPORT_FILE"
