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

### 5. Executor Integrations

内容：

- Sources
- Tool Catalog
- Credential Health
- Provider Health
- readonly capability / delegation boundary

## 页面信息架构

建议页面结构自上而下为：

1. roles / skills 区
2. cron / routines 区
3. team memory / shared context 区
4. platform connectivity 区
5. executor integrations 区

## 页面模块树

- OperationsPage
  - RolesSkillsPanel
  - CronRoutinesPanel
  - TeamMemoryPanel
  - SharedContextPanel
  - PlatformConnectivityPanel
  - SourcesPanel
  - ToolCatalogPanel
  - CredentialHealthPanel
  - ProviderHealthPanel

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
3. 页面可作为 `ProductArchitecturePreviewPage` 的 operations 详情依托
