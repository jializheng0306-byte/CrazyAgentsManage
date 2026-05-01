#!/bin/bash
# daily-reflection.sh - 每日反思脚本
# 每日23:00执行

set -e

LOG_DIR="$HOME/.hermes/logs"
LOG_FILE="$LOG_DIR/daily-reflection-$(date +%Y%m%d).log"
REFLECTION_DIR="$HOME/.hermes/reflections"

mkdir -p "$LOG_DIR" "$REFLECTION_DIR"

echo "=== 每日反思开始 $(date) ===" | tee -a "$LOG_FILE"

# 1. 当日回顾
echo "1. 回顾当日工作..." | tee -a "$LOG_FILE"

# 统计Git提交
cd "$HOME/CrazyAgentsManage" 2>/dev/null || cd "$HOME"
COMMIT_COUNT=$(git log --oneline --since="today" 2>/dev/null | wc -l)
echo "  Git提交数: $COMMIT_COUNT" | tee -a "$LOG_FILE"

# 统计任务完成情况
PROMISE_DIR="$HOME/.hermes/promises"
TODAY_COMPLETED=$(find "$PROMISE_DIR" -name "*.json" -newer "$PROMISE_DIR" -exec grep -l "completed" {} \; 2>/dev/null | wc -l)
echo "  完成承诺数: $TODAY_COMPLETED" | tee -a "$LOG_FILE"

# 2. 效率分析
echo "2. 分析工作效率..." | tee -a "$LOG_FILE"
EFFICIENCY_FILE="$REFLECTION_DIR/efficiency-$(date +%Y%m%d).json"

cat > "$EFFICIENCY_FILE" << EOF
{
  "date": "$(date +%Y-%m-%d)",
  "git_commits": $COMMIT_COUNT,
  "promises_completed": $TODAY_COMPLETED,
  "tasks_planned": 10,
  "tasks_completed": $TODAY_COMPLETED,
  "efficiency_score": $(echo "scale=2; $TODAY_COMPLETED * 10" | bc 2>/dev/null || echo "0")
}
EOF

echo "  效率数据已记录: $EFFICIENCY_FILE" | tee -a "$LOG_FILE"

# 3. 经验总结
echo "3. 总结经验教训..." | tee -a "$LOG_FILE"
REFLECTION_FILE="$REFLECTION_DIR/reflection-$(date +%Y%m%d).md"

cat > "$REFLECTION_FILE" << EOF
# 每日反思 $(date +%Y-%m-%d)

## 今日完成
- Git提交: $COMMIT_COUNT 次
- 承诺完成: $TODAY_COMPLETED 个

## 效率评估
- 计划任务: 10 个
- 实际完成: $TODAY_COMPLETED 个
- 完成率: $(echo "scale=2; $TODAY_COMPLETED * 100 / 10" | bc 2>/dev/null || echo "0")%

## 经验教训
- [待总结]

## 改进计划
- [待制定]

## 明日重点
- [待规划]

---
反思时间: $(date)
EOF

echo "  反思已生成: $REFLECTION_FILE" | tee -a "$LOG_FILE"

# 4. 系统维护
echo "4. 执行系统维护..." | tee -a "$LOG_FILE"

# 清理旧日志（保留7天）
find "$LOG_DIR" -name "*.log" -mtime +7 -delete 2>/dev/null || true
echo "  旧日志已清理" | tee -a "$LOG_FILE"

# 清理临时文件
find /tmp -name "hermes-*" -mtime +1 -delete 2>/dev/null || true
echo "  临时文件已清理" | tee -a "$LOG_FILE"

# 5. 发送到飞书群
echo "5. 发送反思报告到飞书群..." | tee -a "$LOG_FILE"
CHAT_ID="oc_bbde428675a7c267d55c3f0663ca701d"

lark-cli im +messages-send --chat-id "$CHAT_ID" --text "🌙 每日反思 ($(date +%Y-%m-%d))

今日完成:
- Git提交: $COMMIT_COUNT 次
- 承诺完成: $TODAY_COMPLETED 个

效率评估:
- 完成率: $(echo "scale=2; $TODAY_COMPLETED * 100 / 10" | bc 2>/dev/null || echo "0")%

---
📁 反思报告目录: https://bcn7uazoofu0.feishu.cn/drive/folder/YUfPftiTils0wedMGnvcBrr1nEg" 2>&1 | tee -a "$LOG_FILE"

echo "=== 每日反思完成 $(date) ===" | tee -a "$LOG_FILE"
