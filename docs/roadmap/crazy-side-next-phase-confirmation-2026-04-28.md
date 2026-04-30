# Crazy 侧下一阶段启动确认

> 日期: 2026-04-28
> 状态: active-confirmation
> 基线: main@af1ea8d
> 角色: Codex 开发 lane 对双仓联合产品主线的正式确认

---

## 一、同步状态

| 项目 | 状态 |
|------|------|
| 当前分析基线 | `main@af1ea8d` |
| 远端最新版本已同步 | 是 |
| 已看到 #12 (docs/hermes-flowmind-governance-mirror-20260430) | 是 |
| 已看到 #13 (fix/flowmind-capture-link-hardening) | 是 |
| 联合产品功能基线已读取 | 是 |
| 双仓协同治理方案已读取 | 是 |
| 兼容矩阵已读取 | 是 |
| Link Manifest v1 已读取 | 是 |

---

## 二、主线口径

### 2.1 正式确认

Crazy 当前活跃产品主线已经切换：

- 旧 `v0.1.0 ~ v0.5.0` 只是历史能力清单，不再是当前活跃实施顺序
- 新主线以 `HermesAgent-FlowMind-联合产品功能基线-2026-04-30.md` 为准
- 产品定位不变：`一个以 HermesAgent 为宿主的 FlowMind 运营产品`

### 2.2 与现有文档的冲突检查

| 文档 | 是否与新主线冲突 | 说明 |
|------|-----------------|------|
| `docs/prd/hermesagent-hosted-flowmind-product-foundation.md` | 无冲突 | 母 PRD 定位与新主线一致 |
| `docs/prd/technical-implementation-prd.md` | 轻微冲突 | 仍以旧 Phase 1-5 叙述，需标注为历史参考 |
| `docs/prd/operations-implementation-prd.md` | 轻微冲突 | 同上，仍以旧 Phase 叙述 |
| `docs/prd/README.md` | 无冲突 | PRD 体系说明与新主线兼容 |
| `docs/roadmap/prd-execution-roadmap.md` | 冲突 | 仍以 Phase 1-5 (2024 Q1 ~ 2025 Q1) 为活跃主线 |
| `docs/roadmap/master-task-plan.md` | 部分冲突 | Workstream 1-4 仍有价值，但需标注新主线优先 |
| `docs/roadmap/roadmap.md` | 冲突 | v0.1.0~v0.5.0 仍被标记为活跃版本阶梯 |

### 2.3 最小修改建议

1. `docs/roadmap/prd-execution-roadmap.md` — 在文档顶部添加"本路线图已由联合产品功能基线取代为活跃主线，本文档保留作为历史参考"
2. `docs/roadmap/roadmap.md` — 在文档顶部添加同上声明
3. `docs/prd/technical-implementation-prd.md` — 在文档顶部添加"Phase 1-5 为历史规划，当前活跃阶段见联合产品功能基线"
4. `docs/prd/operations-implementation-prd.md` — 同上

---

## 三、HUD 归属

### 3.1 当前 HUD 代码分布

| 代码位置 | 归属 | 角色 |
|----------|------|------|
| `upstream hermes-hud` | 上游参考 | 参考实现，提供 collectors 语义和 session/corrections/patterns 数据模型 |
| `/opt/hermes-webui` | 运行时部署 | Hermes 宿主上的运行实例，非 Crazy 产品代码 |
| `src/webui/` | Crazy 产品代码 | **正式产品模块**，下一阶段主交付面 |

### 3.2 下一阶段主交付面

**Crazy 自己的 WebUI (`src/webui/`)** 是下一阶段唯一主交付面。

- `upstream hermes-hud` 的 collectors 语义应被吸收到 Crazy 的 API 层
- `/opt/hermes-webui` 是部署目标，不是开发目标
- operator 的正式入口是 `/overview`（通过 `src/webui/app.py` 路由）

### 3.3 参考实现 vs 正式产品模块

