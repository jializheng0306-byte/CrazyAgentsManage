# CrazyAgentsManage Memory Candidates 页面 PRD（记忆候选治理）

## 版本信息

| 字段 | 值 |
|------|-------|
| 产品 | CrazyAgentsManage |
| 文档类型 | 页面级 PRD / Collaboration 子表面 |
| 版本 | v0.1.0 |
| 状态 | Implemented |
| Owner | QoderCLI（跨仓变更，FlowMind 侧 CR: FlowMindDeploy `changes/records/CR-20260728-004-memory-candidates-cam-refactor.md`） |
| 最后更新 | 2026-07-28 |

## 页面目标

`/collaboration/memory-candidates` 是 memory_candidate（会话知识候选）的人类治理工作面。数据与语义主权在 FlowMind（Layer C 文件存储 `harness/memory-candidates/`），CAM 只承载展示与人类决策入口（Invariant 12：不覆盖 truth 裁定）。

界面布局与设计理念参照 Context Graph Demo：三栏 = 左 AI Assistant + 中 Context Graph + 右 Decision Trace。

## 三栏结构

| 栏 | 内容 | 数据源 |
|----|------|--------|
| 左 AI Assistant | deep-chat 对话框；候选选择器；Agent Context 可展开区（summary/detail/tags + session anchor 摘录，"带入上下文"注入对话）；Tool Calls 可展开区（E5.3 四层对齐步骤明细） | `/api/flowmind/memory-candidates/<id>` + `/alignment` + `/chat`（SSE） |
| 中 Context Graph | force-graph 力导图 + 节点类型图例（candidate/dsl_object/commitment/session/decision/tag 着色）；拖拽/缩放/单击浮层查看/双击展开 | `/api/flowmind/memory-candidates/<id>/graph` |
| 右 Decision Trace | 决策卡片流（accepted=绿/rejected=红/deferred=黄、confidence%、日期、决策摘要）+ review 提交表单 | `/api/flowmind/memory-candidates/<id>/review-log` + POST `/review` |

## 数据通道

- CAM `src/webui/api.py` 新增 `/api/flowmind/memory-candidates/*` 代理端点（前缀 `flowmind/` 避免与既有 `/api/collaboration/memory-candidates`（promise-review loop）冲突）
- 上游为 FlowMind mcp-server `/api/bridge/memory-candidates`（Bearer bridge token，`FLOWMIND_API_BASE_URL` 配置）
- chat 端点为 SSE 透传：候选内容 + session 摘录拼装 system 上下文 → FlowMind LLM provider → 流式回传 deep-chat
- graph 端点由 CAM 组装：candidate/dsl_object/session/decision/commitment/tag 节点 + REFERENCES/ALIGNED_WITH/ANCHORED_IN/REVIEWED_AS/TAGGED 边

## 前端资产（零 npm 约束）

- `src/webui/templates/memory-candidates.html`
- `src/webui/static/js/memory-candidates.js` / `static/css/memory-candidates.css`
- `src/webui/static/vendor/force-graph.min.js`（vasturiano 2D canvas UMD）
- `src/webui/static/vendor/deep-chat.bundle.js`（web component，module 加载）

## 守卫

- Invariant 1/12：页面只做候选治理与状态展示，review 决策写回 FlowMind `review-log.jsonl`，不裁定 truth.status
- R12/R14：不生成愿景/意义重判内容；chat 助手回复为 INFERRED 参考，人类保留意义重判

## 验证记录（2026-07-28）

- 页面 200；list/get/alignment/review-log/session-excerpt/graph 代理端点均通
- review POST 写入 FlowMind `harness/memory-candidates/review-log.jsonl`
- chat SSE 通道端到端连通（`data:{text}` → `data:{done}`）
