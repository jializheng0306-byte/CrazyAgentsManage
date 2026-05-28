# CrazyAgentsManage 总任务计划

## 文档定位

本文档是当前阶段的统一任务计划文档。

它在以下文档之上做执行收敛：

- `docs/prd/hermesagent-hosted-flowmind-product-foundation.md`
- `docs/prd/technical-implementation-prd.md`
- `docs/prd/operations-implementation-prd.md`
- `docs/roadmap/prd-execution-roadmap.md`
- `docs/prd/pages/*.md`
- `docs/02-engineering/harness/*.md`

它不替代上述文档，而是把它们重组为一个可执行、可验证、可 closeout 的任务总表。

## 一、当前产品与工程共识

### 1. 规范性产品身份

`CrazyAgentsManage` 的唯一主定位是：

`一个以 HermesAgent 为宿主的 FlowMind 运营产品`

当前双仓下一阶段补充解释：

- 它的默认下一阶段主定位应收紧为 `operator-facing control room / control plane`
- 不是第二套 truth authority
- 也不是“继续扩更多 agent 角色”优先的 playground

### 2. 规范性一级信息架构

- `Overview`
- `Runtime`
- `Operations`
- `Governance`
- `Collaboration`

### 3. 规范性协作模型

- `Codex` 负责开发、架构、验证、仓库事实更新
- `HermesAgent` 负责运营 framing、运行态复核、运营验收
- `.omx/` 是 runtime-local
- `docs/` 与 `harness/` 是 durable repository truth

### 4. 当前活跃联合产品主线

当前活跃主线不再是旧的 `v0.1.0 ~ v0.5.0` 顺序，而是：

- `CrazyAgentsManage` 作为 Hermes 侧运营编排系统
- `FlowMindDeploy` 作为下游治理真值系统
- 双方通过双仓治理包和 handshake smoke 共同演进

规范性入口：

- `docs/roadmap/HermesAgent-FlowMind-联合产品功能基线-2026-04-30.md`

## 二、现状梳理

### 1. 已完成基础层

- 已建立产品母文档
- 已拆分技术 PRD 与运营 PRD
- 已建立页面级 PRD 体系
- 已建立 PRD 路线图
- 已把 FlowMind 三个架构展示页吸收到产品 IA 中
- 已在 WebUI 中接入 IA 级过渡路由和架构页占位路由

### 2. 当前主要缺口

- 现有 WebUI 仍主要是旧功能页平铺，尚未完全收敛到新 IA 聚合页
- 架构展示页已接路由，但尚未接入真实 TSX 实现与动态状态数据
- Runtime / Operations / Governance / Collaboration 之间的数据联动仍需标准化
- Harness 机制在当前仓库仅有基础骨架，尚未具备 FlowMindDeploy 那样完整的 critic、closeout、worktree、cross-review 能力

## 三、总目标

本阶段总目标分为两条主线：

### A. 产品与实施主线

把 CrazyAgentsManage 从“旧 Hermes WebUI 功能页集合”推进为“以 HermesAgent 为宿主的 FlowMind 运营产品”。

### B. Harness 与执行治理主线

把 CrazyAgentsManage 从“有协作文档约定”推进为“具备完整 repository-owned Harness 机制”的项目。

### C. 双仓联动主线

把 CrazyAgentsManage 与 FlowMindDeploy 的连接从“脚本级集成”推进为“契约级协同”：

1. 连接加固
2. 运营数据底座
3. 治理闭环回写
4. operator console 收敛
5. 安全自动化升级

### D. Control Plane Hardening 主线

把 CrazyAgentsManage 从“已经能展示真实状态的 operator UI”推进为“可审计的 operator control plane”：

1. task bus
2. automation promotion gate
3. role / credential / memory isolation
4. executor capability plane integration
5. `Operations` control room consolidation

## 四、任务分解

## Workstream 1：产品定义与 PRD 收敛

### 目标

让所有后续实施都以母 PRD、拆分 PRD、页面级 PRD 和路线图为统一事实来源。

### 当前状态

已完成第一轮建立。

### 后续任务

1. 持续维护母 PRD 为唯一顶层定位来源
2. 把所有新工作项映射到 technical lane 或 operations lane
3. 把页面级 PRD 与真实 WebUI 实现持续对齐
4. 在每次非平凡迭代 closeout 时同步更新路线图与相关 PRD

### 验收标准

