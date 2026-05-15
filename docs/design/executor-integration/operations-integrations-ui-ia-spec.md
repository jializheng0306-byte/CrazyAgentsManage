# Crazy Operations × executor Integrations UI/IA Spec

## 文档目的

本文档将 `docs/design/crazy-executor-capability-analysis.md` 与 `docs/design/crazy-operations-executor-integration-plan.md` 进一步落到页面规格层，明确：

- `Operations` 页中与 executor 接入相关的对象族（object families）
- 左侧对象树如何组织
- 列表 / 详情 / 工作面的布局方式
- 每个最小工作面应展示什么
- 状态模型如何定义
- 分阶段实施时哪些先做、哪些后做

本文档不改变 Crazy 当前的产品身份和一级 IA，只定义 `Operations` 分区内部的 IA 扩展与交互模型。

---

# 1. 设计约束

## 1.1 不变的产品边界

以下边界继续冻结：

- `CrazyAgentsManage` 仍然是 **Hermes-hosted FlowMind operating product**
- 一级 IA 不变：
  - Overview
  - Runtime
  - Operations
  - Governance
  - Collaboration
- `executor` 不替代 Crazy 主产品壳
- `executor` 不接管 Runtime truth / Governance truth / Collaboration truth
- 当前路由兼容、BASE-safe、trace / handoff 契约保持不变

## 1.2 本文档只解决的范围

只定义：
- `Operations` 内的 integrations capability plane
- UI/IA 落点
- object model 到页面结构的映射

不定义：
- executor 接入的具体 API 代码
- 后端 schema 变更
- provider 细节实现

---

# 2. Operations 目标重构方向

## 2.1 当前问题

当前 `Operations` 主要围绕：
- Skills
- Cron
- Team Memory
- Alerts

但如果引入 executor 能力，仅靠现有对象族难以表达：
- 外部接入源（sources）
- source 对应的工具目录（tools）
- 凭证与 provider 状态
- 连接与协议层健康态

所以 `Operations` 需要从“传统运营对象页”扩展成：

> **运营对象 + 集成对象 + 外部能力目录的控制台**

## 2.2 目标定位

`Operations` 将被定义为：

> **Crazy 中所有“可配置、可接入、可调度、可执行”的 operator-facing 对象总台**

它负责承载：
- 内部运营对象（cron / alerts / memory / skills）
- 外部接入对象（sources / providers / tools / credentials）
- 将来 optional execution plane 的 operator 入口

---

# 3. 新增 object families

以下 object families 建议纳入 `Operations` 左侧对象树。

## 3.1 保留的现有对象族

### A. Cron Jobs
- 性质：primary work object
- 用途：调度与执行控制

### B. Alerts
- 性质：signal object
- 用途：异常、平台状态、待处理告警

### C. Skills
- 性质：capability object
- 用途：当前系统已安装/可用能力

### D. Team Memory
- 性质：knowledge object
- 用途：团队经验与操作知识回写

---

## 3.2 新增的 executor 对象族

### E. Integrations
- 性质：group root
- 用途：集成能力面总入口

### F. Sources
- 性质：primary integration object
- 用途：OpenAPI / GraphQL / MCP / Discovery 等接入源

### G. Tool Catalog
- 性质：capability detail object
- 用途：某个 source 暴露出的外部工具目录

### H. Credential Health
- 性质：support object
- 用途：secret / provider / credential 的绑定健康态

### I. Provider Health
- 性质：support object
- 用途：provider 层连通性、状态、接入完整度

---

# 4. 左侧导航 / 对象树定义

## 4.1 两层结构

### Level 1（固定）
- Operations

### Level 2（对象族）
建议在 `Operations` 下的对象树中组织为：

- Operations 概览
- Cron Jobs
- Alerts
- Skills
- Team Memory
- Integrations
  - Sources
  - Tool Catalog
  - Credential Health
  - Provider Health

---

## 4.2 树状分组建议

```text
Operations
├─ 运营对象
│  ├─ Cron Jobs
│  ├─ Alerts
│  ├─ Skills
│  └─ Team Memory
└─ 集成能力
   ├─ Sources
   ├─ Tool Catalog
   ├─ Credential Health
   └─ Provider Health
```

---

## 4.3 UI 行为要求

### 选中态
- 当前选中 object family 在左树高亮
- 对应中心工作区切换

### 分组头
- `运营对象`
- `集成能力`

### 搜索
搜索至少支持：
- source name
- tool name
- provider name
- credential status keyword

### chips
建议首批 chips：
- All
- External
- Internal
- Abnormal
- Credentials

---

# 5. 页面布局定义

`Operations` 主页面采用三栏工作台布局。

## 5.1 左栏：对象树 / object pool

用途：
- 选择 object family
- 选择具体对象
- 过滤 / 搜索 / 切换状态

