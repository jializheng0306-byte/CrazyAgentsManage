# CrazyAgentsManage PRD (Product Requirements Document)

## 版本信息

| 字段 | 内容 |
|------|------|
| 产品名称 | CrazyAgentsManage — 多智能体协作管理平台 |
| 版本号 | v0.1.0 |
| 状态 | 草稿 |
| 创建日期 | 2026-04-19 |
| 基于 | Hermes-Agent 多智能体协作架构设计 |
| GitHub | https://github.com/jializheng0306-byte/CrazyAgentsManage |

---

## 一、产品概述

### 1.1 产品定位

CrazyAgentsManage 是一个**多智能体协作管理平台**，在 Hermes-Agent 现有能力基础上，引入角色化智能体、任务编排、团队记忆、共享上下文等核心能力，实现从"单个 AI 助手"到"智能体团队"的升级。

### 1.2 目标用户

- **开发者**：需要多智能体协作完成复杂开发任务
- **项目经理**：需要跟踪多智能体任务执行进度
- **运维工程师**：需要定时任务管理和系统监控
- **团队成员**：需要共享知识沉淀和经验复用

### 1.3 核心价值

| 维度 | 现状 (Hermes-Agent) | 目标 (CrazyAgentsManage) |
|------|---------------------|--------------------------|
| 智能体数量 | 1 个主智能体 + 通用子智能体 | 6 种专业角色智能体 |
| 任务编排 | 手动 delegate_task | DAG 任务图 + 3 状态协议 |
| 记忆系统 | MEMORY.md 文本文件 | 五层分层记忆 + 团队记忆 |
| 协作模式 | 父子智能体线性委派 | 共享上下文文件协作 |
| 定时任务 | Cron 调度 + 本地执行 | Cron + 团队绑定 + 记忆沉淀 |
| 可视化 | 基础会话画像 | 任务编排/DAG/实时监控 |

---

## 二、功能需求

### 2.1 核心功能模块

#### 2.1.1 角色化智能体系统 (Agent Factory)

**需求描述**：
- 支持 6 种预定义角色：Expert/Research/Code/Ops/Cron/Team
- 每个角色有专属工具集和系统提示词模板
- 支持通过 config.yaml 自定义角色配置
- 支持运行时动态切换角色

**用户故事**：
```
作为一个用户
我希望能够指定 delegate_task 使用特定角色（如 "research"）
这样智能体会自动加载对应的工具集和提示词，提高任务执行效率
```

**验收标准**：
- [ ] 通过 `role` 参数创建角色化子智能体
- [ ] 子智能体自动获得角色专属工具集
- [ ] 子智能体使用角色专属系统提示词
- [ ] 角色配置可通过 config.yaml 覆盖
- [ ] 支持中文角色别名（如"研究" → research）

#### 2.1.2 任务编排系统 (Task Orchestrator)

**需求描述**：
- 支持 3 状态协议：pending → running → done
- 支持任务依赖关系（DAG）
- 支持通过 shared-context/ 目录进行任务状态持久化
- 支持并行执行无依赖任务

**用户故事**：
```
作为一个开发者
我希望能够创建一组有依赖关系的任务（研究→编码→测试）
这样系统可以自动按依赖顺序执行，并在 WebUI 中展示任务图
```

**验收标准**：
- [ ] 任务状态机：pending/running/done/failed
- [ ] 任务依赖图（DAG）定义和执行
- [ ] 任务状态持久化到 shared-context/task-*.json
- [ ] 无依赖任务并行执行
- [ ] 任务失败可重试

#### 2.1.3 共享上下文系统 (Shared Context)

**需求描述**：
- 通过文件系统实现跨智能体通信
- 支持任务上下文文件（task-*-context.md）
- 支持任务输出文件（task-*-output.md）
- 支持任务产物目录（task-*-artifacts/）

**用户故事**：
```
作为一个智能体
我希望能够读取其他智能体的输出文件
这样我可以基于前序任务的成果继续工作，无需重复执行
```

