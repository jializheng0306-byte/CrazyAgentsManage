# PRD 文档体系说明

## 目的

`CrazyAgentsManage` 不再依赖单一的大而全 PRD 作为唯一规划入口。

当前项目已经收敛为两条紧密耦合、但职责不同的实施轨道：

1. 技术实现轨
2. 运营实现轨

采用拆分式 PRD，是为了让仓库事实与当前已接受的 `Codex / HermesAgent` 分工保持一致：

- `Codex` 负责开发规划、实现排序、文档版本管理
- `HermesAgent` 负责运营 framing、运行时复核、运营验收

## 共识基线

当前双方已经达成的产品共识是：

- `CrazyAgentsManage` 是 Hermes 侧的运营控制台与运行态管理面
- `FlowMind` 是治理引擎与 canonical truth 层，不是运营控制台本身
- `Codex` 继续担任开发 lane
- `HermesAgent` 继续担任运营 lane

除非仓库事实发生变化，否则不应随意重开这一共识。

## 当前规范文档

### 技术实现 PRD

文件：

- `docs/prd/technical-implementation-prd.md`

用于承载：

- 架构边界
- 前后端实现范围
- 数据契约
- 运行时集成面
- 技术验收标准

### 运营实现 PRD

文件：

- `docs/prd/operations-implementation-prd.md`

用于承载：

- 运营角色与使用者视角
- 运行时信号与仪表板要求
- 运营工作流
- 运营动作入口
- 运营验收标准

### 执行路线图

文件：

- `docs/roadmap/prd-execution-roadmap.md`

用于承载：

- 阶段排序
- 实施顺序
- 文档更新节奏
- 发布与合并门槛

## 旧文档的定位

以下文件仍然是重要背景输入，但不再是唯一 canonical PRD 面：

- `docs/prd/product-requirements.md`
- `docs/prd/multi-agent-architecture-design.md`
- `docs/prd/observability-design.md`
- `docs/06-agent-ops/hermes-agent-operations-design.md`

当这些文件与拆分 PRD 产生冲突时，应优先以拆分后的 PRD 与路线图为准。

## 更新规则

每次发生非平凡迭代后，在宣布该轮完成之前，必须同步更新受影响的文档：

1. 技术 PRD
2. 运营 PRD
3. 执行路线图
4. 若协作状态发生变化，还要更新 harness closeout / handoff 工件

如果某轮只改了运行时运营语义，仍需更新运营 PRD 与路线图。
如果某轮只改了工程实现，仍需更新技术 PRD 与路线图。

## 合并规则

共享分支上的一次迭代，不应被视为“已完成”，除非：

1. 受影响的 PRD 文档已更新
2. 路线图状态已更新
3. `Codex / HermesAgent` 的交接状态与仓库真相一致
