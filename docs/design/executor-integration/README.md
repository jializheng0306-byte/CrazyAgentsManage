# Executor 融合总览

## 文档目的

本目录用于集中描述 CrazyAgentsManage 在当前大版本中的 executor 融合方案，以及它与此前的 UI 重构、后续运行端部署规划之间的关系。

这个版本不是简单“接一个 executor API”，而是三段连续演进：

1. **UI 重构**
   - 把 Crazy 从零散页面升级为统一 shell
   - 收敛到明确的一级 IA：
     - Overview
     - Runtime
     - Operations
     - Governance
     - Collaboration

2. **Executor 融合**
   - 把 executor 作为外部 capability plane 接入
   - 不把 executor 吞成 Crazy 的底座
   - 让 Operations 成为 integrations / sources / tools / credentials / provider health 的统一表面

3. **运行端部署规划**
   - 让 Hermes 继续作为 runtime host
   - 让 Executor 承接外部能力编排与受控代码执行
   - 让 FlowMind 继续作为治理真相层

---

# 1. 当前版本的核心变化

## 1.1 UI 重构

本轮大版本先完成了 Crazy WebUI 的壳层重构：

- 统一 shell / navigation / framing
- 各主分区页面重新组织
- 将产品身份固定为：
  - `Hermes-hosted FlowMind operating product`

这一步的意义是：

> 先把 Crazy 的产品壳立住，再决定哪些能力外接，哪些能力内收。

如果没有先完成 UI 重构，后续 executor 融合会直接混入旧页面结构，导致：

- 集成能力无固定落点
- Runtime / Operations / Governance / Collaboration 职责混乱
- executor 容易反向侵入产品壳

---

## 1.2 Executor 融合

在 UI 壳层稳定后，本轮实现了 executor 融合的第一阶段和第二阶段关键路径：

### 第一阶段：façade + 只读接入
- `Operations` 三栏 workbench
- Sources / Tool Catalog / Credential Health / Provider Health
- Crazy façade API
- sample mode + real HTTP mode

### 第二阶段：受控写入
- plugin-aware source onboarding
- source delete
- source refresh
- credential binding / unbinding
- capability-aware UI gating

### 已实现的真实模式
当前 bridge 已支持真实 executor local server：
- `/api/scope`
- `/api/scopes/:scopeId/sources`
- `/api/scopes/:scopeId/tools`
- plugin-specific source create
- plugin-specific source binding

---

# 2. 这一版为什么不是“把 executor 消化吸收进 Crazy”

这次方案刻意没有把 executor 内嵌为 Crazy 的主底座，原因是：

## 2.1 四者问题域不同
- Crazy = operator-facing product shell
- Hermes = runtime host
- FlowMind = governance truth layer
- Executor = capability plane

## 2.2 真相源不能混
不能让 executor 替代：
- Hermes runtime truth
- FlowMind governance truth
- Crazy collaboration / closeout truth

## 2.3 运行层接入比源码吞并更稳
直接消化 executor 代码的代价是：
- plugin lifecycle 被内嵌
- scope/source/tool/secret 模型被强耦合进 Crazy
- 后续和 upstream executor 分叉维护成本很高

所以当前版本采用的是：

> **运行层对接 + façade 投影 + capability-aware UI**

而不是：

> **源码层吞并 + 主模型替换**

---

# 3. 当前目录内文档说明

## 设计分析
- [capability-analysis.md](capability-analysis.md)
- [decision-summary.md](decision-summary.md)

## 实施方案
- [operations-integration-plan.md](operations-integration-plan.md)
- [operations-integrations-api-boundary-spec.md](operations-integrations-api-boundary-spec.md)
- [operations-integrations-ui-ia-spec.md](operations-integrations-ui-ia-spec.md)
- [aliyun-deployment-assessment-2026-05-18.md](aliyun-deployment-assessment-2026-05-18.md)

## 四系统联动分析
- [crazy-hermes-flowmind-executor-embedding-analysis.md](crazy-hermes-flowmind-executor-embedding-analysis.md)

这份联动分析里已经补齐：
- 产品视角时序图
- 实现视角时序图
- 分层架构图
- 能力边界矩阵

---

# 4. 当前版本的落地结论

## CrazyAgentsManage
- 保持产品壳
- 负责 operator-facing IA 和表面对象组织
- 用 façade 接 executor
- 在 Operations 中承接 integrations family

## HermesAgent
- 保持 runtime host
- 负责 session / trace / task lifecycle
- 在需要 external orchestration 时委派 executor

## FlowMind
- 保持 candidate / truth / review / provenance 真相层
- 不直接承载外部集成能力执行
- 只消费 executor 带来的证据结果

## Executor
- 承担 source / tool / secret / binding / plugin / execution
- 作为 capability plane 被 Crazy/Hermes 调用
- 不接管主产品模型

---

# 5. 将来的运行端部署规划

## 5.1 本地模式
- Executor local server 作为 sidecar 运行
- Crazy 通过 HTTP bridge 接入
- Hermes 通过 execution delegation 使用 executor capability plane

适合：
- 单机开发
- 本地 operator 工作站
- 低耦合快速验证

## 5.2 远端 / 共享环境模式
后续可演进为：
- Hermes runtime host 独立部署
- Crazy product shell 独立部署
- FlowMind governance service 独立部署
- Executor 作为共享 capability service / sidecar cluster

适合：
- 多人协作
- 共享集成能力面
- 更稳定的 provider / secrets / execution 设施

## 5.3 扩展方向
未来最有价值的运行端深化点：

1. **Execution Delegation Spec**
   - 哪些 Hermes task 允许委派给 executor
   - pause / resume / elicitation 如何回流

2. **Evidence Enrichment Pipeline**
   - executor 结果如何进入 FlowMind candidate / evidence

3. **Closeout Writeback Integration**
   - 哪些外部写回动作交给 executor 执行
   - 哪些最终事实仍由 Crazy / Hermes 持久化

---

# 6. 推荐阅读顺序

如果你是总控方 / 评审方，推荐按以下顺序阅读：

1. [decision-summary.md](decision-summary.md)
2. [capability-analysis.md](capability-analysis.md)
3. [operations-integration-plan.md](operations-integration-plan.md)
4. [operations-integrations-api-boundary-spec.md](operations-integrations-api-boundary-spec.md)
5. [operations-integrations-ui-ia-spec.md](operations-integrations-ui-ia-spec.md)
6. [crazy-hermes-flowmind-executor-embedding-analysis.md](crazy-hermes-flowmind-executor-embedding-analysis.md)

---

# 7. 一句话结论

这个大版本的主线不是“把 executor 塞进 Crazy”，而是：

> **先完成 Crazy 的产品壳重构，再把 executor 作为外部 capability plane 融入 Operations，并为将来 Hermes 运行端委派与 FlowMind 治理接入打通结构基础。**
