# Hermes-Agent 多智能体协作架构设计

## 一、OpenClaw 框架核心思想梳理

### 1.1 整体架构模式

OpenClaw 采用 **"1+5+6" 多智能体阵列**：
- **1 个主智能体**：直接与人交互，负责任务分解、委派、协调
- **5 个专业智能体**：claw（编程）、hawk（研究）、owl（安全审查）、panda（代码执行）、gator（系统运维）
- **6 个外部工具/系统**：浏览器、终端、文件系统、网络、MCP服务器、代码编辑器

核心设计哲学：
- **工具优先，模型次之**：工具设计比模型选择更重要
- **上下文隔离**：每个智能体拥有独立的上下文窗口
- **基于文件的协作**：通过 `shared-context/` 目录实现跨智能体通信
- **Harness 上下文管理**：自动压缩、精简对话历史
- **3 状态协议**：`pending → running → done` 标准化任务生命周期

### 1.2 五层记忆系统

```
L1 瞬时记忆 (Session Context)    — 当前对话窗口
L2 工作记忆 (Active Context)     — 当前任务相关文件
L3 参考记忆 (Reference Memory)   — 项目文档、技术规范
L4 经验记忆 (Experience Memory)  — 历史教训、常见问题
L5 身份记忆 (Identity Memory)    — 角色定义、行为准则
```

- **自我改进循环**：每次会话结束后自动更新 `MEMORY.md`，记录成功经验与失败教训
- **分层检索**：按层级递增加载上下文，避免一次性耗尽 token 预算

### 1.3 任务编排机制

- **Harness 管理**：每次启动智能体时从 `shared-context/` 加载任务上下文
- **自动压缩**：当对话接近 token 上限时自动压缩，生成紧凑摘要后继续
- **Task Watcher**：异步监控后台任务状态，轮询文件系统变化
- **Cron 调度**：定时触发智能体执行周期性任务（监控、报告生成）
- **心跳监控**：每 30 秒检测智能体进程状态，异常自动重启

### 1.4 通信协议

**3 状态协议**：
```
pending → running → done
```

**共享上下文目录 (`shared-context/`)**：
```
shared-context/
├── task-001.json        # 任务描述、状态、时间戳
├── task-001-context.md  # 任务上下文文件
├── task-001-output.md   # 任务输出
└── active-task.json     # 当前活跃任务指针
```

---

## 二、Hermes-Agent 现有架构分析

### 2.1 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| **AIAgent** | `run_agent.py` | 主对话循环，LLM API 调用，工具调度 |
| **Tool Registry** | `tools/registry.py` | 工具注册、schema 收集、分发机制 |
| **Delegate Tool** | `tools/delegate_tool.py` | 子智能体系统，隔离上下文，受限工具集 |
| **Gateway** | `gateway/run.py` | 多平台消息路由（Telegram/Discord/Slack/飞书） |
| **SessionDB** | `hermes_state.py` | SQLite 持久化，FTS5 全文搜索 |
| **Model Tools** | `model_tools.py` | 工具集解析，function call 处理 |
| **Terminal Tool** | `tools/terminal_tool.py` | 本地/Docker 终端执行环境 |
| **Prompt Builder** | `agent/prompt_builder.py` | 系统提示词组装 |
| **Context Compressor** | `agent/context_compressor.py` | 自动上下文压缩 |
| **Prompt Caching** | `agent/prompt_caching.py` | Anthropic prompt caching |
| **Skill System** | `agent/skill_commands.py` | 技能加载与管理 |
| **Skin Engine** | `hermes_cli/skin_engine.py` | 主题/皮肤引擎 |
| **Cron Scheduler** | `cron/scheduler.py` + `cron/jobs.py` | 定时任务调度 |

### 2.2 现有子智能体系统 (DelegateTool)

Hermes 已有**生产级子智能体架构**，但功能较为单一：

**能力矩阵**：
```
┌──────────────────────────────────────────────────────────┐
│  parent (depth=0)                                         │
│  ├── child-1 (depth=1, terminal+file+web)                │
│  ├── child-2 (depth=1, terminal+file+web)                │
│  └── child-3 (depth=1, terminal+file+web)                │
│      [MAX_DEPTH=2, 子智能体不能再委派]                     │
│      [BLOCKED: delegate_task, clarify, memory,            │
│       execute_code, send_message]                         │
└──────────────────────────────────────────────────────────┘
```

**关键约束**：
- 子智能体无对话记忆（`skip_context_files=True, skip_memory=True`）
- 最多 3 个并发子智能体（`MAX_CONCURRENT_CHILDREN=3`）
- 最大深度 2 层（父 → 子，不能递归委派）
- 子智能体无法调用 `execute_code`（仅能逐步推理）
- 独立的迭代预算（默认 50 次/子智能体）

### 2.3 现有工具系统

```
tools/registry.py  ← 中央注册中心
    ↑
    ├── file_tools.py         ← 文件读写搜索
    ├── web_tools.py          ← 网络搜索/抓取
    ├── terminal_tool.py      ← 终端执行 (local/docker)
    ├── browser_tool.py       ← 浏览器自动化
    ├── code_execution_tool.py← 代码执行沙箱
    ├── mcp_tool.py           ← MCP 客户端
    ├── delegate_tool.py      ← 子智能体委派
    ├── memory_tool.py        ← 记忆系统
    ├── skill_manager_tool.py ← 技能管理
    ├── cronjob_tools.py      ← 定时任务工具
    ├── send_message_tool.py  ← 消息发送
    └── ... (更多工具)

每个工具通过 registry.register() 注册:
  - schema: OpenAI function calling 格式
  - handler: 执行函数
  - check_fn: 可用性检测
  - requires_env: 环境变量依赖
```

### 2.4 现有会话与记忆

- **SessionDB**：SQLite + FTS5 全文搜索，支持跨会话搜索
- **MEMORY.md**：文本文件记忆系统，跨会话持久化
- **会话压缩**：`context_compressor.py` 自动压缩长对话
- **Prompt Caching**：Anthropic prompt caching 优化
- **Cron 系统**：`cron/jobs.py`（任务存储）+ `cron/scheduler.py`（调度执行）

### 2.5 现有 Cron 定时任务系统

Hermes 已有完整的定时任务调度能力：

```
~/.hermes/cron/
├── jobs.json           # 任务定义列表
└── output/             # 任务输出目录
    └── {job_id}/
        └── {timestamp}.md  # 每次执行结果

scheduler.py 核心逻辑:
  - tick() 每 60 秒检查到期任务
  - 文件锁防止并发执行
  - 支持 auto-deliver 推送结果到 Gateway 平台
  - SILENT_MARKER 标记无需推送的结果
```

### 2.6 现有 WebUI 架构 (基于阿里云部署的 hermes-webui)

当前 WebUI 已实现以下功能模块（基于 5 张截图分析）：

#### 2.6.1 会话画像面板
- 会话元数据：来源、模型、开始时间、状态、耗时
- 高频工具统计：终端执行、加载技能、读文件、搜文件、任务清单等
- 子代理树：展示由 `delegate_task` 派生的子会话层级
- 工具异常记录：技能未找到、连接失败等错误
- Trace 事件：会话级别的事件追踪

