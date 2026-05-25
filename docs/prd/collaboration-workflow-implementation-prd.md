# CrazyAgentsManage Collaboration 工作流实现 PRD

## 版本信息

| 字段 | 值 |
|------|-------|
| 产品 | CrazyAgentsManage |
| 文档类型 | 技术子 PRD / Collaboration Workflow |
| 版本 | v0.1.0 |
| 状态 | Draft |
| Owner | Codex |
| 继承自 | `docs/prd/technical-implementation-prd.md` |
| 最后更新 | 2026-05-25 |

## 文档目的

本文档将技术实现 PRD 中的 `Collaboration` 分区继续拆解为可执行实施范围，聚焦：

- handoff packets
- runtime snapshots
- closeout evidence
- governance evidence reading order
- `.omx/` 与 `docs/` / `harness/` 的证据链
- 技术架构页中的协作链路状态投影

## 继承关系

本文档继承：

- `docs/prd/hermesagent-hosted-flowmind-product-foundation.md`
- `docs/prd/technical-implementation-prd.md`
- `docs/prd/operations-implementation-prd.md`

## Collaboration 分区的产品职责

`Collaboration` 分区负责回答：

- Codex 交付了什么
- HermesAgent 复核了什么
- 哪些事实已被回写为仓库真相
- 哪些协作链路仍未闭环

## 实施范围

### 1. Handoff Surface

目标：

- 让 handoff packet 成为产品可见对象

实现要求：

- 标题、目标、关联 artifacts、问题清单、状态必须可见
- handoff 不得只停留在 chat 或 tmux 上下文里
- 当 handoff 需要携带治理上下文摘要时，默认应继承 Crazy page-facing canonical surface（`/api/runtime/handoffs?recordId=...`）或其上游 replay 结果，**不得**让 generator 再独立直连 `context-pack` 自造另一套摘要主链

### 2. Runtime Snapshot Surface

目标：

- 让 runtime snapshot 成为 operator 可检查的协作状态输入

实现要求：

- snapshot 的 phase、status、actor、summary 需可见
- runtime-local 属性需被明确标注

### 3. Closeout Evidence Surface

目标：

- 让 closeout 记录和仓库事实之间形成稳定证据链

实现要求：

- closeout 应能回链到 PRD、roadmap、handoff、相关文档
- 必须区分“已接受事实”和“运行时临时状态”
- 当需要组合治理结论时，应按 shared 顺序读取：
  - change record
  - deploy fact
  - acceptance / eval
  - closeout seed
  - governance report

### 4. Collaboration Graph Projection

目标：

- 让 `TechArchitecturePreviewPage` 展示协作链路的动态状态

实现要求：

- Codex、HermesAgent、handoff、runtime snapshot、closeout、repo truth 至少映射为稳定节点
- 每个节点支持已存在、进行中、缺失、异常四类状态

当前已落第一版 canonical surface：

- `GET /api/collaboration/graph-projection`
- `TechArchitecturePreviewPage` 读取同一条聚合状态源，而不是再独立拼另一套协作判断逻辑
- 当前链路节点已继续细化到 `Reviewer`、`Hermes Acceptance`、`PRD Closeout`

### 5. Collaboration Summary Aggregation

目标：

- 为 `Overview` 和 `Collaboration` 页面提供汇总层

实现要求：

- 至少提供 open handoff、pending closeout、missing writeback、unreviewed artifact 四类摘要
- 可供架构展示页复用

当前已落第一版 canonical surface：

- `GET /api/collaboration/summary`
- `Collaboration` 页面顶部 briefing / next hop / triage / evidence jumps
- 当前还会显式给出：
  - `reviewer / Hermes acceptance / PRD closeout` unified evidence chain
  - `next actor / next action`
  - repo-tracked evidence refs
  - `writebackConfirmation`
  - acceptance artifact 优先消费

### 6. Loop / Cycle Collaboration Surface

目标：

- 把 handoff / acceptance / feedback / memory candidate 的闭环表达，沉淀成 `Collaboration` 下的显式子表面

实现要求：

- `Loop Surface` 不单独升格为新的一级 IA
- 至少能表达：
  - 当前 round / cycle
  - 当前 gate
  - 待提交 feedback
  - 待确认 memory candidate
- 必须明确该面是协作/运营表达，不是新的治理 authority

## 实施优先级

### P0

- handoff、runtime snapshot、closeout 具备可见状态
- runtime-local 与 durable-truth 边界清楚

### P1

- `TechArchitecturePreviewPage` 获得第一版协作链路状态覆盖层
- 证据链可以回跳到 PRD / roadmap / harness

### P2

- 更强的协作自动化
- reviewer / acceptance 结果与 handoff contract 的更细粒度耦合

## 非目标

本文档不定义：

- 群聊交互细节
- 字段级页面原型
- 底层脚本实现细节

## 完成标准

1. 协作流程不再只是过程知识，而是产品表面的一部分
2. operator 能看见 handoff 到 closeout，再到 PRD / roadmap / tracker 的证据链
3. 技术架构页能展示协作链路的动态状态
