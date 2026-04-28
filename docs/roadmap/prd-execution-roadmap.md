# PRD 执行路线图

## 目的

这份路线图是拆分 PRD 体系的统一执行跟踪面。

它负责协调：

- 技术实现工作
- 运营实现工作
- 文档版本管理
- `Codex / HermesAgent` 的 closeout 更新

## 规范输入

本路线图必须始终与以下文档保持一致：

1. `docs/prd/technical-implementation-prd.md`
2. `docs/prd/operations-implementation-prd.md`
3. `docs/codex-hermes-role-design.md`
4. `docs/02-engineering/harness/CODEX-HERMES-COLLABORATION-MECHANISM.md`

## 责任归属

- `Codex` 负责路线图编辑、节奏排序和文档版本管理
- `HermesAgent` 负责从运营验收视角复核路线图变化

## 当前产品共识

项目目前已经达成的基线共识是：

- `CrazyAgentsManage` 是 Hermes 侧的运营控制台
- `FlowMind` 是治理引擎 / canonical truth 层
- `Codex` 负责实施规划与交付推进
- `HermesAgent` 负责运营 framing 与验收

## 工作流分组

### 工作流 A：技术实现

来源：

- `docs/prd/technical-implementation-prd.md`

关注点：

- adapters
- task / delegation substrate
- team / shared-context substrate
- runtime controls
- observability UI

### 工作流 B：运营实现

来源：

- `docs/prd/operations-implementation-prd.md`

关注点：

- operator views
- operator actions
- alerts / reports
- FlowMind 关联运营状态
- acceptance gates

## 执行阶段

### Phase 0 — 文档基线

状态：进行中

目标：

- 把 PRD 拆成技术与运营两份文档
- 建立路线图作为 canonical 执行跟踪面
- 把文档更新接入 harness 流程

完成条件：

- 拆分 PRD 文件存在
- 路线图存在
- harness 入口已经指向新的文档治理流程

### Phase 1 — Runtime / Substrate Readiness

目标：

- 稳定技术 substrate
- 暴露真实 runtime signals
- 明确可被运营使用的运行时对象

主要产出：

- adapter hardening
- task / delegation 可见性
- runtime signal exposure

### Phase 2 — Operator Surface Readiness

目标：

- 让 UI / API 表面对齐真实运行时动作
- 暴露不依赖 mock 的运营工作流

主要产出：

- session / task / cron / alert 视图
- 结构化运营动作
- 运行时对象间的 cross-linking

### Phase 3 — Governance / FlowMind Readiness

目标：

- 让 CrazyAgentsManage 对齐真实 FlowMind bridge surfaces
- 区分 Hermes runtime truth 与 FlowMind canonical truth

主要产出：

- bridge-aware operator UX
- candidate / truth distinction
- review 与 feedback 可见性

### Phase 4 — 运营体系：情报链路与记忆迭代

状态：🟡 进行中（P0+P1 已落地，P2 待实施）

来源：
- `docs/prd/operations-implementation-prd.md`（差距审计 1-5）
- 参考：《OpenClaw 实战》文章描述的完整运营体系

目标：
- 建立完整的情报采集→评估→决策→落地链路
- 实现记忆自主迭代循环
- 补齐 Harness 配置防退化机制
- 建立 Tech Radar 结构化技术跟踪

主要产出：

**P0 — 情报与记忆基础（本周）**：

| 任务 | 状态 | 说明 |
|------|------|------|
| 创建 `shared-context/tech-radar.json` | 🟢已落地 | Adopt/Trial/Assess 三级结构 |
| 升级晨间/晚间 cron 为 agent 模式 | 🟢已落地 | 08:30/20:00 agent 模式，5星评估+影响分析+Tech Radar更新 |
| 创建 `.learnings/` 目录结构 | 🟢已落地 | harness/learnings/{ERRORS,LEARNINGS,FEATURE_REQUESTS}.md |
| 升级反思 cron 支持 .learnings/ 审查 | 🟢已落地 | 审查 pending 条目，≥3次 promote 到 MEMORY.md |

**P1 — 记忆与可观测性（下周）**：

| 任务 | 状态 | 说明 |
|------|------|------|
| 配置 session Harness 参数 | 🟢已落地 | auto_prune=true, retention=7d, compression.threshold=0.4 |
| 实现 bootstrap hook 加载历史经验 | 🟢已落地 | bootstrap-context.sh + prefill_messages_file |
| MEMORY.md 容量管理 | 🟢已落地 | memory-maintenance.sh + 每周日 cron |
| cron 可观测性 | 🟢已落地 | cron-health-check.sh + 每日两次 cron |

**P2 — 完整链路（月底）**：

| 任务 | 状态 | 说明 |
|------|------|------|
| 情报→影响分析→行动建议 | 🔴 | 每条有价值情报必须有对现有系统的评估 |
| Tech Radar 周审查 | 🔴 | Zoe 每周审查 Adopt/Trial/Assess 变化 |
| 评估→确认→委派编码 | 🔴 | 用户确认后自动 delegate_task 给 Codex/Claude Code |
| 情报 cron 覆盖午间 | 🔴 | 补充 noon-paper-review 12:00 |

## 迭代收口规则

每次非平凡迭代结束后，必须同步更新：

1. 技术 PRD（若技术范围有变化）
2. 运营 PRD（若运营语义有变化）
3. 本路线图（若阶段/状态/优先级有变化）
4. harness closeout 工件（若 `Codex / HermesAgent` 协作状态有变化）

## 合并门槛

一次共享分支上的迭代，只有在以下条件都满足时，才算真正完成：

1. 受影响的 PRD 文档已更新
2. 路线图状态已更新
3. 仓库工件已经反映接受后的真相
4. HermesAgent 的验收意见已解决，或被明确延期

## 当前直接下一步

1. 继续把 split PRD set 作为 planning baseline
2. 新任务必须明确归入技术实现或运营实现
3. 每次迭代 closeout 都必须触发文档更新