#### 2.6.2 会话流水线索引
- 全局统计：根会话数 (698)、子代理会话 (611)、总会话数 (1309)
- Trace 事件总数 (23315)、注入日志 (757)、来源分布 (224)
- 会话卡片：入口指令、调用技能、最终回复、会话结构、Token 统计
- 支持来源过滤：cli, cron, feishu 等多平台来源

#### 2.6.3 团队与角色管理
- 团队统计：团队数 (5)、角色编制 (35)、记忆文件 (61)、团队记忆 (14)
- 团队记忆：项目章程、项目总看板、审计报告、目录结构规范等
- 角色记忆：项目经理 (10份)、产品经理 (10份)、UI/UX设计 (5份)、Web前端 (7份)、Python后端 (4份)、功能测试 (6份)、DevOps (5份)、数据分析 (2份)
- 每个角色有独立的技能分配和经验沉淀

#### 2.6.4 定时任务管理
- 任务总数、运行中数量、下次运行倒计时
- 任务卡片：系统健康检查、晨间报告、记忆治理专项审计、每日项目精稿备份、中文社区日报、社区专题提炼周报
- 每个任务显示：调度规则（每小时/每天/每周）、下次运行时间、最后状态
- 支持查看详情和执行命令预览

#### 2.6.5 技能中心
- 技能统计：内置技能 (104)、自创技能 (135)、功能分类 (37)、技能总数 (239)
- 分类浏览：所有技能、自创技能、奥学教育、达摩院团队、数据与地图、飞书播报、通用工具、Hermes 运维、自媒体
- 技能卡片：技能名称、描述、所属分类、标签（内置/自创）
- 搜索与筛选功能

### 2.7 WebUI 与核心架构的关系

```
┌─────────────────────────────────────────────────────────────┐
│                    hermes-webui (Flask)                      │
│  /opt/hermes-webui/  (阿里云)  +  localhost  (Windows)       │
│                                                              │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   │
│  │ 会话画像   │ │ 流水线索引 │ │ 团队与角色 │ │ 定时任务   │   │
│  │ (agent)   │ │ (pipeline)│ │ (team)    │ │ (cron)    │   │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘   │
│  ┌───────────┐                                               │
│  │ 技能中心   │                                               │
│  │ (skills)  │                                               │
│  └───────────┘                                               │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP
┌────────────────────────▼────────────────────────────────────┐
│                    Hermes Agent (核心)                       │
│                                                              │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │ API Server    │  │ SessionDB     │  │ Cron System   │   │
│  │ (:8642)       │  │ (state.db)    │  │ (cron/)       │   │
│  └───────────────┘  └───────────────┘  └───────────────┘   │
│                                                              │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │ Skill System  │  │ Tool Registry │  │ Gateway       │   │
│  │ (~/.hermes/   │  │ (tools/)      │  │ (platforms/)  │   │
│  │  skills/)     │  │               │  │               │   │
│  └───────────────┘  └───────────────┘  └───────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## 三、Hermes-Agent 多智能体协作架构设计

### 3.1 总体架构

```
┌───────────────────────────────────────────────────────────────────┐
│                        用户交互层                                  │
│  CLI (prompt_toolkit) │ WebUI │ Gateway (Telegram/Discord/飞书)    │
└──────────────────────────────┬────────────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────────────┐
│                    主智能体 (Coordinator Agent)                    │
│                                                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐     │
│  │ AIAgent     │  │ Prompt       │  │ Context              │     │
│  │ run_        │  │ Builder      │  │ Compressor           │     │
│  │ conversation│  │ (system      │  │ (自动压缩)            │     │
│  │ ()          │  │  prompt)     │  │                      │     │
│  └──────┬──────┘  └──────────────┘  └──────────────────────┘     │
│         │                                                         │
│         ▼                                                         │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    工具调度层                                 │ │
│  │                                                             │ │
│  │  Tool Registry (central dispatch)                           │ │
│  │  ├── file / web / terminal / browser / MCP / ...           │ │
│  │  ├── delegate_task (子智能体委派)                           │ │
│  │  ├── memory (记忆读写)                                      │ │
│  │  ├── execute_code (代码沙箱)                                │ │
│  │  └── cronjob_tools (定时任务管理)                           │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│         ▼                                                         │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              多智能体编排层 (NEW)                             │ │
│  │                                                             │ │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   │ │
│  │  │ Expert    │ │ Research  │ │ Code      │ │ Ops       │   │ │
│  │  │ Agent     │ │ Agent     │ │ Agent     │ │ Agent     │   │ │
│  │  │ (专家)    │ │ (研究)    │ │ (编程)    │ │ (运维)    │   │ │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘   │ │
│  │                                                             │ │
│  │  ┌───────────────────────────────────────────────────────┐  │ │
│  │  │              Task Orchestrator (NEW)                   │  │ │
│  │  │  - 任务分解 / DAG 构建 / 依赖管理                      │  │ │
│  │  │  - 3 状态协议 (pending/running/done)                   │  │ │
│  │  │  - 共享上下文目录 (shared-context/)                    │  │ │
│  │  └───────────────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────────────┐
│                    持久化与记忆层                                  │
│                                                                   │
│  ┌──────────────────┐  ┌─────────────────────────────────────┐   │
│  │ SessionDB        │  │ 五层记忆系统 (NEW)                   │   │
│  │ (SQLite + FTS5)  │  │                                     │   │
│  │                  │  │ L1: 瞬时记忆 — 当前对话窗口          │   │
│  │ - 会话记录       │  │ L2: 工作记忆 — 当前任务文件          │   │
│  │ - 消息历史       │  │ L3: 参考记忆 — 项目文档/规范         │   │
│  │ - 全文搜索       │  │ L4: 经验记忆 — 历史教训/模式         │   │
│  │ - Token 统计     │  │ L5: 身份记忆 — 角色/行为准则         │   │
│  │ - 任务表 (NEW)   │  │                                     │   │
│  └──────────────────┘  └─────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────┐  ┌─────────────────────────────────────┐   │
│  │ Skill System     │  │ Shared Context Store                │   │
│  │ (技能注册)        │  │ (shared-context/ 目录)              │   │
│  │                  │  │                                     │   │
│  │ ~/.hermes/skills/│  │ - task-*.json (任务状态)            │   │
│  │ - 技能加载       │  │ - task-*-context.md (任务上下文)    │   │
│  │ - 动态注册工具   │  │ - task-*-output.md (任务输出)       │   │
│  │                  │  │ - active-task.json (活跃任务)       │   │
│  └──────────────────┘  └─────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────┐  ┌─────────────────────────────────────┐   │
│  │ Cron Scheduler   │  │ Team Memory Store                   │   │
│  │ (已有)           │  │ (团队记忆存储)                        │   │
│  │                  │  │                                     │   │
│  │ ~/.hermes/cron/  │  │ ~/.hermes/teams/                    │   │
│  │ - jobs.json      │  │ - {team_name}/                      │   │
│  │ - output/        │  │   ├── team-memory.md                │   │
│  │                  │  │   └── roles/                        │   │
│  │                  │  │       ├── pm.md                     │   │
│  │                  │  │       └── dev.md                    │   │
│  └──────────────────┘  └─────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
```

### 3.2 多智能体团队设计

#### 3.2.1 智能体角色定义

在现有 `delegate_tool.py` 基础上扩展，引入**专业化子智能体**：

| 角色 | 工具集 | 用途 | 现有基础 |
|------|--------|------|---------|
| **Coordinator** (主智能体) | 全部工具 | 任务分解、委派、协调、与用户交互 | AIAgent (已有) |
| **Expert Agent** (专家) | terminal, file, web, MCP | 复杂推理、调试、代码审查 | delegate_task (已有) |
| **Research Agent** (研究) | web, file | 网络搜索、信息收集、综述 | delegate_task (已有) |
| **Code Agent** (编程) | terminal, file, code_execution, browser | 代码编写、测试、调试 | delegate_task + execute_code |
| **Ops Agent** (运维) | terminal, file | 系统运维、部署、监控 | delegate_task (已有) |
| **Cron Agent** (定时) | terminal, file, web, memory | 定时任务执行、报告生成 | cron/ (已有) + delegate_task |
| **Team Agent** (团队) | file, memory, send_message | 团队记忆管理、角色协调 | team memory (NEW) |

#### 3.2.2 智能体创建工厂 (新增)

```python
# agent/agent_factory.py (新增)

