# Crazy 侧开发团队确认结果

> 日期: 2026-04-30
> 执行人: HermesAgent
> 状态: 确认完成

---

## 一、同步状态

- **当前分析基线**: commit `a704402`（合并 PR #12 governance-mirror + PR #13 capture-link-hardening 后的 HEAD）
- **当前分支**: `docs/ops-prd-intelligence-pipeline-update`
- **是否已同步远端最新版本**: ✅ 已同步。`origin/main`、`origin/docs/hermes-flowmind-governance-mirror-20260430`、`origin/fix/flowmind-capture-link-hardening` 均已合并到当前工作分支
- **是否已看到 #12 / #13**: ✅ #12（治理包镜像 + PRD/路线图对齐，commit `356b016`）和 #13（flowmind_capture.py 契约修复 + handshake smoke，commit `330144a`）均已合并

---

## 二、主线确认

### 2.1 Crazy 当前是否已真正接受新主线

**结论：是，但存在表述残留需要清理。**

已接受的证据：
1. `docs/roadmap/HermesAgent-FlowMind-联合产品功能基线-2026-04-30.md` 明确声明旧 `v0.1.0 ~ v0.5.0` 是"历史能力清单"而非"当前实施顺序"
2. `docs/roadmap/master-task-plan.md` 第四节"当前活跃联合产品主线"已写入新口径
3. `docs/prd/README.md` 已增加联合产品基线入口说明
4. `docs/02-engineering/harness/HERMES-FLOWMIND-双仓协同治理方案-2026-04-30.md` 已定义双系统分工

### 2.2 与新主线冲突的表述

| 文件 | 问题 | 严重性 | 建议 |
|------|------|--------|------|
| `docs/roadmap/prd-execution-roadmap.md` | Phase 0-4 结构仍使用旧分层（Runtime→Operator Surface→Governance→情报链路），未映射到新基线 Phase 1-5（Link Hardening→Ops Data Plane→Governance Roundtrip→Console Convergence→Security Automation） | **中** | 在 roadmap 顶部增加一段说明："以下 Phase 0-4 为旧版产品内部分阶段，当前活跃执行顺序以 `联合产品功能基线` 为准。本文档保留作为细粒度任务参考。" |
| `docs/prd/technical-implementation-prd.md` | 版本号仍为 v0.1.0，最后更新 2026-04-26，未反映双仓治理包引入 | **低** | 更新版本号为 v0.2.0，最后更新改为 2026-04-30，在"产品边界"节增加对双仓治理方案的引用 |
| `docs/prd/operations-implementation-prd.md` | 同上，版本号和更新日期过旧 | **低** | 同上处理 |
| `docs/prd/hermesagent-hosted-flowmind-product-foundation.md` | 未提及双仓联合产品线、未引用治理包 | **低** | 在"产品框架"节增加一段："当前产品已进入与 FlowMindDeploy 双仓联合演进阶段，详见 `docs/02-engineering/harness/HERMES-FLOWMIND-双仓协同治理方案-2026-04-30.md`" |

**是否必须本轮修改**: roadmap 的映射说明建议本轮加，其余三个低优先级可下轮迭代顺手更新。

---

## 三、真实数据源清单

### 3.1 确认的运行态数据源

| 数据源 | 类型 | 当前状态 | 适合接入 HUD | 说明 |
|--------|------|----------|-------------|------|
| `state.db` | SQLite | ✅ 存在可读 | **是（P0）** | Hermes 运行时核心数据库，session/token/gateway 状态的 canonical source |
| `gateway_state.json` | JSON | ✅ 存在可读 | **是（P0）** | 平台连接状态，feishu/webhook/api_server 连接信息 |
| `~/.hermes/skills/` | 文件系统 | ✅ 存在 | **是（P1）** | 技能清单，可用于 skills inventory 视图 |
| `~/.hermes/memories/` | 文件系统 | ✅ 存在 | **是（P1）** | Agent 记忆，可用于 team memory 视图 |
| cron job 状态 | Hermes 内部 | ✅ 可查询 | **是（P0）** | 通过 `hermes cron list` 或内部 API |
| `shared-context/` | Git-tracked JSON | ✅ 完整 | **是（P1）** | tech-radar.json、bitable-sync-state.json、flowmind-link-state.json、monitor-tasks/、agent-requests/ |
| Bitable（飞书多维表格） | 外部 API | ✅ 13 条记录在库 | **是（P0）** | 情报价值追踪，app_token=Kxkmb7H1EaXFzgs9pklcGVN5nGb |
| `scripts/flowmind_capture.py` 输出 | 脚本日志 | ✅ 可执行 | **是（P2）** | Bitable→FlowMind 同步，需作为治理状态的数据来源 |
| `scripts/flowmind_handshake_smoke.py` 输出 | 脚本日志 | ✅ 可执行 | **是（P2）** | 双仓握手验证 |
| `/opt/hermes-webui/` | Flask 应用 | ✅ 运行中 | 参考 | 原始 Hermes WebUI，提供 API 路由参考 |
| cron 输出日志 | 文件系统 | ✅ 在 ~/.hermes/cron/ | **是（P1）** | 晨间/午间/晚间情报、反思、巡检等 cron 产出 |

