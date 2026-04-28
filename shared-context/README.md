# shared-context/ 跨 Agent 共享状态目录

> 基于《OpenClaw 实战》文章的 shared-context/ 标准化设计

## 目录结构

```
shared-context/
├── tech-radar.json          # 技术雷达（Adopt/Trial/Assess 三级）
├── intel/                   # 情报共享（晨报/午报/晚报原始数据+评估结果）
├── roundtable/              # 圆桌讨论记录（三态协议通信）
├── decisions/               # 重大决策存档（P0/P1 评估结论）
├── status/                  # 各 Agent 当前状态 JSON
├── monitor-tasks/           # Task Watcher 持久化存储
├── agent-requests/          # 通信 Guardrail 请求生命周期
└── job-status/              # cron 任务状态
```

## 设计原则

1. **状态驱动 > 消息驱动**：Agent 直接读文件，不依赖 sessions_send 的可靠性
2. **文件可追溯**：所有状态变更都有文件级审计
3. **DRI 原则**：一个文件只有一个 Directly Responsible Individual
4. **终态协议**：三态通信(request→confirmed→final)防止 ACK 风暴

## 使用方式

- 情报 cron → 写入 `intel/` + 更新 `tech-radar.json`
- 圆桌讨论 → 写入 `roundtable/`（按 ack_id 组织）
- 重大决策 → 写入 `decisions/`
- Agent 状态 → 写入 `status/`（JSON 格式）
- Task Watcher → 写入 `monitor-tasks/`

## 参考

- 文章：《OpenClaw 实战：一个人、一台 Mac、六个 AI Agent》
- 设计文档：`docs/06-agent-ops/hermes-agent-operations-design.md`
- 协议文档：`docs/06-agent-ops/three-state-protocol.md`
