# PRD 执行路线图

> **⚠️ 活跃主线说明（2026-04-30）**
>
> 本文档的 Phase 0-4 是旧版产品内部分阶段，用于细粒度任务参考。
> 当前活跃的联合产品执行顺序以以下文档为准：
>
> - `docs/roadmap/HermesAgent-FlowMind-联合产品功能基线-2026-04-30.md`
>
> Phase 映射关系：
> - 旧 Phase 0-1（文档基线 + Runtime Readiness）→ 新 Phase 1（Link Hardening）+ Phase 2（Ops Data Plane）
> - 旧 Phase 2（Operator Surface）→ 新 Phase 4（Operator Console Convergence）
> - 旧 Phase 3（Governance/FlowMind）→ 新 Phase 3（Governance Roundtrip）
> - 旧 Phase 4（情报链路）→ 已并入 Phase 2（Ops Data Plane）

## 目的

这份路线图是拆分 PRD 体系的统一执行跟踪面。

它负责协调：

- 技术实现工作
- 运营实现工作
- 文档版本管理
- Codex/HermesAgent closeout 更新

## 规范性输入

本路线图必须与以下文档保持对齐：

0. `docs/roadmap/HermesAgent-FlowMind-联合产品功能基线-2026-04-30.md`
0.1 `FlowMindDeploy/docs/01-product/HermesAgent-FlowMind-交互框架设计-2026-04-29.md`
0.2 `FlowMindDeploy/docs/01-product/HermesAgent-FlowMind-产品功能基线与迭代路线图-2026-04-30.md`
0.3 `FlowMindDeploy/docs/01-product/双仓-Control-Room-First-定位与规划调整-2026-05-22.md`

1. `docs/prd/hermesagent-hosted-flowmind-product-foundation.md`
2. `docs/prd/technical-implementation-prd.md`
3. `docs/prd/operations-implementation-prd.md`
4. `docs/prd/runtime-observability-implementation-prd.md`
5. `docs/prd/governance-surface-implementation-prd.md`
6. `docs/prd/operations-surface-implementation-prd.md`
7. `docs/prd/collaboration-workflow-implementation-prd.md`
8. `docs/prd/governance-operator-workflow-prd.md`
9. `docs/prd/collaboration-operator-workflow-prd.md`
10. `docs/prd/pages/overview-page-prd.md`
11. `docs/prd/pages/runtime-page-prd.md`
12. `docs/prd/pages/governance-page-prd.md`
13. `docs/prd/pages/operations-page-prd.md`
14. `docs/prd/pages/collaboration-page-prd.md`
15. `docs/prd/pages/architecture-visualization-pages-prd.md`
16. `docs/prd/pages/webui-route-template-alignment.md`
17. `docs/codex-hermes-role-design.md`
18. `docs/02-engineering/harness/CODEX-HERMES-COLLABORATION-MECHANISM.md`
19. `docs/roadmap/master-task-plan.md`

## Owner

- `Codex` 负责路线图编辑、阶段排序和文档版本管理
- `HermesAgent` 从运营验收角度复核路线图变更

## Cross-Repo Sync Gate

这份路线图是 Crazy 仓的执行入口，但不是联合产品的 canonical source。

如果 `FlowMindDeploy/docs/01-product/` 下的联合主 PRD / 主路线图发生变化，则在 Crazy 侧 closeout 前必须同时满足：

1. `docs/roadmap/HermesAgent-FlowMind-联合产品功能基线-2026-04-30.md` 已同步
2. `docs/prd/README.md` 已同步
3. 本路线图已同步
4. cross-repo PRD sync checker 已通过

检查命令：

```bash
scripts/check_cross_repo_prd_sync.sh
```

当 `FlowMindDeploy` 的 Phase 6 canonical docs 变化时，Crazy 侧还必须同步以下镜像口径：

- `FlowMindDeploy/docs/01-product/Operator-Console-最小职责边界-2026-05-04.md`
- `FlowMindDeploy/docs/01-product/handoff-packet-contract-v1-2026-05-04.md`
- `FlowMindDeploy/docs/01-product/Phase6-默认SOP与提示词同步-2026-05-04.md`
- `FlowMindDeploy/docs/01-product/外部执行面-读写边界-v1-2026-05-04.md`
- `FlowMindDeploy/docs/01-product/治理动作分层口径-v1-2026-05-07.md`
- `FlowMindDeploy/docs/01-product/执行包字段对照与消费顺序-v1-2026-05-07.md`
- `FlowMindDeploy/docs/05-version-control/治理证据资产索引-v1-2026-05-07.md`

至少要保持以下默认规则不漂移：