from enum import Enum

class AgentRole(Enum):
    COORDINATOR = "coordinator"
    EXPERT = "expert"
    RESEARCH = "research"
    CODE = "code"
    OPS = "ops"
    CRON = "cron"
    TEAM = "team"

# 每个角色的工具集配置
ROLE_TOOLSETS = {
    AgentRole.EXPERT: ["terminal", "file", "web", "mcp"],
    AgentRole.RESEARCH: ["web", "file"],
    AgentRole.CODE: ["terminal", "file", "code_execution"],
    AgentRole.OPS: ["terminal", "file"],
    AgentRole.CRON: ["terminal", "file", "web", "memory"],
    AgentRole.TEAM: ["file", "memory", "send_message"],
}

# 每个角色的系统提示词模板
ROLE_PROMPTS = {
    AgentRole.EXPERT: "You are an expert analyst...",
    AgentRole.RESEARCH: "You are a research specialist...",
    AgentRole.CODE: "You are a coding expert...",
    AgentRole.OPS: "You are a system operations expert...",
    AgentRole.CRON: "You are a scheduled task executor...",
    AgentRole.TEAM: "You are a team coordinator managing shared memory...",
}

def create_agent_for_role(role, parent_agent, task_context):
    """根据角色创建配置好的子智能体"""
```

### 3.3 任务编排系统 (Task Orchestrator)

#### 3.3.1 3 状态协议

在现有 delegate_tool 的基础上，增强任务状态管理：

```python
# agent/task_orchestrator.py (新增)

from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path

class TaskState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"

@dataclass
class TaskDef:
    """任务定义"""
    id: str
    goal: str
    role: AgentRole
    state: TaskState = TaskState.PENDING
    context: str = ""
    dependencies: list = field(default_factory=list)
    output: str = ""
    created_at: float = 0.0
    started_at: float = 0.0
    completed_at: float = 0.0
```

#### 3.3.2 共享上下文目录

```
HERMES_HOME/
├── shared-context/
│   ├── tasks/
│   │   ├── task-001.json        # 任务元数据
│   │   ├── task-001-context.md  # 任务上下文
│   │   ├── task-001-output.md   # 任务输出
│   │   └── task-001-artifacts/  # 任务产物
│   ├── active-task.json         # 当前活跃任务
│   └── task-graph.json          # 任务依赖图
├── teams/                        # 团队记忆目录 (NEW)
│   ├── {team_name}/
│   │   ├── team-memory.md       # 团队共享记忆
│   │   ├── roles/               # 角色记忆目录
│   │   │   ├── pm.md            # 项目经理记忆
│   │   │   ├── dev.md           # 开发角色记忆
│   │   │   └── test.md          # 测试角色记忆
│   │   └── docs/                # 团队文档
│   │       ├── charter.md       # 团队章程
│   │       ├── specs.md         # 技术规范
│   │       └── audit.md         # 审计报告
│   └── default/                  # 默认团队
│       └── team-memory.md
```

#### 3.3.3 任务图 (DAG) 执行

```
task-001 (research) ──┐
                      ├──→ task-003 (code) ──→ task-005 (test)
task-002 (research) ──┘
                              │
task-004 (ops) ──────────────┘
```

**执行策略**：
1. **拓扑排序**：根据依赖关系确定执行顺序
2. **并行执行**：无依赖任务并行执行（利用现有 ThreadPoolExecutor）
3. **状态轮询**：监控任务状态变化（借鉴 OpenClaw Task Watcher 模式）
4. **失败重试**：失败任务可重试或降级

### 3.4 五层记忆系统设计

在现有 MEMORY.md 和 SessionDB 基础上，构建分层记忆：

```
┌────────────────────────────────────────────────────────────┐
│ L5 身份记忆 (Identity)                                      │
│ ~/.hermes/identity.md — 角色定义、行为准则、用户偏好         │
├────────────────────────────────────────────────────────────┤
│ L4 经验记忆 (Experience)                                    │
│ ~/.hermes/experiences/                                      │
│   ├── patterns.md — 常见模式与最佳实践                      │
│   ├── lessons.md — 历史教训与失败分析                       │
│   └── solutions.md — 已验证的解决方案                       │
├────────────────────────────────────────────────────────────┤
│ L3 参考记忆 (Reference)                                     │
│ ~/.hermes/references/                                       │
│   ├── api-docs.md — API 文档                                │
│   ├── project-specs.md — 项目规范                           │
│   └── architecture.md — 架构文档                            │
├────────────────────────────────────────────────────────────┤
│ L2 工作记忆 (Active)                                        │
│ 当前任务相关文件（由 Prompt Builder 动态加载）               │
│ - 编辑中的代码文件                                          │
│ - 当前项目结构                                              │
├────────────────────────────────────────────────────────────┤
│ L1 瞬时记忆 (Session)                                       │
│ SessionDB (SQLite) — 当前对话历史                           │
│ - 消息历史                                                  │
│ - 工具调用记录                                              │
│ - Token 统计                                                │
│ - 任务记录 (NEW)                                            │
└────────────────────────────────────────────────────────────┘
```

#### 3.4.1 团队记忆系统 (NEW)

基于现有 WebUI "团队与角色" 模块的 UI 模式，构建团队记忆系统：

```
团队记忆架构:
┌──────────────────────────────────────────────────────────────┐
│ 团队层 (Team Level)                                          │
│ ~/.hermes/teams/{team_name}/                                 │
│                                                              │
│  ├── team-memory.md           # 团队共享记忆（自动更新）      │
│  ├── team-charter.md          # 团队章程                      │
│  ├── team-specs.md            # 技术规范                      │
│  └── roles/                   # 角色记忆目录                  │
│      ├── pm.md                # 项目经理：需求分析、任务拆解  │
│      ├── product.md           # 产品经理：PRD编写、故事板    │
│      ├── uiux.md              # UI/UX设计：设计系统、交互稿  │
│      ├── frontend.md          # Web前端：Activity Feed、Agents│
│      ├── backend.md           # Python后端：API开发、Session │
│      ├── test.md              # 功能测试：三轮分享交流       │
│      ├── devops.md            # DevOps：CI/CD、Prometheus    │
│      └── data.md              # 数据分析：Excel表格分析      │
└──────────────────────────────────────────────────────────────┘

