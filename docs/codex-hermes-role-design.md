# CrazyAgentsManage 角色设计与协作分工

## 1. 结论

`CrazyAgentsManage` 不应再被定义为一个单纯的 `hermes-webui` demo，而应被定义为：

- 面向 **Hermes-Agent 运行体系** 的观测与运营控制台
- 面向 **FlowMind 插件联动状态** 的集成可视化层
- 面向未来 **专家 / 技能 / 工作流 / 定时任务 / 运营规范** 的运营底座

因此，后续项目应采用“双机器人分工”：

- `Codex`：开发负责人
- `HermesAgent`：运营负责人

两者不是平行开发关系，而是“开发实现 + 运营编排”的上下游关系。

## 2. 从现有 demo 提炼出的核心数据对象

根据当前 demo 文档和适配层实现，CrazyAgentsManage 已经围绕 Hermes-Agent 暴露出 5 类核心数据面：

### 2.1 会话运行面

来源：

- `state.db`

核心对象：

- `sessions`
- `messages`
- `parent_session_id` 形成的子会话树
- `tool_call_count`
- `input_tokens / output_tokens / reasoning_tokens`
- `billing_provider / cost_usd`

对应页面：

- 概览
- 监控仪表板
- 会话流水线
- Token 管理
- 任务编排

### 2.2 网关与接入面

来源：

- `gateway_state.json`
- 平台运行状态与日志

核心对象：

- Gateway 总状态
- 各平台连接状态
- 来源分布：`cli / cron / feishu / telegram / api_server`
- 告警事件

对应页面：

- 告警
- 监控仪表板
- 概览

### 2.3 技能与工具面

来源：

- `~/.hermes/skills/`
- `tools/registry`

核心对象：

- 技能目录
- `SKILL.md`
- 工具集与工具能力
- 角色可用工具集合

对应页面：

- 技能中心
- 智能体管理

### 2.4 团队记忆与角色面

来源：

- `~/.hermes/memories/`

核心对象：

- `MEMORY.md`
- `USER.md`
- 现阶段以 Hermes 既有记忆文件为主
- `teams/` / `shared-context/` 属于未来能力，不应假定当前环境已存在

对应页面：

- 团队记忆
- 概览

### 2.5 调度与运营面

来源：

- `cron/jobs.json`
- `cron/output/`
- Hermes 内置 Cron API（由 Hermes web server 暴露）

核心对象：

- Cron 任务定义
- 执行状态
- 调度规则
- 输出沉淀
- auto-deliver 结果分发

说明：

- `cron/jobs.json` 不存在时，优先判断为“当前环境未配置真实 cron job”，而不是“框架缺失 cron 能力”
- CrazyAgentsManage 后续应优先对接 Hermes 已有 Cron API，而不是自行重建一套 cron 状态机

对应页面：

- 定时任务
- 告警
- 概览

## 3. CrazyAgentsManage 下一阶段的产品定位

现有 demo 已经证明：Hermes-Agent 的只读观测层是可行的。

但新项目目标比 demo 更高，应该从“展示 Hermes”升级为“运营 Hermes + FlowMind 联动体系”。建议将产品边界收敛为 3 层：

### 3.1 L1 运行态可视化

回答“系统现在是否正常运行”：

- Hermes 会话是否健康
- Gateway 是否在线
- Cron 是否按预期执行
- Token 消耗是否异常

### 3.2 L2 运营对象管理

回答“我们运营的对象有哪些，状态如何”：

- 专家角色
- 技能
- 团队记忆
- 工作流
- 定时任务
- 平台接入

### 3.3 L3 FlowMind 联动治理

回答“Hermes 与 FlowMind 的结合是否产生了有效治理”：

- FlowMind 插件是否在线
- FlowMind 接收到哪些 Hermes 侧数据
- 哪些任务、会话、记忆、工作流已进入 FlowMind
- 联动链路是否健康
- 是否支持后续运营闭环

### 3.4 运行边界修正

根据最新的 HermesAgent 复核，需要明确区分三类对象：

1. `CrazyAgentsManage` 仓库本地协作工件

- `scripts/runtime/*`
- `.omx/`
- `harness/`
- `docs/02-engineering/harness/*`

这些属于项目仓库自身的协作协议与 runtime-local 辅助层，不属于 Hermes 自带全局框架目录。

2. Hermes 既有运行时能力

