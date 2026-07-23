# CR-20260724-001: BKN Studio 前端能力融合（P0+P1+P2）

**日期**: 2026-07-24
**仓库**: CrazyAgentsManage
**分支**: `codebuddy/obkn-studio-fusion`
**复杂度**: L4（跨技术栈 + 架构决策 + 多文件）

## 变更概述

将 OpenBKN BKN Studio 前端能力融入 CrazyAgentsManage，分三个阶段落地：
- **P0**: API 契约对齐 — 7 个 v2 Blueprint 模块（只读投影）
- **P1**: React 微应用骨架 — OntologyGraphView 力导向图谱 + AgentChat 骨架
- **P2**: skills.html 原生 JS 增强 — 工程化元数据面板（文件树 + allowed_tools）

## 设计决策（ADR-001~008）

完整 ADR 见 `D:\bkn_docs\04-bkn-studio-frontend-and-cam-fusion.md` §4.5。

| ADR | 决策 |
|-----|------|
| ADR-001 | 采用路径 C（能力对接 + 选择性移植），非全量替换 |
| ADR-002 | React 微应用隔离在 `frontend/` 子目录，iframe 集成 |
| ADR-003 | 新增路由按 Blueprint 拆分，URL 前缀 `/api/v2/`，不污染旧 api.py |
| ADR-004 | 数据源：文件直读 DSL + HTTP 调 FMD mcp-server，只读 |
| ADR-005 | 鉴权：同源 iframe 自动携带 Flask session cookie |
| ADR-006 | knowledge-network `supportsEmbedded` 在 CAM 副本改 true |
| ADR-007 | worktree 隔离：`CrazyAgentsManage-codebuddy-obkn-studio-fusion` |
| ADR-008 | 构建链：pnpm+Vite，dist gitignore，CI 构建 |

## P0 实现：API 契约对齐

**新增文件** (`src/webui/blueprints/`):
- `fmd_client.py` — 共享 FMD 数据访问（文件直读 + HTTP 通道 + 缓存）
- `knowledge_networks.py` — DSL 全景概览（by_kind/by_owner/domain）
- `object_types.py` — kind=object 条目（31 个）+ 详情
- `relation_types.py` — kind=relation 条目（8 个）
- `action_types.py` — kind=action 条目（10 个）+ input/output/authority_profile
- `context_loader.py` — ContextLoader 调试台（HTTP→FMD mcp-server）
- `skills_enhanced.py` — Hermes skills/ 目录投影 + 文件树
- `mcp_tools.py` — MCP 实例投影（mcp_servers.json）
- `__init__.py` — Blueprint 注册

**修改文件**:
- `src/webui/app.py` — 注册 7 个 v2 Blueprint + `/studio/*` 路由 + frontend/dist 静态服务

**数据通道**（复用 api.py 既有模式）:
- 文件直读: `_FLOWMIND_ROOT / packages/ontology/semantic-dsl/`（6 kind 目录，112 条目）
- HTTP 调用: `FLOWMIND_API_BASE_URL`（默认 127.0.0.1:3001）→ FMD mcp-server
- 缓存: TTL 60s

**测试** (`src/webui/test_blueprints.py`):
- 16 个测试全部通过
- 覆盖：列表/详情/404/缓存/只读不变量（POST/PUT/DELETE 返回 405）

## P1 实现：React 微应用

**新增目录** `frontend/`:
- `package.json` — React 19.2 + Vite 7.1 + AntD 5.28 + @ant-design/icons 6 + TypeScript 5.9
- `vite.config.ts` — 多入口构建（graph + agent）+ dev proxy 到 Flask
- `tsconfig.json` — strict mode
- `index.html` / `agent.html` — 两个 SPA 入口
- `src/main-graph.tsx` + `src/App-graph.tsx` — 图谱页面（加载 /api/v2/knowledge-networks/）
- `src/main-agent.tsx` + `src/App-agent.tsx` — Agent 调试骨架（动作类型清单）
- `src/components/OntologyGraphView.tsx` — 自实现力导向图谱（repulsion+spring，缩放+选中+邻居高亮）
- `src/api/client.ts` — CAM API 客户端
- `src/types.ts` — 类型定义

**iframe 集成** (`templates/`):
- `studio-index.html` — Studio 入口
- `studio-graph.html` — iframe 加载 frontend/dist/index.html
- `studio-agent.html` — iframe 加载 frontend/dist/agent.html

**验证**:
- `pnpm typecheck` — 0 错误
- `pnpm build` — 成功（graph 43KB + agent 123KB + zh_CN locale 598KB）

## P2 实现：skills.js 增强

**修改文件** `src/webui/static/js/skills.js`:
- 追加 `loadEnhancedSkillMeta()` — 调用 `/api/v2/skills/<id>` 获取元数据
- 追加 `renderEnhancedMeta()` — 在 skill detail 底部渲染文件树 + allowed_tools
- Hook `renderSkillDetail` — 渲染后自动加载增强元数据
- **surgical**: 不修改现有 loadSkillsList/selectSkill 逻辑

## P3：暂不实施项

以下能力因依赖 bkn-backend 特有服务或架构差异过大，暂不在 CAM 实施：

| 项 | 原因 | 后续条件 |
|----|------|----------|
| 模型管理 | 依赖 bkn-backend 模型服务，CAM 无对应后端 | 需先建 CAM 模型配置层 |
| 数据资源治理 | 依赖 bkn-backend 数据连接/目录 + 向量索引 | 需先建 CAM 数据层 |
| OpenAPI/cURL 导入 | 依赖 bkn-backend 执行工厂契约 | 需先对齐 CAM task-bus 契约 |
| AgentChat 流式对话 | 需 ai SDK + FMD mcp-server 对话 bridge | P1 已留骨架，待 bridge surface 就绪 |
| 度量管理 | FMD DSL 无 metric kind | 需 FMD 扩展度量 DSL |

## 验证结果

- ✅ P0: 16 个 unittest 全部通过（含只读不变量守卫）
- ✅ P1: TypeScript 类型检查 0 错误 + Vite 构建成功
- ✅ P2: skills.js 增强追加，不影响现有功能
- ✅ Invariant 1: 所有 v2 API 只读，不写 truth（POST/PUT/DELETE 返回 405）
- ✅ 跨仓边界: CAM 只读消费 FMD ontology，不修改

## 跨仓引用

- 分析文档: `D:\bkn_docs\04-bkn-studio-frontend-and-cam-fusion.md`（含 8 个 ADR）
- 前序 OpenBKN 吸收: FMD PR #47/#48/#49 + CAM PR #22（已 merged）
- bkn-studio 仓库: github.com/openbkn-ai/bkn-studio（分析对象，未修改）
