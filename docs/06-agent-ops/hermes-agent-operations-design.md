# 基于 OpenClaw 实战文章的 HermesAgent 运营体系设计

> **文档版本**: v1.0  
> **创建日期**: 2026-04-26  
> **状态**: 初稿，待与 Codex CLI 同步定稿  
> **参考文章**: 《OpenClaw 实战：一个人、一台 Mac、六个 AI Agent — 从"能聊天"到"能干活"的工程实战》

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

| 维度 | 当前状态 | 目标状态 |
|------|----------|----------|
| **静态维度** | FlowMind 产品设计 + Demo 原型 | 结构化的承诺治理系统 |
| **动态维度** | 单一 Agent 执行任务 | 多 Agent 协作的运营体系 |

### 1.3 核心洞察（来自文章）

> *"90% 的时间花在工程问题上，不是 AI 问题上。Agent 系统的瓶颈不是模型能力，是基础设施的成熟度。"*

文章的核心观点是：**Agent 的价值不在于"能聊天"，而在于"能干活"**——即 7×24 稳定运行、自主学习、多 Agent 协作。

---

## Part 1: 整体框架设计

### 2.1 架构概览

基于文章的"1+5+6"阵型理念，结合 FlowMind 的承诺治理语义，设计以下架构：

```
┌─────────────────────────────────────────────────────────────────┐
│                      用户层 (User Layer)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  飞书群聊    │  │  Web UI     │  │  CLI 接口   │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                      │
└─────────┼────────────────┼────────────────┼─────────────────────┘
          │                │                │
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
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    专家层 (Expert Layer)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  承诺管家    │  │  情报哨兵    │  │  内容策展   │             │
│  │  (Promise)  │  │  (Intel)    │  │  (Content)  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│  ┌─────────────┐  ┌─────────────┐                              │
│  │  运维卫士    │  │  编码专家    │                              │
│  │  (Ops)      │  │  (Coder)    │                              │
│  └─────────────┘  └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    能力层 (Capability Layer)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  技能库      │  │  MCP 工具    │  │  Cron 任务  │             │
│  │  (Skills)   │  │  (Tools)    │  │  (Schedule) │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
          │                │                │
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
          │                │                │
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

**职责**：
- 任务分派与协调（基于 ACP 协议）
- 圆桌讨论主持（三态通信协议）
- 系统巡检与维护（3次/天）
- 记忆系统管理（weekly maintenance）

**实现方式**：
- 基于 HermesAgent 的主实例
- 使用 `delegate_task` 委派任务给专家
- 使用 `cronjob` 定时执行巡检
- 使用 `memory` 管理持久化记忆

#### 2.2.2 专家层

| 专家角色 | 职责 | 核心能力 |
|---------|------|----------|
| **承诺管家 (Promise)** | FlowMind 承诺治理 | 承诺创建/查询/追踪、状态管理、Review 触发 |
| **情报哨兵 (Intel)** | 信息采集与分析 | RSS/网页监控、趋势分析、情报摘要 |
| **内容策展 (Content)** | 内容生成与发布 | 文案撰写、多平台适配、发布管理 |
| **运维卫士 (Ops)** | 系统运维与监控 | 健康检查、告警处理、性能优化 |
| **编码专家 (Coder)** | 代码开发与调试 | 委派给 Codex CLI / Claude Code |

#### 2.2.3 能力层

- **技能库**：基于 ClawHub 的 100+ Skills，按需加载
- **MCP 工具**：通过 MCP 协议接入外部服务
- **Cron 任务**：52+ 定时任务覆盖全时段

### 2.3 与 FlowMind 的映射

| FlowMind 概念 | 架构组件 | 实现方式 |
|--------------|---------|----------|
| Canonical Truth | 承诺管家 | 基于 FlowMind API 的承诺对象管理 |
| Capture/Clarify | 情报哨兵 | 信息采集 + 人工确认流程 |
| Query/Review | 承诺管家 + Zoe | 结构化查询 + Review 工作流 |
| Governed Integration | 编码专家 | ACP 协议 + 审查流程 |

---

## Part 2: HermesAgent 运营体系落地方案

### 3.1 专家角色设定

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
- `flowmind-candidate-ingress`: 发送候选数据到 FlowMind API
- `flowmind-pilot`: Pilot 测试执行模式
- `webhook-subscriptions`: 事件驱动的 Webhook 管理

**Cron 任务**：
```yaml
# 每日承诺 Review
- schedule: "0 9 * * *"
  name: "daily-promise-review"
  prompt: "检查所有待办承诺的状态，识别 overdue/blocked/stale 条目，生成 Review 报告"