- `truth.status` 是主状态唯一来源
- `feedback.eventType` 只进入运营动作层
- `timeline` 只消费 `traceEvents[]`
- `handoff` 默认消费 `moduleDetails.handoff + semanticContext + latestEvidence`
- `confirm / reject / clarify` 属于 review decision actions
- `approve / commit` 属于 truth promotion actions
- `confirmed / blocked / clarified / deferred / cancelled` 属于 operational feedback events
- `moduleDetails.handoff / semanticContext / latestEvidence / executionBoundary / handoffContract` 不得混写成同一种摘要
- closeout / governance 结论应按 `change record -> deploy fact -> acceptance/eval -> closeout seed -> governance report` 组合读取，而不是分散挑读
- `review decision actions` 继续只负责评审动作层
- `truth promotion actions` 继续只负责真值提升层
- `operational feedback events` 继续只负责运营反馈层
- `operational follow-up` 默认消费同一 Slice 1 projection，不由 Crazy / Hermes 本地重解释 `needsFollowUp / followUpKind / nextActor`
- `Slice 1` authoritative docs 继续是 `运营Follow-Up最小默认解释-v0-2026-05-14.md`、`Slice1-read-model-projection-任务分解-v0-2026-05-14.md` 与 `Slice1-read-model-projection-验收证据骨架-v0-2026-05-14.md`

## 当前产品共识

项目已经形成以下产品方向共识：

- `CrazyAgentsManage` 是一个以 HermesAgent 为宿主的 FlowMind 运营产品
- 在当前下一阶段中，它的主定位应收紧为 `operator-facing control room / control plane`
- `FlowMind` 是治理引擎 / canonical truth 层
- `Codex` 负责实施规划与交付
- `HermesAgent` 负责运营 framing 与验收

## 工作流分道

### Workstream A — 技术实现

来源：

- `docs/prd/technical-implementation-prd.md`
- `docs/prd/runtime-observability-implementation-prd.md`
- `docs/prd/governance-surface-implementation-prd.md`
- `docs/prd/operations-surface-implementation-prd.md`
- `docs/prd/collaboration-workflow-implementation-prd.md`

重点：

- adapters
- task/delegation substrate
- team/shared-context substrate
- runtime controls
- observability UI
- governance data surfaces
- operations-state surfaces
- collaboration evidence surfaces

### Workstream B — 运营实现

来源：

- `docs/prd/operations-implementation-prd.md`
- `docs/prd/governance-operator-workflow-prd.md`
- `docs/prd/collaboration-operator-workflow-prd.md`

重点：

- operator views
- operator actions
- alerts/reports
- FlowMind 关联运营状态
- acceptance gates

## 执行阶段

### Phase 0 — 文档基线

状态：完成

目标：

- 建立上位产品基础文档作为顶层规范定义
- 将 PRD 拆分为技术与运营文档
- 建立路线图作为规范性执行跟踪器
- 将文档更新规则绑定到 harness workflow

完成条件：

- 上位产品基础文档存在
- 拆分 PRD 文件存在
- 路线图存在
- harness 入口已指向新的治理流程

### Phase 1 — Runtime / Substrate Readiness

目标：

- 稳定技术 substrate
- 暴露真实 runtime signals
- 定义 operator-visible runtime objects

主要产出：

- adapter hardening
- task/delegation visibility
- runtime signal exposure
- `Overview` / `Runtime` 一级分区具备真实数据基础
- Harness 通用核心完成迁移并可作为 substrate closeout/governance 基础设施使用

### Phase 2 — Operator Surface Readiness

目标：

- 让 UI 与 API surface 对齐真实 runtime actions
- 在没有 mock 歧义的前提下暴露 operator workflows

主要产出：

- session / task / cron / alert views
- structured operator actions
- runtime objects 之间的 cross-linking
- `Operations` 分区对齐

### Phase 3 — Governance / FlowMind Readiness

目标：

- 让 CrazyAgentsManage 对齐真实存在的 FlowMind bridge surface
- 区分 Hermes runtime truth 与 FlowMind canonical truth

主要产出：

- bridge-aware operator UX
- candidate / truth distinction
- review 与 feedback visibility
- 第一版可用的 `Governance` 分区

### Phase 4 — Collaboration Productization

目标：

- 让 Codex/HermesAgent 协作 artifacts 成为产品可见 workflow state
- 让 closeout discipline 与 handoff status 可审阅

主要产出：

- collaboration evidence surfaces
- handoff / closeout traceability
- `Collaboration` 分区导航对齐
- Harness success / failure / critic / closeout 机制进入仓库实际工作流

### Phase 5 — Page-System Convergence

状态：进行中

目标：

