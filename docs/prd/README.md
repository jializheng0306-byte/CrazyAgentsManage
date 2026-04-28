# PRD 体系说明

## 文档目的

CrazyAgentsManage 现在使用一套拆分式 PRD 体系，而不再依赖单一的大一统产品文档。

之所以拆分，是因为项目已经收敛出两条紧密耦合但职责不同的实施路径：

1. 技术实现路径
2. 运营实现路径

这种拆分方式也更符合仓库中已经接受的 Codex/HermesAgent 角色模型：

- `Codex` 负责开发规划、实施节奏和文档版本管理
- `HermesAgent` 负责运营 framing、运行时复核和运营验收

## 当前共识基线

当前仓库共享的产品理解是：

- `CrazyAgentsManage` 是一个以 HermesAgent 为宿主的 FlowMind 运营产品
- `FlowMind` 是治理引擎与 canonical truth 层，而不是 operator console 本身
- `Codex` 仍然是开发 lane
- `HermesAgent` 仍然是运营 lane

这个基线不应被随意重开。只有在仓库证据发生变化时才应更新。

## 规范性文档

### 上位产品基础文档

文件：

- `docs/prd/hermesagent-hosted-flowmind-product-foundation.md`

适用范围：

- 顶层产品定位
- 一级信息架构
- 运营策略
- 产品叙事冲突的统一口径

所有下游 PRD 都应继承它。

### 技术实现 PRD

文件：

- `docs/prd/technical-implementation-prd.md`

适用范围：

- 架构边界
- 前后端实现范围
- 数据契约
- 运行时集成表面
- 技术验收标准

### 运营实现 PRD

文件：

- `docs/prd/operations-implementation-prd.md`

适用范围：

- operator personas
- runtime signals 与 dashboards
- operator workflows
- action surfaces
- 运营验收标准

### 执行路线图

文件：

- `docs/roadmap/prd-execution-roadmap.md`

适用范围：

- phase 排序
- 实施顺序
- 文档更新节奏
- 发布与 merge gate

### 下一级技术子 PRD

文件：

- `docs/prd/runtime-observability-implementation-prd.md`
- `docs/prd/governance-surface-implementation-prd.md`
- `docs/prd/operations-surface-implementation-prd.md`
- `docs/prd/collaboration-workflow-implementation-prd.md`

适用范围：

- 在技术 PRD 之下继续拆分关键实施面
- 将 `Runtime` 与 `Governance` 两个一级分区收敛为可执行范围

### 下一级运营工作流 PRD

文件：

- `docs/prd/governance-operator-workflow-prd.md`
- `docs/prd/collaboration-operator-workflow-prd.md`

适用范围：

- 将 `Governance` 与 `Collaboration` 两个一级分区继续拆成 operator 可执行工作流
- 让状态展示继续推进为运营闭环

### 页面级 PRD

文件：

- `docs/prd/pages/overview-page-prd.md`
- `docs/prd/pages/runtime-page-prd.md`
- `docs/prd/pages/governance-page-prd.md`
- `docs/prd/pages/operations-page-prd.md`
- `docs/prd/pages/collaboration-page-prd.md`
- `docs/prd/pages/architecture-visualization-pages-prd.md`
- `docs/prd/pages/webui-route-template-alignment.md`

适用范围：

- 将一级 IA 继续拆成正式页面需求
- 为后续 UI 规格、交互稿和实施任务提供页面层约束
- 将现有 WebUI 模板与路由映射到新的 IA

## 旧文档定位

以下文档仍然有价值，但现在更适合作为背景输入，而不是唯一的规范性 PRD 表面：

- `docs/prd/product-requirements.md`
- `docs/prd/multi-agent-architecture-design.md`
- `docs/prd/observability-design.md`
- `docs/06-agent-ops/hermes-agent-operations-design.md`

当这些文档与当前体系发生冲突时，应以"上位产品基础文档 + 拆分 PRD + roadmap"为当前有效基线。

## 更新规则

每次出现非平凡迭代，在宣布完成前都应更新受影响的文档：

1. 如果产品身份、一级 IA 或运营策略变化，更新上位产品基础文档
2. 更新技术 PRD
3. 更新运营 PRD
4. 更新执行路线图
5. 如果协作状态变化，更新 harness closeout / handoff artifacts

如果一次迭代只影响 runtime 运营表面，运营 PRD 和 roadmap 仍需更新。
如果一次迭代只影响工程实现范围，技术 PRD 和 roadmap 仍需更新。

## Merge 规则

共享分支上的一次变更，在以下条件全部满足前，不应被视为真正完成：

1. 受影响的 PRD 已更新
2. roadmap 状态已更新
3. Codex/HermesAgent handoff 状态与仓库事实一致