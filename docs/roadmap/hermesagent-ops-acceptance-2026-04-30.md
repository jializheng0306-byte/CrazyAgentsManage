# HermesAgent 运营验收

> 日期: 2026-04-30
> 验收人: HermesAgent（运营验收方）
> 验收范围: CrazyAgentsManage 下一阶段启动前运营就绪性
> 验收基线: commit `52ea7be`（docs/ops-prd-intelligence-pipeline-update，已合并 PR #12 + #13）

---

## 验收结果

- **主线口径是否通过**：⚠️ 有条件通过
- **运营数据面是否通过**：❌ 不通过
- **HUD / Operator Console 是否通过**：❌ 不通过
- **FlowMind 联动基础是否通过**：⚠️ 有条件通过

---

## 一、主线口径验收

### 判定：⚠️ 有条件通过

### 已确认的事实

1. `docs/roadmap/HermesAgent-FlowMind-联合产品功能基线-2026-04-30.md` 已明确定义双系统分工：Crazy = 运营编排，FlowMind = 治理真值
2. `docs/roadmap/master-task-plan.md` 第四节已写入新主线口径
3. `docs/prd/README.md` 已增加联合产品基线入口
4. `docs/02-engineering/harness/HERMES-FLOWMIND-双仓协同治理方案-2026-04-30.md` 已定义系统边界
5. 旧 `v0.1.0~v0.5.0` 在联合产品基线文档中已被降级为"历史能力清单"

### 仍存在的问题

1. **`docs/prd/technical-implementation-prd.md` 仍是 v0.1.0（2026-04-26）** — 它没有引用双仓治理包，也没有提到联合产品基线。如果一个新 operator 打开这份文档，他会以为 Crazy 仍然是独立演进的 Hermes WebUI 产品。
2. **`docs/prd/operations-implementation-prd.md` 同理** — 版本和日期过旧，没有体现双仓联合演进的上下文。
3. **`docs/prd/hermesagent-hosted-flowmind-product-foundation.md`（产品母文档）未引用治理包** — 这是上位文档，它不提双仓联合，下游 PRD 就没有根。
4. **`docs/roadmap/prd-execution-roadmap.md` 的 Phase 0-4 结构与新基线 Phase 1-5 不一致** — 虽然已加映射说明，但两套 Phase 编号并存会让 operator 困惑。

### 运营验收方的判断

主线口径在"规划文档层"已经切换，但在"实施文档层"（技术 PRD、运营 PRD、产品母文档）还没有同步。这不会阻止下一阶段启动，但如果不在 Phase 1 正式开始前修复，会导致实施团队在执行时产生歧义。

---

## 二、运营数据面验收

### 判定：❌ 不通过

### 当前运行态数据源实际状态

| 数据源 | 是否存在 | 是否有数据 | operator 能看到吗 | 运营意义 |
|--------|----------|-----------|-------------------|----------|
| `state.db` | ✅ | ✅ 181 sessions, 7206 messages, 3405 tool calls | ❌ 无 UI 暴露 | **数据丰富但完全不可见** |
| `gateway_state.json` | ✅ | ✅ 3 platforms connected | ❌ 无 UI 暴露 | 平台连接状态对 operator 至关重要 |
| cron jobs | ✅ | ✅ 2 jobs running | ❌ 无 UI 暴露 | FlowMind 巡检 + 每日反思在运行 |
| `shared-context/` | ✅ | ✅ tech-radar, bitable-sync, flowmind-link, monitor-tasks | ❌ 无 UI 暴露 | 跨 agent 共享状态 |
| Bitable | ✅ | ✅ 13 records | ❌ 无 UI 暴露 | 情报价值追踪 |
| cron 输出 | ✅ | ✅ 在 ~/.hermes/cron/output/ | ❌ 无 UI 暴露 | 晨间/午间/晚间情报产出 |

### 核心问题

**当前没有任何一个运行态数据源被 operator 可见。**

所有数据都"存在"于文件系统或外部 API 中，但没有一个被加工成 operator 可读的信息。operator 要看任何数据，必须 SSH 到服务器用命令行读取——这完全不满足运营 PRD 中定义的"运营者无需 shell 访问即可判断 runtime 健康"的 P0 验收标准。

### 具体 gap

1. **session 数据**：state.db 有 181 个 session，包含 message_count、tool_call_count、input_tokens、output_tokens、estimated_cost_usd 等丰富字段，但 estimated_cost_usd 全部为 0（成本追踪未生效），且无任何 UI 展示。
2. **token/cost 数据**：input_tokens 总计 127M，output_tokens 总计 1.5M，但成本字段未填充。operator 无法回答"今天花了多少钱"。
3. **cron 健康**：2 个 cron job 正常运行（FlowMind 巡检 + 每日反思），但 operator 无法在任何界面看到 cron 状态、上次运行时间、成功/失败。
4. **platform 连接**：gateway_state.json 显示 feishu/webhook/api_server 三个平台全部 connected，但 operator 无法在任何界面看到。
5. **alerts**：当前没有任何告警机制。没有"session stuck"检测、没有"cron 失败"告警、没有"FlowMind 连接断开"告警。