- 不再出现多个互相竞争的顶层产品叙事
- 每个新增工作项都能回链到 PRD 或页面级 PRD
- roadmap 能反映真实阶段状态

## Workstream 2：IA 与 WebUI 收敛

### 目标

把当前 WebUI 从旧模块平铺过渡到新的一级 IA。

### 当前状态

- 已新增：
  - `/runtime`
  - `/operations`
  - `/governance`
  - `/collaboration`
  - `/architecture/philosophy`
  - `/architecture/product`
  - `/architecture/tech`
- 已保留旧路由兼容

### 后续任务

1. 统一旧模板顶部导航为新 IA 导航
2. 将 `runtime.html`、`operations.html`、`governance.html`、`collaboration.html` 从过渡壳层升级为真实聚合页
3. 建立架构页节点到真实状态页和证据页的跳转
4. 将旧页面数据汇总逻辑抽象为可复用状态源

### 验收标准

- 用户可以通过新 IA 完整浏览主要产品表面
- 架构页不是静态说明页，而是具备状态和跳转能力
- 旧路由只作为兼容层，而不是主要产品入口

## Workstream 3：Runtime / Operations / Governance / Collaboration 实施

### 目标

让五个一级 IA 都具备真实运行意义，而不是仅有文档定义。

### 子任务

#### 3.1 Runtime

- 加固 session / token / lineage / trace 适配层
- 建立 stuck / zombie / failure inference
- 补齐可供架构页使用的动态状态投影

#### 3.2 Operations

- skills、cron、team memory、alerts 的真实状态接入
- 区分未配置、异常、已失效
- 将 operator action 与真实能力绑定

#### 3.3 Governance

- 对齐 candidate / truth / review / feedback / drift 状态
- 建立 FlowMind bridge-aware 的状态表达

#### 3.4 Collaboration

- 暴露 handoff packet、runtime snapshot、closeout artifact
- 建立从运行态证据跳转到仓库事实的链路

### 验收标准

- 每个 IA 分区都能回答它被定义时应该回答的问题
- 主要状态能回链到真实数据或真实工件
- 不再依赖 chat-only 解释

## Workstream 3.5：Control Plane Hardening

### 目标

在 Sprint 1 聚合页基础上，把 Crazy 的下一阶段重点从“继续补页面”提升为“让控制平面本身成为产品能力”。

### 当前状态

- Sprint 1 已在 Crazy lane 本地形成两轮 Lore 提交：
  - `5e88b51` freeze baseline
  - `cedc03c` close remaining overview hardening risks
- `Operations / Overview / host health / focused Playwright gate` 已完成闭环，tunnel-backed live gate 已产品化为 canonical 验证路径
- `Centaur Loop` 借鉴线当前已从纯分析层推进到两份执行文档：
  - `docs/prd/pages/loop-surface-page-prd.md`
  - `docs/roadmap/sprint2-cycle-upgrade-first-batch-2026-05-22.md`

### 子项状态

| 子项 | Owner | 状态 | 当前口径 |
|---|---|---|---|
| Task Bus Productization | Crazy 主 | `completed-in-lane` | `Tasks` 已承接 `requests.jsonl + events.jsonl`，并显式暴露 `inbox / working / outbox / archive` 四条 lane、status transition 与事件审计 |
| Automation Promotion Gate | Crazy 主 | `completed-in-lane` | `Tasks` 已支持 `prototype → rehearsed → approved-for-automation → automated` 晋升链，并对 `evidence / approval / rollback rule` 执行最小门槛校验 |
| Executor Capability Plane Integration | Crazy 主 | `completed-in-lane` | `Operations` 已承接 `Sources / Tool Catalog / Credential Health / Provider Health / readonly delegation boundary` 五类 capability objects，并将 repo-tracked readonly delegation policy 投影为正式产品对象 |
| Role / Credential / Memory Isolation | Crazy 主 | `completed-in-lane` | `Operations` 已承接 role registry、credential ownership、memory boundaries 与 runbook visibility，并能在部署副本回退读取运行仓库事实 |
| Operations Control Room Consolidation | Crazy 主 | `completed-in-lane` | `Operations` 已补齐 `task registry / automation maturity / host health / runbooks` 四组 control-room 对象，并通过同一聚合层输出 next-hop 巡检面 |
| Loop Surface PRD | Crazy 主 | `completed-in-lane` | `loop-surface-page-prd.md` 已落地，且 `/collaboration/loops` 已接入最小 vertical slice 模板与 API |
| Cycle Upgrade First Batch | Crazy 主 | `completed-in-lane` | 已落 `promise-review-cycle` 与 `morning-intel-cycle` 两条首批 cycle 对象，并由 `/collaboration/loops` 统一消费 |
| Memory Candidate Confirmation | Crazy 主 | `completed-in-lane` | `Loop Surface` 已支持 `confirm / reject / defer` 本地留痕，并持久化到 `shared-context/loop-surface/memory-candidate-decisions.jsonl`；该动作只作用于 host-memory 候选，不等于 repo-side canonical accept |
| Feedback Input Surface | Crazy 主 | `completed-in-lane` | `Loop Surface` 已支持 manual-form-first 本地 operator queue，并持久化到 `shared-context/loop-surface/feedback-inputs.jsonl`；当前仍不直接写入 FlowMind feedback authority |
| FlowMind Contract Gate | Shared | `standing-gate` | 继续只在 Crazy 明确上报新的 contract/read-surface gap 时切回 FlowMind 开发执行 |