角色记忆内容:
  - 角色定义和职责
  - 常用技能列表（如：aooxe-data-query, aooxe-edu-development）
  - 项目经验沉淀
  - 最佳实践和规范
```

#### 3.4.2 自我改进循环 (NEW)

```python
# agent/memory_improvement.py (新增)

class SelfImprovementLoop:
    """会话结束后的自动记忆更新"""

    def on_session_end(self, session_result):
        """分析会话结果，更新经验记忆"""
        if session_result.success:
            self._extract_pattern(session_result)
        else:
            self._extract_lesson(session_result)

        self._update_memory_file()

    def update_team_memory(self, team_name, role, experience):
        """更新特定团队角色的记忆"""
        team_path = get_team_path(team_name)
        role_file = team_path / "roles" / f"{role}.md"
        append_experience(role_file, experience)
```

#### 3.4.3 记忆加载策略

在 `prompt_builder.py` 中集成记忆加载：

```python
def build_system_prompt_with_memory(session_db, task_context=None):
    """分层加载记忆"""
    parts = []

    # L5 始终加载 (身份)
    parts.append(load_identity())

    # L4 按需加载 (经验)
    if task_context:
        parts.append(load_relevant_experiences(task_context))

    # L3 按需加载 (参考)
    parts.append(load_references())

    # L2 动态加载 (工作记忆)
    parts.append(build_active_context())

    # L1 已有 (SessionDB 恢复)
    parts.append(session_db.get_system_prompt_snapshot())

    # 团队记忆 (NEW)
    if task_context and task_context.get("team"):
        parts.append(load_team_memory(task_context["team"]))

    return "\n".join(parts)
```

### 3.5 Cron 定时任务系统增强

现有 Cron 系统已很完善，主要增强方向：

#### 3.5.1 与多智能体集成

```python
# cron/scheduler.py 增强

# 现有: tick() 每 60 秒检查到期任务
# 增强: 到期任务可以委派给专门的 Cron Agent

def execute_cron_job(job):
    """执行定时任务"""
    # 1. 检查是否有团队分配
    if job.get("team"):
        # 委派给团队 Cron Agent
        return delegate_to_team_agent(job)

    # 2. 否则使用默认执行方式（原有逻辑）
    return execute_job_locally(job)
```

#### 3.5.2 Cron 任务与 Team 绑定

```yaml
# ~/.hermes/cron/jobs.json 增强字段

{
  "id": "daily-report",
  "command": "生成每日项目进度报告",
  "schedule": "0 7 * * *",
  "deliver": "origin",
  "team": "阿里达摩院",           # NEW: 绑定团队
  "role": "pm",                  # NEW: 执行角色
  "skills": ["ali-damo-academy-workflow"],  # 使用特定技能
  "output_template": "daily-report-template.md"  # NEW: 输出模板
}
```

#### 3.5.3 Cron 输出自动沉淀到团队记忆

```python
# cron/jobs.py 增强

def save_job_output_with_team_memory(job_id, output, team=None):
    """保存任务输出，并可选地沉淀到团队记忆"""
    # 1. 原有逻辑：保存到 ~/.hermes/cron/output/
    save_job_output(job_id, output)

    # 2. NEW: 如果绑定了团队，同时沉淀到团队记忆
    if team:
        team_path = get_team_path(team)
        append_to_team_memory(team_path, output)
```

### 3.6 上下文管理增强 (Harness)

在现有 `context_compressor.py` 基础上，引入 **Harness 模式**：

```python
# agent/harness.py (新增)

class HarnessContextManager:
    """智能上下文管理器"""

    def __init__(self, max_tokens, compression_threshold=0.85):
        self.max_tokens = max_tokens
        self.compression_threshold = compression_threshold

    def should_compact(self, current_tokens):
        """判断是否需要压缩"""
        return current_tokens / self.max_tokens > self.compression_threshold

    def compact(self, conversation, shared_context=None):
        """压缩对话历史"""
        # 1. 保留最近 N 条消息
        # 2. 压缩中间对话为摘要
        # 3. 注入 shared-context 相关信息
        # 4. 保留所有 reasoning 内容

    def inject_context(self, task_def):
        """从 shared-context/ 注入任务上下文"""
        context_file = get_shared_context_path(task_def.id)
        return load_context_file(context_file)
```

### 3.7 心跳与自愈 (借鉴 OpenClaw)

```python
# agent/health_monitor.py (新增)

class HealthMonitor:
    """智能体心跳监控"""

    def __init__(self, interval=30):
        self.interval = interval  # 30秒

    def check_health(self, agent):
        """检测智能体状态"""
        # 1. 检查进程是否存活
        # 2. 检查最后活跃时间
        # 3. 检查是否有未完成的任务

    def auto_recover(self, agent, task_context):
        """自动恢复"""
        # 1. 保存当前状态
        # 2. 重启智能体
        # 3. 从 shared-context 恢复任务
        # 4. 继续执行
```

### 3.8 任务监控器 (Task Watcher)

```python
# agent/task_watcher.py (新增)

class TaskWatcher:
    """异步任务监控"""

    def __init__(self, poll_interval=5):
        self.poll_interval = poll_interval
        self._watching = {}

    def watch_task(self, task_id, output_path, callback):
        """监控任务输出文件"""
        self._watching[task_id] = {
            "output_path": output_path,
            "callback": callback,
            "last_size": 0,
        }

    async def poll(self):
        """轮询文件系统变化"""
        for task_id, info in self._watching.items():
            current_size = get_file_size(info["output_path"])
            if current_size != info["last_size"]:
                info["last_size"] = current_size
                content = read_file_tail(info["output_path"])
                info["callback"](task_id, content)
```

---

## 四、与现有 Hermes 组件的集成点

### 4.1 与 AIAgent 集成

```
现有 AIAgent.run_conversation() 循环保持不变

新增: 在工具调度层增加 delegate_task 增强:
  - 支持角色化的子智能体创建
  - 支持任务图 (DAG) 执行
  - 支持 shared-context 注入
```

### 4.2 与 Tool Registry 集成

```
现有 registry.register() 机制保持不变

新增: 注册新的编排工具:
  - orchestrate_tasks: 任务图执行
  - check_task_status: 查询任务状态
  - manage_shared_context: 管理共享上下文
  - manage_team_memory: 管理团队记忆