- 把五个一级 IA 分区收敛为正式页面级需求
- 让架构展示页与真实状态页形成互跳关系

主要产出：

- Overview / Runtime / Governance / Operations / Collaboration 页面级 PRD
- Architecture Visualization 页面级 PRD
- WebUI 路由与模板对齐文档
- 页面与子 PRD / workflow PRD 的清晰映射

当前进度：

- `Overview` 已切换到五分区 IA 导航壳，并改为 `BASE` 感知的 API / 链接生成
- 旧功能模板的静态资源路径正在从硬编码 `/manage/static/*` 收口到 `{{ BASE }}/static/*`
- 治理摘要与协作摘要已进入 `Overview` 入口语义，但真实聚合数据仍待后续 API 补齐
- 2026-05-22 的双仓 control-room-first 校准已把 Phase 5 之后的默认下一跳收紧为 Crazy `Sprint 2 Control Plane Hardening`，其优先级高于继续扩更多 IA 聚合页
- 2026-05-28 的 Phase C 收尾线已经推进到第五切片并完成收口：`accept / reject / defer` 现在有独立 acceptance artifact，`writebackConfirmation` 也已在 `/collaboration` 中对象化；reviewer / Hermes acceptance 不再构成新的主产品 gap，后续如需更细粒度 handoff contract writeback 仅按增强项处理
- 2026-05-28 起 Phase D 的起手不再是新增页面，而是先把 `Overview` / `Runtime` / `Operations` 的状态源收敛成统一 canonical projection；`Overview` 已切到 `overview/support-projection`，`Runtime` 已切到 `runtime/summary`，`Operations` 已切到 `operations/support-projection`，状态源收口已经完成，后续只剩更细粒度对象卡片和跳转等增强项
- 2026-05-28 的 `Governance / Collaboration / Operations` gap audit 进一步确认没有新的 repo-tracked contract/read-surface gap；Phase D 已收口，后续不再保留活跃维护阶段

### Phase 5 之后的当前默认顺序（2026-05-22）

1. Crazy `Sprint 1 Operator Console Real Aggregation`
   - 当前状态：已在 Crazy lane 以已发布提交 `5e88b51`、`cedc03c` 收口
2. Crazy `Sprint 2 Control Plane Hardening`
   - 默认任务：
     - task bus 产品化
     - automation promotion gate 固化
     - role / credential / memory isolation 做实
     - executor capability plane integration
     - `Operations` 升级为真正 control room
     - `Loop Surface` 页面级 PRD
     - `daily-promise-review.py` + `morning-intel-v2.py` 首批 cycle 升级拆解
3. FlowMind `contract-gate`
   - 只在 Crazy 明确上报新的 contract/read-surface gap 后，才切回 FlowMind 开发执行

## 迭代收口规则

每次非平凡迭代结束后，至少更新：

1. 如果产品身份、一级 IA 或运营策略变化，更新上位产品基础文档
2. 如果实现范围变化，更新技术 PRD
3. 如果 operator-facing 含义变化，更新运营 PRD
4. 更新本路线图中的 phase / status
5. 如果 Codex/Hermes 协作状态变化，更新 harness closeout artifacts

## Merge Gate

共享分支上的一次迭代，在以下条件满足前，不应视为完成：

1. 受影响的 PRD 已更新
2. roadmap 状态已更新
3. 仓库 artifacts 已反映被接受的事实
4. HermesAgent 的 acceptance comments 已解决或被显式延后
5. 如果联合主规划发生变化，cross-repo PRD sync checker 已通过

## 当前运行态整改入口（2026-05-04）

当前 Crazy 侧更实的整改主线，不再是继续补抽象 PRD，而是围绕 Issue #14 的运行态断链做系统收口。

当前裁定文档：

- `docs/02-engineering/harness/issue-14-governance-ruling-2026-05-04.md`

该裁定把 Issue #14 重分为三组：

1. 可关闭
2. 降级但不关闭
3. 当前主阻塞

后续推进顺序固定为：

1. 调度 authority 收口
2. 反思与学习产物收口
3. 治理-行动链收口
4. Promise 治理稳定化

这意味着：

- Issue #14 现在是当前 runtime remediation 的正式入口
- 但它不改写联合产品主线，只承接运行态整改层

## 当前立即动作

1. 以上位产品基础文档作为产品身份与 IA 真相来源
2. 把新工作项显式路由到 technical lane 或 operations lane
3. 按五个一级 IA 分区继续推导 phase work
4. 在每次迭代 closeout 时强制执行文档更新
5. 以 `docs/roadmap/master-task-plan.md` 作为当前阶段的统一任务执行面
6. 对所有非平凡迭代启用 Harness closeout writeback