# 每周承诺盘点
- schedule: "0 18 * * 5"
  name: "weekly-promise-audit"
  prompt: "生成本周承诺完成率、下周计划、风险预警报告"
```

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
- `blogwatcher`: 监控博客和 RSS/Atom feed
- `youtube-content`: 获取 YouTube 视频转录
- `arxiv`: 搜索学术论文
- `polymarket`: 查询预测市场数据

**Cron 任务**：
```yaml
# 晨间情报 (08:30)
- schedule: "30 8 * * *"
  name: "morning-intel"
  prompt: "采集过去 12 小时的重要信息，生成晨报，推送到飞书群"

# 午间论文解读 (12:00)
- schedule: "0 12 * * *"
  name: "noon-paper-review"
  prompt: "搜索 arXiv 最新 AI/Agent 论文，选择 Top3 进行解读"

# 晚间趋势分析 (20:00)
- schedule: "0 20 * * *"
  name: "evening-trend-analysis"
  prompt: "分析今日技术趋势，更新 tech-radar.json"
```

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
- `marketing-content-creator`: 多平台内容创作
- `marketing-xiaohongshu-operator`: 小红书运营
- `marketing-wechat-operator`: 微信生态运营
- `marketing-douyin-strategist`: 抖音策略

**Cron 任务**：
```yaml
# 每日内容规划 (10:00)
- schedule: "0 10 * * *"
  name: "daily-content-planning"
  prompt: "消费今日情报，生成内容创意，规划发布计划"

# 每周内容复盘 (18:00 周日)
- schedule: "0 18 * * 0"
  name: "weekly-content-review"
  prompt: "分析本周内容效果，调整下周策略"
```

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
- `hermes-stuck-session-diagnosis`: 诊断卡住的会话
- `clickhouse-log-rescue`: ClickHouse 日志紧急修复
- `server-maintain`: 服务器远程维护

**Cron 任务**：
```yaml
# 系统健康检查 (每 15 分钟)
- schedule: "*/15 * * * *"
  name: "system-health-check"
  prompt: "检查系统状态：磁盘、内存、CPU、网络、服务状态"

# 每日运维报告 (23:00)
- schedule: "0 23 * * *"
  name: "daily-ops-report"
  prompt: "生成今日运维报告：故障、恢复、优化建议"
```

#### 3.1.5 编码专家 (Coder Expert)

**实现方式**：
- 不直接运行，而是通过 ACP 协议委派给：
  - Codex CLI（主要）
  - Claude Code（备选）
  - OpenCode（轻量任务）

**委派策略**：
```yaml
# 任务分派规则
- 代码实现: Codex CLI
- 架构设计: Claude Code
- 简单修复: OpenCode
- 代码审查: HermesAgent 自身
```

### 3.2 插件安装方案

#### 3.2.1 核心插件（必须）

| 插件 | 用途 | 安装命令 |
|------|------|----------|
| `ima-note` | IMA 笔记服务 | 已安装 |
| `flowmind-candidate-ingress` | FlowMind 候选数据入口 | `npx clawhub install flowmind-candidate-ingress` |
| `flowmind-pilot` | FlowMind Pilot 测试 | `npx clawhub install flowmind-pilot` |
| `webhook-subscriptions` | Webhook 事件驱动 | `npx clawhub install webhook-subscriptions` |
| `feishu-lark-cli-docs` | 飞书文档操作 | `npx clawhub install feishu-lark-cli-docs` |

#### 3.2.2 能力插件（按需）

| 插件 | 用途 | 适用专家 |
|------|------|----------|
| `blogwatcher` | RSS/博客监控 | 情报哨兵 |
| `youtube-content` | YouTube 转录 | 情报哨兵 |
| `arxiv` | 学术论文搜索 | 情报哨兵 |
| `marketing-content-creator` | 内容创作 | 内容策展 |
| `hermes-stuck-session-diagnosis` | 会话诊断 | 运维卫士 |
| `server-maintain` | 服务器维护 | 运维卫士 |

#### 3.2.3 安装脚本

```bash
#!/bin/bash
# install-core-plugins.sh