- `~/.hermes/memories/`
- `~/.hermes/cron/`
- Hermes web server 暴露的 Cron CRUD API
- `gateway_state.json`
- `state.db`

这些属于当前 Hermes 已有能力，CrazyAgentsManage 应优先对接，而不是重复实现。

3. 未来扩展能力

- `~/.hermes/teams/`
- `~/.hermes/shared-context/`

这些目前不应被视为“缺失”，而应被视为后续产品化能力。

## 4. `Codex` 与 `HermesAgent` 的职责边界

## 4.1 Codex：开发负责人

`Codex` 对代码与系统设计负责，职责固定为以下 6 类：

1. 负责 CrazyAgentsManage 的领域建模。
   目标是把 Hermes-Agent 和 FlowMind 的运行对象沉淀为稳定的数据模型、API 契约和页面结构。

2. 负责后端与前端实现。
   包括 API、页面、组件、聚合逻辑、缓存、搜索、状态流、错误处理、测试。

3. 负责联动集成设计。
   包括 Hermes 数据源读取、FlowMind 插件状态接入、跨系统字段映射、健康检查接口、告警口径，以及优先复用 Hermes 既有 API（尤其是 Cron API）而不是重复造轮子。

4. 负责开发期验证。
   包括本地验证、测试补齐、回归验证、部署前检查、问题定位和修复。

5. 负责工程规范。
   包括目录结构、代码边界、数据访问方式、文档沉淀、可维护性控制。

6. 负责将运营需求转成可交付的软件能力。
   `HermesAgent` 提出的运营需求，最终都应被转译为可执行的页面、接口、规则或配置机制。

`Codex` 不负责：

- 线上日常巡检
- 运营口径定义的长期维护
- 群内日常播报与跟进
- 定时任务的内容运营

## 4.2 HermesAgent：运营负责人

`HermesAgent` 不应承担代码实现责任，而应承担“运行体系运营”责任，职责固定为以下 6 类：

1. 负责运营视角的需求提出。
   明确“管理台上应该看什么、为什么看、运营人员如何处理”。

2. 负责线上运行信息组织。
   包括会话分类、专家角色口径、技能分类、团队视图、任务标签、告警规则建议。

3. 负责日常巡检与发现问题。
   包括：
   - 哪些任务失败了
   - 哪些技能缺失或失效
   - 哪些网关不在线
   - 哪些 FlowMind 联动链路异常

4. 负责运营动作执行。
   包括：
   - 发起巡检任务
   - 维护周期性报告
   - 整理团队记忆
   - 维护技能与专家的业务语义

5. 负责验收“是否满足运营使用”。
   `Codex` 实现页面后，`HermesAgent` 要从真实运营视角判定：
   - 信息是否够用
   - 是否易于发现异常
   - 是否能支持后续运营动作
   - 是否真正接上了 Hermes 已有运行时能力，而不是停留在 demo/mock

6. 负责把运营结论回流给开发。
   即把“线上观察到的问题”转成结构化的产品反馈，而不是直接给模糊意见。

`HermesAgent` 不负责：

- 架构方案拍板
- 代码实现
- 重构策略
- 测试设计与修复
- 发布工艺

## 5. 双方的协作接口

为了避免“运营需求直接打断开发”或“开发闭门造车”，建议约定固定交接物。

### 5.1 HermesAgent → Codex

HermesAgent 每次提需求时，输出以下结构：

- 场景：发生在什么运营场景
- 对象：涉及哪类对象
- 指标：想看到什么指标
- 动作：运营人员要采取什么动作
- 风险：如果看不到，会导致什么问题

推荐模板：

```md
## 运营需求
- 场景：
- 目标对象：
- 需要展示的字段：
- 需要支持的操作：
- 触发频率：
- 优先级：
- 验收标准：
```

### 5.2 Codex → HermesAgent

Codex 每次交付后，输出以下结构：

- 本次交付页面或接口
- 数据来源
- 已支持的操作
- 未覆盖的风险
- 需要 HermesAgent 验收的点

推荐模板：

```md
## 开发交付
- 功能：
- 页面/API：
- 数据源：
- 当前限制：
- 验收方式：
- 后续候选增强：
```

## 6. 建议采用的 RACI

| 事项 | Codex | HermesAgent |
|---|---|---|
| 数据模型设计 | R | C |
| 页面与 API 开发 | R | C |
| 运行态巡检 | C | R |
| 技能/专家分类口径 | C | R |
| 团队记忆内容治理 | C | R |
| 告警规则产品化 | R | C |
| 告警日常处理 | C | R |
| FlowMind 联动字段定义 | R | C |
| 发布验证 | R | C |
| 运营验收 | C | R |