**验收标准**：
- [ ] shared-context/ 目录自动创建
- [ ] 任务执行时自动写入 context 和 output 文件
- [ ] 后续任务可读取前序任务的 output
- [ ] 文件路径对智能体可见（通过工具描述）

#### 2.1.4 团队记忆系统 (Team Memory)

**需求描述**：
- 支持多团队组织（如"阿里达摩院"、"奥学教育"）
- 每个团队有独立的记忆目录结构
- 支持团队共享记忆和角色专属记忆
- 支持记忆文件自动更新（自我改进循环）

**用户故事**：
```
作为一个项目经理
我希望为团队配置角色记忆（pm.md, dev.md, test.md）
这样不同角色的智能体执行任务时能加载对应的经验和规范
```

**验收标准**：
- [ ] ~/.hermes/teams/ 目录结构
- [ ] 团队记忆文件（team-memory.md）
- [ ] 角色记忆文件（roles/pm.md 等）
- [ ] 团队文档目录（docs/）
- [ ] 记忆文件支持追加和更新操作
- [ ] Prompt Builder 自动加载相关记忆

#### 2.1.5 五层记忆系统

**需求描述**：
- L1 瞬时记忆：当前对话窗口（SessionDB）
- L2 工作记忆：当前任务相关文件
- L3 参考记忆：项目文档、技术规范
- L4 经验记忆：历史教训、常见问题
- L5 身份记忆：角色定义、行为准则

**验收标准**：
- [ ] 五层记忆目录结构创建
- [ ] 分层加载策略实现
- [ ] 自我改进循环（会话后更新 L4）
- [ ] 记忆检索按相关性排序

#### 2.1.6 Cron 定时任务增强

**需求描述**：
- 支持 Cron 任务绑定团队和角色
- 支持 Cron 输出自动沉淀到团队记忆
- 支持定时任务使用特定技能

**验收标准**：
- [ ] jobs.json 支持 team/role/skills 字段
- [ ] 定时任务执行后自动更新团队记忆
- [ ] 支持 output_template 配置

#### 2.1.7 智能体实时监控仪表板 (Agent Observability Dashboard)

**需求描述**：
基于 Vercel Workflow SDK 观测性仪表板设计风格，在 WebUI 中新增一个对所有智能体及其任务执行过程的全景监控画面。

**UI 设计风格**（参考 Vercel Workflow 仪表板）：

参考截图：
```
┌──────────────────────────────────────────────────────────────────────┐
│  generateBirthdayCard  wrun_01KP45XGBHRMT7H0JXXHKBEQS4  ● Completed   │
│  [View Logs] [...]                                                    │
│                                                                       │
│  Created    Completed    Duration    Expiry      Storage              │
│  2d ago     2d ago       1m 48s      in 28d      8 MB                 │
│                                                                       │
│  [Trace]  [Events]  [Streams]                                        │
│  ──────────────────────────────────────────────────────────────────  │
│                                                                       │
│  ── 0 ─── 10s ─── 20s ─── 30s ─── 40s ─── 50s ─── 1m ─── 1m10s ───  │
│                                                                       │
│  generateBirthdayCard  [Queued 200.03ms · Executed 1m 48s] ── 1m 48s │
│  ├─ generateI... ──────────────────────────────────────────          │
│  │  hook_01KP45XGJK16SW3BS6GGC5A04B  Waiting 1m 6s · Received 29.5s  │
│  │  ────────────────────────────────────────────── 1m 35s            │
│  │     sleep  Sleeping 20.77s ────── 20.77s                          │
│                                                                       │
│  [Search spans...]                                    [🔍] [-] [+]   │
└──────────────────────────────────────────────────────────────────────┘
```

**核心设计元素**（提取自 Vercel Workflow）：

