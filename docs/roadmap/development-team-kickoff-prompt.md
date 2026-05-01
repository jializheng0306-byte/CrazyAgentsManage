# CrazyAgentsManage 开发团队启动提示词

## 使用方式

把下面整段提示词直接发给将要进入本项目开发的团队或开发 Agent。

这份提示词的目标不是让团队“自由发挥”，而是让他们在当前已经完成的产品定义、PRD、路线图和 Harness 机制之上，开始规范化开发。

---

## 提示词正文

你现在进入的是 `CrazyAgentsManage` 项目。

你的任务不是重新定义产品，也不是从零做方案，而是基于当前仓库里已经确认的产品定位、信息架构、PRD、路线图和 Harness 机制，开始实际开发工作，并把每一轮迭代的结果沉淀为可验证、可审阅、可 closeout 的仓库事实。

## 一、先理解你的工作边界

你要开发的不是一个通用 Agent playground，也不是一个随意扩展的多智能体 demo。

当前项目的唯一主定位已经确定为：

`一个以 HermesAgent 为宿主的 FlowMind 运营产品`

这意味着：

- `HermesAgent` 是运行时宿主与运营执行面
- `FlowMind` 是治理引擎与 canonical truth 层
- `CrazyAgentsManage` 是产品层，负责让运行态可见、让运营对象可管理、让治理闭环可执行

你不需要重新讨论这件事。你需要在这个基础上开发。

## 二、你必须先按顺序阅读这些材料

在开始任何设计、编码、拆任务之前，按下面顺序阅读。

### A. 仓库与 Harness 入口

1. `AGENTS.md`
2. `docs/02-engineering/harness/HARNESS-ENTRY.md`
3. `docs/02-engineering/harness/HAGENT-WORKFLOW.md`
4. `docs/02-engineering/harness/CROSS-REVIEW-PROCESS.md`
5. `docs/02-engineering/harness/WORKTREE-BOOTSTRAP.md`
6. `docs/02-engineering/harness/HARNESS-CAPABILITY-MAPPING.md`

阅读目的：

- 理解仓库级执行纪律
- 理解 worktree、closeout、critic、trace 的使用方式
- 理解什么是 `.omx/`，什么是 `docs/` / `harness/`

### B. CrazyAgentsManage 专用协作机制

7. `docs/02-engineering/harness/CODEX-HERMES-WORKFLOW.md`
8. `docs/02-engineering/harness/CODEX-HERMES-COLLABORATION-MECHANISM.md`
9. `docs/02-engineering/harness/HERMESAGENT-ENTRY.md`
10. `docs/codex-hermes-role-design.md`
11. `docs/02-engineering/harness/PRD-DOCUMENT-GOVERNANCE.md`

阅读目的：

- 理解 `Codex ↔ HermesAgent` 的职责边界
- 理解 HermesAgent 是运营验收 lane，不是第二开发 lane
- 理解 PRD / roadmap 的强制更新规则

### C. 产品与 PRD 母文档

12. `docs/prd/hermesagent-hosted-flowmind-product-foundation.md`
13. `docs/prd/technical-implementation-prd.md`
14. `docs/prd/operations-implementation-prd.md`
15. `docs/roadmap/prd-execution-roadmap.md`
16. `docs/roadmap/master-task-plan.md`

阅读目的：

- 理解产品主定位
- 理解五个一级信息架构
- 理解技术 lane 和 operations lane 的边界
- 理解当前总任务计划与阶段排序

### D. 页面级与子 PRD

17. `docs/prd/runtime-observability-implementation-prd.md`
18. `docs/prd/governance-surface-implementation-prd.md`
19. `docs/prd/operations-surface-implementation-prd.md`
20. `docs/prd/collaboration-workflow-implementation-prd.md`
21. `docs/prd/governance-operator-workflow-prd.md`
22. `docs/prd/collaboration-operator-workflow-prd.md`
23. `docs/prd/pages/overview-page-prd.md`
24. `docs/prd/pages/runtime-page-prd.md`
25. `docs/prd/pages/governance-page-prd.md`
26. `docs/prd/pages/operations-page-prd.md`
27. `docs/prd/pages/collaboration-page-prd.md`
28. `docs/prd/pages/architecture-visualization-pages-prd.md`
29. `docs/prd/pages/webui-route-template-alignment.md`

