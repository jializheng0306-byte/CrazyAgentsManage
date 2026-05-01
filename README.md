# CrazyAgentsManage

> 以 HermesAgent 为宿主的 FlowMind 运营编排系统

## 项目概述

CrazyAgentsManage 当前的规范性定位是：

- `HermesAgent` 运行时宿主
- `FlowMind` 下游治理真值层
- `CrazyAgentsManage` 运营编排、观测、协作与 operator product 层

仓库里仍然保留多智能体协作、共享上下文、任务编排等能力，但它们不再是唯一产品叙事。

当前核心能力包括：

- **角色化智能体**：6 种专业角色（Expert/Research/Code/Ops/Cron/Team）
- **任务编排**：DAG 任务图 + 3 状态协议（pending → running → done）
- **共享上下文**：基于文件的跨智能体通信（shared-context/）
- **团队记忆**：多层级团队/角色记忆系统（~/.hermes/teams/）
- **五层记忆**：分层记忆加载 + 自我改进循环
- **Cron 增强**：定时任务与团队/角色绑定

## 快速开始

### 前置条件

- Python 3.11+
- Hermes-Agent（已安装并配置）

### 安装

```bash
# 克隆仓库
git clone https://github.com/jializheng0306-byte/CrazyAgentsManage.git
cd CrazyAgentsManage

# 安装依赖（与 Hermes-Agent 共享）
pip install -r requirements.txt
```

### 配置

```yaml
# ~/.hermes/config.yaml

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
```

## 文档

| 文档 | 说明 |
|------|------|
| [架构设计](docs/architecture.md) | 完整的多智能体协作架构设计 |
| [PRD 体系说明](docs/prd/README.md) | 当前生效的 PRD 分层入口 |
| [联合产品镜像基线](docs/roadmap/HermesAgent-FlowMind-联合产品功能基线-2026-04-30.md) | Crazy 侧镜像的联合产品主线 |
| [执行路线图](docs/roadmap/prd-execution-roadmap.md) | 当前生效的执行路线图 |

## 项目结构

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

## 核心功能

### 1. 角色化智能体

```python
# 创建研究角色子智能体
result = delegate_task(
    role="research",
    goal="研究项目架构并生成技术方案",
    context="当前项目使用 Flask + SQLite..."
)
```

### 2. 任务编排

```
task-001 (research) ──┐
                      ├──→ task-003 (code) ──→ task-005 (test)
task-002 (research) ──┘
```

### 3. 团队记忆

```
~/.hermes/teams/阿里达摩院/
├── team-memory.md       # 团队共享记忆
├── docs/                # 团队文档
│   ├── charter.md
│   └── specs.md
└── roles/               # 角色记忆
    ├── pm.md            # 项目经理
    ├── dev.md           # 开发者
    └── test.md          # 测试工程师
```

## 开发指南

### 添加新角色

1. 在 `src/agent/agent_factory.py` 中定义角色
2. 配置工具集和提示词模板
3. 在 config.yaml 中添加角色配置

### 添加新工具

1. 在 `src/tools/` 中创建工具文件
2. 使用 `registry.register()` 注册工具
3. 更新角色工具集配置

## 路线图

当前活跃路线图详见 [执行路线图](docs/roadmap/prd-execution-roadmap.md)

旧路线图 [docs/roadmap/roadmap.md](docs/roadmap/roadmap.md) 现在更适合作为历史能力清单，而不是活跃实施顺序。

- **v0.1.0**：基础架构（Agent Factory, Task Orchestrator, Shared Context）
- **v0.2.0**：记忆系统（团队记忆、五层记忆、自我改进）
- **v0.3.0**：Cron 增强（团队绑定、输出沉淀）
- **v0.4.0**：上下文管理（Harness, Task Watcher, Health Monitor）
- **v0.5.0**：WebUI 集成（任务编排、子代理监控、团队记忆）

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

---

*基于 Hermes-Agent 和 OpenClaw 框架设计*
