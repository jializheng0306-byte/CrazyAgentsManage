# CrazyAgentsManage 路线图 (Roadmap)

## 版本规划

### v0.1.0 — 基础架构 (预计 2-3 周)

**目标**：建立多智能体协作的核心基础设施

| 任务 | 模块 | 文件 | 优先级 | 状态 |
|------|------|------|--------|------|
| Agent Factory 核心 | agent | `src/agent/agent_factory.py` | P0 | 待开始 |
| Task Orchestrator | agent | `src/agent/task_orchestrator.py` | P0 | 待开始 |
| Shared Context Manager | agent | `src/agent/shared_context.py` | P0 | 待开始 |
| Delegate Tool 角色化增强 | tools | `tools/delegate_tool.py` | P0 | 待开始 |
| SessionDB tasks 表 | core | `hermes_state.py` | P1 | 待开始 |
| 配置 Schema 定义 | core | `config/schema.yaml` | P1 | 待开始 |
| 单元测试框架 | tests | `tests/test_agent_factory.py` | P2 | 待开始 |

**里程碑**：
- [ ] 可通过 `delegate_task(role="research", goal="...")` 创建角色化子智能体
- [ ] 任务状态自动持久化到 shared-context/task-*.json
- [ ] 子智能体自动获得角色专属工具集

---

### v0.2.0 — 记忆系统 (预计 2-3 周)

**目标**：实现五层分层记忆和团队记忆系统

| 任务 | 模块 | 文件 | 优先级 | 状态 |
|------|------|------|--------|------|
| 团队记忆目录初始化 | memory | `src/memory/team_memory.py` | P0 | 待开始 |
| 五层记忆加载器 | memory | `src/memory/memory_loader.py` | P0 | 待开始 |
| 自我改进循环 | memory | `src/memory/memory_improvement.py` | P0 | 待开始 |
| Prompt Builder 增强 | agent | `agent/prompt_builder.py` | P0 | 待开始 |
| 团队记忆 CLI 命令 | cli | `hermes_cli/commands.py` | P1 | 待开始 |
| 记忆检索优化 | memory | `src/memory/retrieval.py` | P2 | 待开始 |

**里程碑**：
- [ ] `~/.hermes/teams/` 目录自动创建
- [ ] Prompt Builder 自动加载 L1-L5 记忆
- [ ] 会话结束后自动更新经验记忆

---

### v0.3.0 — Cron 增强 (预计 1-2 周)

**目标**：定时任务与团队/角色绑定

| 任务 | 模块 | 文件 | 优先级 | 状态 |
|------|------|------|--------|------|
| Cron-Team 绑定 | scheduler | `cron/jobs.py` | P0 | 待开始 |
| Cron 输出沉淀到团队记忆 | scheduler | `cron/jobs.py` | P0 | 待开始 |
| Cron Agent 角色 | agent | `src/agent/agent_factory.py` | P1 | 待开始 |
| Cron 工具增强 | tools | `tools/cronjob_tools.py` | P1 | 待开始 |

**里程碑**：
- [ ] Cron 任务可配置 team/role/skills
- [ ] 定时任务输出自动追加到团队记忆

---

### v0.4.0 — 上下文管理 (预计 1-2 周)

**目标**：智能上下文管理和任务监控

| 任务 | 模块 | 文件 | 优先级 | 状态 |
|------|------|------|--------|------|
| Harness Manager | context | `src/context/harness.py` | P0 | 待开始 |
| Task Watcher | monitoring | `src/monitoring/task_watcher.py` | P0 | 待开始 |
| Health Monitor | monitoring | `src/monitoring/health_monitor.py` | P1 | 待开始 |
| 上下文压缩策略 | context | `agent/context_compressor.py` | P1 | 待开始 |

**里程碑**：
- [ ] 上下文接近上限时自动压缩
- [ ] 异步监控任务输出文件变化
- [ ] 智能体异常自动恢复

---

### v0.5.0 — WebUI 集成 (预计 3-4 周)

**目标**：WebUI 多智能体可视化（含 Vercel 风格监控仪表板 + 会话流水线索引）