| 模块 | 分类 |
|------|------|
| `src/webui/app.py` + `api.py` | 正式产品模块 |
| `src/webui/templates/*.html` | 正式产品模块 |
| `src/webui/static/js/*.js` | 正式产品模块 |
| `src/webui/static/css/*.css` | 正式产品模块 |
| `src/agent/*` | 正式产品模块 |
| `src/context/*` | 正式产品模块 |
| `src/memory/*` | 正式产品模块 |
| `src/monitoring/*` | 正式产品模块 |
| `scripts/flowmind_capture.py` | 正式产品模块（需 #13 修复后生效） |
| `scripts/flowmind_handshake_smoke.py` | 正式产品模块（需 #13 修复后生效） |
| `scripts/bitable_sync.py` | 正式产品模块 |
| `upstream hermes-hud` collectors | 参考实现，语义应吸收到 Crazy API 层 |
| `tools/original-arch-preview/` | 参考实现，非正式产品模块 |

---

## 四、真实数据源

### 4.1 当前真实数据源清单

| 数据源 | 路径/位置 | 类型 | 是否长期使用 | 适合接入 HUD |
|--------|----------|------|-------------|-------------|
| `state.db` | Hermes 宿主 SQLite | 结构化数据 | 是 | **高优先** |
| `gateway_state.json` | Hermes 宿主 | 网关状态 | 是 | **高优先** |
| cron 输出 | `shared-context/cron-*.json` | 结构化输出 | 是 | 中优先 |
| `shared-context/` | 文件系统 | 跨智能体通信 | 是 | 中优先 |
| Bitable | 钉钉多维表格 | 运营状态 | 是 | **高优先** |
| `hermes-hud` collectors | upstream 代码 | session/corrections/patterns | 语义吸收 | **高优先**（语义吸收，非代码复制） |
| `scripts/bitable_sync.py` | 本仓脚本 | Bitable 同步 | 是 | 中优先 |
| `scripts/flowmind_capture.py` | 本仓脚本 | FlowMind candidate | 是（#13 修复后） | 高优先 |
| `scripts/memory_promote.py` | 本仓脚本 | 记忆提升 | 是 | 低优先 |
| `scripts/cron-health-check.sh` | 本仓脚本 | 健康巡检 | 是 | 中优先 |

### 4.2 hermes-hud collectors 吸收优先级

**应优先吸收：**
1. `session collector` — session 是运行时可观测性的核心数据，当前 WebUI 已部分消费但未完全打通
2. `corrections collector` — 修正是治理闭环的关键输入，直接支撑 Governance 分区
3. `patterns collector` — 模式识别支撑运营日报和情报价值追踪

**不值得现在优先做：**
1. `cost estimator` — 依赖外部定价数据，当前精度不足
2. `deployment collector` — 部署状态更适合由 FlowMind 侧管理
3. `alert aggregator` — 当前 alerts 已有独立数据源，无需从 HUD 二次聚合

---

## 五、正式运营状态字段

### 5.1 Bitable 运营状态字段定义

| 字段名 | 含义 | 是否落库 | 使用场景 |
|--------|------|---------|----------|
| `sync_status` | 同步状态 | **是** | 追踪条目在双仓协同中的当前位置 |
| `pending_review` | 待确认 | **是** | 情报/运营事件进入后，等待人工确认是否送入 FlowMind |
| `synced_to_flowmind` | 已同步到 FlowMind | **是** | 确认已通过 candidate ingress 送入 FlowMind |
| `flowmind_reviewing` | FlowMind 审查中 | **是** | FlowMind 侧已进入 review queue |
| `flowmind_rejected` | 已拒绝 | **是** | FlowMind 侧 review 后拒绝，需回写原因 |
| `entered_truth` | 已进入 Truth | **是** | FlowMind 侧确认进入 canonical truth |
| `sync_failed` | 同步失败 | **是** | capture 或 sync 过程中出现技术错误 |
| `last_sync_ts` | 最后同步时间 | **是** | 追踪同步时效性 |
| `flowmind_instance_id` | FlowMind 实例 ID | **是** | 关联 FlowMind 侧的 candidate/truth 记录 |

