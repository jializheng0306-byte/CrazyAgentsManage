# CrazyAgentsManage — Epic & Sprint 计划

> 基于 implementation-gap-analysis.md 分析结果  
> 目标平台: hermes-agent (D:\opensource\hermes-agent), hermes-webui (D:\opensource\hermes-webui)  
> 创建时间: 2026-04-21

---

## Epic 总览

| Epic | 名称 | 优先级 | Sprint | 涉及项目 |
|------|------|--------|--------|----------|
| E1 | 后端 API 框架 + 数据源连接 | P0 | Sprint 1 | hermes-webui |
| E2 | 监控仪表板 | P0 | Sprint 2 | hermes-webui |
| E3 | 会话流水线索引 | P0 | Sprint 2 | hermes-webui |
| E4 | 团队记忆管理 | P1 | Sprint 3 | hermes-webui |
| E5 | Token 管理 | P1 | Sprint 3 | hermes-webui |
| E6 | 系统告警 | P1 | Sprint 4 | hermes-webui |
| E7 | 概览主页 | P1 | Sprint 4 | hermes-webui |
| E8 | Agent 管理 | P2 | Sprint 5 | hermes-webui |
| E9 | 任务编排 | P2 | Sprint 5 | hermes-webui |

---

## Sprint 1: 后端 API 框架 + 数据源连接 (E1)

### 目标
在 hermes-webui 中建立与 hermes-agent 数据源的完整连接层，为所有后续功能提供数据基础。

### 用户故事
- 作为开发者，我希望 WebUI 能直接读取 hermes-agent 的 state.db 数据库
- 作为开发者，我希望 WebUI 能读取 cron/jobs.json 定时任务配置
- 作为开发者，我希望 WebUI 能读取 gateway_state.json 网关状态
- 作为开发者，我希望 WebUI 能读取 tools/registry 工具注册表

### 任务列表
1. **T1.1**: 创建 `api/hermes_adapter.py` — 封装对 hermes-agent 数据源的访问
   - SessionDB 连接器（读取 state.db）
   - CronJobs 连接器（读取 jobs.json）
   - GatewayStatus 连接器（读取 gateway_state.json）
   - ToolRegistry 连接器（读取工具注册表）
2. **T1.2**: 创建 `api/overview.py` — 概览 API Blueprint
   - GET `/api/overview/stats` — 聚合统计
   - GET `/api/overview/teams` — 团队列表
   - GET `/api/overview/memories` — 记忆文件列表
3. **T1.3**: 修改 `api/routes.py` — 注册新 API 路由
4. **T1.4**: 编写测试 `tests/test_hermes_adapter.py`
5. **T1.5**: 编写测试 `tests/test_overview_api.py`

### 验收标准
- [ ] 所有 API 端点返回正确的 JSON 数据
- [ ] 测试覆盖率 > 80%
- [ ] 数据源连接稳定，无内存泄漏

---

## Sprint 2: 监控仪表板 + 会话流水线 (E2 + E3)

### 目标
实现实时监控仪表板和会话流水线索引功能。

### 用户故事
- 作为运维人员，我希望在仪表板上实时查看所有活跃会话
- 作为运维人员，我希望看到网关状态和平台连接情况
- 作为开发者，我希望搜索和浏览历史会话
- 作为开发者，我希望查看会话的完整消息流

### 任务列表
1. **T2.1**: 创建 `api/dashboard.py` — 仪表板 API
   - GET `/api/dashboard/stats` — 统计指标
   - GET `/api/dashboard/sessions` — 活跃会话列表
   - GET `/api/dashboard/session/<id>` — 会话详情
   - GET `/api/dashboard/gateway-status` — 网关状态
2. **T2.2**: 创建 `api/sessions_api.py` — 会话流水线 API
   - GET `/api/sessions/list` — 会话索引
   - GET `/api/sessions/detail/<id>` — 会话详情
   - GET `/api/sessions/search` — FTS5 搜索
   - GET `/api/sessions/tree/<id>` — 子会话树
   - GET `/api/sessions/stats` — 会话统计
3. **T2.3**: 创建 `static/dashboard.js` — 仪表板前端
4. **T2.4**: 创建 `static/sessions-browser.js` — 会话浏览器前端
5. **T2.5**: 编写测试

### 验收标准
- [ ] 仪表板显示实时会话数据（5秒轮询）
- [ ] FTS5 搜索返回正确结果
- [ ] 子会话树正确展示

---

## Sprint 3: 团队记忆 + Token 管理 (E4 + E5)

### 目标
实现团队记忆管理和 Token 统计功能。

### 任务列表
1. **T3.1**: 创建 `api/memory_api.py` — 团队记忆 API
2. **T3.2**: 创建 `api/tokens_api.py` — Token 管理 API
3. **T3.3**: 创建 `static/team-memory.js` — 团队记忆前端
4. **T3.4**: 创建 `static/tokens.js` — Token 管理前端
5. **T3.5**: 编写测试

---

## Sprint 4: 系统告警 + 概览主页 (E6 + E7)

### 目标
实现系统告警监控和概览主页聚合统计。

### 任务列表
1. **T4.1**: 创建 `api/alerts_api.py` — 告警 API
2. **T4.2**: 完善 `api/overview.py` — 概览主页 API
3. **T4.3**: 创建 `static/alerts.js` — 告警前端
4. **T4.4**: 完善 `static/home.js` — 概览主页前端
5. **T4.5**: 编写测试

---

## Sprint 5: Agent 管理 + 任务编排 (E8 + E9)

### 目标
实现 Agent 管理和任务编排 DAG 可视化。

### 任务列表
1. **T5.1**: 创建 `api/agents_api.py` — Agent 管理 API
2. **T5.2**: 创建 `api/tasks_api.py` — 任务编排 API
3. **T5.3**: 创建 `static/agents.js` — Agent 管理前端
4. **T5.4**: 创建 `static/tasks.js` — 任务编排前端（含 DAG）
5. **T5.5**: 编写测试

---

## 技术约束

1. **hermes-webui 不使用 Flask**，使用 Python 标准库 `http.server`
2. **数据源路径**由环境变量 `STATE_DIR` 和 `AGENT_DIR` 控制
3. **hermes-agent 的 SessionDB** 使用 SQLite WAL 模式，支持并发读
4. **所有 API 必须兼容现有路由分发机制**（`api/routes.py` 的 `handle_get/handle_post`）
5. **前端为原生 JavaScript**，无框架依赖

---

## GitHub 工作流

每个 Sprint:
1. 创建 feature 分支: `feature/sprint-N-<name>`
2. 开发完成后创建 PR
3. 推送到远端仓库
4. 在 PR 上发布迭代结论评论
