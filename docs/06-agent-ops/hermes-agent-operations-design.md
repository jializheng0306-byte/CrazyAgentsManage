# 基于 OpenClaw 实战文章的 HermesAgent 运营体系设计

> **文档版本**: v2.0  
> **创建日期**: 2026-04-26  
> **修订日期**: 2026-04-26（按 Codex CLI 4 点评审意见修订）  
> **状态**: 第二稿，待 Codex CLI 复核  
> **参考文章**: 《OpenClaw 实战：一个人、一台 Mac、六个 AI Agent — 从"能聊天"到"能干活"的工程实战》

**v2.0 修订说明**（基于 Codex CLI 评审 4 点 + 仓库边界纠正）：
1. Part 3 API 表改为"已落地接口 / 拟新增接口"双栏，对齐四类桥接契约审计结论
2. 全文严格分层：【现状】= 代码+测试可验证；【目标】= 架构设计；【路线图】= 实施计划
3. "编码专家"从 Hermes 内部专家层移除，改为"对外开发执行接口"（能力层）
4. 所有插件/技能/Cron 清单加三级状态标注：🟢已安装 🟡已验证未安装 🔴计划开发
5. 仓库边界纠正：文档归属 CrazyAgentsManage（HermesAgent 运营宿主层），不再误放 FlowMindDeploy

---

## 目录