```

### 4.3 与 SessionDB 集成

```
现有 SessionDB 保持不变

增强: 新增任务相关表:
  CREATE TABLE tasks (
      id TEXT PRIMARY KEY,
      state TEXT NOT NULL,
      goal TEXT,
      role TEXT,
      team TEXT,               # NEW: 所属团队
      parent_task_id TEXT,
      shared_context_path TEXT,
      created_at REAL,
      started_at REAL,
      completed_at REAL,
      result TEXT,
      error TEXT
  );
```

### 4.4 与 Gateway 集成

```
现有 Gateway 消息路由保持不变

增强: Gateway 可以:
  - 接收来自共享上下文目录的任务更新通知
  - 推送任务进度到用户聊天
  - 支持多用户协作场景
```

### 4.5 与 Cron 系统集成

```
现有 Cron 系统保持不变 (cron/scheduler.py + cron/jobs.py)

增强:
  - Cron 任务可绑定团队和角色
  - Cron 输出自动沉淀到团队记忆
  - Cron Agent 可作为专门的定时任务执行角色
  - 与 Task Orchestrator 联动（定时任务作为特殊任务类型）
```

### 4.6 与 Skill System 集成

```
现有 Skill 系统 (agent/skill_commands.py) 保持不变

增强:
  - 技能可以作为特定角色智能体的专属工具集
  - 技能按团队分类组织（如现有 WebUI 的"达摩院团队"分类）
  - 动态加载的专业能力包
  - 跨智能体共享的知识模块
  - 技能可以绑定到团队记忆（如"奥学教育"分类下的技能）
```

### 4.7 与 WebUI 集成

```
现有 WebUI 保持不变 (/opt/hermes-webui/)

增强: 新增页面模块:
  - 任务编排视图: DAG 任务图可视化 + 3 状态协议展示
  - 团队记忆管理: 团队/角色层次结构管理
  - 共享上下文浏览器: shared-context/ 目录浏览
  - 子代理实时监控: delegate_task 派生的子智能体状态
```

---

## 五、实施路线图 (调整版)

### Phase 1: 基础架构 (1-2 周)

| 任务 | 文件 | 说明 |
|------|------|------|
| Agent Factory | `agent/agent_factory.py` | 角色化智能体创建 |
| Task Orchestrator | `agent/task_orchestrator.py` | 3 状态协议 + 任务定义 |
| Shared Context | `agent/shared_context.py` | shared-context/ 目录管理 |
| 增强 Delegate Tool | `tools/delegate_tool.py` | 支持角色 + shared-context |
| 任务表 Schema | `hermes_state.py` | SessionDB 新增 tasks 表 |

### Phase 2: 记忆系统 (1-2 周)

| 任务 | 文件 | 说明 |
|------|------|------|
| 团队记忆目录结构 | `~/.hermes/teams/` | 团队/角色记忆目录 |
| 五层记忆加载 | `agent/memory_loader.py` | 分层加载逻辑 |
| 自我改进循环 | `agent/memory_improvement.py` | 会话后自动更新 |
| 团队记忆工具 | `tools/team_memory_tool.py` | 团队记忆读写工具 |
| Prompt Builder 增强 | `agent/prompt_builder.py` | 集成团队记忆加载 |

### Phase 3: Cron 增强 (1 周)

| 任务 | 文件 | 说明 |
|------|------|------|
| Cron-Team 绑定 | `cron/jobs.py` | 任务绑定团队/角色 |
| Cron 输出沉淀 | `cron/jobs.py` | 输出自动沉淀到团队记忆 |
| Cron Agent 角色 | `agent/agent_factory.py` | Cron 专用智能体角色 |
| Cron 工具增强 | `tools/cronjob_tools.py` | 团队感知定时任务管理 |

### Phase 4: 上下文管理 (1 周)

| 任务 | 文件 | 说明 |
|------|------|------|
| Harness Manager | `agent/harness.py` | 上下文压缩与注入 |
| Task Watcher | `agent/task_watcher.py` | 异步任务监控 |
| Health Monitor | `agent/health_monitor.py` | 心跳与自愈 |

### Phase 5: 集成与优化 (1-2 周)

| 任务 | 文件 | 说明 |
|------|------|------|
| Gateway 集成 | `gateway/run.py` | 任务进度推送 |
| CLI 命令 | `hermes_cli/commands.py` | /tasks /teams /status 等 |
| WebUI 改造 | `/opt/hermes-webui/` | 新增多智能体视图 |
| API 扩展 | `webui/api/` | 团队/任务 API |

---

## 六、关键技术决策

### 6.1 为什么基于文件协作而非内存共享？

| 方案 | 优点 | 缺点 |
|------|------|------|
| **内存共享** | 低延迟，实时 | 进程隔离时不可用，难以持久化 |
| **文件共享** | 跨进程，可持久化，易于调试 | 需要轮询，延迟较高 |

**决策**：采用文件共享（`shared-context/` + `teams/`），因为：
1. Hermes 支持多平台 Gateway（不同进程）
2. 文件可持久化，支持断点续传
3. 与现有文件工具系统天然集成
4. 与现有 WebUI 团队记忆模式一致

### 6.2 为什么保留现有 Delegate Tool 模式？

现有 `delegate_tool.py` 已是生产级实现：
- 线程安全（ThreadPoolExecutor）
- 上下文隔离（skip_context_files, skip_memory）
- 工具集控制（blocked tools, 受限工具集）
- 凭据路由（override provider/model）

**增强而非重写**：在现有基础上增加角色化、任务图、共享上下文。

### 6.3 为什么采用 3 状态协议？

| 协议 | 状态数 | 适用场景 |
|------|--------|---------|
| 2 状态 (pending/done) | 2 | 简单任务，无法区分运行中/已完成 |
| **3 状态 (pending/running/done)** | **3** | **通用场景，清晰区分生命周期** |
| 4 状态 (pending/running/done/failed) | 4 | 更精细，但增加复杂度 |

**决策**：3 状态协议是最佳平衡点。failed 状态可作为 done 的特殊标记。

### 6.4 为什么基于现有 WebUI 架构改造而非重写？

现有 hermes-webui 已实现：
- 会话画像（子代理树、工具异常、Trace 事件）
- 流水线索引（全局统计、会话卡片）
- 团队与角色（团队记忆、角色记忆）
- 定时任务（Cron 任务管理）
- 技能中心（技能分类、搜索）

**增强而非重写**：在现有 Flask + 原生 JS 架构上增加多智能体视图，复用现有 API 层。

---

## 七、配置示例

### 7.1 config.yaml

```yaml
# 多智能体配置
multi_agent:
  enabled: true
  max_concurrent_agents: 5
  max_depth: 3

  # 角色定义
  roles:
    expert:
      toolsets: [terminal, file, web, mcp]
      model: "anthropic/claude-sonnet-4-20250514"
      prompt_template: "You are an expert analyst..."

    research:
      toolsets: [web, file]
      model: "openrouter/deepseek-chat-v3"
      prompt_template: "You are a research specialist..."

    code:
      toolsets: [terminal, file, code_execution]
      model: "anthropic/claude-opus-4.6"
      prompt_template: "You are a coding expert..."

    ops:
      toolsets: [terminal, file]
      model: "openrouter/claude-sonnet-4-20250514"
      prompt_template: "You are a system operations expert..."

    cron:
      toolsets: [terminal, file, web, memory]
      model: "openrouter/claude-sonnet-4-20250514"
      prompt_template: "You are a scheduled task executor..."

    team:
      toolsets: [file, memory, send_message]
      model: "openrouter/claude-sonnet-4-20250514"
      prompt_template: "You are a team coordinator..."

  # 任务监控
  watcher:
    poll_interval: 5  # 秒
    timeout: 3600     # 超时时间

  # 心跳监控
  health:
    interval: 30      # 秒
    auto_recover: true

  # 记忆系统
  memory:
    identity_file: "~/.hermes/identity.md"
    experience_dir: "~/.hermes/experiences/"
    reference_dir: "~/.hermes/references/"
    team_dir: "~/.hermes/teams/"
    auto_improve: true