说明：

- `R` = 直接负责
- `C` = 提供输入 / 参与评审

## 7. 第一阶段建议分工

建议第一阶段不要同时做“全能控制台”，而是先做 4 个运营最关键的面。

### 7.1 Codex 第一阶段开发范围

1. 补齐仓库级协作工件。
   先把 `scripts/runtime/*`、`harness/*`、`docs/02-engineering/harness/*` 变成真实可执行、可追踪的仓库事实，而不是只停留在文档描述。

2. 补 Hermes 运行态的真实信号。
   优先把 `Codex` / `HermesAgent` / `FlowMind link` 的存活、卡死、异常、Cron 逾期等信号显式暴露出来。

3. 对接 Hermes 既有 Cron API。
   不重建 Cron 基础设施，优先让 CrazyAgentsManage 的 Flask/API 层代理 Hermes 已有的 Cron CRUD 能力。

4. 做 session stuck 推断。
   第一阶段可以先在 CrazyAgentsManage 读模型层做“推断型 stuck 标记”，验证有效后再考虑回推 Hermes session schema。

5. 再推进统一领域模型和 FlowMind 联动页。
   等上面 4 项成立后，再稳定 `session / agent / skill / cron / gateway / flowmind_link` 的正式对象模型和页面结构。

### 7.2 HermesAgent 第一阶段运营范围

1. 给出专家体系清单。
   包括专家名称、职责、依赖技能、归属团队、运营标签。

2. 给出技能体系清单。
   包括技能分类、启用条件、关联场景、使用频率、风险等级。

3. 给出工作流清单。
   包括哪些工作流需要监控、哪些节点要展示、失败后如何处理。

4. 给出定时任务治理规则。
   包括哪些任务必须可见、哪些结果必须沉淀、哪些异常必须告警，并明确当前 Hermes 已有 Cron API 中哪些能力应优先被运营使用。

5. 给出 FlowMind 联动关注点。
   包括插件健康、数据同步、任务映射、状态一致性、回写需求。

6. 负责对现有能力做“不要重造轮子”的审查。
   当 Hermes 已有 API 或运行时能力可直接复用时，应优先指出，而不是把问题继续描述成“从零实现”。

## 8. 推荐工作机制

建议采用下面的节奏：

### 周期节奏

- `Codex`：按迭代开发，每轮交付一个清晰的页面或能力面
- `HermesAgent`：按日巡检与按周整理，持续提供运营输入

### 日常协作

1. HermesAgent 发现运营痛点，提交结构化需求。
2. Codex 把需求映射为页面/API/数据模型改动。
3. Codex 完成交付并标注验证路径。
4. HermesAgent 在线上环境按运营场景验收。
5. 双方把结论沉淀为规则或后续需求。

## 9. 当前阶段的最终建议

当前最合理的组织方式是：

- 你：产品 owner，决定 CrazyAgentsManage 的业务边界与优先级
- `Codex`：研发 owner，负责把系统做出来
- `HermesAgent`：运营 owner，负责定义“什么值得被管理、被监控、被沉淀”

一句话概括：

- `Codex` 负责“把系统做对”
- `HermesAgent` 负责“把系统用对”

如果后续继续推进，我建议下一步直接进入：

1. 先补齐仓库级协作工件与 runtime 脚本
2. 再对接 Hermes 既有 Cron API 与真实运行态信号
3. 然后做 session stuck 推断与派单入口
4. 最后再稳定统一领域模型与 FlowMind 联动页

## 10. 最终收敛结论

### 10.1 分类原则

以下结论严格区分两类对象：

- **A 类 — 仓库工件**：`CrazyAgentsManage` 仓库内应交付但尚未落地的脚本、配置、文档。属于 Codex 开发职责。
- **B 类 — 运行时对接**：Hermes-Agent 已有的运行时能力，CrazyAgentsManage 应对接但尚未对接的。属于双方协作。

不设"框架缺失"这一分类。Hermes-Agent 的既有运行时能力是事实存在，CrazyAgentsManage 未接入 ≠ Hermes 框架缺件。

### 10.2 Runtime Gap

