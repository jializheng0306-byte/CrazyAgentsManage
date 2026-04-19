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

**目标**：WebUI 多智能体可视化（含 Vercel 风格监控仪表板）

| 任务 | 模块 | 文件 | 优先级 | 状态 |
|------|------|------|--------|------|
| 智能体监控仪表板 API | api | `api/agent_dashboard.py` | P0 | 待开始 |
| 时间线数据接口 | api | `api/timeline.py` | P0 | 待开始 |
| 事件流接口 | api | `api/events.py` | P0 | 待开始 |
| 监控仪表板页面 | webui | `templates/dashboard.html` | P0 | 待开始 |
| 时间线 CSS 组件 | webui | `static/css/timeline.css` | P0 | 待开始 |
| 任务编排 API | api | `api/task_orchestrator.py` | P0 | 待开始 |
| 团队记忆 API | api | `api/team_memory.py` | P0 | 待开始 |
| 任务编排页面 | webui | `templates/tasks.html` | P1 | 待开始 |
| 团队记忆页面 | webui | `templates/team_memory.html` | P1 | 待开始 |
| DAG 可视化 | webui | `static/js/dag_view.js` | P1 | 待开始 |
| 导航栏改造 | webui | `templates/index.html` | P1 | 待开始 |

**里程碑**：
- [ ] WebUI 新增"监控"菜单项
- [ ] 深色主题仪表板（纯黑背景 #000）
- [ ] 顶部状态栏：工作流名称 + 来源 + 状态圆点（参考 Vercel）
- [ ] 元数据行：开始时间/完成时间/耗时/Token 用量（参考 Vercel Created/Completed/Duration）
- [ ] Trace/Events 标签页（参考 Vercel）
- [ ] 搜索框 + 时间轴刻度（参考 Vercel Search spans）
- [ ] 时间线视图（水平刻度 + 彩色任务条）
- [ ] 嵌套任务层级（竖线连接，最多 3 层，参考 Vercel 缩进树）
- [ ] 工具调用子跨度条（深蓝色 #1e3a5f，参考 Vercel hook/span）
- [ ] 右侧持续时间标签（参考 Vercel 1m 48s 标签）
- [ ] 缩放控制 +/-（参考 Vercel 右下角按钮）
- [ ] 实时数据刷新（SSE 或 5 秒轮询）
- [ ] 工具异常高亮显示（红色 #ef4444）

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