```

### 7.2 团队记忆目录结构示例

```
~/.hermes/teams/
├── default/
│   ├── team-memory.md       # 默认团队共享记忆
│   └── roles/
│       └── general.md       # 通用角色记忆
├── 阿里达摩院/
│   ├── team-memory.md       # 达摩院团队共享记忆
│   ├── team-charter.md      # 团队章程
│   ├── docs/
│   │   ├── project-specs.md # 项目规范
│   │   └── audit-report.md  # 审计报告
│   └── roles/
│       ├── pm.md            # 项目经理 (10份记忆)
│       ├── product.md       # 产品经理 (10份记忆)
│       ├── uiux.md          # UI/UX设计 (5份记忆)
│       ├── frontend.md      # Web前端 (7份记忆)
│       ├── backend.md       # Python后端 (4份记忆)
│       ├── test.md          # 功能测试 (6份记忆)
│       ├── devops.md        # DevOps (5份记忆)
│       └── data.md          # 数据分析 (2份记忆)
└── 奥学教育/
    ├── team-memory.md
    └── roles/
        └── general.md
```

---

## 八、Hermes WebUI 多智能体改造方案

基于现有 hermes-webui 架构（Flask + 原生 JS，已部署在阿里云 /opt/hermes-webui/ 和本地），以下是完整的 WebUI 改造方案：

### 8.1 新增页面模块

#### 8.1.1 任务编排视图 (Task Orchestration)

```
┌─────────────────────────────────────────────────────────────────┐
│  任务编排                        [刷新] [新建任务] [DAG视图]      │
├─────────────────────────────────────────────────────────────────┤
│  总任务: 12  │  运行中: 4  │  待执行: 5  │  已完成: 3           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  task-001    │───→│  task-003    │───→│  task-005    │      │
│  │  Research    │    │  Code        │    │  Test        │      │
│  │  running     │    │  pending     │    │  pending     │      │
│  │  Expert      │    │  Code Agent  │    │  Ops Agent   │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│        │                                                       │
│  ┌─────▼──────┐                                                │
│  │  task-002  │                                                │
│  │  Research  │                                                │
│  │  done      │                                                │
│  │  Research  │                                                │
│  │  Agent     │                                                │
│  └────────────┘                                                │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  任务详情: task-001                                            │
│  目标: 研究项目架构并生成技术方案                               │
│  角色: Expert Agent                                             │
│  状态: running (已运行 120s)                                    │
│  工具调用: read_file ×3, web_search ×2, terminal ×1            │
│  输出: [查看实时输出...]                                        │
└─────────────────────────────────────────────────────────────────┘
```

**后端 API 改造** (`/opt/hermes-webui/api/task_orchestrator.py`):
```python
# 新增路由
@app.route('/api/tasks', methods=['GET'])
def list_tasks():
    """获取所有任务列表"""

@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """获取任务详情"""

@app.route('/api/tasks', methods=['POST'])
def create_task():
    """创建新任务"""

@app.route('/api/tasks/<task_id>/output', methods=['GET'])
def get_task_output(task_id):
    """获取任务实时输出"""

@app.route('/api/task-graph', methods=['GET'])
def get_task_graph():
    """获取任务依赖图 (DAG)"""
```

#### 8.1.2 子代理实时监控 (Sub-Agent Monitor)

基于现有"会话画像"中已有的子代理树，增强为实时监控面板：

```
┌─────────────────────────────────────────────────────────────────┐
│  子代理实时监控                                      [自动刷新]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  根会话: Fixing Page Darkening Overlay Bug                      │
│  模型: gpt-5.3-codex  │  状态: active  │  耗时: 进行中           │
│                                                                 │
│  子代理树:                                                      │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  root (coordinator)                                       │ │
│  │  ├── child-1 (expert) ── running ── 读文件 ×3, 搜文件 ×2  │ │
│  │  ├── child-2 (research) ── done ── 120s                  │ │
│  │  │   └── grandchild-1 (code) ── [深度限制]               │ │
│  │  └── child-3 (ops) ── pending                            │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  工具异常: 3 条                                                  │
│  - Skill 'software-development:systematic-debugging' not found  │
│  - Skill 'delegation:browser-automation-playwright' not found   │
│  - Cannot connect to Camofox at localhost:9377                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**后端 API 改造** (`/opt/hermes-webui/api/agent_monitor.py`):
```python
# 新增路由
@app.route('/api/agents/active', methods=['GET'])
def list_active_agents():
    """获取所有活跃智能体"""

@app.route('/api/agents/<agent_id>/tree', methods=['GET'])
def get_agent_tree(agent_id):
    """获取智能体子代理树"""

@app.route('/api/agents/<agent_id>/errors', methods=['GET'])
def get_agent_errors(agent_id):
    """获取智能体工具异常"""
```

#### 8.1.3 团队记忆管理增强

基于现有"团队与角色"页面，增强为可交互的团队记忆管理：

```
┌─────────────────────────────────────────────────────────────────┐
│  团队记忆管理                  [新建团队] [全部展开] [全部收起]   │
├─────────────────────────────────────────────────────────────────┤
│  阿里达摩院 (核心开发)                                          │
│  团队记忆: 14份  │  角色编制: 10  │  角色记忆: 47份              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─── 团队记忆 (14份) ───────────────────────────────────────┐ │
│  │  [项目章程] [项目总看板] [审计报告] [目录结构规范]         │ │
│  │  [端口分配规范] [模型分配方案] [规范文档清单]              │ │
│  │  [会话续接指南] [项目整理报告] [项目选择调查]              │ │
│  │  [目录对比分析] [一期任务分派] [一期开发经验]              │ │
│  │  [项目状态模板]                                           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─── 角色记忆 (47份) ───────────────────────────────────────┐ │
│  │  项目经理 (10)  │  产品经理 (10)  │  UI/UX设计 (5)        │ │
│  │  Web前端 (7)    │  Python后端 (4) │  功能测试 (6)         │ │
│  │  DevOps (5)     │  数据分析 (2)   │                        │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─── 项目经理记忆 ──────────────────────────────────────────┐ │
│  │  [需求分析] [任务拆解] [PRD编写] [用户故事]                │ │
│  │  [项目跟踪流程] [WebUI完整解决方案]                        │ │
│  │                                                           │ │
│  │  最近更新的 2 条经验:                                      │ │
│  │  1. 项目跟踪流程：项目状态模板定义各阶段应遵循的状态文档格式 │ │
│  │  2. WebUI完整解决方案：完整功能测试报告，V2迭代升级验收    │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**后端 API 改造** (`/opt/hermes-webui/api/team_memory.py`):
```python
# 新增路由
@app.route('/api/teams', methods=['GET'])
def list_teams():
    """获取所有团队列表"""

