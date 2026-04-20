# CrazyAgentsManage WebUI — 功能规划与实施步骤

## 架构概述

### 数据流架构
```
WebUI (Flask :5000)
  ├── 前端 HTML/CSS/JS（浏览器）
  ├── 后端 API Blueprint（Flask JSON API）
  │     ├── 直接读取 state.db (SessionDB)
  │     ├── 直接读取 cron/jobs.json
  │     ├── 直接读取 gateway_state.json
  │     ├── 直接读取 tools/registry
  │     └── 调用 Hermes API Server (:8642) 执行操作
  └── SSE 推送（实时更新）
```

### 关键数据源映射

| 页面 | 数据源 | 读取方式 |
|------|--------|----------|
| 概览主页 | state.db + cron/jobs.json + 文件系统 | SessionDB + JSON + os.walk |
| Agent管理 | tools/registry + state.db | registry.get_available_toolsets() + SessionDB |
| 任务编排 | state.db (会话中的tool_call) | SessionDB.get_messages() |
| 监控仪表板 | state.db + gateway_state.json | SessionDB + read_runtime_status() |
| 技能中心 | ~/.hermes/skills/ 目录 | os.walk + YAML解析 |
| 团队记忆 | ~/.hermes/memory/ 目录 | os.walk + 文件读取 |
| 定时任务 | cron/jobs.json + cron/output/ | load_jobs() + 文件读取 |
| 流水线 | state.db (FTS5) | SessionDB.search_messages() |
| 告警 | gateway_state.json + 日志 | read_runtime_status() + 文件tail |
| Token | state.db (token统计) | SessionDB SQL聚合查询 |

---

## 页面1: 概览主页 (/)

### 功能规划
1. **实时统计卡片** — 从state.db查询会话数、角色数、记忆文件数、团队数
2. **团队卡片** — 读取 ~/.hermes/memory/ 下的团队目录结构
3. **记忆文件网格** — 列出所有记忆文件（.md），显示标题和摘要
4. **角色记忆网格** — 按角色分组显示记忆文件
5. **快速操作** — 新建会话、搜索、跳转到各子页面

### 实施步骤
1. 创建 `/api/overview/stats` API — 聚合state.db统计
2. 创建 `/api/overview/teams` API — 扫描memory目录
3. 创建 `/api/overview/memories` API — 列出记忆文件
4. 更新 home.js — fetch API数据并渲染
5. 添加自动刷新（30秒间隔）

---

## 页面2: Agent管理 (/agent)

### 功能规划
1. **智能体列表** — 从tools/registry获取所有工具集和工具
2. **智能体状态** — 从state.db查询每个角色的会话数和token消耗
3. **智能体配置** — 显示/编辑每个角色的可用工具、模型配置
4. **实时状态指示** — 通过gateway_state.json判断哪些平台在线
5. **创建新智能体** — 调用API Server创建新会话

### 实施步骤
1. 创建 `/api/agents/list` API — 从registry获取工具集信息
2. 创建 `/api/agents/stats` API — 从state.db聚合每个角色的统计
3. 创建 `/api/agents/status` API — 读取gateway运行状态
4. 更新 agent.js — 动态渲染智能体卡片
5. 添加"创建会话"功能 — POST /v1/chat/completions

---

## 页面3: 任务编排 (/tasks)

### 功能规划
1. **DAG可视化** — 从会话消息中提取delegate_task调用链
2. **任务列表** — 显示所有会话中的任务执行记录
3. **任务状态** — 实时显示运行中/等待中/已完成的任务
4. **任务详情** — 点击任务查看完整消息流
5. **新建任务** — 通过API创建新的多步骤任务

### 实施步骤
1. 创建 `/api/tasks/list` API — 查询state.db中的delegate_task调用
2. 创建 `/api/tasks/detail/<id>` API — 获取任务完整消息链
3. 创建 `/api/tasks/dag` API — 构建任务依赖图
4. 更新 tasks.js — 渲染DAG和任务列表
5. 添加任务创建表单

---