echo "=== 安装核心插件 ==="

# FlowMind 相关
npx clawhub install flowmind-candidate-ingress
npx clawhub install flowmind-pilot

# 事件驱动
npx clawhub install webhook-subscriptions

# 飞书集成
npx clawhub install feishu-lark-cli-docs
npx clawhub install feishu-outbound-mention

# 信息采集
npx clawhub install blogwatcher
npx clawhub install arxiv

# 内容运营
npx clawhub install marketing-content-creator

# 运维诊断
npx clawhub install hermes-stuck-session-diagnosis

echo "=== 核心插件安装完成 ==="
```

### 3.3 技能设计

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

#### 3.3.2 核心技能示例：承诺管家

**技能文件**：`skills/promise-governance/capture-clarify/SKILL.md`

```markdown
---
name: promise-capture-clarify
description: |
  承诺采集与澄清技能。从用户输入、外部 Agent、系统事件中识别潜在承诺，
  通过 Clarify 流程确认后持久化到 FlowMind Canonical Truth。
---

# 承诺采集与澄清

## 触发条件
- 用户说"帮我记一下..."、"我需要..."、"待办..."
- 外部 Agent 提交 Candidate
- 系统事件触发（如 deadline 到期）

## 工作流程

### 1. 识别 Candidate
从输入中提取：
- 承诺内容
- 截止时间（可选）
- 关联项目（可选）
- 优先级（可选）

### 2. Clarify 流程
如果信息不完整，进入澄清：
```
用户：帮我记一下明天开会
Agent：好的，我需要确认几个信息：
1. 会议主题是什么？
2. 具体时间？
3. 需要准备什么？
```

### 3. 确认与持久化
```bash
# 调用 FlowMind API 创建承诺
flowmind-candidate-ingress --type commitment \
  --content "明天 14:00 产品评审会" \
  --deadline "2026-04-27T14:00:00+08:00" \
  --source "user-chat" \
  --confidence 0.9
```

### 4. 反馈确认
```
Agent：已记录承诺：
- 内容：明天 14:00 产品评审会
- 截止：2026-04-27 14:00
- 状态：待确认

需要我设置提醒吗？
```