### Sprint 2 后续深化

1. 继续保持 `task bus / promotion gate` 与 harness closeout / runtime snapshot 的证据耦合，而不是退回聊天流
2. 保持 `FlowMind` 只作为 contract/truth authority，不在 Crazy 本地重写主治理状态
3. 将 `Loop Surface` 做成 `Collaboration` 子表面，而不是新一级 IA
4. 如继续扩 `Operations`，下一批只进入 `recovery path / env drift / backup coverage` 深化，而不是重新打开 Sprint 2 主边界

### 验收标准

- 任务流转不再只靠群聊口头 ACK
- 自动化晋升有明确证据、审批与回退规则
- 凭证、角色、记忆边界可在产品中被审计
- executor integration 不再只停留在设计文档，而进入 `Operations` 的正式能力面
- `Operations` 可作为 control room，而不只是对象列表页

## Workstream 4：Harness 机制迁移与产品化

### 目标

将 `FlowMindDeploy` 的完整 Harness 核心迁入 CrazyAgentsManage，并改写为适配 `Codex ↔ HermesAgent` 模型。

### 本次迁移范围

1. canonical harness docs
2. cross-review process
3. worktree bootstrap process
4. structured success / failure trace
5. harness critic
6. harness closeout writeback
7. worktree creation script

### 迁移任务

1. 补齐 `docs/02-engineering/harness/` 的通用机制文档
2. 补齐 `scripts/` 下的 Harness 记录、critic、closeout、worktree 脚本
3. 升级 `harness/README.md`
4. 保持现有 `Codex ↔ HermesAgent` 专用文档不被覆盖，而是成为通用 Harness 之上的协作适配层
5. 把 PRD closeout、runtime snapshot、Hermes handoff 与新 Harness 打通

### 验收标准

- 当前项目能写 success / failure trace
- 当前项目能运行 harness critic 并回写 memory
- 当前项目能通过脚本创建 agent worktree
- 当前项目的 HARNESS 入口文档清晰说明通用 Harness 与 Hermes 专用协作层的关系

## 五、阶段计划

### Phase A：计划与文档收敛

状态：进行中

产出：

- 母 PRD
- 技术 PRD
- 运营 PRD
- 页面级 PRD
- 路线图
- 总任务计划文档

### Phase B：Harness 机制完整迁入

状态：completed-published

产出：

- Harness 文档补齐
- success / failure / critic / closeout 脚本补齐
- worktree bootstrap 脚本补齐
- harness README 升级

当前已落最小 starter slice：

- `Operations > Harness`
  - 暴露 success / failure trace 计数
  - 暴露 closeout artifact 计数
  - 暴露 critic / closeout / worktree readiness
  - 暴露 harness runbooks 与默认命令链
  - 宿主 smoke 已产生 `S-20260524-001` + `C-20260524-001`
- non-trivial trace 默认不再允许 direct 调 `record-success.cjs` / `record-failure.cjs`
- canonical closeout 入口已收敛到 `harness-closeout-writeback.cjs`

当前这条线已完成 published closeout，后续不再属于“先把 Harness 补齐”，而是：

- 把 reviewer / Hermes acceptance / PRD closeout 进一步贴到同一条 evidence 链

### Phase C：Harness 与 Hermes 协作层对齐

状态：完成（fifth-slice landed）

产出：

