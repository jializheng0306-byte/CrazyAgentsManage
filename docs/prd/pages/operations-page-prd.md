# CrazyAgentsManage Operations 页面 PRD

## 版本信息

| 字段 | 值 |
|------|-------|
| 产品 | CrazyAgentsManage |
| 文档类型 | 页面级 PRD / Operations |
| 版本 | v0.1.0 |
| 状态 | Draft |
| Owner | Codex |
| 最后更新 | 2026-04-27 |

## 页面目标

`Operations` 页面负责让用户管理支撑系统日常运转的运营对象。

它要回答：

- 当前有哪些 roles / skills / jobs / memory / connectivity 对象
- 当前有哪些 executor sources / tools / credentials / providers
- 哪些对象缺失配置
- 哪些对象异常
- 哪些对象可继续操作

当前实现还额外承担一层 page-level aggregation shell：

- briefing
- summary grid
- next hop
- subpage framing

因此 `Operations` 不只是对象列表，而是 Crazy control room 的第一块聚合页壳。

## 继承关系

本文档继承：

- `docs/prd/operations-surface-implementation-prd.md`
- `docs/prd/operations-implementation-prd.md`

## 页面应承载的核心信息

### 1. Roles / Skills

内容：

- 角色资源
- skill inventory
- 缺失 / 失效 / 正常状态

### 2. Cron / Routines

内容：

- job 列表
- 运行状态
- next run / last run

### 3. Team Memory / Shared Context

内容：

- 团队级 memory
- 角色级 memory
- shared context 摘要

### 4. Platform Connectivity

内容：

- Hermes、FlowMind、外部平台、输入端连接状态
- 在线 / 异常 / 未配置区分

### 5. Task Registry / Automation Maturity

内容：

- task registry
- bus lanes
- automation promotion state
- evidence / approval / rollback visibility

### 6. Executor Integrations

内容：

- Sources
- Tool Catalog
- Credential Health
- Provider Health
- readonly capability / delegation boundary

### 7. Role / Credential / Memory Isolation

内容：

- role registry
- credential ownership
- memory boundaries
- runbook visibility

### 8. Host Health / Runbooks

内容：

- disk / memory / gateway / alert evidence
- linked runbooks
- next-hop operator guides

### 9. Harness Readiness

内容：

- success / failure trace
- closeout artifacts
- critic readiness
- closeout writeback readiness
- worktree bootstrap readiness
- non-trivial round canonical closeout entry
- pending closeout detection

### 10. Env Map / Backup / Recovery / Recovery Paths

内容：

- deploy shell / runtime root / Hermes home / provider mode
- executor / FlowMind base URLs
- backup coverage
- mirror / deploy backup / recovery path visibility

### 11. Summary Shell / Next Hop

内容：

- briefing
- summary grid
- next hop
- subpage cards

目标：

- 让 `Operations` 先给出 operator 该从哪个对象族继续巡检，而不是一打开就直接落入细节列表

## 页面信息架构

建议页面结构自上而下为：

1. roles / skills 区
2. cron / routines 区
3. team memory / shared context 区
4. platform connectivity 区
5. task registry / automation maturity 区
6. executor integrations 区
7. role / credential / memory isolation 区
8. host health / runbooks 区
9. harness readiness 区
10. env map / backup / recovery 区
11. summary shell / next hop 区

## 页面模块树

- OperationsPage
  - RolesSkillsPanel
  - CronRoutinesPanel
  - TeamMemoryPanel
  - SharedContextPanel
  - PlatformConnectivityPanel
  - TaskRegistryPanel
  - AutomationMaturityPanel
  - SourcesPanel
  - ToolCatalogPanel
  - CredentialHealthPanel
  - ProviderHealthPanel
  - IsolationPanel
  - HostHealthPanel
  - RunbooksPanel
  - HarnessPanel
  - EnvMapPanel
  - BackupRecoveryPanel
  - SummaryBriefingPanel
  - NextHopPanel

## 关键交互

- 从 skills 异常跳转到阻断链路
- 从 cron 异常跳转到 runtime 或 alerts
- 从 connectivity 节点跳转到架构展示页
- 从 provider / credential 异常跳转到 `Operations > Integrations`
- 从 readonly capability 节点跳转到 delegation boundary / runbook

## 依赖来源

- roles / skills inventory surface
- cron / routine surface
- team memory / shared context surface
- platform connectivity surface
- executor / integrations capability surface

## 非目标

本文档不定义：

- 对象详情字段级布局
- 配置表单设计细节
- API 协议

## 完成标准

1. 页面不再只是资源罗列，而能表达运营健康度
2. 外部连接和内部运维对象有统一状态口径
3. 页面具备 page-level aggregation shell，而不是只剩对象列表
4. 页面可作为 `ProductArchitecturePreviewPage` 的 operations 详情依托