## 注意事项
- 不要假设用户的意图，不确定就问
- 外部 Agent 的输入必须标记为 Candidate，不能直接成为 Canonical Truth
- 每次创建承诺都要记录来源和置信度
```

### 3.4 工作流设定

#### 3.4.1 每日工作流

```
07:00  系统启动，加载 SOUL.md + MEMORY.md
08:00  情报哨兵开始采集（晨报）
08:30  推送晨报到飞书群
09:00  承诺管家执行每日 Review
10:00  内容策展开始创意规划
12:00  情报哨兵推送午间论文解读
14:00  Zoe 执行午间巡检
18:00  情报哨兵推送晚间趋势分析
20:00  内容策展执行发布计划
22:00  Zoe 执行晚间巡检
23:00  各专家执行每日反思
23:30  Zoe 汇总全团队产出
23:45  推送日报到飞书群
```

#### 3.4.2 协作工作流

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

| 任务名称 | 调度时间 | 执行专家 | 任务描述 |
|---------|---------|---------|---------|
| `morning-intel` | 08:30 | 情报哨兵 | 采集过去 12 小时的重要信息 |
| `daily-promise-review` | 09:00 | 承诺管家 | 检查所有待办承诺状态 |
| `daily-content-planning` | 10:00 | 内容策展 | 消费情报，生成内容创意 |
| `noon-paper-review` | 12:00 | 情报哨兵 | 搜索 arXiv 最新论文 |
| `noon-ops-check` | 14:00 | Zoe | 执行午间系统巡检 |
| `evening-trend-analysis` | 20:00 | 情报哨兵 | 分析今日技术趋势 |
| `daily-content-publish` | 20:00 | 内容策展 | 执行发布计划 |
| `nightly-ops-check` | 22:00 | Zoe | 执行晚间系统巡检 |
| `daily-reflection` | 23:00 | 各专家 | 执行每日反思 |
| `daily-summary` | 23:30 | Zoe | 汇总全团队产出 |
| `daily-digest` | 23:45 | Zoe | 推送日报到飞书群 |
| `weekly-promise-audit` | 18:00 周五 | 承诺管家 | 生成本周承诺盘点 |
| `weekly-content-review` | 18:00 周日 | 内容策展 | 分析本周内容效果 |
| `weekly-memory-maintenance` | 10:00 周日 | Zoe | 执行记忆系统维护 |

#### 3.5.2 Cron 任务配置示例

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

| 层级 | 存储 | 时间尺度 | 管理方式 | 典型内容 |
|------|------|---------|---------|---------|
| L1 身份层 | SOUL.md | 永恒 | 人工确认修改 | 身份 + 硬约束 + 决策框架 |
| L2 长期记忆 | MEMORY.md | 长期 | Agent 自主维护 | 结构化经验 |
| L3 中期记忆 | memory/YYYY-MM-DD.md | 中期 | 自动提取 | Session 精华快照 |
| L4 短期记忆 | .learnings/ | 短期 | 即时记录 | 错误记录、用户纠正 |
| L5 持久化 | Skills + Obsidian | 持久 | 共享/归档 | 技能库 + 知识归档 |

#### 3.6.2 记忆自主迭代循环

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

#### 3.6.3 配置示例

```yaml
# ~/.hermes/config.yaml
memory:
  auto_compaction: true
  compaction_threshold: 40000  # tokens
  max_memory_size: 3000  # tokens
  
  # 自动维护
  maintenance:
    enabled: true
    schedule: "weekly"
    prune_after: "7d"
    max_disk_bytes: 104857600  # 100MB

  # 记忆搜索
  search:
    enabled: true
    providers: ["local", "mem0"]  # 可选外部记忆
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
│  │  HermesAgent (Zoe + 专家团队)                        │   │
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
│  │  - 承诺对象                                          │   │
│  │  - 项目对象                                          │   │
│  │  - Next Actions                                     │   │
│  │  - Waiting Fors                                     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

#### 4.1.3 FlowMind 提供的核心能力

| 能力 | API 端点 | 用途 |
|------|---------|------|
| Candidate Ingress | `POST /api/candidates` | 接收承诺候选 |
| Clarify Workflow | `POST /api/clarify` | 执行澄清流程 |
| Truth Query | `GET /api/truth/query` | 查询承诺真相 |
| Review Trigger | `POST /api/review/trigger` | 触发 Review |
| Mutation Request | `POST /api/mutations` | 请求变更 |
| Provenance Inspection | `GET /api/provenance` | 审计追溯 |

### 4.2 运营能力建设需求

#### 4.2.1 Phase 1: 基础能力（当前）

**目标**：让 HermesAgent 能够通过 API 与 FlowMind 交互

**需求**：
1. **Candidate Ingress API**
   - 接收结构化承诺候选
   - 返回 Candidate ID
   - 支持批量提交

2. **Clarify Workflow API**
   - 支持多轮澄清
   - 返回澄清状态
   - 支持超时处理

3. **Truth Query API**
   - 按项目查询
   - 按状态查询（overdue/blocked/stale）
   - 按时间窗查询

4. **Webhook 回调**
   - 承诺状态变更通知
   - Review 完成通知
   - Deadline 预警通知

**实现优先级**：
```
P0: Candidate Ingress + Truth Query
P1: Clarify Workflow + Webhook
P2: Review Trigger + Mutation Request
```