内容：
- 分组树
- 搜索框
- chips
- 当前对象列表

---

## 5.2 中栏：主工作区 / main workspace

用途：
- 展示当前选中 object family 的主要工作面
- 列表 + 主要详情

根据 object family 切换不同主工作区：

### Cron Jobs
- 列表
- 调度状态
- 最近执行
- 下次执行
- 输出摘要

### Alerts
- 待处理告警列表
- 严重程度
- 来源
- 当前状态

### Skills
- 技能列表
- 分类
- 可用性
- 描述

### Team Memory
- 团队 / 文件列表
- 最近更新
- 内容摘要

### Sources
- source 列表
- source 类型
- 状态
- tool 数量
- scope

### Tool Catalog
- 当前 source 对应的工具列表
- tool schema 摘要
- required auth
- invoke availability

### Credential Health
- provider / source 的 credential 状态
- missing / expired / healthy

### Provider Health
- provider reachable / degraded / failed
- source count / tool count

---

## 5.3 右栏：detail / context rail

用途：
- 当前对象详情
- 证据
- next actions
- 关联对象

根据 object family 变化：

### Cron Job detail
- schedule
- last run
- next run
- deliver
- output count

### Alert detail
- source
- level
- message
- platform state

### Skill detail
- category
- description
- config presence

### Memory file detail
- team/source
- file path
- size
- preview

### Source detail
- source name
- source type
- scope
- health
- tool count

### Tool detail
- tool name
- source
- schema summary
- auth dependency

### Credential detail
- provider type
- binding state
- affected sources

### Provider detail
- provider state
- failing sources
- auth issues

---

# 6. 每个最小工作面定义

## 6.1 Source Work Surface

### Header
- Source name
- Source type
- Scope
- Status

### Main section
- tool count
- provider binding
- description / summary

### Right rail
- credentials
- last sync / health
- next actions

---

## 6.2 Tool Catalog Work Surface

### Header
- Source name
- tool count

### Main section
- tools table/list
- per-tool summary
- schema preview

### Right rail
- selected tool detail
- auth dependency
- source linkage

---

## 6.3 Credential Health Work Surface

### Header
- provider
- status summary

### Main section
- list of missing / expired / valid credentials
- affected sources

### Right rail
- selected binding
- provider detail
- remediation hints

---

## 6.4 Provider Health Work Surface

### Header
- provider cluster
- health summary

### Main section
- provider cards
- state counts
- source coverage

### Right rail
- failing provider detail
- source impact

---

# 7. 状态模型

## 7.1 Source 状态
- healthy
- degraded
- missing-auth
- disabled
- failed

## 7.2 Tool 状态
- available
- auth-required
- disabled
- invalid-schema

## 7.3 Credential 状态
- healthy
- missing
- expired
- invalid

## 7.4 Provider 状态
- reachable
- degraded
- failed
- unknown

## 7.5 UI 表达约定
- green = healthy / available
- amber = degraded / requires attention
- red = failed / invalid / missing auth
- slate = unknown / inactive

---

# 8. 路由与页面落点建议

这一阶段**不要求**先新增大量独立路由。

## 8.1 第一阶段优先策略
建议先在现有 `Operations` 主页面中通过：
- 左树切换
- 中栏主工作区切换
- 右栏 detail 切换
来承载这些对象族

## 8.2 如需后续拆路由
建议后续再扩展为：
- `/operations/integrations`
- `/operations/sources`
- `/operations/tools`
- `/operations/credentials`
- `/operations/providers`

但这不是第一阶段的前提。

---

# 9. 分阶段实施建议

## Phase 1：只读接入
先展示：
- source list
- tool list
- credential status
- provider health

不做写操作。

## Phase 2：受控写入
再支持：
- source import
- connection create/update
- credential bind/update

## Phase 3：execution plane（可选）
只有在需要 external-tool orchestration 时，再引入 execution engine。

---

# 10. 第一阶段验收标准

## IA
- `Operations` 左树里出现新增 object families
- 不破坏现有 Skills / Cron / Memory / Alerts

## UI
- 主工作区能在 object family 间切换
- detail rail 能展示选中对象的细节
- 弱态 / 空态清晰

## 技术
- 不改 Crazy 主产品身份
- 不引入新的真相源冲突
- 不接管 Runtime / Governance / Collaboration 主模型

---

# 11. 推荐的下一步

如果要继续进入更细的实施前设计，建议下一份文档为：

## `Crazy Operations Integrations API/Boundary Spec`

重点定义：
- Crazy 与 executor 的边界 API
- 数据由谁持有
- Crazy UI 显示哪些投影字段
- source/tool/credential/provider 查询接口如何桥接

这样可以把当前这份 UI/IA Spec 进一步推进到真正可开发的接口规格。