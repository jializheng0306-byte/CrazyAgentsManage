# CrazyAgentsManage

> 一个以 HermesAgent 为宿主的 FlowMind 运营产品

## 产品定位

CrazyAgentsManage 是**一个以 HermesAgent 为宿主的 FlowMind 运营产品**，负责为 AI Agent 运行系统提供运行时可观测性、运营对象管理和治理闭环执行能力。

- **HermesAgent** 是运行时宿主与运营执行面
- **FlowMind** 是治理引擎与规范真相层
- **CrazyAgentsManage** 是产品层，负责让运行态可见、让运营对象可管理、让治理闭环可执行

## 一级信息架构

| 分区 | 职责 | 入口 |
|------|------|------|
| **Overview** | 顶层系统健康概览 + 运营注意力聚合 | `/overview` |
| **Runtime** | Session 流水线 / Trace / Token / 延迟 / 异常 | `/runtime` |
| **Operations** | Roles / Skills / Team Memory / Cron / Alerts | `/operations` |
| **Governance** | Candidate / Truth / Review / Drift 状态 | `/governance` |
| **Collaboration** | Handoff / Closeout / 证据链 | `/collaboration` |

## 快速开始

### 前置条件

- Python 3.11+
- Hermes-Agent（已安装并配置）

### 安装

```bash
# 克隆仓库
git clone https://github.com/jializheng0306-byte/CrazyAgentsManage.git
cd CrazyAgentsManage

# 安装依赖
pip install -r requirements.txt
```

### 启动 WebUI

```bash
cd src/webui
python app.py
# 访问 http://localhost:5002/manage/overview
```

## 文档

| 文档 | 说明 |
|------|------|
| [母 PRD](docs/prd/hermesagent-hosted-flowmind-product-foundation.md) | 上位产品基础文档（规范性定位） |
| [技术实现 PRD](docs/prd/technical-implementation-prd.md) | 技术实施规范 |
| [运营实现 PRD](docs/prd/operations-implementation-prd.md) | 运营面实施规范 |
| [路线图](docs/roadmap/roadmap.md) | 版本规划和实施路线 |
| [总任务计划](docs/roadmap/master-task-plan.md) | 统一任务计划文档 |

## 项目结构

```
CrazyAgentsManage/
├── docs/                       # 文档（仓库事实层）
│   ├── prd/                    # 产品需求（母PRD + 拆分PRD）
│   ├── 02-engineering/harness/ # Harness 机制文档
│   └── roadmap/                # 路线图 + 任务计划
├── src/                        # 源代码
│   ├── agent/                  # 智能体工厂 + 任务编排 + 上下文压缩
│   ├── context/                # Harness Manager（上下文生命周期）
│   ├── memory/                 # 五层记忆系统 + 团队记忆 + 检索
│   ├── monitoring/             # Task Watcher + Health Monitor
│   ├── tools/                  # 委派工具 + Cron 工具
│   ├── webui/                  # Flask WebUI（五大 IA 聚合页）
│   │   ├── api.py              # 全部 API 端点
│   │   ├── templates/          # Jinja2 模板
│   │   ├── static/css/         # Vercel Workflow 风格纯黑主题
│   │   └── static/js/          # 页面逻辑
│   ├── config/                 # 配置 Schema
│   ├── cron/                   # Cron 调度器
│   └── hermes_cli/             # CLI 命令
├── tests/                      # 测试
├── harness/                    # Harness 持久化学习层
├── scripts/                    # Harness 运行时脚本
└── requirements.txt            # Python 依赖清单
```

## 核心能力

以下能力作为从属能力支撑上述五个一级信息架构：

### 运行时可观测性 (Runtime)

- Session 流水线索引：根会话索引 + 详情面板 + 会话画像
- Vercel Trace 风格监控仪表板：嵌套树视图 + 实时刷新
- Token 监控与成本追踪
- Agent 健康监控与自动恢复

### 运营对象管理 (Operations)

- 角色化智能体（7 种角色）：Coordinator / Expert / Research / Code / Ops / Cron / Team
- DAG 任务编排：3 状态协议 + 依赖注入 + 自动压缩
- 团队记忆系统：多团队/多角色分层记忆
- 定时任务管理：Cron 与团队/角色绑定
- 技能中心与告警管理

### 治理闭环 (Governance)

- 架构可视化页面：产品哲学 / 产品架构 / 技术架构
- Harness 机制：上下文快照 / Token 预算分配 / 自动压缩
- 协作证据链：Handoff packet / Closeout record

### 协作层 (Collaboration)

- Codex ↔ HermesAgent 协作工作流
- 任务编排可视化（DAG 图）
- 团队记忆 Web 管理

## 开发指南

### 添加新角色

1. 在 `src/agent/agent_factory.py` 中定义 `AgentRole` 枚举值
2. 配置工具集和提示词模板
3. 在 `config/schema.yaml` 中添加角色配置

### 添加新 API 端点

1. 在 `src/webui/api.py` 中添加路由函数
2. 使用 `_db_query()` 或 `_remote_query()` 访问数据
3. 对应的前端 JS 文件中添加 fetch 调用

### 添加新页面

1. 在 `src/webui/templates/` 创建 Jinja2 模板
2. 包含 `{% include 'ia-nav.html' %}` 并设置 `active_nav`
3. 创建对应的 CSS (`static/css/`) 和 JS (`static/js/`)
4. 在 `src/webui/app.py` 中注册路由

## 测试

```bash
cd src/webui
python -m pytest ../../tests/test_sprint4.py -v
```

## 路线图

详见 [路线图](docs/roadmap/roadmap.md)

| 版本 | 内容 | 状态 |
|------|------|------|
| v0.1.0 | 基础架构（Agent Factory, Task Orchestrator, Shared Context） | 已完成 |
| v0.2.0 | 记忆系统（团队记忆、五层记忆、自我改进） | 已完成 |
| v0.3.0 | Cron 增强（团队绑定、输出沉淀） | 已完成 |
| v0.4.0 | 上下文管理（Harness Manager, Task Watcher, 上下文压缩） | 已完成 |
| v0.5.0 | WebUI 集成（会话流水线索引、监控仪表板、DAG 可视化） | 已完成 |

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

---

*基于 Hermes-Agent 运行时 · FlowMind 治理引擎 · Codex ↔ HermesAgent 协作模型*
