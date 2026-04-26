# CrazyAgentsManage 技术实现 PRD

## 版本信息

| 字段 | 内容 |
|------|------|
| 产品 | CrazyAgentsManage |
| 文档类型 | 技术实现 PRD |
| 版本 | v0.1.0 |
| 状态 | 当前主基线 |
| 负责人 | Codex |
| 运营复核方 | HermesAgent |
| 最后更新 | 2026-04-26 |

## 范围

本 PRD 定义的是：为了把 `CrazyAgentsManage` 做成真正可用的 Hermes 侧运营控制台，当前需要推进的工程实现工作。

覆盖内容包括：

- 运行时数据接入
- API 与适配层
- 前后端实现范围
- 技术验收标准
- 分阶段实施顺序

它不负责细化运营策略，运营策略单独由以下文档定义：

- `docs/prd/operations-implementation-prd.md`

## 产品边界

### 当前已接受的边界

- `CrazyAgentsManage` 是 Hermes 运行时 / 运营控制台
- `FlowMind` 是治理引擎与 canonical truth 层
- `CrazyAgentsManage` 可以展示、转发、运营化 FlowMind 相关状态
- `CrazyAgentsManage` 不应擅自重定义 FlowMind 语义

### 技术上的含义

实现时必须把以下三条缝保持清晰：

1. Hermes 运行时与 session substrate
2. CrazyAgentsManage 运营控制台与适配层
3. FlowMind 治理与 truth 接口

## 当前技术基线

### 已存在的运行时事实

- Hermes 运行时数据源已存在且可读取：
  - `state.db`
  - `gateway_state.json`
  - `~/.hermes/skills/`
  - `~/.hermes/memories/`
  - cron / 运行进程状态
- CrazyAgentsManage 已有一套 WebUI/API 观测层 demo
- `Codex / HermesAgent` 分工已经定稿，实施阶段不应重辩角色边界

### 当前仍成立的技术缺口

- session stuck / zombie inference 还需要更可靠的技术处理
- 运行时信号仍需标准化后才能真正给运营使用
- 部分控制面仍是 mock 或不完整
- FlowMind 侧接口必须对齐真实 bridge contract，而不是想象中的 API

## 实施域

### 1. 运行时状态适配层

需要构建并加固的读取适配层包括：

- session 状态
- message / token 统计
- task / delegation lineage
- skills inventory
- cron job 状态
- alerts 与异常指示器

验收标准：

- 适配层能容忍缺失/部分存在的运行时文件
- 适配层能区分“未配置”与“已损坏”
- 输出能够标准化给前端消费

### 2. 任务 / 委派 substrate

需要实现或补完的能力包括：

- 角色化委派
- shared context / task state 文件
- task graph lineage
- 跨 session 的任务跟踪

验收标准：

- 委派任务会留下持久状态工件
- 父子 lineage 可查询、可渲染
- 失败状态不能靠“沉默推断”，必须有显式状态

### 3. Team / Memory substrate

需要实现仓库侧的以下部分：

- team memory
- shared context 目录结构
- role memory 加载
- 迭代后的 memory writeback

验收标准：

- team / shared-context 结构可预测创建
- 读写边界明确
- 记忆更新可追溯、可审阅

### 4. 运行时控制面

需要实现真实可操作的控制面：

- cron 可视化与操作
- session 检查
- task dispatch entry
- bridge 状态检查
- runtime alert acknowledgement

验收标准：

- UI 暴露的每个控制，都必须对应真实动作，或明确说明其当前不可执行
- mock endpoint 要么替换，要么清晰标注

### 5. 可观测性 UI

需要实现的运营 UI 包括：

- sessions
- task graph / lineage
- runtime health
- skills inventory
- cron surfaces
- token/cost 可见性
- alerts 与异常

验收标准：

- 无需 shell 访问即可看懂主要运行状态
- 异常状态具备根因 breadcrumbs
- 高频页面在大数据量下仍可用

## FlowMind 集成契约

CrazyAgentsManage 必须对齐 `FlowMindDeploy` 里已经存在的真实 FlowMind-facing 接口。

### 当前 bridge 对齐面

- candidate ingress
- truth query
- context compilation
- truth change feedback

### 规则

除非明确标记为“提案”，否则技术规划里不得新造 API 名称替代已实现 bridge surface。

## 非目标

本技术 PRD 不授权以下行为：

- 重定义 FlowMind 产品语义
- 把 Hermes 当成 canonical truth 的来源
- 把 HermesAgent 拉回第二开发 lane
- 只靠聊天做架构决策而不落仓库工件

## 技术验收门槛

### P0

- runtime state adapter 可靠
- 真实 runtime 信号已暴露
- session/task 异常可识别
- 关键运营控制面不再停留在 mock

### P1

- task dispatch entry 可用
- skill 扫描一致
- memory/team substrate 可工作
- 关键页面具备运营可导航性

### P2

- 更高级的自动化与优化层
- 长尾 dashboard
- 次级集成与便利性能力

## 变更控制

当任务改变了技术范围时，必须同步更新：

1. 本技术 PRD
2. `docs/roadmap/prd-execution-roadmap.md`
3. 如果角色协作状态发生变化，还要更新 harness closeout 工件