### 运营验收方的判断

运营数据面不通过。数据源本身足够支撑下一阶段的基础运营需求，但数据加工和暴露完全缺失。在 HUD 交付之前，operator 等于"瞎子"。

---

## 三、HUD / Operator Console 验收

### 判定：❌ 不通过

### 当前 Web 界面实际状态

| 服务 | 端口 | 是什么 | 运行状态 | 归属 |
|------|------|--------|----------|------|
| Hermes WebUI | 8080 | `/opt/hermes-webui/`，原始 Hermes 界面 | ✅ 运行中 | 非本仓库所有 |
| MiMo Chat UI | 8000 | "Hermes AI - 小米MiMo"聊天界面 | ✅ 运行中 | 非本仓库所有 |
| Crazy WebUI | 5000 | `src/webui/`，本仓库 Flask 应用 | ❌ **未运行** | 本仓库所有 |

### 核心问题

1. **Crazy WebUI 未运行** — 这是本仓库唯一正式的 operator console，但它根本没有启动。operator 打开 localhost:5000 得不到任何响应。
2. **三个 Web 界面并存，无明确入口** — operator 不知道该看 8080 还是 8000 还是 5000。文档中没有任何地方说明"operator 的正式入口是 X"。
3. **8080 的 Hermes WebUI 是参考实现，不是产品** — 它读取的是 Hermes 自己的 session 数据（17 个），不是 state.db 的全量数据（181 个）。它不展示 Bitable、不展示 FlowMind 状态、不展示 cron 健康。
4. **Crazy WebUI 的路由仍是旧版平铺** — `app.py` 中定义的路由是 `/agent`、`/tasks`、`/dashboard` 等旧模块，没有 `/runtime`、`/operations`、`/governance`、`/collaboration` 等新 IA 路由。
5. **Crazy WebUI 的模板仍是旧版设计** — `home.html` 显示"团队与角色"，导航栏仍然是旧模块平铺（概览/Agent/任务/监控仪表板/技能/团队记忆/定时任务/图谱/流水线/告警/Token），不是新 IA 导航。

### 运营验收方的判断

HUD / Operator Console 不通过。当前 operator 没有一个可用的、正式的、能展示运营数据的入口。Crazy WebUI 未运行、未更新到新 IA、未接入真实数据。下一阶段必须以 Crazy WebUI 为主交付面，但在那之前，operator 处于"无 console"状态。

---

## 四、FlowMind 联动验收

### 判定：⚠️ 有条件通过

### 已确认的联动基础

1. **`flowmind_capture.py` 已修复** — PR #13 已合并，脚本可以正确构建 candidate ingress payload，包含 instanceId / sourceAgent / title / rawText / confidence / sourceContext / timestamp
2. **`flowmind_handshake_smoke.py` 已就绪** — 可执行端到端冒烟：注册 instance → 发送 candidate → 验证 review queue → reject 清理 → 验证 feedback/context-pack/truth
3. **compatibility matrix 已建立** — 明确标注了各维度的兼容状态（compatible / incompatible_until_p0_fix / partial）
4. **link manifest 已建立** — 机器可读，包含 contracts / runtimeTriggers / syncMode / knownConditions
5. **`flowmind-link-state.json` 已保存** — 记录了 instanceId、apiKey、baseUrl 等运行时配置
6. **Bitable 已有 FlowMind 同步字段** — `FlowMind同步` 字段当前值为 `未同步` / `不需要`

### 仍存在的问题

1. **handshake smoke 从未正式运行过** — 脚本存在但没有运行记录。compatibility matrix 中 Candidate ingress 仍标记为 `incompatible_until_p0_fix`。
2. **operator 无法看到 FlowMind 联动状态** — 没有任何 UI 展示"哪些 Bitable 记录已同步到 FlowMind"、"FlowMind 审查状态如何"、"handshake 是否通过"。
3. **状态回写链路未建立** — FlowMind 审查后的结果（accept/reject/clarify）无法自动回写到 Bitable 的 `FlowMind同步` 字段。
4. **webhook 未纳入 manifest** — compatibility matrix 中 webhook 路由标记为 `partial`，尚未纳入正式双仓兼容校验。

### 运营验收方的判断

联动基础设施已就绪，但尚未经过实际验证。handshake smoke 必须在下一阶段正式开始前至少运行一次并通过。状态回写链路可以在 Phase 3 建立，但 handshake 必须在 Phase 1 完成。

---

## 五、发现的问题

### Runtime gap

1. **session stuck/zombie 检测不存在** — state.db 中有 82 个 session 的 `ended_at` 为 NULL，但没有任何机制判断它们是"仍在运行"还是"已僵死"。operator 无法回答"什么卡住了"。
2. **成本追踪未生效** — estimated_cost_usd 全部为 0。operator 无法回答"花了多少钱"。
3. **session 标题缺失** — 大量 cron session 的 title 为 NULL，operator 无法快速识别 session 用途。

### Operations gap