@app.route('/api/teams/<team_name>', methods=['GET'])
def get_team(team_name):
    """获取团队详情（包含角色记忆）"""

@app.route('/api/teams/<team_name>/memory', methods=['PUT'])
def update_team_memory(team_name):
    """更新团队记忆"""

@app.route('/api/teams/<team_name>/roles/<role_name>', methods=['GET'])
def get_role_memory(team_name, role_name):
    """获取角色记忆"""

@app.route('/api/teams/<team_name>/roles/<role_name>', methods=['PUT'])
def update_role_memory(team_name, role_name):
    """更新角色记忆"""

@app.route('/api/teams/<team_name>/docs/<doc_name>', methods=['GET'])
def get_team_doc(team_name, doc_name):
    """获取团队文档"""
```

#### 8.1.4 Cron 定时任务增强视图

基于现有"定时任务"页面，增强为支持团队绑定的任务管理：

```
┌─────────────────────────────────────────────────────────────────┐
│  定时任务                                  [刷新] [新建任务]     │
├─────────────────────────────────────────────────────────────────┤
│  总任务数: 6  │  运行中: 6  │  下次运行: 39分钟后                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─── 系统健康检查 + 记忆增量整理 ───────────────────────────┐ │
│  │  团队: 阿里达摩院  │  角色: DevOps                          │ │
│  │  调度: 每小时 :00                                           │ │
│  │  下次运行: 04/19 17:00  │  最后状态: 成功                   │ │
│  │  命令: 你是 Hermes 系统守护进程...                          │ │
│  │  技能: health-check, memory-governance                     │ │
│  │  [点击查看详情]                                             │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─── 记忆治理专项审计 ──────────────────────────────────────┐ │
│  │  团队: 阿里达摩院  │  角色: 项目经理                        │ │
│  │  调度: 周一 08:30                                           │ │
│  │  下次运行: 04/20 08:30  │  最后状态: 成功                   │ │
│  │  命令: 基于预运行脚本输出，生成一份...                      │ │
│  │  技能: ali-damo-academy-workflow                           │ │
│  │  [点击查看详情]                                             │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**后端 API 改造** (`/opt/hermes-webui/api/cron.py` 增强):
```python
# 增强现有 cron API
@app.route('/api/cron/jobs', methods=['GET'])
def list_cron_jobs():
    """获取定时任务列表（含团队绑定信息）"""

@app.route('/api/cron/jobs/<job_id>', methods=['GET'])
def get_cron_job(job_id):
    """获取定时任务详情"""

@app.route('/api/cron/jobs', methods=['POST'])
def create_cron_job():
    """创建定时任务（支持团队绑定）"""
```

#### 8.1.5 技能中心增强

基于现有"技能中心"页面，增强为团队/角色感知的技能管理：

```
┌─────────────────────────────────────────────────────────────────┐
│  技能中心                                                       │
│  239个技能 · 内置104 · 自创135 · 37个功能分类                     │
├─────────────────────────────────────────────────────────────────┤
│  [搜索技能名称或描述...]     [全部239] [内置104] [自创135]        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  类别筛选:                                                       │
│  ┌─── 奥学教育 (4) ──────────────────────────────────────────┐ │
│  │  [aooxe-data-query] [aooxe-edu-development]                │ │
│  │  [aooxe-edu-pack-deploy] [aooxe-feishu-query]              │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─── 达摩院团队 (10) ───────────────────────────────────────┐ │
│  │  [ali-damo-academy-acceptance-workflow]                    │ │
│  │  [ali-damo-academy-channel-directory]                      │ │
│  │  [ali-damo-academy-directory-structure]                    │ │
│  │  [ali-damo-academy-inter-team-knowledge-sharing]           │ │
│  │  [ali-damo-academy-port-allocation]                        │ │
│  │  [ali-damo-academy-team-sharing]                           │ │
│  │  [ali-damo-academy-workflow]                               │ │
│  │  [ali-damo-project-development-workflow]                   │ │
│  │  [project-audit-and-standardization]                       │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─── 数据与地图 (4) ────────────────────────────────────────┐ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 WebUI 前端架构改造

#### 8.2.1 新增前端页面

```
/opt/hermes-webui/templates/
├── index.html              # 主页面（已有）
├── chat.html               # 聊天界面（已有）
├── files.html              # 文件浏览器（已有）
├── settings.html           # 设置页面（已有）
│
├── tasks.html              # NEW: 任务编排视图
├── agent_monitor.html      # NEW: 子代理实时监控
├── team_memory.html        # NEW: 团队记忆管理
├── cron_enhanced.html      # NEW: 增强定时任务（可选）
└── skills_enhanced.html    # NEW: 增强技能中心（可选）

/opt/hermes-webui/static/js/
├── app.js                  # 主应用 JS（已有）
│
├── task_orchestrator.js    # NEW: 任务编排前端逻辑
├── agent_monitor.js        # NEW: 子代理监控前端逻辑
├── team_memory.js          # NEW: 团队记忆前端逻辑
└── dag_view.js             # NEW: DAG 图可视化
```

#### 8.2.2 导航栏改造

```
现有导航栏:
  [概览] [Agent] [文件] [设置]

改造后:
  [概览] [Agent] [任务] [技能] [图谱] [流水线] [告警] [Token]
  
  新增:
  - [任务] → 任务编排视图 (tasks.html)
  - [图谱] → 团队记忆图谱 (team_memory.html)
  - [流水线] → 会话流水线索引 (已有)
  - [告警] → 工具异常监控 (agent_monitor.html 的子功能)
```

### 8.3 WebUI 后端 API 改造

#### 8.3.1 新增 API 路由文件

```
/opt/hermes-webui/api/
├── __init__.py             # 已有
├── chat.py                 # 聊天 API（已有）
├── files.py                # 文件 API（已有）
├── sessions.py             # 会话 API（已有）
├── settings.py             # 设置 API（已有）
│
├── task_orchestrator.py    # NEW: 任务编排 API
├── agent_monitor.py        # NEW: 子代理监控 API
├── team_memory.py          # NEW: 团队记忆 API
├── cron_enhanced.py        # NEW: Cron 增强 API
└── skills_enhanced.py      # NEW: 技能增强 API
```

#### 8.3.2 核心 API 实现

```python
# /opt/hermes-webui/api/task_orchestrator.py