## 页面4: 监控仪表板 (/dashboard)

### 功能规划
1. **旁路监听** — 读取state.db实时会话状态（轮询模式）
2. **会话列表** — 左侧面板显示所有活跃会话
3. **会话详情** — 右侧面板显示选中会话的完整信息
4. **统计指标** — 顶部统计栏（会话数/子会话/消息/TRACE/注入日志）
5. **来源分布** — 按cli/cron/feishu等来源分组统计
6. **实时刷新** — SSE或轮询更新活跃会话状态

### 实施步骤
1. 创建 `/api/dashboard/stats` API — 聚合state.db统计
2. 创建 `/api/dashboard/sessions` API — 列出最近会话（含分页）
3. 创建 `/api/dashboard/session/<id>` API — 获取会话详情
4. 创建 `/api/dashboard/gateway-status` API — 读取gateway_state.json
5. 更新 dashboard.js — fetch + 轮询刷新（5秒间隔）
6. 添加SSE端点 `/api/dashboard/events` — 实时推送

---

## 页面5: 技能中心 (/skills)

### 功能规划
1. **已安装技能列表** — 扫描 ~/.hermes/skills/ 目录
2. **技能详情** — 读取技能的 YAML/JSON 配置文件
3. **技能启用/禁用** — 修改 skills_config
4. **技能市场** — 浏览可用技能（预留接口）
5. **技能安装** — 从URL安装新技能

### 实施步骤
1. 创建 `/api/skills/list` API — 扫描skills目录
2. 创建 `/api/skills/detail/<name>` API — 读取技能配置
3. 创建 `/api/skills/toggle` API — 启用/禁用技能
4. 更新 skills.js — 动态渲染技能列表
5. 添加技能安装功能

---

## 页面6: 团队记忆 (/team-memory)

### 功能规划
1. **团队列表** — 左侧面板显示所有团队
2. **团队共享记忆** — 显示团队的共享记忆文件内容
3. **角色专属记忆** — 按角色标签页切换显示
4. **记忆编辑** — 在线编辑记忆文件（Markdown编辑器）
5. **文档库** — 团队文档的上传/下载/删除
6. **记忆搜索** — 全文搜索记忆内容

### 实施步骤
1. 创建 `/api/memory/teams` API — 列出团队目录
2. 创建 `/api/memory/team/<name>` API — 获取团队记忆内容
3. 创建 `/api/memory/role/<name>` API — 获取角色记忆
4. 创建 `/api/memory/update` API — 更新记忆文件（PUT）
5. 创建 `/api/memory/search` API — FTS5搜索
6. 更新 team-memory.js — 动态渲染 + Markdown编辑器

---

## 页面7: 定时任务 (/cron)

### 功能规划
1. **任务列表** — 从cron/jobs.json读取所有任务
2. **任务状态** — 显示运行中/暂停/失败状态
3. **任务操作** — 暂停/恢复/立即执行/删除
4. **创建任务** — 表单创建新定时任务
5. **执行历史** — 读取cron/output/目录的输出文件
6. **Cron表达式编辑器** — 可视化编辑cron表达式

### 实施步骤
1. 创建 `/api/cron/list` API — 调用load_jobs()
2. 创建 `/api/cron/create` API — 调用create_job()
3. 创建 `/api/cron/<id>/pause` API — 调用pause_job()
4. 创建 `/api/cron/<id>/resume` API — 调用resume_job()
5. 创建 `/api/cron/<id>/run` API — 调用trigger_job()
6. 创建 `/api/cron/<id>/delete` API — 调用remove_job()
7. 创建 `/api/cron/<id>/output` API — 读取输出文件
8. 更新 cron.js — 动态渲染 + 操作按钮

---

## 页面8: 会话流水线 (/sessions)

### 功能规划
1. **会话索引** — 左侧面板显示根会话列表（FTS5搜索）
2. **会话详情** — 右侧面板显示入口提示/高亮/结果/系统结果/Token
3. **来源筛选** — 按cli/cron/feishu/telegram筛选
4. **全文搜索** — FTS5搜索消息内容
5. **会话画像** — 显示来源/时间/状态/工具列表
6. **子会话树** — 显示delegate_task产生的子会话层级