| # | 差距 | 分类 | 说明 |
|---|------|------|------|
| R1 | `scripts/runtime/*` 未落地 | A | 仓库协作工件，属于 Codex 交付物 |
| R2 | `harness/*` / `.omx/*` 未落地 | A | 仓库协作工件，属于 Codex 交付物 |
| R3 | CrazyAgentsManage 未对接 Hermes Cron API | B | Hermes 已有 Cron CRUD API，CrazyAgentsManage 应代理而非重建 |
| R4 | Session stuck 无推断机制 | B | Hermes session schema 无 stuck 标记，CrazyAgentsManage 可先做读模型推断 |

### 10.3 Operations Gap

| # | 差距 | 分类 | 说明 |
|---|------|------|------|
| O1 | 无派单入口 | A | 仓库工件：运营动作无法通过 WebUI 触发 |
| O2 | 无真实运行态信号到达 WebUI | B | Gateway / Cron / Session 存活、卡死、逾期信号未暴露到页面 |
| O3 | 技能路径未统一 | B | `~/.hermes/skills/` vs `/opt/hermes-webui/skills/` 两套路径未归一 |

### 10.4 Missing Signal

| # | 信号 | 来源 | 当前状态 |
|---|------|------|---------|
| S1 | Gateway 在线状态 | `gateway_state.json` | 数据源已有，WebUI 未消费 |
| S2 | Cron 执行状态 | Hermes Cron API | API 已有，未对接 |
| S3 | Session stuck 标记 | `state.db` sessions | 需读模型推断，无原生标记 |
| S4 | FlowMind 插件健康 | FlowMind ingress API | 未接入 |

### 10.5 Missing Action

| # | 动作 | 触发条件 | 当前状态 |
|---|------|---------|---------|
| A1 | 运营巡检触发 | 定时 / 手动 | Cron API 可用但未配置真实巡检 job |
| A2 | 僵尸 session 处理 | stuck 标记命中 | 推断机制未实现 |
| A3 | 告警通知 | 异常信号触发 | 无告警规则与分发机制 |
| A4 | 派单 | 运营发现需修复的问题 | 无 WebUI 入口 |

### 10.6 Accept / Reject

| # | 判定 | 内容 | 理由 |
|---|------|------|------|
| ✅ | Accept | 角色分工方向：Codex = 开发, HermesAgent = 运营 | 上下游关系合理 |
| ✅ | Accept | P0 收敛为 4 项 blocker | 比之前的"框架缺失"描述更精确 |
| ✅ | Accept | `~/.hermes/memories/` 为正确路径 | `memory/` 是旧写法 |
| ✅ | Accept | Cron 未配置 ≠ 框架无 cron | 区分"能力"与"配置" |
| ✅ | Accept | `teams/` `shared-context/` 为未来能力 | 不应被视为现有环境缺件 |
| ❌ | Reject | 把仓库工件未落地描述为"框架缺失" | 混淆了 A 类和 B 类 |
| ❌ | Reject | 把 Cron 未对接描述为"Hermes 无 cron" | 事实错误，Hermes 已有 Cron API |
| ❌ | Reject | 混合描述仓库工件和运行时框架 | 必须严格分类 |
| ❌ | Reject | 把 `~/.hermes/teams/` / `~/.hermes/shared-context/` 当成当前环境 blocker | 归入"未来能力未引入"，不是当前缺件 |

### 10.7 Follow-up Requested from Codex

| # | 跟进项 | 优先级 | 分类 | 备注 |
|---|--------|--------|------|------|
| F1 | `scripts/runtime/*` 落地为可执行脚本 | P0 | A | |
| F2 | `harness/*` / `.omx/*` 落地为仓库级协作协议 | P0 | A | |
| F3 | 对接 Hermes Cron API（代理而非重建） | P0 | B | |
| F4 | 暴露真实运行态信号到 WebUI | P0 | B | |
| F5 | 实现 session stuck 读模型推断 | P1 | B | |
| F6 | 实现派单入口 | P1* | A | *P0 完成后立即再评估，若运营 lane 仍无法向开发 lane 交付结构化任务，则上提为 P0.5 |
| F7 | 统一技能路径 | P1 | B | 若技能中心已纳入主运营闭环则上提 |

### 10.8 优先级定稿

- **P0 = R1–R4**：打通最小运行态与 Cron 对接，消除先天阻断项
- **P1 = O1–O3 + F5–F7**：补齐运营闭环，F6 在 P0 完成后做再评估
- 不再为边界定义继续拉锯，后续发现新问题以增量方式追加