import json
import os
from pathlib import Path
from flask import Blueprint, request, jsonify
from hermes_constants import get_hermes_home

task_bp = Blueprint('tasks', __name__)

HERMES_HOME = get_hermes_home()
TASKS_DIR = HERMES_HOME / "shared-context" / "tasks"

@task_bp.route('/api/tasks', methods=['GET'])
def list_tasks():
    """获取所有任务列表"""
    tasks = []
    if TASKS_DIR.exists():
        for task_file in TASKS_DIR.glob("task-*.json"):
            with open(task_file) as f:
                task = json.load(f)
                tasks.append(task)
    return jsonify({
        "tasks": tasks,
        "total": len(tasks),
        "by_state": _count_by_state(tasks)
    })

@task_bp.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """获取任务详情 + 实时输出"""
    task_file = TASKS_DIR / f"{task_id}.json"
    output_file = TASKS_DIR / f"{task_id}-output.md"

    task = json.loads(task_file.read_text()) if task_file.exists() else None
    output = output_file.read_text() if output_file.exists() else ""

    return jsonify({
        "task": task,
        "output": output,
        "output_size": len(output) if output else 0
    })

@task_bp.route('/api/task-graph', methods=['GET'])
def get_task_graph():
    """获取任务依赖图"""
    graph_file = HERMES_HOME / "shared-context" / "task-graph.json"
    if graph_file.exists():
        return jsonify(json.loads(graph_file.read_text()))
    return jsonify({"nodes": [], "edges": []})

def _count_by_state(tasks):
    states = {"pending": 0, "running": 0, "done": 0, "failed": 0}
    for task in tasks:
        state = task.get("state", "pending")
        if state in states:
            states[state] += 1
    return states
```

### 8.4 WebUI 与核心架构的数据流

```
┌─────────────────────────────────────────────────────────────────┐
│                    用户操作 WebUI                                │
│  [新建任务] [查看团队记忆] [监控子代理] [管理Cron任务]           │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP API
┌──────────────────────────────▼──────────────────────────────────┐
│              WebUI Backend (Flask)                              │
│  /opt/hermes-webui/api/                                         │
│                                                              │
│  task_orchestrator.py  ←→  shared-context/                     │
│  team_memory.py        ←→  ~/.hermes/teams/                    │
│  agent_monitor.py      ←→  SessionDB (state.db)               │
│  cron_enhanced.py      ←→  ~/.hermes/cron/                     │
└──────────────────────────────┬──────────────────────────────────┘
                               │ 文件读写 + SQLite
┌──────────────────────────────▼──────────────────────────────────┐
│              Hermes Agent 核心                                    │
│                                                              │
│  Task Orchestrator    ←→  shared-context/ (任务文件)            │
│  Team Memory Tool     ←→  ~/.hermes/teams/ (团队记忆)           │
│  Delegate Tool        ←→  SessionDB (子会话记录)                │
│  Cron Scheduler       ←→  ~/.hermes/cron/ (定时任务)            │
│  AIAgent              ←→  LLM API (智能体执行)                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.5 WebUI 改造实施步骤

#### 步骤 1: 后端 API 扩展 (1-2 天)

```bash
# 在服务器上
cd /opt/hermes-webui/api/

# 新建 API 文件
touch task_orchestrator.py
touch agent_monitor.py
touch team_memory.py

# 在 app.py 中注册新蓝图
```

#### 步骤 2: 前端页面开发 (2-3 天)

```bash
cd /opt/hermes-webui/templates/

# 新建 HTML 模板
touch tasks.html
touch agent_monitor.html
touch team_memory.html

# 在 index.html 导航栏添加新链接
```

#### 步骤 3: JavaScript 前端逻辑 (2-3 天)

```bash
cd /opt/hermes-webui/static/js/

# 新建 JS 文件
touch task_orchestrator.js
touch agent_monitor.js
touch team_memory.js
touch dag_view.js
```

#### 步骤 4: 与核心架构集成 (1-2 天)

```bash
# 在 hermes-agent 代码库中
# 1. 确保 shared-context/ 目录结构正确
# 2. 确保 ~/.hermes/teams/ 目录结构正确
# 3. 增强 delegate_tool.py 支持角色化
# 4. 增强 cron/jobs.py 支持团队绑定
```

#### 步骤 5: 测试与部署 (1-2 天)

```bash
# 在服务器上
systemctl restart hermes-webui

# 验证 API
curl http://localhost:8080/api/tasks
curl http://localhost:8080/api/teams
curl http://localhost:8080/api/agents/active
```

---

## 九、总结

本架构设计的核心思想是**在 Hermes-Agent 现有的生产级基础上**，借鉴 OpenClaw 框架经过验证的模式，并充分利用现有 WebUI 的 UI 模式：

### 9.1 继承现有

| 组件 | 状态 | 增强方向 |
|------|------|---------|
| AIAgent | 已有 | 支持角色化子智能体创建 |
| Tool Registry | 已有 | 注册新编排工具 |
| Delegate Tool | 已有 | 支持角色 + shared-context |
| SessionDB | 已有 | 新增 tasks 表 |
| Skill System | 已有 | 团队/角色感知技能加载 |
| Cron System | 已有 | 团队绑定 + 输出沉淀 |
| WebUI (会话画像) | 已有 | 增强为子代理实时监控 |
| WebUI (流水线索引) | 已有 | 任务可视化集成 |
| WebUI (团队与角色) | 已有 | 增强为可交互团队记忆管理 |
| WebUI (定时任务) | 已有 | 增强为团队绑定任务管理 |
| WebUI (技能中心) | 已有 | 增强为团队/角色感知 |

### 9.2 增强扩展

- **角色化智能体**：Expert/Research/Code/Ops/Cron/Team 6 种专业角色
- **任务编排**：DAG 任务图 + 3 状态协议 + 共享上下文
- **五层记忆**：在现有 MEMORY.md + SessionDB 基础上分层扩展
- **团队记忆**：基于现有 WebUI "团队与角色" 模式构建
- **Cron 增强**：团队绑定 + 输出自动沉淀到团队记忆

### 9.3 新增组件

- **Task Orchestrator**：任务图执行引擎
- **Harness Manager**：上下文压缩与共享上下文注入
- **Task Watcher**：异步任务监控
- **Health Monitor**：心跳与自愈
- **Team Memory Tool**：团队记忆读写工具
- **WebUI 新页面**：任务编排、子代理监控、团队记忆管理

### 9.4 关键设计原则

- **向后兼容**：所有新功能都是可选的，不影响现有用户
- **渐进式**：Phase 1-5 分阶段实施，每阶段可独立使用
- **基于文件**：利用文件系统实现跨进程、跨平台的协作
- **配置驱动**：所有角色、工具集、模型均可通过 config.yaml 配置
- **UI 驱动**：充分利用现有 WebUI 的 UI 模式，增强而非重写