#### 4.2.2 Phase 2: 协作能力（中期）

**目标**：支持多 Agent 协作治理

**需求**：
1. **Agent 身份认证**
   - 每个 Agent 有独立身份
   - 区分用户操作和 Agent 操作
   - 权限分级

2. **协作工作流**
   - Agent 间任务分派
   - 承诺交接与确认
   - 冲突检测与解决

3. **审计追溯**
   - 操作日志
   - 变更历史
   - 决策依据

#### 4.2.3 Phase 3: 智能能力（远期）

**目标**：让 FlowMind 具备自主治理能力

**需求**：
1. **智能 Clarify**
   - 自动识别缺失信息
   - 智能提问策略
   - 上下文感知

2. **Drift Detection**
   - 承诺漂移检测
   - 自动触发 Review
   - 修复建议

3. **学习与优化**
   - 从用户行为学习
   - 优化 Clarify 策略
   - 预测承诺风险

### 4.3 数据流向设计

#### 4.3.1 承诺生命周期数据流

```
用户输入
    ↓
HermesAgent 识别为 Candidate
    ↓
调用 FlowMind Candidate Ingress API
    ↓
FlowMind 写入 Candidate Store
    ↓
触发 Clarify Workflow（如需要）
    ↓
用户确认 → 提升为 Canonical Truth
    ↓
写入 Truth Store
    ↓
触发 Webhook 通知
    ↓
HermesAgent 接收通知 → 更新记忆
```

#### 4.3.2 Review 工作流数据流

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

### 5.1 Phase 1: 基础搭建（2 周）

**Week 1**：
- [ ] 安装核心插件
- [ ] 配置 SOUL.md（各专家角色）
- [ ] 设置基础 Cron 任务（5 个核心任务）
- [ ] 实现 Candidate Ingress API 调用

**Week 2**：
- [ ] 实现 Truth Query API 调用
- [ ] 配置飞书消息推送
- [ ] 测试承诺生命周期
- [ ] 文档化工作流

### 5.2 Phase 2: 能力扩展（2 周）

**Week 3**：
- [ ] 实现 Clarify Workflow
- [ ] 配置 Webhook 回调
- [ ] 扩展 Cron 任务（10+ 任务）
- [ ] 实现三态通信协议

**Week 4**：
- [ ] 实现记忆体系
- [ ] 配置自动反思
- [ ] 测试多 Agent 协作
- [ ] 性能优化

### 5.3 Phase 3: 生产就绪（2 周）

**Week 5**：
- [ ] 实现 Review 工作流
- [ ] 配置告警与恢复
- [ ] 实现审计追溯
- [ ] 压力测试

**Week 6**：
- [ ] 文档完善
- [ ] 用户培训
- [ ] 上线部署
- [ ] 监控与优化

---

## 附录：参考架构

### A.1 文章核心配置参考

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
# 检查核心插件是否安装
skills_list | grep -E "flowmind|webhook|feishu|blogwatcher|arxiv"

# 检查 Cron 任务是否配置
cronjob list

# 检查记忆配置
cat ~/.hermes/config.yaml | grep -A 10 "memory:"

# 检查 SOUL.md
ls -la ~/.hermes/profiles/*/SOUL.md
```

---

## 待与 Codex CLI 讨论的要点

1. **FlowMind API 接口设计**
   - Candidate Ingress 的请求/响应格式
   - Clarify Workflow 的状态机设计
   - Truth Query 的查询语法

2. **多 Agent 协作协议**
   - 三态协议的实现细节
   - 冲突检测与解决机制
   - 审计追溯的数据结构

3. **记忆体系集成**
   - FlowMind 如何与 HermesAgent 记忆同步
   - 承诺变更如何触发记忆更新
   - Review 结果如何沉淀为经验

4. **部署架构**
   - FlowMind API 的部署方式
   - 与 HermesAgent 的通信协议
   - 监控与告警配置

---

**文档状态**: 初稿完成，待与 Codex CLI 同步定稿  
**下一步**: 推送到远端仓库，@Codex CLI 进行讨论