1. **operator 无入口** — 没有运行中的 operator console。
2. **cron 可观测性为零** — 2 个 cron job 在运行，但 operator 无法看到状态。
3. **告警机制不存在** — 没有任何自动告警（stuck session、cron 失败、FlowMind 断连）。
4. **Bitable 与 HUD 未连接** — 情报价值追踪数据存在 Bitable 中，但 operator 无法在任何 console 中看到。

### Missing signal

1. **platform 连接状态** — gateway_state.json 有数据但未暴露给 operator。
2. **token 使用趋势** — state.db 有逐 session 的 token 数据但未聚合。
3. **FlowMind 同步状态** — Bitable 有字段但未在任何 UI 中展示。
4. **cron 运行历史** — 有输出但未结构化展示。

### Missing action

1. **operator 无法触发 handshake smoke** — 必须 SSH 到服务器运行脚本。
2. **operator 无法查看/操作 cron** — 必须通过命令行。
3. **operator 无法确认/拒绝 Bitable 中的情报条目** — 必须直接打开飞书 Bitable。
4. **operator 无法查看 FlowMind review queue** — 必须直接调用 FlowMind API。

---

## 六、对开发方的要求

### 必须先补的事（Phase 1 启动前）

| 优先级 | 事项 | 理由 |
|--------|------|------|
| **P0** | 启动 Crazy WebUI（`src/webui/`）并确保可访问 | operator 必须有入口 |
| **P0** | 运行 `flowmind_handshake_smoke.py` 并记录结果 | compatibility matrix 中 candidate ingress 仍标记为 incompatible，必须验证 |
| **P0** | 在 roadmap 或确认文档中明确"operator 正式入口 = Crazy WebUI :5000" | 消除三端口混淆 |
| **P1** | Crazy WebUI 至少展示 session 列表和 platform 连接状态 | 回答"什么在运行"和"平台是否连通" |
| **P1** | 更新技术 PRD / 运营 PRD 的版本号和双仓引用 | 避免实施歧义 |

### 可以后置的事

| 事项 | 建议阶段 |
|------|----------|
| Bitable 字段改名（`FlowMind同步` → `FlowMind同步状态`） | Phase 1 |
| 新 IA 路由收敛（旧模块→五大分区） | Phase 2 |
| token/cost 聚合和趋势展示 | Phase 2 |
| 告警机制（stuck session / cron 失败 / FlowMind 断连） | Phase 2 |
| FlowMind 状态回写链路 | Phase 3 |
| webhook 纳入 manifest 和 handshake | Phase 3 |

### 不应继续做偏的方向

1. **不应继续在 `/opt/hermes-webui/` 上投入** — 它是参考实现，不是产品。不要修它的 bug 或加它的功能。
2. **不应继续把端口 8000 的 MiMo Chat UI 当成产品入口** — 它是独立聊天界面，不是 operator console。
3. **不应继续在没有 HUD 的情况下积累更多脚本** — 脚本存在≠产品能力。先把已有数据暴露给 operator，再加新数据源。
4. **不应继续把"文档存在"等同于"运营就绪"** — PRD 写了"operator 无需 shell 访问"，但当前 operator 必须 shell 访问。这是 gap，不是已完成。

---

## 七、验收结论

### 结论：revise

### 理由

主线口径在文档层已基本切换，FlowMind 联动基础设施已就绪，但**运营数据面和 HUD 两个核心维度不满足下一阶段启动条件**：

1. **operator 无入口** — Crazy WebUI 未运行，三个端口并存无主入口
2. **operator 无数据** — 运行态数据全部存在但无一被加工暴露
3. **handshake 未验证** — 联动脚本存在但从未运行，compatibility matrix 仍标记 incompatible

### 修订要求

在下一阶段（Phase 1: Link Hardening）正式启动前，必须完成：

1. ✅ 启动 Crazy WebUI 并确认可访问
2. ✅ 运行 handshake smoke 并记录结果
3. ✅ 在仓库文档中明确 operator 正式入口
4. ✅ Crazy WebUI 至少展示 session + platform 两个核心信号

以上 4 项完成后，可接受进入 Phase 1。其余 gap 可在 Phase 1-2 期间逐步补齐。

---

## 附录：验收时检查的运行态事实

| 检查项 | 实际值 |
|--------|--------|
| state.db sessions | 181 total, 82 active, 99 ended |
| state.db messages | 7,206 |
| state.db tool calls | 3,405 |
| state.db input tokens | 127,832,128 |
| state.db output tokens | 1,526,197 |
| state.db estimated_cost_usd | 全部为 0（未生效） |
| gateway platforms | feishu=connected, webhook=connected, api_server=connected |
| cron jobs | 2 (FlowMind巡检 08:00/20:00, 每日反思 23:30) |
| Bitable records | 13 |
| Bitable FlowMind同步 | 1 条"不需要", 12 条"未同步" |
| WebUI port 8080 | /opt/hermes-webui/ 运行中（参考实现） |
| WebUI port 8000 | MiMo Chat UI 运行中（非产品入口） |
| WebUI port 5000 | Crazy WebUI **未运行** |
