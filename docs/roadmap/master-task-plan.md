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
- 已完成：统一旧模板顶部导航为新 IA 导航（ia-nav.html）
- 已完成：runtime/operations/governance/collaboration 从过渡壳层升级为真实聚合页
- 已完成：架构页节点到真实状态页和证据页的跳转
- 已完成：各聚合页数据汇总逻辑抽象为独立JS模块

### 后续任务

1. ~~统一旧模板顶部导航为新 IA 导航~~ ✅ 已完成
2. ~~将 `runtime.html`、`operations.html`、`governance.html`、`collaboration.html` 从过渡壳层升级为真实聚合页~~ ✅ 已完成
3. ~~建立架构页节点到真实状态页和证据页的跳转~~ ✅ 已完成
4. ~~将旧页面数据汇总逻辑抽象为可复用状态源~~ ✅ 已完成
5. 后续：Runtime信号进一步打通（stuck/zombie/failure inference）
6. 后续：Governance candidate/truth/review/drift 数据面接入
7. 后续：Collaboration handoff/closeout evidence 更深层可视化

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

状态：已完成

产出：

- 母 PRD
- 技术 PRD
- 运营 PRD
- 页面级 PRD
- 路线图
- 总任务计划文档

### Phase B：Harness 机制完整迁入

状态：已完成

产出：

- Harness 文档补齐
- success / failure / critic / closeout 脚本补齐
- worktree bootstrap 脚本补齐
- harness README 升级

### Phase C：Harness 与 Hermes 协作层对齐

状态：已完成

产出：

- 通用 Harness 与 `Codex ↔ HermesAgent` 机制的清晰分层
- PRD / roadmap / runtime / handoff / closeout 的统一 closeout 流程

### Phase D：页面系统与状态源收敛

状态：已完成（切片1-6）

产出：

- 新 IA 导航全面替换旧导航（18个模板已收敛到ia-nav.html）
- 五大一级分区形成真实聚合页（Overview/Runtime/Operations/Governance/Collaboration）
- 架构页接入动态状态和跳转
- 新增 /api/runtime/summary 聚合API端点
- 各聚合页具备独立CSS/JS和实时数据刷新能力

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
