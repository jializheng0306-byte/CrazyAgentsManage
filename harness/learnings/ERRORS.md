# 错误记录

> Agent 操作失败、用户纠正、系统异常时即时记录。
> 每日反思 cron 会审查 pending 条目，≥3 次复现的 promote 到 MEMORY.md。

## 格式

```
- [LRN-YYYYMMDD-NNN] ERR | priority: high/medium/low | status: pending/promoted/dismissed
  描述：发生了什么错误
  根因：为什么会发生
  修复：怎么解决的（如果已解决）
  复现次数：N
```

## 记录

<!-- 新记录追加在此行下方 -->

- [LRN-20260501-001] ERR | priority: high | status: pending
  描述：GitHub Trending 晨间情报采集返回空数据，cron 报告成功但实际无数据
  根因：morning-intel-collector.sh 第82行使用 `topic:ai-agent+OR+topic:llm-agent`，GitHub search API 不允许在 qualifier 间使用 OR，返回 422 错误；脚本用 `2>/dev/null` 静默丢弃了 stderr
  修复：简化查询为 `topic:ai-agent`，验证返回 5 个仓库
  复现次数：1（但 bug 自脚本创建以来一直存在，实际影响多天）

- [LRN-20260501-002] ERR | priority: medium | status: pending
  描述：午间论文 cron 生成的 knowledge/paper-20260501.md 为空模板，实际内容未写入
  根因：cron job 的 agent prompt 未明确要求将论文摘要写入 knowledge/paper-YYYYMMDD.md，agent 只写了 noon-paper 和 noon-value-assessment 两个文件
  修复：待修复——需更新 cron job prompt 添加 output manifest
  复现次数：1