### 5.2 状态流转

```
pending_review → synced_to_flowmind → flowmind_reviewing → entered_truth
                                                       → flowmind_rejected
pending_review → sync_failed (可重试)
synced_to_flowmind → sync_failed (可重试)
```

### 5.3 字段名调整说明

- 使用 `sync_status` 作为统一状态字段名，而非分散的布尔字段
- `pending_review` 替代"待确认"，语义更精确
- `synced_to_flowmind` 替代"已同步到 FlowMind"，与 link manifest 中的 candidate ingress 对齐
- `flowmind_reviewing` 替代"FlowMind 审查中"，与 FlowMind 的 review queue 对齐
- `entered_truth` 替代"已进入 Truth"，与 FlowMind 的 truth 概念对齐
- `sync_failed` 替代"同步失败"，包含可重试语义

---

## 六、需要修改的文档

| 文件路径 | 修改原因 | 是否必须本轮修改 |
|----------|---------|-----------------|
| `docs/roadmap/prd-execution-roadmap.md` | 添加"已由联合产品功能基线取代"声明 | 是 |
| `docs/roadmap/roadmap.md` | 添加"v0.1.0~v0.5.0 为历史能力清单"声明 | 是 |
| `docs/prd/technical-implementation-prd.md` | 添加"Phase 1-5 为历史规划"声明 | 是 |
| `docs/prd/operations-implementation-prd.md` | 添加"Phase 1-5 为历史规划"声明 | 是 |
| `docs/roadmap/master-task-plan.md` | 添加新主线引用 | 是 |

---

## 七、对下一阶段的输入

### 7.1 给 FlowMind 侧的明确约束

1. Candidate ingress 契约以 `hermes-flowmind-link-manifest-v1.json` 为准，Crazy 侧不会绕过标准接口
2. `flowmind_capture.py` 修复后需完成一次端到端 handshake smoke 才能进入 `handshake-passed`
3. Bitable 状态回写需要 FlowMind 侧提供 `instanceId` 关联字段
4. Feedback / Context Pack 消费逻辑需要 FlowMind 侧确认当前 contract 是否稳定

### 7.2 给实现侧的明确约束

1. HUD 只读优先、动作受控，不演化出第二套 truth
2. Webhook 是运行时触发通道，不是治理事实源
3. 所有 FlowMind 相关脚本修改必须同步检查 compatibility matrix
4. 新数据源接入必须走 `src/webui/api.py` 统一端点，不允许绕过 API 层直接读文件

### 7.3 仍未决的问题

1. `flowmind_capture.py` 修复后何时能完成端到端 handshake smoke — 依赖 #13 合并
2. Bitable 状态回写的具体触发时机 — 需要与运营方确认人工闸门策略
3. `hermes-hud` collectors 语义吸收的具体实现方式 — 需要评估是 API 层适配还是数据层适配
4. `/opt/hermes-webui` 与 `src/webui/` 的部署同步机制 — 当前手动，是否需要自动化

---

## 八、验收结论

- **accept**
- 理由：
  1. 远端最新版本已同步并确认（main@af1ea8d）
  2. #12 和 #13 内容已读取并纳入判断
  3. Crazy 当前主线口径明确：旧 v0.1.0~v0.5.0 为历史能力清单，新主线以联合产品功能基线为准
  4. 真实数据源清单明确，10 个数据源已标注优先级
  5. HUD 归属策略明确：`src/webui/` 为唯一主交付面，`upstream hermes-hud` 为参考实现
  6. 运营状态字段明确：9 个字段已定义，含状态流转图
  7. 需修改的 5 个文档已列出，均为最小化声明添加
