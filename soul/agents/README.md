# Agent 注册表

> 定义每个 Agent 的身份、存储路径和职责边界

| Agent | SOUL.md | .learnings/ | MEMORY.md | 职责 |
|-------|---------|-------------|-----------|------|
| intel-sentinel | soul/agents/intel-sentinel/SOUL.md | soul/agents/intel-sentinel/learnings/ | 共享主 MEMORY.md | 情报采集+评估+Tech Radar |
| promise-keeper | soul/agents/promise-keeper/SOUL.md | soul/agents/promise-keeper/learnings/ | 共享主 MEMORY.md | 承诺治理+状态追踪 |
| ops-guardian | soul/agents/ops-guardian/SOUL.md | soul/agents/ops-guardian/learnings/ | 共享主 MEMORY.md | 系统运维+Cron可观测性 |

## 独立进程模型

当前实现：单实例 + 角色切换（cron agent prompt 指定角色）
目标实现：每个 Agent 独立 Hermes 实例（需要框架级支持）

中间态：每个 Agent 有独立的 SOUL.md 和 .learnings/，但共享 MEMORY.md 和 cron 调度。
这比纯 prompt 切换更好——Agent 有持久化的身份和学习空间。

## 协作规则

1. 每个 Agent 只修改自己的 .learnings/，不修改其他 Agent 的
2. 共享的 shared-context/ 通过三态协议通信
3. SOUL.md 修改需要用户确认
