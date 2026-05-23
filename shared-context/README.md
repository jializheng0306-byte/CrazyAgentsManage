# shared-context/ 跨 Agent 共享状态目录

> 基于《OpenClaw 实战》文章的 shared-context/ 标准化设计

## One-Page Summary

### 这个目录解决什么问题

- 作为跨 Agent 的文件化共享状态层
- 为情报、决策、状态、task watcher、job-status 提供可追溯交换面
- 给 Hermes 宿主运行态和 Crazy 运营面提供中间状态缓冲

### 谁应该读

- 需要读写 shared-context 的开发者
- 需要理解 task watcher、tech radar、intel、三态协议的人
- 需要区分 shared-context 与仓库事实层的人

### 先读哪三份

1. [hermes-agent-operations-design.md](/home/flowmind/CrazyAgentsManage/docs/06-agent-ops/hermes-agent-operations-design.md)
2. [three-state-protocol.md](/home/flowmind/CrazyAgentsManage/docs/06-agent-ops/three-state-protocol.md)
3. [daily-workflow.md](/home/flowmind/CrazyAgentsManage/docs/06-agent-ops/daily-workflow.md)

### 典型工作流

1. Hermes / cron / watcher 写入 shared-context
2. Crazy 读取并转成运营动作、Bitable、handoff 或治理输入
3. 真正的 durable truth 仍需回写到 `docs/` 或 `harness/`

### 常见误区

- 把 shared-context 当长期规范事实层
- 只写状态，不补对应的治理或 closeout 文档
- 混淆 runtime signal、operator state、canonical truth

## 目录结构

```
shared-context/
├── tech-radar.json          # 技术雷达（Adopt/Trial/Assess 三级）
├── intel/                   # 情报共享（晨报/午报/晚报原始数据+评估结果）
├── roundtable/              # 圆桌讨论记录（三态协议通信）
├── decisions/               # 重大决策存档（P0/P1 评估结论）
├── status/                  # 各 Agent 当前状态 JSON
├── monitor-tasks/           # Task Watcher 持久化存储
├── agent-requests/          # request bus + automation promotion gate 生命周期
├── loop-surface/            # cycle / feedback input / memory candidate 本地 operator 留痕
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
- Task Bus / Promotion Gate → 写入 `agent-requests/requests.jsonl` + `agent-requests/events.jsonl`
- Loop Surface operator 动作 → 写入 `loop-surface/`

## 参考

- 文章：《OpenClaw 实战：一个人、一台 Mac、六个 AI Agent》
- 设计文档：`docs/06-agent-ops/hermes-agent-operations-design.md`
- 协议文档：`docs/06-agent-ops/three-state-protocol.md`