阅读目的：

- 理解每个分区应该承载什么
- 理解当前 WebUI 已经做了哪些 IA 接入
- 理解哪些地方仍然是“过渡壳层”

### E. 代码现实基线

30. `src/webui/app.py`
31. `src/webui/templates/`
32. `src/ProductPhilosophyPreviewPage.tsx`
33. `src/ProductArchitecturePreviewPage.tsx`
34. `src/TechArchitecturePreviewPage.tsx`

阅读目的：

- 判断文档定义和当前代码现实之间的差距
- 不要假设三张架构页已经完整落地

## 三、你必须遵守的核心原则

### 1. 不重开顶层产品定位

不要再把项目表述为：

- 通用多智能体协作平台
- Hermes demo shell
- 任意 Agent playground

统一以母文档为准。

### 2. 不把 `.omx/` 当成仓库事实

`.omx/` 只能作为 runtime-local 会话状态。

持久事实必须写入：

- `docs/`
- `harness/`
- 受追踪源码 / 配置 / 模板

### 3. 不假设 HermesAgent 是第二开发团队

HermesAgent 的职责是：

- 运营 framing
- runtime / operator 视角复核
- acceptance

不是：

- 常规编码实施
- 替代验证
- 绕过 PRD 直接定产品结构

### 4. 不假设架构展示页已经完整实现

当前三张架构页已经进入 PRD 和 IA，但仓库里看到的是预览入口，不是完整产品实现。

你需要：

- 基于现有真实代码推进
- 不虚构不存在的组件和状态源

### 5. 所有开发都必须回链到 PRD 与路线图

任何新增工作都要回答：

- 它属于哪个一级 IA？
- 它对应哪份 PRD？
- 它属于 technical lane 还是 operations lane？
- 它处于 roadmap 哪个 phase？

## 四、开始开发前，你先做这四件事

### 第一步：判断你要做的是哪个 Workstream

从 `docs/roadmap/master-task-plan.md` 中定位你属于哪一条主线：

- Workstream 1：产品定义与 PRD 收敛
- Workstream 2：IA 与 WebUI 收敛
- Workstream 3：Runtime / Operations / Governance / Collaboration 实施
- Workstream 4：Harness 机制迁移与产品化

### 第二步：确定你的任务归属

写清楚：

- 一级 IA：`Overview` / `Runtime` / `Operations` / `Governance` / `Collaboration`
- 文档归属：对应 PRD / 页面 PRD / 路线图章节
- 风险级别：L1 / L2 / L3 / L4

### 第三步：决定是否需要独立 worktree

如果是：

- 多文件改动
- PRD + 代码联动改动
- Harness 改动
- 路由 / 页面结构改动
- 架构页接入改动

优先使用独立 worktree。

参考：

- `docs/02-engineering/harness/WORKTREE-BOOTSTRAP.md`
- `scripts/worktree/create-agent-worktree.sh`

### 第四步：如果任务非平凡，先写执行计划

执行计划放在：

- `harness/exec-plans/`

至少写清楚：

- 背景
- 目标
- 范围
- 非目标
- 受影响文件
- 验证方式
- closeout 需要更新的文档

## 五、开发团队的标准执行流程

请严格使用下面流程推进，而不是边想边散改。

### 1. 读文档并确认任务边界

输出：

- 本次任务属于哪个 IA
- 对应哪份 PRD
- 本次不做什么

### 2. 检查代码现实

输出：

- 当前已有实现
- 当前缺口
- 计划如何复用现有代码，而不是重造一层

### 3. 形成最小实现切片

每轮开发优先做小而完整的切片，例如：

- 一条路由收敛
- 一个 IA 分区聚合页
- 一个 runtime state adapter
- 一个 operator action 接真实能力
- 一个 handoff / closeout 证据表面

不要一次同时改很多概念层。

### 4. 实施前明确验证标准

必须预先写清楚：

- 代码验证怎么做
- 页面验证怎么做
- 文档验证怎么做
- closeout 时需要更新哪些文件

### 5. 实施

实施原则：

- 优先复用现有模式
- 不扩散无关重构
- 不在本轮引入不必要抽象
- 保持旧入口兼容，除非 PRD 明确要求切断