### 3.2 hermes-hud collectors 优先级

**当前 `hermes-hud` 包未安装**（`pip show hermes-hud` 返回 not found）。文档中引用的 `hermes-hud` 指的是上游 collector 语义模式，不是可安装包。

建议优先吸收的 collector 语义（按优先级排序）：

| 优先级 | Collector | 数据源 | 理由 |
|--------|-----------|--------|------|
| **P0** | session collector | `state.db` | 运营者最核心的问题"现在什么在运行"的答案 |
| **P0** | health collector | `gateway_state.json` + cron 状态 | 平台连接和定时任务健康是运营底线 |
| **P1** | token/cost collector | `state.db` | 成本可见性是运营必需 |
| **P1** | skill inventory collector | `~/.hermes/skills/` | 技能完整性和失效检测 |
| **P2** | correction/pattern collector | cron 输出 + session 日志 | 模式识别和纠偏信号，需要更多数据积累 |

**不值得现在优先做的**：
- ❌ FlowMind review queue 实时轮询 — 治理层尚未稳定，过早接入会产生噪声
- ❌ 自动化 cost alert — 当前 token 数据量不足以设定合理阈值
- ❌ 跨 session lineage graph — 数据结构尚未标准化

---

## 四、HUD 归属确认

### 4.1 当前三套 UI 的归属

| 组件 | 路径 | 归属 | 角色 |
|------|------|------|------|
| upstream `hermes-hud` | 未安装，仅文档引用 | 上游参考 | **参考实现** — collector 语义来源，不作为交付面 |
| `/opt/hermes-webui/` | `/opt/hermes-webui/` | 独立部署的 Flask 应用 | **参考实现 + API 路由来源** — 保留其 API 模式，但不作为产品主入口 |
| Crazy WebUI | `src/webui/`（本仓库） | **仓库所有** | **正式产品模块** — 下一阶段的主交付面 |

### 4.2 下一阶段主交付面

**正式入口：`src/webui/`（本仓库的 Crazy WebUI）**

理由：
1. 它是仓库所有，受 PRD 和 harness 约束
2. 它的路由应映射到五大一级 IA（Overview / Runtime / Operations / Governance / Collaboration）
3. 它是唯一能与 `shared-context/`、Bitable、FlowMind bridge 同步演进的 UI 层

### 4.3 Operator 正式入口

**单一入口：Crazy WebUI 的 Overview 页面（`/`）**

当前 `src/webui/app.py` 的路由仍是旧版平铺结构（`/agent`、`/tasks`、`/dashboard` 等），尚未收敛到新 IA。下一阶段应：
1. 将现有路由重映射到新 IA 分区
2. Overview 页作为 operator 的唯一入口
3. 旧路由保留为兼容重定向，不作为主入口

**禁止多个页面同时充当"主入口"** — `/opt/hermes-webui/` 的旧首页和 Crazy WebUI 的首页不能同时声称自己是 operator 入口。

---

## 五、运营状态字段确认

### 5.1 当前 Bitable 字段

现有 13 条记录，11 个字段：

| 字段名 | 类型 | 当前值 |
|--------|------|--------|
| 价值点名称 | 文本 | 技术/项目名称 |
| 优先级 | 单选 | P0/P1/P2 |
| 影响评估 | 文本 | 对系统的影响分析 |
| 建议行动 | 文本 | 建议的下一步 |
| 来源 | 文本 | 发现来源 |
| 状态 | 单选 | `pending` / `已确认` |
| 发现日期 | 日期 | 发现日期 |
| 备注 | 文本 | 补充说明 |
| 关联任务 | URL | 相关链接 |
| 序号 | 数字 | 排序 |
| FlowMind同步 | 单选 | `未同步` / `不需要` |

### 5.2 正式运营状态字段定义

#### 字段一：`状态`（现有字段，扩展值域）

| 值 | 含义 | 使用场景 |
|----|------|---------|
| `待评估` | 新发现的情报条目，尚未做影响评估 | 晨间/午间/晚间 cron 自动写入 |
| `已评估` | 已完成影响评估和优先级标注，待人工确认 | cron 评估完成后 |
| `已确认` | 人工确认有价值，可进入下一步 | 用户在 Bitable 或 HUD 中确认 |
| `已拒绝` | 评估后认为无价值或不适用 | 用户主动拒绝 |

注意：现有 `pending` 应统一为 `待评估`，现有 `已确认` 保持不变。

#### 字段二：`FlowMind同步`（现有字段，扩展值域并改名）

建议改名为：**`FlowMind同步状态`**