1. [背景与目标](#背景与目标)
2. [Part 1: 整体框架设计](#part-1-整体框架设计)
3. [Part 2: HermesAgent 运营体系落地方案](#part-2-hermesagent-运营体系落地方案)
4. [Part 3: FlowMind 角色定位与运营能力建设](#part-3-flowmind-角色定位与运营能力建设)
5. [实施路线图](#实施路线图)
6. [附录：参考架构](#附录参考架构)

---

## 背景与目标

### 1.1 项目背景

我们的目标是基于 FlowMind（承诺治理系统）的产品理念，结合 HermesAgent 的能力，构建一个**真实世界可运行的 AI Agent 运营体系**。

### 1.2 两个维度的演进

| 维度 | 【现状】 | 【目标】 |
|------|----------|----------|
| **静态维度** | FlowMind 产品设计 + Demo 原型 | 结构化的承诺治理系统 |
| **动态维度** | 单一 Agent 执行任务 | 多 Agent 协作的运营体系 |

### 1.3 核心洞察（来自文章）

> *"90% 的时间花在工程问题上，不是 AI 问题上。Agent 系统的瓶颈不是模型能力，是基础设施的成熟度。"*

文章的核心观点是：**Agent 的价值不在于"能聊天"，而在于"能干活"**——即 7×24 稳定运行、自主学习、多 Agent 协作。

---

## Part 1: 整体框架设计

### 2.1 架构概览

> **【目标】** 以下架构为设计目标，各层落地状态见逐节标注。

基于文章的"1+5+6"阵型理念，结合 FlowMind 的承诺治理语义，设计以下架构：

```
┌─────────────────────────────────────────────────────────────────┐
│                      用户层 (User Layer)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  飞书群聊    │  │  Web UI     │  │  CLI 接口   │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
└─────────┼────────────────┼────────────────┼─────────────────────┘
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    编排层 (Orchestration Layer)                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Zoe (首席编排者) - 基于 HermesAgent                      │   │
│  │  - 任务分派与协调                                         │   │
│  │  - 圆桌讨论主持                                           │   │
│  │  - 系统巡检与维护                                         │   │
│  │  - 记忆系统管理                                           │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    专家层 (Expert Layer) — 4 个常驻角色          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  承诺管家    │  │  情报哨兵    │  │  内容策展   │             │
│  │  (Promise)  │  │  (Intel)    │  │  (Content)  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│  ┌─────────────┐                                               │
│  │  运维卫士    │  ⚠️ 编码专家不在专家层，见能力层"对外开发接口"  │
│  │  (Ops)      │                                               │
│  └─────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    能力层 (Capability Layer)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  技能库      │  │  MCP 工具    │  │  Cron 任务  │             │
│  │  (Skills)   │  │  (Tools)    │  │  (Schedule) │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│  ┌─────────────────────────────────────────────┐               │
│  │  对外开发执行接口 (Codex/Claude Code/OpenCode) │               │
│  │  ⚠️ 非 Hermes 内部角色，通过 delegate_task/ACP 调用 │           │
│  └─────────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────┘
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    记忆层 (Memory Layer)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  SOUL.md    │  │  MEMORY.md  │  │  Skills     │             │
│  │  (身份层)   │  │  (长期记忆)  │  │  (程序性)   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│  ┌─────────────┐  ┌─────────────┐                              │
│  │  .learnings/│  │  memory/    │                              │
│  │  (经验库)   │  │  (日报归档)  │                              │
│  └─────────────┘  └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    数据层 (Data Layer)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  shared-    │  │  Obsidian   │  │  Vector DB  │             │
│  │  context/   │  │  Vault      │  │  (可选)     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件说明

#### 2.2.1 编排层 - Zoe

**【现状】** HermesAgent 已具备 `delegate_task`、`cronjob`、`memory` 等原生能力。

**【目标】职责**：
- 任务分派与协调（基于 ACP 协议）
- 圆桌讨论主持（三态通信协议）
- 系统巡检与维护（3次/天）
- 记忆系统管理（weekly maintenance）

**【现状】实现方式**：
- 基于 HermesAgent 的主实例
- 使用 `delegate_task` 委派任务给专家
- 使用 `cronjob` 定时执行巡检
- 使用 `memory` 管理持久化记忆

#### 2.2.2 专家层（4 个常驻角色）

| 专家角色 | 职责 | 核心能力 | 落地状态 |
|---------|------|----------|---------|
| **承诺管家 (Promise)** | FlowMind 承诺治理 | 承诺创建/查询/追踪、状态管理、Review 触发 | 🔴【目标】待建立 |
| **情报哨兵 (Intel)** | 信息采集与分析 | RSS/网页监控、趋势分析、情报摘要 | 🔴【目标】待建立 |
| **内容策展 (Content)** | 内容生成与发布 | 文案撰写、多平台适配、发布管理 | 🔴【目标】待建立 |
| **运维卫士 (Ops)** | 系统运维与监控 | 健康检查、告警处理、性能优化 | 🔴【目标】待建立 |

> ⚠️ **编码专家不在此层**。代码开发由 Codex CLI 负责，HermesAgent 通过"对外开发执行接口"委派，不自身执行代码。详见 2.2.3。

#### 2.2.3 对外开发执行接口（能力层，非专家角色）

**【现状】** HermesAgent 已具备 `delegate_task` 能力，可通过 ACP 协议调用外部开发 Agent。

**【目标】** 明确编码工作不属于 Hermes 内部职责，而是通过接口委派：

| 被委派方 | 适用场景 | 调用方式 |
|---------|---------|---------|
| Codex CLI | 代码实现、架构设计 | `delegate_task(acp_command="codex")` |
| Claude Code | 复杂编码任务 | `delegate_task(acp_command="claude")` |
| OpenCode | 轻量修复 | `delegate_task(acp_command="opencode")` |

**Hermes 自身角色**：仅负责任务编排、需求传达、结果验收，不做代码执行。

#### 2.2.4 能力层

- **技能库**：基于 ClawHub 的 Skills，按需加载
- **MCP 工具**：通过 MCP 协议接入外部服务
- **Cron 任务**：定时任务覆盖关键时段

### 2.3 与 FlowMind 的映射

| FlowMind 概念 | 架构组件 | 实现方式 | 落地状态 |
|--------------|---------|----------|---------|
| Canonical Truth | 承诺管家 | 基于 FlowMind API 的承诺对象管理 | 🔴【目标】 |
| Capture/Clarify | 情报哨兵 | 信息采集 + 人工确认流程 | 🔴【目标】 |
| Query/Review | 承诺管家 + Zoe | 结构化查询 + Review 工作流 | 🟡【目标】Truth Query API 已落地 |
| Governed Integration | 对外开发接口 | ACP 协议 + 审查流程 | 🟡【目标】delegate_task 已可用 |

---

## Part 2: HermesAgent 运营体系落地方案

### 3.1 专家角色设定

> **【目标】** 以下为各专家角色的设计规范，落地需逐步实施。

#### 3.1.1 承诺管家 (Promise Keeper)

**SOUL.md 核心约束**：
```markdown
# 身份定义
你是 FlowMind 的承诺管家，负责管理用户的所有承诺和待办事项。

# 核心职责
1. 承诺生命周期管理：创建 → 确认 → 执行 → 完成/取消
2. 状态追踪与提醒：deadline 预警、blocked 检测、stale 告警
3. Review 工作流触发：定期 Review、drift detection

# 绝对禁止
- 不得未经用户确认就创建正式承诺
- 不得删除或修改已确认的承诺（只能追加）
- 不得绕过 Write Gate 直接修改 Canonical Truth

# 决策框架
- 用户输入 → 识别为 Candidate → Clarify → 确认 → 持久化
- 外部 Agent 输入 → 作为 Candidate 进入治理流程
```

**技能配置**：
- 🟢 `flowmind-candidate-ingress`: 发送候选数据到 FlowMind API（已安装）
- 🟢 `flowmind-pilot`: Pilot 测试执行模式（已安装）
- 🟡 `webhook-subscriptions`: 事件驱动的 Webhook 管理（已验证未安装）

#### 3.1.2 情报哨兵 (Intel Sentinel)

**SOUL.md 核心约束**：
```markdown
# 身份定义
你是系统的情报中枢，负责从多源采集信息并生成可行动的情报。

# 核心职责
1. 信息采集：RSS、网页监控、GitHub Trending、arXiv
2. 情报分析：5 星评估、影响分析、行动建议
3. 情报分发：按优先级推送、存档

# 绝对禁止
- 不得推送未经验证的信息
- 不得编造数据或来源
- 不得在情报中掺杂个人判断（必须标注置信度）

# 决策框架
- 采集 → 去重 → 评估 → 分级 → 推送/归档
- 每条情报必须带原文 URL，无法验证的标注"单源，建议核实"
```

**技能配置**：
- 🟡 `blogwatcher`: 监控博客和 RSS/Atom feed（已验证未安装）
- 🟡 `youtube-content`: 获取 YouTube 视频转录（已验证未安装）
- 🟡 `arxiv`: 搜索学术论文（已验证未安装）
- 🟡 `polymarket`: 查询预测市场数据（已验证未安装）

#### 3.1.3 内容策展 (Content Curator)

**SOUL.md 核心约束**：
```markdown
# 身份定义
你是内容策略师，负责从团队情报中提取素材并生成优质内容。

# 核心职责
1. 素材提取：从情报哨兵、承诺管家等获取原始素材
2. 内容创作：文案撰写、多平台适配
3. 发布管理：定时发布、效果追踪

# 绝对禁止
- 不得发布未经审核的内容
- 不得在内容中暴露内部系统细节
- 不得使用"AI 味"过重的表达

# 决策框架
- 消费情报 → 生成创意 → 撰写初稿 → 传播预测 → 投递
- 内容必须有明确的价值主张，不是为了发而发
```

**技能配置**：
- 🟡 `marketing-content-creator`: 多平台内容创作（已验证未安装）
- 🟡 `marketing-xiaohongshu-operator`: 小红书运营（已验证未安装）
- 🟡 `marketing-wechat-operator`: 微信生态运营（已验证未安装）
- 🟡 `marketing-douyin-strategist`: 抖音策略（已验证未安装）

#### 3.1.4 运维卫士 (Ops Guardian)

**SOUL.md 核心约束**：
```markdown
# 身份定义
你是系统运维专家，负责保障系统 7×24 稳定运行。

# 核心职责
1. 健康检查：定时巡检、异常检测
2. 告警处理：故障响应、自动恢复
3. 性能优化：资源监控、容量规划

# 绝对禁止
- 不得在生产环境未经确认执行高风险操作
- 不得删除日志或监控数据
- 不得绕过审批流程进行变更

# 决策框架
- 检测 → 分类 → 响应 → 恢复 → 复盘
- P0 故障立即响应，P1 故障 15 分钟内响应
```

**技能配置**：
- 🟢 `hermes-stuck-session-diagnosis`: 诊断卡住的会话（已安装）
- 🟡 `clickhouse-log-rescue`: ClickHouse 日志紧急修复（已验证未安装）
- 🟢 `server-maintain`: 服务器远程维护（已安装）

### 3.2 插件安装方案

#### 3.2.1 核心插件

| 插件 | 用途 | 状态 | 安装命令 |
|------|------|------|----------|
| `flowmind-candidate-ingress` | FlowMind 候选数据入口 | 🟢已安装 | — |
| `flowmind-pilot` | FlowMind Pilot 测试 | 🟢已安装 | — |
| `feishu-lark-cli-docs` | 飞书文档操作 | 🟢已安装 | — |
| `feishu-outbound-mention` | 飞书 @ 提醒修复 | 🟢已安装 | — |
| `webhook-subscriptions` | Webhook 事件驱动 | 🟡已验证未安装 | `npx clawhub install webhook-subscriptions` |

#### 3.2.2 能力插件（按需）

| 插件 | 用途 | 适用专家 | 状态 |
|------|------|---------|------|
| `blogwatcher` | RSS/博客监控 | 情报哨兵 | 🟡已验证未安装 |
| `youtube-content` | YouTube 转录 | 情报哨兵 | 🟡已验证未安装 |
| `arxiv` | 学术论文搜索 | 情报哨兵 | 🟡已验证未安装 |
| `polymarket` | 预测市场数据 | 情报哨兵 | 🟡已验证未安装 |
| `marketing-content-creator` | 内容创作 | 内容策展 | 🟡已验证未安装 |
| `marketing-xiaohongshu-operator` | 小红书运营 | 内容策展 | 🟡已验证未安装 |
| `hermes-stuck-session-diagnosis` | 会话诊断 | 运维卫士 | 🟢已安装 |
| `server-maintain` | 服务器维护 | 运维卫士 | 🟢已安装 |
| `clickhouse-log-rescue` | ClickHouse 日志修复 | 运维卫士 | 🟡已验证未安装 |

### 3.3 技能设计

> **【目标】** 以下技能体系为设计规划，绝大部分尚未创建（🔴计划开发）。

#### 3.3.1 技能分类体系

```
skills/
├── agent-ops/           # Agent 运营技能
│   ├── soul-management/ # SOUL.md 管理
│   ├── memory-maintenance/ # 记忆维护
│   └── protocol-design/ # 协议设计
├── promise-governance/  # 承诺治理技能
│   ├── capture-clarify/ # 采集与澄清
│   ├── review-trigger/  # Review 触发
│   └── drift-detection/ # 漂移检测
├── intel-collection/    # 情报采集技能
│   ├── rss-monitor/     # RSS 监控
│   ├── web-scraper/     # 网页抓取
│   └── paper-analysis/  # 论文分析
├── content-creation/    # 内容创作技能
│   ├── copywriting/     # 文案撰写
│   ├── platform-adapter/# 平台适配
│   └── publish-manager/ # 发布管理
└── ops-maintenance/     # 运维技能
    ├── health-check/    # 健康检查
    ├── alert-response/  # 告警响应
    └── performance-opt/ # 性能优化
```

**状态标注**：以上全部为 🔴计划开发，尚未创建任何 SKILL.md。

### 3.4 工作流设定

> **【目标】** 以下为每日工作流设计，大部分为规划，仅少量 Cron 已配置。

#### 3.4.1 每日工作流

```
07:00  系统启动，加载 SOUL.md + MEMORY.md          【现状】已实现
08:00  情报哨兵开始采集（晨报）                      【目标】待实施
08:30  推送晨报到飞书群                              【目标】待实施
09:00  承诺管家执行每日 Review                        【目标】待实施
10:00  内容策展开始创意规划                           【目标】待实施
12:00  情报哨兵推送午间论文解读                       【目标】待实施
14:00  Zoe 执行午间巡检                              【目标】待实施
18:00  情报哨兵推送晚间趋势分析                       【目标】待实施
20:00  内容策展执行发布计划                           【目标】待实施
22:00  Zoe 执行晚间巡检                              【目标】待实施
23:00  各专家执行每日反思                             【目标】待实施
23:30  Zoe 汇总全团队产出                            【目标】待实施
23:45  推送日报到飞书群                              【目标】待实施
```

#### 3.4.2 协作工作流

> **【目标】** 三态通信协议为设计规范，代码中尚未实现。

基于文章的三态通信协议：

```
[request]   @专家B + ack_id + 期望动作 + 截止时间
[confirmed] @发起方 + ack_id + 版本号/生效时间/关键结论
[final]     @相关方 + ack_id + 终态收敛（全线程仅 1 条）
```

**示例：承诺 Review 工作流**

```
Zoe: @承诺管家 [state=request] [ack_id=review-20260426]
     请执行今日承诺 Review，识别 overdue/blocked/stale 条目
     截止时间：09:30

承诺管家: @Zoe [state=confirmed] [ack_id=review-20260426]
         已识别 3 个 overdue、1 个 blocked、2 个 stale
         详情见附件

Zoe: @承诺管家 [state=final] [ack_id=review-20260426]
     Review 完成，已推送提醒给用户
     [全员静默]
```

### 3.5 定时任务设定

#### 3.5.1 任务清单

| 任务名称 | 调度时间 | 执行专家 | 任务描述 | 状态 |
|---------|---------|---------|---------|------|
| `morning-intel` | 08:30 | 情报哨兵 | 采集过去 12 小时的重要信息 | 🔴计划开发 |
| `daily-promise-review` | 09:00 | 承诺管家 | 检查所有待办承诺状态 | 🔴计划开发 |
| `daily-content-planning` | 10:00 | 内容策展 | 消费情报，生成内容创意 | 🔴计划开发 |
| `noon-paper-review` | 12:00 | 情报哨兵 | 搜索 arXiv 最新论文 | 🔴计划开发 |
| `noon-ops-check` | 14:00 | Zoe | 执行午间系统巡检 | 🔴计划开发 |
| `evening-trend-analysis` | 20:00 | 情报哨兵 | 分析今日技术趋势 | 🔴计划开发 |
| `daily-content-publish` | 20:00 | 内容策展 | 执行发布计划 | 🔴计划开发 |
| `nightly-ops-check` | 22:00 | Zoe | 执行晚间系统巡检 | 🔴计划开发 |
| `daily-reflection` | 23:00 | 各专家 | 执行每日反思 | 🔴计划开发 |
| `daily-summary` | 23:30 | Zoe | 汇总全团队产出 | 🔴计划开发 |
| `daily-digest` | 23:45 | Zoe | 推送日报到飞书群 | 🔴计划开发 |
| `weekly-promise-audit` | 18:00 周五 | 承诺管家 | 生成本周承诺盘点 | 🔴计划开发 |
| `weekly-content-review` | 18:00 周日 | 内容策展 | 分析本周内容效果 | 🔴计划开发 |
| `weekly-memory-maintenance` | 10:00 周日 | Zoe | 执行记忆系统维护 | 🔴计划开发 |

> ⚠️ 以上 14 个 Cron 任务全部为 🔴计划开发，当前无任何已配置运行的专用运营 Cron。

#### 3.5.2 Cron 任务配置示例

> **【目标】** 以下为 Cron 配置示例，尚未注册到 Hermes。

```yaml
# 晨间情报采集
- schedule: "30 8 * * *"
  name: "morning-intel"
  prompt: |
    你是情报哨兵，执行晨间情报采集任务。
    
    步骤：
    1. 使用 blogwatcher 检查订阅的 RSS feed
    2. 使用 browser 工具采集 GitHub Trending
    3. 使用 arxiv 搜索最新 AI/Agent 论文
    4. 对采集的信息进行 5 星评估
    5. 生成晨报，推送到飞书群（CrazyAgentsManage）
    
    输出格式：
    - 标题：【晨间情报】2026-04-26
    - 结构：按重要性排序，每条带原文链接
    - 评估：5 星制 + 影响分析
  deliver: "feishu:oc_bbde428675a7c267d55c3f0663ca701d"
  skills: ["blogwatcher", "arxiv"]
```

### 3.6 记忆体系设计

#### 3.6.1 五层记忆架构

| 层级 | 存储 | 时间尺度 | 管理方式 | 落地状态 |
|------|------|---------|---------|---------|
| L1 身份层 | SOUL.md | 永恒 | 人工确认修改 | 🟢已实现 |
| L2 长期记忆 | MEMORY.md | 长期 | Agent 自主维护 | 🟢已实现 |
| L3 中期记忆 | memory/YYYY-MM-DD.md | 中期 | 自动提取 | 🟡部分实现（compaction 机制存在但无结构化归档） |
| L4 短期记忆 | .learnings/ | 短期 | 即时记录 | 🔴计划开发 |
| L5 持久化 | Skills + Obsidian | 持久 | 共享/归档 | 🟡Skills 已实现，Obsidian 未集成 |

#### 3.6.2 记忆自主迭代循环

> **【目标】** 以下循环为设计规范，自动 promote 机制尚未实现。

```
触发事件（操作失败/用户纠正/发现更优做法）
    ↓
.learnings/ 即时记录
    ↓
每日反思 Cron (23:00)
    ↓
评估复现频率 → ≥3 次？ → promote 到 MEMORY.md
    ↓
下次 Session 加载（bootstrap hook）
    ↓
Agent 行为改进
```

---

## Part 3: FlowMind 角色定位与运营能力建设

### 4.1 FlowMind 在方案中的角色

#### 4.1.1 核心定位

**FlowMind 是整个运营体系的"承诺治理引擎"**，负责：
- 维护 Canonical Truth（承诺真相）
- 执行 Capture/Clarify 流程
- 提供 Query/Review 能力
- 治理外部集成

#### 4.1.2 与 HermesAgent 的协作模式

```
┌─────────────────────────────────────────────────────────────┐
│                        用户                                 │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  HermesAgent (Zoe + 4 专家团队)                      │   │
│  │  - 接收用户输入                                       │   │
│  │  - 识别承诺候选                                       │   │
│  │  - 执行 Clarify 流程                                 │   │
│  │  - 调用 FlowMind API                                 │   │
│  └───────────────────────┬─────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  FlowMind API                                       │   │
│  │  - Candidate Ingress (接收候选)                      │   │
│  │  - Write Gate (治理写入)                             │   │
│  │  - Truth Query (查询真相)                            │   │
│  │  - Review Trigger (触发 Review)                      │   │
│  └───────────────────────┬─────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Canonical Truth Store                              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

#### 4.1.3 FlowMind API 接口（双栏：已落地 / 拟新增）

> **对齐四类桥接契约审计结论（2026-04-26）**

| 能力 | 【已落地接口】（代码+测试可验证） | 【拟新增接口】（文档定义，代码未实现） |
|------|--------------------------------|--------------------------------------|
| Candidate Ingress | `POST /api/integrations/candidate-ingress` ✅ | — |
| Truth Query | `GET /bridge/truth` + `GET /bridge/truth/:id` ✅ | — |
| Context Compilation | `POST /bridge/context-pack` ✅ | — |
| Truth Change Feedback | `POST /bridge/feedback` + `GET /bridge/feedback/:instanceId` ✅ | — |
| Clarify Workflow | — | `POST /api/clarify`（多轮澄清状态机）🔴 |
| Review Trigger | — | `POST /api/review/trigger`（Review 工作流触发）🔴 |
| Mutation Request | — | `POST /api/mutations`（请求变更）🔴 |
| Provenance Inspection | — | `GET /api/provenance`（审计追溯）🔴 |

**四类桥接当前状态（审计结论）**：

| 桥接 | 状态 | 测试 | 关键 Gap |
|------|------|------|---------|
| Candidate Ingress | ✅已成立 | 5 UT | 无 |
| Truth Query | ⚠️测试不足 | 仅 auth 测试 | 缺服务层 UT + e2e |
| Context Compilation | ⚠️测试不足 | 间接 e2e | 缺独立 UT + ontology 可选注入 |
| Truth Change Feedback | ⚠️架构缺口 | 无 | 无推送机制 / submitDecision 未自动联动 / 无 UT |

### 4.2 运营能力建设需求

#### 4.2.1 Phase 1: 基础能力（当前）

**目标**：让 HermesAgent 能够通过 API 与 FlowMind 交互

**需求**：
1. **Candidate Ingress API** — 🟢已落地
2. **Truth Query API** — 🟢已落地（⚠️需补 UT）
3. **Context Compilation API** — 🟢已落地（⚠️需补 UT）
4. **Truth Change Feedback API** — 🟡已落地但有架构缺口（P0：自动联动 + SSE 推送）

**实现优先级**：
```
✅ 已完成: Candidate Ingress + Truth Query + Context Compilation + Feedback 基础
P0 (当前): Feedback 自动联动（submitDecision→recordFeedback） + SSE 推送
P1: 补齐 Truth Query / Context Compilation UT + provenanceRefs 修正
P2: ontology 可选注入→必选或降级提示
```

#### 4.2.2 Phase 2: 协作能力（中期）

**目标**：支持多 Agent 协作治理

**需求**：
1. **Agent 身份认证** — 🔴待设计
2. **协作工作流** — 🔴待设计（三态通信协议）
3. **审计追溯** — 🔴待设计

#### 4.2.3 Phase 3: 智能能力（远期）

**目标**：让 FlowMind 具备自主治理能力

**需求**：
1. **智能 Clarify** — 🔴待设计
2. **Drift Detection** — 🔴待设计
3. **学习与优化** — 🔴待设计

### 4.3 数据流向设计

> **【目标】** 以下数据流为设计规范，部分路径已可运行。

#### 4.3.1 承诺生命周期数据流

```
用户输入
    ↓
HermesAgent 识别为 Candidate                    【现状】人工触发
    ↓
调用 FlowMind Candidate Ingress API              【现状】已落地
    ↓
FlowMind 写入 Candidate Store                    【现状】已落地
    ↓
触发 Clarify Workflow（如需要）                   【目标】拟新增
    ↓
用户确认 → 提升为 Canonical Truth                【现状】已落地（submitDecision）
    ↓
写入 Truth Store                                 【现状】已落地
    ↓
触发 Webhook 通知                                【目标】拟新增（当前仅 SSE 事件）
    ↓
HermesAgent 接收通知 → 更新记忆                  【目标】拟新增
```

#### 4.3.2 Review 工作流数据流

> **【目标】** 整条链路均为拟新增，代码中尚未实现。

```
Cron 触发 / 手动触发
    ↓
HermesAgent 调用 Review Trigger API
    ↓
FlowMind 执行 Review 扫描
    ↓
生成 Review 报告
    ↓
推送到飞书群 / 用户
    ↓
用户决策 → 触发 Mutation Request
    ↓
FlowMind 执行变更 → 记录 Provenance
```

---

## 实施路线图

> **【路线图】** 以下为分阶段实施计划。

### 5.1 Phase 1: 基础搭建（2 周）

**Week 1**：
- [x] 安装核心插件（🟢已完成：flowmind-candidate-ingress、flowmind-pilot、feishu 相关）
- [ ] 配置 SOUL.md（各专家角色定义）🔴待实施
- [ ] 设置基础 Cron 任务（5 个核心任务）🔴待实施
- [x] 实现 Candidate Ingress API 调用（🟢已落地）

**Week 2**：
- [x] 实现 Truth Query API 调用（🟢已落地，⚠️需补 UT）
- [x] 实现 Context Compilation API 调用（🟢已落地，⚠️需补 UT）
- [ ] 实现 Truth Change Feedback 自动联动 🔴P0 进行中
- [ ] 配置飞书消息推送（🟢基础能力已有）
- [ ] 测试承诺生命周期 🔴待实施
- [ ] 文档化工作流 🔴待实施

### 5.2 Phase 2: 能力扩展（2 周）

**Week 3**：
- [ ] 实现 Clarify Workflow 🔴待设计
- [ ] 配置 Webhook 回调 🔴待设计
- [ ] 扩展 Cron 任务（10+ 任务）🔴待实施
- [ ] 实现三态通信协议 🔴待设计

**Week 4**：
- [ ] 完善记忆体系（L3-L5）🔴待实施
- [ ] 配置自动反思 🔴待实施
- [ ] 测试多 Agent 协作 🔴待实施
- [ ] 性能优化 🔴待实施

### 5.3 Phase 3: 生产就绪（2 周）

**Week 5**：
- [ ] 实现 Review 工作流 🔴待设计
- [ ] 配置告警与恢复 🔴待实施
- [ ] 实现审计追溯 🔴待设计
- [ ] 压力测试 🔴待实施

**Week 6**：
- [ ] 文档完善 🔴待实施
- [ ] 用户培训 🔴待实施
- [ ] 上线部署 🔴待实施
- [ ] 监控与优化 🔴待实施

---

## 附录：参考架构

### A.1 文章核心配置参考

> **【目标】** 以下为 OpenClaw 文章推荐的配置范例，供设计参考。

```json
{
  "compaction": {
    "mode": "safeguard",
    "memoryFlush": {
      "enabled": true,
      "softThresholdTokens": 40000,
      "prompt": "Distill to memory/YYYY-MM-DD.md. Focus: decisions, state changes, lessons, blockers."
    }
  },
  "contextPruning": {
    "mode": "cache-ttl",
    "ttl": "6h",
    "keepLastAssistants": 3
  },
  "session": {
    "reset": {
      "mode": "daily",
      "atHour": 5,
      "idleMinutes": 30
    },
    "maintenance": {
      "pruneAfter": "7d",
      "maxDiskBytes": 104857600
    }
  },
  "hooks": {
    "bootstrap": ["self-improving-agent"]
  }
}
```

### A.2 三态通信协议模板

> **【目标】** 协议模板，代码中尚未实现。

```markdown
# 请求
@专家B [state=request] [ack_id=topic-YYYYMMDDHHMM]
期望动作：[具体描述]
截止时间：[HH:MM]

# 确认
@发起方 [state=confirmed] [ack_id=topic-YYYYMMDDHHMM]
版本：v[N]
生效时间：[HH:MM]
关键结论：[摘要]

# 终态
@相关方 [state=final] [ack_id=topic-YYYYMMDDHHMM]
终态结论：[完整结论]
[全员静默，收到/感谢/OK → NO_REPLY]
```

### A.3 技能安装检查清单

```bash
# 检查已安装技能
hermes skills list | grep -E "flowmind|webhook|feishu|blogwatcher|arxiv"

# 检查 Cron 任务是否配置
hermes cron list

# 检查记忆配置
cat ~/.hermes/config.yaml | grep -A 10 "memory:"

# 检查 SOUL.md
ls -la ~/.hermes/profiles/*/SOUL.md
```

---

## 落地状态汇总

| 分类 | 🟢已落地 | 🟡已验证未安装 | 🔴计划开发 |
|------|---------|---------------|-----------|
| API 接口 | 4 个（四类桥接） | 0 | 4 个（Clarify/Review/Mutation/Provenance） |
| 插件 | 5 个 | 8 个 | 0 |
| 技能 | 0 | 0 | 15+ 个（全部技能目录） |
| Cron 任务 | 0 | 0 | 14 个 |
| 记忆层级 | L1+L2 | L3+L5部分 | L4 |

---

**文档状态**: 第二稿（CrazyAgentsManage 仓库），待 Codex CLI 最终签字  
**下一步**: @Codex CLI 签字确认后，合并到 CrazyAgentsManage `feature/sprint4-search-responsive` 分支  
**v2.0 修订依据**: Codex CLI 评审 4 点意见  
**仓库归属**: CrazyAgentsManage（HermesAgent 运营宿主层基线文档）