### 6. 交叉审查或运营复核

如果任务是 L3/L4，或者涉及以下内容，必须加 review：

- Harness 机制
- PRD / roadmap
- 一级 IA 改动
- 架构展示页接入
- operator action
- governance / collaboration 规则

参考：

- `docs/02-engineering/harness/CROSS-REVIEW-PROCESS.md`

### 7. Closeout

完成后必须：

1. 更新相关 PRD
2. 更新路线图
3. 必要时更新 `master-task-plan.md`
4. 写入 Harness success / failure trace
5. 如有重复失败模式，运行 critic 并考虑回写 memory

## 六、开发团队必须使用的进度管理方式

不要只汇报“做完了多少文件”。

请按下面格式管理进度：

### 进度视角一：按 IA

- `Overview`：完成了什么 / 还缺什么
- `Runtime`：完成了什么 / 还缺什么
- `Operations`：完成了什么 / 还缺什么
- `Governance`：完成了什么 / 还缺什么
- `Collaboration`：完成了什么 / 还缺什么

### 进度视角二：按 Phase

以 `docs/roadmap/prd-execution-roadmap.md` 为准：

- Phase 1：Runtime / Substrate Readiness
- Phase 2：Operator Surface Readiness
- Phase 3：Governance / FlowMind Readiness
- Phase 4：Collaboration Productization
- Phase 5：Page-System Convergence

每次汇报要说明本轮工作推进了哪个 Phase。

### 进度视角三：按交付物

每次汇报至少列出：

- 变更文件
- 对应 PRD
- 对应 IA
- 对应验证
- 是否已 closeout

## 七、你在当前项目里最值得优先做的开发方向

如果没有额外指定任务，优先级顺序按下面执行：

### P0

1. 把旧 WebUI 导航统一收敛到新的一级 IA
2. 把 `runtime` / `operations` / `governance` / `collaboration` 从过渡壳层做成真实聚合页
3. 打通 runtime 信号到 IA 页面和架构展示页的共享状态源
4. 让 collaboration 表面能看到 handoff / closeout / evidence

### P1

5. 接入更真实的 operator actions
6. 完成 governance candidate / truth / review / feedback 的显式表达
7. 让架构页支持状态与跳转，而不是静态占位页

### P2

8. 持续完善 Harness 的实际使用率
9. 把每轮非平凡迭代都纳入 success / failure / critic / closeout 流程

## 八、你必须产出的交付物

每轮非平凡开发至少产出：

1. 代码改动
2. 对应文档更新
3. 验证结果
4. Harness closeout 记录

如果任务涉及 HermesAgent 运营复核，还必须产出：

5. runtime state snapshot
6. Hermes handoff packet
7. closeout evidence

## 九、你的汇报格式

每次向负责人汇报时，使用下面结构：

### 1. 本轮任务

- 任务名称
- 所属 IA
- 所属 PRD
- 所属 Phase

### 2. 已完成

- 做了哪些实现
- 更新了哪些文档
- 处理了哪些风险

### 3. 验证

- 运行了哪些验证
- 结果如何
- 还有哪些未验证项

### 4. Closeout

- 是否已写 success / failure trace
- 是否已更新 roadmap / PRD
- 是否需要 HermesAgent 做运营复核

### 5. 下一步

- 下一轮最小切片是什么

## 十、最后的执行要求

请把自己当成“在既定产品体系上推进实施”的团队，不要把自己当成“重新发明这个项目的人”。

优先做：

- 对齐
- 收敛
- 落地
- 验证
- 回写

不要优先做：

- 重开顶层定义
- 额外扩张产品边界
- 虚构不存在的系统能力
- 跳过文档直接编码
- 跳过 closeout 直接宣称完成

当你完成一轮工作时，以仓库事实证明完成，而不是以口头说明证明完成。

---

## 给负责人使用的建议

如果你要把这份提示词交给不同团队，建议在最前面再补一段任务指令：

```md
请基于 `docs/roadmap/master-task-plan.md` 和本提示词，先输出：

1. 你负责的 IA 分区
2. 你负责的最小实施切片
3. 你计划阅读的文件清单
4. 你预计更新的代码与文档
5. 你的验证方案

在这 5 项输出完成前，不要开始编码。
```
