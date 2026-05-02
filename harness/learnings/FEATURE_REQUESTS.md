# 功能需求

> Agent 在工作中发现的能力缺口、用户提出的新需求、可以改进的方向。

## 格式

```
- [LRN-YYYYMMDD-NNN] FEAT | priority: high/medium/low | status: pending/promoted/dismissed
  需求：需要什么能力
  场景：在什么情况下需要
  现状：当前怎么绕过的
```

## 记录

<!-- 新记录追加在此行下方 -->

- [LRN-20260501-003] FEAT | priority: high | status: pending
  需求：飞书 DocX block API 内容写入能力
  场景：午间论文 cron 创建了飞书文档但无法填充内容，API 返回 block 创建错误 1770029
  现状：文档创建成功但内容为空，多次尝试不同 block type 均失败

- [LRN-20260501-004] FEAT | priority: high | status: pending
  需求：Cron job output manifest（必须产出的文件列表）
  场景：午间论文 cron 漏写了 knowledge/paper-YYYYMMDD.md，agent 不清楚完整输出要求
  现状：每个 cron job 的输出文件依赖 agent 自行理解 prompt，没有显式声明