| 元素 | Vercel 实现 | 本仪表板适配 |
|------|-------------|-------------|
| **背景色** | 纯黑 (#000) | 相同，保持深色主题一致性 |
| **顶部状态栏** | 白色文字 + 绿色状态圆点 | 智能体名称 + 来源 + 状态圆点 |
| **元数据行** | Created/Completed/Duration/Expiry/Storage | 开始时间/完成时间/耗时/Token 用量/存储 |
| **标签页** | Trace / Events / Streams | Trace / Events（简化版） |
| **时间轴** | 水平刻度条，带时间标记 | 相同，支持缩放 |
| **任务条** | 蓝色横条，显示任务名称和耗时 | 智能体任务跨度条，按角色着色 |
| **嵌套层级** | 缩进 + 竖线连接 | 父子任务缩进树，竖线连接 |
| **子跨度** | 灰色条纹 + 蓝色/橙色条 | 工具调用子跨度条 |
| **状态颜色** | 蓝色=完成，绿色=进行中，橙色=等待 | 相同 |
| **搜索框** | 顶部搜索栏 | 相同 |
| **缩放控制** | 右下角 +/- 按钮 | 相同 |
| **持续时间标签** | 右侧显示耗时 | 相同 |

**颜色方案**（基于 Vercel Workflow 仪表板实际截图）：

| 状态 | 颜色 | Hex | 用途 |
|------|------|-----|------|
| Completed / Done | 蓝色 | #3b82f6 | 任务完成（Vercel 蓝色任务条） |
| Executing / Running | 绿色 | #10b981 | 任务执行中（Vercel 绿色状态圆点） |
| Queued / Pending | 灰色条纹 | #4b5563 | 任务排队中（Vercel 灰色条纹） |
| Waiting | 橙色 | #f59e0b | 等待依赖（Vercel 橙色 sleep 条） |
| Failed / Error | 红色 | #ef4444 | 任务失败 |
| 背景 | 纯黑 | #000000 | 主背景（Vercel 纯黑） |
| 表面 | 深灰 | #111111 | 卡片/面板背景 |
| 边框 | 灰 | #1f2937 | 边框/分隔线 |
| 文字 | 白色 | #ffffff | 主文字 |
| 次要文字 | 灰 | #9ca3af | 次要信息 |
| 工具调用条 | 深蓝 | #1e3a5f | 工具执行跨度（Vercel hook/span） |

**核心功能**：

- **全局概览**：顶部统计面板（总智能体数、运行中、已完成、失败）
- **时间线追踪**：
  - 每个工作流（conversation）作为一个水平行
  - 任务以彩色条展示在时间轴上
  - 父子任务以缩进方式嵌套显示，竖线连接
  - 鼠标悬停显示任务详情（目标、角色、耗时、输出预览）
  - 右侧显示持续时间标签
- **智能体面板**：
  - 显示 Coordinator Agent 名称、来源 (cli/cron/feishu)、状态圆点
  - 显示派生的子智能体（Expert/Research/Code/Ops 等）
  - 每个智能体显示当前状态、角色、工具调用次数
- **工具调用跨度**：
  - 子任务条下方显示工具调用的耗时条
  - 工具名称 + 耗时显示（如 `sleep: 20.77s`）
  - 支持展开/折叠
- **事件流**：
  - Trace 事件时间线（类似 Vercel Events 标签）
  - 工具异常高亮显示（红色标记）
  - 点击事件可跳转到对应任务
- **筛选与搜索**：
  - 按来源筛选（cli/cron/feishu/telegram）
  - 按角色筛选（expert/research/code/ops）
  - 按状态筛选（pending/running/done/failed）
  - 全文搜索任务目标/输出
  - 时间范围选择器

**用户故事**：
```
作为一个项目经理
我希望看到一个类似 Vercel Workflow 的时间线仪表板
这样我可以一目了然地看到所有智能体在做什么、任务依赖关系、
每个任务耗时多长、是否有卡住或失败的任务
```

**验收标准**：
- [ ] 仪表板采用深色主题，与 Vercel Workflow 风格一致
- [ ] 顶部显示工作流名称、来源、状态圆点
- [ ] 元数据行显示开始时间、完成时间、耗时、Token 用量
- [ ] 时间线支持水平滚动和缩放
- [ ] 嵌套任务层级正确展示（最多 3 层），竖线连接
- [ ] 任务条显示名称、状态、持续时间标签
- [ ] 工具调用以子跨度条显示（深蓝色）
- [ ] 实时数据刷新（SSE 或 5 秒轮询）
- [ ] 鼠标悬停显示任务详情 tooltip
- [ ] 支持按来源/角色/状态筛选
- [ ] 支持搜索任务
- [ ] 工具异常高亮显示（红色）
- [ ] 响应式设计，适配不同屏幕

**技术实现**：
- **前端**：基于现有 hermes-webui Flask 模板，使用 CSS Grid + Flexbox 布局
- **时间线渲染**：使用纯 CSS 实现时间条（无需第三方库）
- **数据源**：
  - SessionDB（state.db）获取会话和任务记录
  - shared-context/ 目录获取任务状态和输出
  - HealthMonitor 获取智能体心跳状态
- **后端 API**：
  - `GET /api/agents/overview` — 全局概览统计
  - `GET /api/agents/timeline` — 时间线数据
  - `GET /api/agents/<agent_id>/spans` — 智能体任务跨度
  - `GET /api/agents/events` — 事件流

#### 2.1.8 WebUI 改造（其他页面）

**需求描述**：
基于现有 hermes-webui 架构，新增以下页面：

| 页面 | 功能 | 优先级 |
|------|------|--------|
| 智能体监控 | Vercel 风格实时观测仪表板 | P0 |
| 任务编排 | DAG 任务图 + 3 状态展示 | P0 |
| 团队记忆管理 | 团队/角色层次结构 | P1 |
| Cron 增强 | 团队绑定任务管理 | P1 |
| 技能中心增强 | 团队/角色感知 | P2 |

**验收标准**：
- [ ] 新增 API 路由（agents, tasks, teams）
- [ ] 新增前端页面（dashboard.html, tasks.html, team_memory.html）
- [ ] 导航栏新增菜单项
- [ ] 实时数据刷新（SSE 或轮询）

---

## 三、非功能需求

### 3.1 性能需求

| 指标 | 要求 |
|------|------|
| 并发子智能体 | 最多 5 个 |
| 任务状态查询延迟 | < 500ms |
| WebUI 页面加载时间 | < 2s |
| Cron 任务调度精度 | ± 60s |

### 3.2 兼容性需求

| 需求 | 说明 |
|------|------|
| 向后兼容 | 所有新功能可选，不影响现有 Hermes-Agent 用户 |
| Python 版本 | 3.11+ |
| 操作系统 | Linux / Windows / macOS |

### 3.3 安全需求

| 需求 | 说明 |
|------|------|
| 凭据隔离 | 子智能体不暴露父智能体 API Key |
| 工具权限 | 角色化工具集自动过滤危险工具 |
| 文件权限 | shared-context 仅允许任务相关智能体访问 |

---

## 四、技术架构

详见 [架构设计文档](architecture.md)

### 4.1 核心组件

| 组件 | 路径 | 状态 |
|------|------|------|
| Agent Factory | `src/agent/agent_factory.py` | 规划中 |
| Task Orchestrator | `src/agent/task_orchestrator.py` | 规划中 |
| Shared Context | `src/agent/shared_context.py` | 规划中 |
| Team Memory | `src/memory/team_memory.py` | 规划中 |
| Memory Loader | `src/memory/memory_loader.py` | 规划中 |
| Harness Manager | `src/context/harness.py` | 规划中 |
| Task Watcher | `src/monitoring/task_watcher.py` | 规划中 |
| Health Monitor | `src/monitoring/health_monitor.py` | 规划中 |

### 4.2 目录结构

```
CrazyAgentsManage/
├── docs/                       # 文档
│   ├── architecture.md         # 架构设计
│   ├── prd/                    # 产品需求
│   └── roadmap/                # 路线图
├── src/                        # 源代码
│   ├── core/                   # 核心组件
│   ├── agent/                  # 智能体相关
│   ├── tools/                  # 工具扩展
│   ├── memory/                 # 记忆系统
│   ├── context/                # 上下文管理
│   ├── scheduler/              # 调度器
│   ├── monitoring/             # 监控组件
│   ├── webui/                  # WebUI 扩展
│   ├── cli/                    # CLI 扩展
│   ├── gateway/                # Gateway 扩展
│   └── api/                    # API 扩展
├── tests/                      # 测试
├── config/                     # 配置示例
└── scripts/                    # 工具脚本
```

---

## 五、里程碑

详见 [路线图](roadmap/)

### 5.1 Phase 1: 基础架构

- Agent Factory
- Task Orchestrator
- Shared Context
- Delegate Tool 增强
- SessionDB tasks 表

### 5.2 Phase 2: 记忆系统

- 团队记忆目录
- 五层记忆加载
- 自我改进循环
- 团队记忆工具

### 5.3 Phase 3: Cron 增强

- Cron-Team 绑定
- 输出沉淀
- Cron Agent 角色

### 5.4 Phase 4: 上下文管理

- Harness Manager
- Task Watcher
- Health Monitor

### 5.5 Phase 5: WebUI 集成

- 任务编排视图
- 子代理监控
- 团队记忆管理
- CLI/WebUI 命令

---

## 六、风险与依赖

### 6.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 文件轮询延迟 | 任务状态同步延迟 | 使用文件系统事件监听替代轮询 |
| 上下文超限 | 多智能体 token 消耗过快 | Harness 自动压缩 + 分层记忆加载 |
| 并发冲突 | 多个智能体同时写文件 | 文件锁机制 |

### 6.2 外部依赖

| 依赖 | 说明 |
|------|------|
| Hermes-Agent | 核心依赖，所有功能基于现有 Hermes 架构 |
| OpenClaw | 参考框架，借鉴其模式和最佳实践 |
| hermes-webui | 前端依赖，WebUI 改造基于现有 Flask 架构 |

---

## 七、配置示例

### 7.1 config.yaml

```yaml
multi_agent:
  enabled: true
  max_concurrent_agents: 5
  max_depth: 3

  roles:
    expert:
      toolsets: [terminal, file, web, mcp]
      model: "anthropic/claude-sonnet-4-20250514"

    research:
      toolsets: [web, file]
      model: "openrouter/deepseek-chat-v3"

    code:
      toolsets: [terminal, file, code_execution]
      model: "anthropic/claude-opus-4.6"

    ops:
      toolsets: [terminal, file]
      model: "openrouter/claude-sonnet-4-20250514"

    cron:
      toolsets: [terminal, file, web, memory]
      model: "openrouter/claude-sonnet-4-20250514"

    team:
      toolsets: [file, memory, send_message]
      model: "openrouter/claude-sonnet-4-20250514"

  watcher:
    poll_interval: 5
    timeout: 3600

  health:
    interval: 30
    auto_recover: true

  memory:
    identity_file: "~/.hermes/identity.md"
    experience_dir: "~/.hermes/experiences/"
    reference_dir: "~/.hermes/references/"
    team_dir: "~/.hermes/teams/"
    auto_improve: true
```

---

## 八、验收标准总结

| 模块 | 核心验收标准 |
|------|-------------|
| Agent Factory | 6 种角色可创建、工具集自动分配、提示词自动注入 |
| Task Orchestrator | 3 状态协议、DAG 执行、文件持久化 |
| Shared Context | 跨智能体文件通信、context/output 自动写入 |
| Team Memory | 团队/角色目录、记忆文件读写、自动更新 |
| Five-Layer Memory | 分层加载、自我改进、相关性检索 |
| Cron Enhancement | team/role 绑定、输出沉淀到团队记忆 |
| WebUI | 5 个新页面、实时数据、DAG 可视化 |

---

*文档维护者：CrazyAgentsManage 团队*
*最后更新：2026-04-19*
