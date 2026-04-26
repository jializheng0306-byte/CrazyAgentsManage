# CrazyAgentsManage 运营实现 PRD

## 版本信息

| 字段 | 内容 |
|------|------|
| 产品 | CrazyAgentsManage |
| 文档类型 | 运营实现 PRD |
| 版本 | v0.1.0 |
| 状态 | 当前主基线 |
| 文档管理者 | Codex |
| 运营复核方 | HermesAgent |
| 最后更新 | 2026-04-26 |

## 范围

本 PRD 定义的是：为了让 Hermes 侧运营真正可用，系统必须向运营者暴露什么、支持什么、以及怎样才算达到运营可接受状态。

覆盖内容包括：

- 运营角色视角
- 必须可见的运行时对象
- 运营工作流
- 告警、报告、动作入口
- 运营验收标准

它不负责后端实现细节，后端与前端实现细节由以下文档定义：

- `docs/prd/technical-implementation-prd.md`

## 运营基线

### 已接受的角色模型

- `HermesAgent` 是运营 lane
- `Codex` 是开发 lane
- 运营工作应输出结构化反馈，而不是直接重写架构方案

### 运营最核心的 5 个问题

运营者必须能快速回答：

1. 现在什么在运行？
2. 什么卡住了？
3. 什么失败了？
4. 哪里需要介入？
5. 哪些 FlowMind 关联状态正在漂移？

## 运营必须可见的运行时对象

控制台至少要显式展示：

- sessions
- delegated tasks / child runs
- skills
- cron jobs
- runtime alerts
- gateway / platform connection state
- FlowMind bridge state
- token / cost usage

## 必需的运营视图

### 1. Session 视图

运营者需要看到：

- active / completed / suspect sessions
- 父子任务 lineage
- message / tool / token 摘要
- stuck 指示器

### 2. Task / Delegation 视图

运营者需要看到：

- pending / running / done / failed 状态
- 依赖关系
- 子智能体归属
- 下一步可操作入口

### 3. Skills 视图

运营者需要看到：

- 已安装 skills
- 缺失 / 失效 skills
- 角色 / 领域分组
- 哪些 skill 故障会阻断真实工作

### 4. Cron 视图

运营者需要看到：

- 已配置任务
- 上次运行 / 下次运行
- 成功 / 失败状态
- pause / resume / trigger 入口（前提是真有后端能力）

### 5. Alerts 视图

运营者需要看到：

- 明确异常记录
- 严重级别
- 受影响运行时对象
- 建议下一步动作

## 必需的运营动作

系统最终必须支持以下结构化动作：

- 确认告警
- 打开受影响对象
- 发起或重新发起任务
- 检查 session / task 证据
- 触发 review 例行流程
- 在有真实后端支持时操作 cron job

如果某个动作当前还不存在，UI 不得假装它存在。

## FlowMind 侧运营需求

从运营视角，CrazyAgentsManage 必须清楚区分：

- Hermes 运行时真相
- FlowMind 治理真相
- 尚未确认的 candidate 状态

### 对 FlowMind 关联状态的运营要求

- candidate 状态必须与 canonical truth 区分开
- review / feedback 闭环必须可见
- drift 或 blockage 必须以运营问题的形式暴露，而不是藏在日志里

## 报告需求

运营侧需要固定输出，例如：

- 每日运行摘要
- 每周运营审计
- pending / stuck review 清单
- failed task / failed cron 汇总

这些报告可以从半自动开始，但在 PRD 层必须被视为显式产品要求。

## 运营验收门槛

### P0

- 运营者无需 shell 访问即可判断 runtime 健康
- stuck / failed 状态清晰可见
- FlowMind 关联状态不会被误标成 canonical truth
- 关键运营视图不再是 mock-only

### P1

- 运营者能执行基本的结构化后续动作
- 报告与 review 流程稳定
- skill / cron / session 表面互相关联

### P2

- 更丰富的自动化
- 预测式告警
- 治理辅助与优化闭环

## 非目标

本运营 PRD 不授权：

- 让 HermesAgent 直接承担代码实现责任
- 用聊天结论替代仓库真相
- 把任何未来能力都误写成当前运行时承诺

## 变更控制

当某轮迭代改变了运营语义时，必须同步更新：

1. 本运营 PRD
2. `docs/roadmap/prd-execution-roadmap.md`
3. 若协作状态变化，再更新对应 harness closeout 记录
