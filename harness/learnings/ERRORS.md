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