| 任务 | 模块 | 文件 | 优先级 | 状态 |
|------|------|------|--------|------|
| 会话流水线索引 API | api | `api/sessions.py` | P0 | 待开始 |
| 会话统计 API | api | `api/sessions_stats.py` | P0 | 待开始 |
| 会话详情 API | api | `api/session_detail.py` | P0 | 待开始 |
| 会话流水线索引页面 | webui | `templates/sessions.html` | P0 | 待开始 |
| 会话列表 CSS | webui | `static/css/sessions.css` | P0 | 待开始 |
| 智能体监控仪表板 API | api | `api/agent_dashboard.py` | P0 | 待开始 |
| 时间线数据接口 | api | `api/timeline.py` | P0 | 待开始 |
| 事件流接口 | api | `api/events.py` | P0 | 待开始 |
| 监控仪表板页面 | webui | `templates/dashboard.html` | P0 | 已完成 |
| 时间线 CSS 组件 | webui | `static/css/timeline.css` | P0 | 已完成 |
| 任务编排 API | api | `api/task_orchestrator.py` | P1 | 待开始 |
| 团队记忆 API | api | `api/team_memory.py` | P1 | 待开始 |
| 任务编排页面 | webui | `templates/tasks.html` | P1 | 已完成 |
| 团队记忆页面 | webui | `templates/team_memory.html` | P1 | 已完成 |
| DAG 可视化 | webui | `static/js/dag_view.js` | P1 | 待开始 |
| 导航栏改造 | webui | `templates/index.html` | P1 | 待开始 |

**里程碑**：
- [ ] **会话流水线索引（P0 核心）**
  - [x] PRD 2.1.9 节已完成需求定义
  - [ ] 顶部统计面板：6个统计卡片（会话/代笔任务/状态记录/trace事件/日志注入/来源分布）
  - [ ] 左侧根会话索引列表（可滚动、虚拟滚动支持10000+条）
  - [ ] 会话卡片显示：标题 + 标签(异常/cron/手动) + 时间戳 + 工具摘要 + 状态
  - [ ] 右侧流水线详情面板（入口提示/高亮片段/基础结果/最终结果/系统结果/Token用量）
  - [ ] 底部会话画像（来源/时间/状态/工具列表）
  - [ ] 筛选功能：按来源(cli/cron/feishu)/状态/时间范围/标签筛选
  - [ ] 搜索功能：全文搜索 + 关键词高亮
  - [ ] 收藏夹功能（⭐标记重要会话）
  - [ ] 导出功能（Markdown/PDF/JSON/CSV）
- [ ] **监控仪表板（Vercel Workflow 风格）**
  - [x] 基础页面框架已完成
  - [ ] 后端API对接
  - [ ] 实时数据刷新
- [ ] **通用UI规范**
  - [ ] 纯黑背景主题 (#000000)
  - [ ] Vercel Workflow 配色方案
  - [ ] 响应式布局
  - [ ] 全中文界面

---

## 任务依赖关系

```
v0.1.0 (基础架构)
    ├── Agent Factory ──────┐
    ├── Task Orchestrator ──┤
    ├── Shared Context ─────┼──→ v0.2.0 (记忆系统)
    ├── Delegate Tool ──────┤       ├── 团队记忆
    └── SessionDB ──────────       ├── 五层记忆
                                    └── 自我改进
                                          │
                                    v0.3.0 (Cron 增强)
                                          ├── Cron-Team 绑定
                                          └── 输出沉淀
                                                │
                                    v0.4.0 (上下文管理)
                                          ├── Harness
                                          ├── Task Watcher
                                          └── Health Monitor
                                                │
                                    v0.5.0 (WebUI 集成)
                                          ├── 任务编排页面
                                          ├── 子代理监控页面
                                          └── 团队记忆页面
```

---

## 优先级定义

| 优先级 | 说明 |
|--------|------|
| **P0** | 核心功能，无此功能产品不可用 |
| **P1** | 重要功能，影响用户体验 |
| **P2** | 优化功能，可延后实现 |

---

## 进度跟踪

| 版本 | 计划开始 | 计划完成 | 实际开始 | 实际完成 | 状态 |
|------|----------|----------|----------|----------|------|
| v0.1.0 | 2026-04-19 | TBD | - | - | 未开始 |
| v0.2.0 | TBD | TBD | - | - | 未开始 |
| v0.3.0 | TBD | TBD | - | - | 未开始 |
| v0.4.0 | TBD | TBD | - | - | 未开始 |
| v0.5.0 | TBD | TBD | - | - | 未开始 |

---

## 风险与缓解

| 风险 | 影响版本 | 缓解措施 |
|------|----------|----------|
| Hermes-Agent API 变更 | 全部 | 保持与上游同步，使用适配层 |
| 文件系统性能瓶颈 | v0.1.0, v0.2.0 | 使用文件锁 + 异步 I/O |
| Token 预算超限 | v0.1.0, v0.4.0 | Harness 自动压缩 |
| WebUI 兼容性 | v0.5.0 | 渐进增强，保持向后兼容 |

---

*文档维护者：CrazyAgentsManage 团队*
*最后更新：2026-04-19*
