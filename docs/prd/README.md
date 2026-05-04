# PRD 体系说明

## One-Page Summary

### 这个目录解决什么问题

- 固定 Crazy 的拆分式 PRD 体系
- 把技术实现、运营实现、联合产品镜像和执行路线图区分清楚
- 给双仓联动提供 Crazy 侧的受追踪镜像入口

### 谁应该读

- 需要更新 PRD、roadmap、镜像基线的人
- 需要做产品边界判断和运营验收的人
- 需要确认 Crazy 当前规范性文档顺序的人

### 先读哪三份

1. [hermesagent-hosted-flowmind-product-foundation.md](/home/flowmind/CrazyAgentsManage/docs/prd/hermesagent-hosted-flowmind-product-foundation.md)
2. [technical-implementation-prd.md](/home/flowmind/CrazyAgentsManage/docs/prd/technical-implementation-prd.md)
3. [operations-implementation-prd.md](/home/flowmind/CrazyAgentsManage/docs/prd/operations-implementation-prd.md)

当前联合镜像与执行入口同时应参考：

- [HermesAgent-FlowMind-联合产品功能基线-2026-04-30.md](/home/flowmind/CrazyAgentsManage/docs/roadmap/HermesAgent-FlowMind-%E8%81%94%E5%90%88%E4%BA%A7%E5%93%81%E5%8A%9F%E8%83%BD%E5%9F%BA%E7%BA%BF-2026-04-30.md)
- [prd-execution-roadmap.md](/home/flowmind/CrazyAgentsManage/docs/roadmap/prd-execution-roadmap.md)

当前 FlowMind canonical 的 Phase 6 默认口径还应同时参考：

- [Operator-Console-最小职责边界-2026-05-04.md](/home/flowmind/FlowMindDeploy/docs/01-product/Operator-Console-%E6%9C%80%E5%B0%8F%E8%81%8C%E8%B4%A3%E8%BE%B9%E7%95%8C-2026-05-04.md)
- [handoff-packet-contract-v1-2026-05-04.md](/home/flowmind/FlowMindDeploy/docs/01-product/handoff-packet-contract-v1-2026-05-04.md)
- [Phase6-默认SOP与提示词同步-2026-05-04.md](/home/flowmind/FlowMindDeploy/docs/01-product/Phase6-%E9%BB%98%E8%AE%A4SOP%E4%B8%8E%E6%8F%90%E7%A4%BA%E8%AF%8D%E5%90%8C%E6%AD%A5-2026-05-04.md)
- [外部执行面-读写边界-v1-2026-05-04.md](/home/flowmind/FlowMindDeploy/docs/01-product/%E5%A4%96%E9%83%A8%E6%89%A7%E8%A1%8C%E9%9D%A2-%E8%AF%BB%E5%86%99%E8%BE%B9%E7%95%8C-v1-2026-05-04.md)

### 典型工作流

1. 先确认是技术范围变化、运营范围变化，还是联合产品镜像变化
2. 按 PRD 分层更新对应文档
3. 如果触发 FlowMind canonical 变化，再同步更新 roadmap 和镜像入口并跑双仓检查

### 常见误区

- 只改某个子 PRD，不改上位产品基础文档或路线图
- 把旧背景文档继续当唯一规范表面
- FlowMind canonical 变化后，只在 Crazy 一侧口头说明，不做 mirror update

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

## 当前活跃规划入口

当前除了拆分式 PRD 之外，新增一个联合产品主线入口：

- `docs/roadmap/HermesAgent-FlowMind-联合产品功能基线-2026-04-30.md`

它的作用是：

- 重新定义当前活跃的联合产品实施顺序
- 说明旧 `v0.1.0 ~ v0.5.0` 路线图现在更适合作为能力清单，而不是当前实施顺序
- 对齐 `FlowMindDeploy` 侧已经完成的 phase 5/6 收口与双仓治理包

这个入口本质上是 mirror entrypoint，不是第二套母本。

它必须镜像以下 canonical docs：

- `FlowMindDeploy/docs/01-product/HermesAgent-FlowMind-交互框架设计-2026-04-29.md`
- `FlowMindDeploy/docs/01-product/HermesAgent-FlowMind-产品功能基线与迭代路线图-2026-04-30.md`

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

当这些文档与当前体系发生冲突时，应以“上位产品基础文档 + 拆分 PRD + roadmap”为当前有效基线。

## 更新规则

每次出现非平凡迭代，在宣布完成前都应更新受影响的文档：

1. 如果产品身份、一级 IA 或运营策略变化，更新上位产品基础文档
2. 更新技术 PRD
3. 更新运营 PRD
4. 更新执行路线图
5. 如果协作状态变化，更新 harness closeout / handoff artifacts

如果迭代触发了 `FlowMindDeploy/docs/01-product/` 下的 canonical 联合 PRD / 路线图变更，还必须同步更新：

1. `docs/roadmap/HermesAgent-FlowMind-联合产品功能基线-2026-04-30.md`
2. `docs/prd/README.md`
3. `docs/roadmap/prd-execution-roadmap.md`

必要时还要更新：

4. `README.md`

如果一次迭代只影响 runtime 运营表面，运营 PRD 和 roadmap 仍需更新。
如果一次迭代只影响工程实现范围，技术 PRD 和 roadmap 仍需更新。

联合规划同步检查命令：

```bash
scripts/check_cross_repo_prd_sync.sh
```

## Merge 规则

共享分支上的一次变更，在以下条件全部满足前，不应被视为真正完成：

1. 受影响的 PRD 已更新
2. roadmap 状态已更新
3. Codex/HermesAgent handoff 状态与仓库事实一致
4. 如果 canonical 联合主文档变化，cross-repo PRD sync checker 已通过