| 值 | 含义 | 使用场景 |
|----|------|---------|
| `未同步` | 已确认但尚未发送到 FlowMind | 默认状态 |
| `已发送` | `flowmind_capture.py` 已成功 POST 到 candidate ingress | 脚本执行成功后自动更新 |
| `审查中` | FlowMind review queue 中正在审查 | 需要从 FlowMind 拉取状态后更新 |
| `已进入Truth` | FlowMind 已将其固化为 canonical truth | 需要从 FlowMind 拉取状态后更新 |
| `已拒绝` | FlowMind 审查后拒绝 | 需要从 FlowMind 拉取状态后更新 |
| `同步失败` | capture 脚本执行失败 | 脚本异常时自动更新 |
| `不需要` | 无需同步到 FlowMind（如已落地的本地实践） | 人工标注 |

### 5.3 状态流转图

```
待评估 → 已评估 → 已确认 → 未同步 → 已发送 → 审查中 → 已进入Truth
                  ↓                    ↓         ↓
                已拒绝              同步失败    已拒绝
```

### 5.4 需要落库的状态

以上所有状态**都需要落库到 Bitable**，因为：
1. Bitable 是 Crazy 侧运营状态的 canonical surface
2. HUD 从 Bitable 读取状态做展示，不自己维护第二套状态
3. `flowmind_capture.py` 和后续的状态回写脚本以 Bitable 为读写目标

---

## 六、需要修改的文档

| 文件路径 | 修改原因 | 是否必须本轮修改 |
|----------|----------|-----------------|
| `docs/roadmap/prd-execution-roadmap.md` | 在顶部增加与新基线 Phase 1-5 的映射说明 | **建议本轮** |
| `docs/prd/technical-implementation-prd.md` | 更新版本号和日期，增加双仓治理引用 | 下轮即可 |
| `docs/prd/operations-implementation-prd.md` | 同上 | 下轮即可 |
| `docs/prd/hermesagent-hosted-flowmind-product-foundation.md` | 增加双仓联合产品线引用 | 下轮即可 |
| Bitable 字段名 | `FlowMind同步` → `FlowMind同步状态`；`状态` 值域 `pending` → `待评估` | **建议本轮**（通过 lark-cli 修改） |

---

## 七、对下一阶段的输入

### 7.1 给 FlowMind 侧的明确约束

1. **candidate ingress 契约已锁定** — `flowmind_capture.py` 当前发送的 payload 结构（instanceId / sourceAgent / title / rawText / confidence / sourceContext / timestamp）必须被 FlowMind 接受，不得随意变更 required fields
2. **状态回写必须双向** — FlowMind 审查完 candidate 后，必须提供状态变更信号（通过 feedback API 或直接查询），让 Crazy 侧能更新 Bitable 中的 `FlowMind同步状态`
3. **handshake smoke 必须定期运行** — 至少每次 FlowMind 部署后运行一次 `flowmind_handshake_smoke.py`，确保双仓链路未断裂
4. **不要等 Crazy 侧 HUD 完善后再提供 feedback API** — feedback / context-pack 接口应先行稳定

### 7.2 给实现侧的明确约束

1. **HUD 只读优先** — 下一阶段 HUD 以展示为主，不实现写操作（除非有明确的 operator action 需求）
2. **Bitable 是运营状态的 single source of truth** — HUD 从 Bitable 读取，不自己维护状态副本
3. **新 IA 路由收敛** — 将现有 `/agent`、`/tasks` 等路由映射到五大 IA 分区，Overview 为唯一入口
4. **先做 session + health + Bitable 三个 collector** — 这三个覆盖运营者最核心的三个问题
5. **不要引入新的外部依赖** — 当前技术栈（Flask + Jinja2 + lark-cli + Python scripts）已足够

### 7.3 仍未决的问题

1. **Bitable 字段改名是否需要通知已有 cron 脚本** — `flowmind_capture.py` 和 `bitable_sync.py` 中硬编码了 `FlowMind同步` 字段名，改名后需同步修改
2. **`/opt/hermes-webui/` 的退役时间表** — 当前它仍在运行，Crazy WebUI 何时能完全替代它？
3. **FlowMind 侧 feedback API 的调用频率** — Crazy 侧应多久轮询一次 FlowMind 的审查状态？实时 webhook 回调 vs 定期轮询？
4. **handshake smoke 的自动化集成** — 是否应将其纳入 CI/CD 或定期 cron？

---

## 八、验收结论

**结论：accept（附带 1 项 revise 建议）**

### accept 理由

1. ✅ 远端最新版本已同步（PR #12 + #13 均已合并）
2. ✅ Crazy 当前主线口径明确（以联合产品功能基线为准，旧 v0.1.0~v0.5.0 为能力清单）
3. ✅ 真实数据源清单明确（10 个确认数据源，按优先级标注）
4. ✅ HUD 归属策略明确（Crazy WebUI src/webui/ 为正式产品模块，其余为参考实现）
5. ✅ 运营状态字段明确（两个核心字段的完整值域和流转图）

### revise 建议

1. `prd-execution-roadmap.md` 的 Phase 结构需要与新基线建立映射关系（本轮建议修改）
2. Bitable 字段名 `FlowMind同步` 建议改名为 `FlowMind同步状态`，`状态` 值域 `pending` 建议改为 `待评估`（本轮建议修改，需同步更新脚本）