- 通用 Harness 与 `Codex ↔ HermesAgent` 机制的清晰分层
- PRD / roadmap / runtime / handoff / closeout 的统一 closeout 流程

当前已落第一切片：

- `Collaboration Summary Aggregation`
  - `/api/collaboration/summary`
  - `open handoff / pending closeout / missing writeback / unreviewed artifact`
  - `Evidence Jumps`
- `TechArchitecturePreviewPage` 协作链投影
  - `/api/collaboration/graph-projection`
  - `Codex / HermesAgent / handoff / runtime snapshot / closeout / repo truth`

当前已落第二切片：

- `Unified Evidence Chain`
  - reviewer
  - Hermes acceptance
  - PRD closeout
- `/collaboration` 已显式给出
  - next actor
  - next action
  - repo-tracked evidence refs
- `/architecture/tech` 已把上述阶段继续投影为链路节点，而不是停留在第一版粗粒度节点

当前已落第三切片：

- `Action Playbooks`
  - 每个 degraded 协作阶段都带出 route / command / writeback path
  - `next hop` 不再只是裸链接，而是带 action context 的落地入口
- `Tasks` / `Operations` 已支持 context-aware landing
  - `Tasks` 可接 `action / focus / stage`
  - `Operations` 可接 `family / action / focus`
  - 页面打开后会直接显示对应协作处理上下文

当前已落第四切片：

- `Writeback Confirmation`
  - `reviewer-state / hermes-acceptance / prd-closeout` 三段 evidence chain 都会显式返回 `writebackConfirmation`
  - `/collaboration` 会直接显示 object-level artifact ready / missing 状态
  - operator 不再需要自己比对 handoff / snapshot / closeout / docs 路径

当前已落第五切片：

- `Acceptance Artifact`
  - `accept / reject / defer` 已有独立 repo-owned artifact
  - `Hermes Acceptance` 会优先消费 `harness/acceptance/*.json`
  - playbook 已给出 acceptance artifact 的 canonical writeback 命令

结论：

- reviewer / Hermes acceptance 已经通过 acceptance artifact 和 `writebackConfirmation` 完成收口
- 当前没有新的 FlowMind contract gap
- 如果未来再细化 handoff contract writeback，归类为增强项而非 Phase C 主线继续推进项

### Phase D：页面系统与状态源收敛

状态：进行中（state-source convergence complete，enhancement-only）

产出：

- 新 IA 导航全面替换旧导航
- 五大一级分区形成真实聚合页
- 架构页接入动态状态和跳转

当前切片：

- `Overview` 已切到 `overview/support-projection`，把 support signals 从散接口收口到单一投影
- `Runtime` 已切到 `runtime/summary`，把 overview dashboard 与 agent list 收口到单一投影
- `Operations` 已切到 `operations/support-projection`，把 summary 与 provider mode 收口到单一投影
- Phase D 的主问题不再是“是否切导航”，而是“是否把各分区的状态源收敛成稳定的 canonical projection”
- 第一优先级是把 `Overview` / `Operations` / `Runtime` 的聚合数据口径继续收紧，避免各页各自解释同一组事实
- 旧功能页保留兼容入口，但不再作为主产品叙事

下一步：

- 再评估是否需要补足更细粒度的页面级跳转与细分对象卡片
- 如果后续发现新的 contract gap，再回 FlowMind 补最小上游契约；否则当前 Phase D 只剩页面级增强项，不再是状态源收敛问题

## 六、关键依赖

### 上游依赖

- Hermes runtime 真实数据面
- FlowMind bridge 真实状态接口
- 当前仓库中的 runtime scripts

### 执行依赖

- `docs/` 与 `harness/` 必须持续作为 durable truth
- `.omx/` 只作为 runtime-local
- 非平凡迭代必须执行 closeout writeback

## 七、Closeout 规则

每次重要迭代结束至少要完成：

1. 更新相关 PRD
2. 更新路线图
3. 必要时更新本总任务计划
4. 写入 success / failure trace
5. 必要时运行 critic 并把反复失败模式回写到 harness memory
6. 如涉及 HermesAgent 评审，保留 handoff 与 closeout 证据

## 八、当前立即动作

1. 完成本总任务计划文档落库
2. 迁入 FlowMindDeploy 的 Harness 核心机制
3. 将迁入结果回写到 CrazyAgentsManage 的 Harness 入口文档
4. 输出“该机制如何在当前项目中落地”的能力映射说明