### 实施步骤
1. 创建 `/api/sessions/list` API — 调用list_sessions_rich()
2. 创建 `/api/sessions/detail/<id>` API — 调用get_session() + get_messages()
3. 创建 `/api/sessions/search` API — 调用search_messages()
4. 创建 `/api/sessions/tree/<id>` API — 递归查询子会话
5. 创建 `/api/sessions/stats` API — 聚合统计
6. 更新 sessions.js — 动态渲染 + 搜索 + 分页

---

## 页面9: 系统告警 (/alerts)

### 功能规划
1. **告警列表** — 从gateway_state.json + 日志文件提取告警
2. **告警级别** — 严重/警告/信息三级分类
3. **平台状态** — 显示各消息平台的连接状态
4. **进程监控** — 检测gateway进程是否存活
5. **告警规则配置** — 设置阈值和通知渠道
6. **告警确认** — 标记告警已读/已处理

### 实施步骤
1. 创建 `/api/alerts/list` API — 读取gateway_state.json
2. 创建 `/api/alerts/platform-status` API — 各平台连接状态
3. 创建 `/api/alerts/process-check` API — 进程存活检测
4. 创建 `/api/alerts/rules` API — 告警规则CRUD
5. 更新 alerts.js — 动态渲染 + 自动刷新

---

## 页面10: Token管理 (/tokens)

### 功能规划
1. **月度统计** — 从state.db聚合token消耗和费用
2. **按服务商分布** — 按billing_provider分组统计
3. **按智能体分布** — 按会话来源/模型分组统计
4. **预算进度** — 显示当前月度预算使用率
5. **消耗趋势** — 按天/周/月显示token消耗趋势
6. **消耗明细** — 最近的token消耗记录

### 实施步骤
1. 创建 `/api/tokens/stats` API — SQL聚合查询
2. 创建 `/api/tokens/by-provider` API — 按provider分组
3. 创建 `/api/tokens/by-agent` API — 按source分组
4. 创建 `/api/tokens/trend` API — 按天聚合趋势
5. 创建 `/api/tokens/recent` API — 最近消耗记录
6. 更新 tokens.js — 动态渲染 + 图表

---

## 实施优先级

### P0 — 核心功能（第一轮）
1. **后端API框架** — Flask Blueprint + 数据源连接
2. **监控仪表板** — 旁路监听 + 实时会话
3. **定时任务** — 完整CRUD + 执行
4. **会话流水线** — FTS5搜索 + 详情

### P1 — 重要功能（第二轮）
5. **团队记忆** — 文件浏览 + 编辑
6. **Token管理** — 统计 + 费用
7. **系统告警** — 状态监控
8. **概览主页** — 聚合统计

### P2 — 增强功能（第三轮）
9. **Agent管理** — 工具集 + 配置
10. **任务编排** — DAG可视化
11. **技能中心** — 技能管理

---

## 技术实现要点

### 1. 后端API层 (api.py)
- 使用Flask Blueprint组织API路由
- 直接import hermes_state.SessionDB（共享SQLite读取）
- 直接import cron.jobs（共享jobs.json读写）
- 直接import tools.registry（共享工具注册表）
- 直接import gateway.status（共享网关状态）
- 所有API返回JSON格式

### 2. 前端数据对接
- 使用fetch()调用后端API
- 轮询模式：setInterval定期刷新（5-30秒可配置）
- SSE模式：关键页面使用EventSource实时推送
- 错误处理：网络异常时显示重试提示

### 3. Profile隔离
- 所有路径使用get_hermes_home()获取
- API层接受profile参数，设置HERMES_HOME环境变量
- SessionDB实例化时传入正确的db_path

### 4. 安全考虑
- API只读为主，写操作需要确认
- 不暴露API密钥和敏感配置
- 文件编辑操作需要备份原文件
