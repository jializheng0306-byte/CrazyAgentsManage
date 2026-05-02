# HermesAgent × FlowMind 交互框架设计评审报告（修订版 v2）

> 状态: 评审完成 | 日期: 2026-04-29
> 评审人: HermesAgent（初审）→ Codex CLI（复核修正）→ HermesAgent（整合）
> 评审对象: `docs/design/hermes-flowmind-capture-integration.md` + `scripts/flowmind_capture.py`
> 综合评级: **B+**（方向正确，接口契约和数据口径需修正）

---

## 一、评审范围

| 文件 | 路径 | 角色 |
|------|------|------|
| 交互框架设计文档 | `docs/design/hermes-flowmind-capture-integration.md` | 设计方案 |
| Capture 同步脚本 | `scripts/flowmind_capture.py` | 实现代码 |
| 运营评估报告 | `docs/06-agent-ops/ops-system-evaluation-20260429.md` | 覆盖度数据来源 |
| Bitable 配置 | `shared-context/bitable-config.json` | 数据源配置 |

---

## 二、逐项审查结论

### 2.1 ✅ 确认成立的问题

#### P0-1: API 地址硬编码错误

**位置**: `flowmind_capture.py` 第 25 行

```python
FLOWMIND_API = "https://flowmind.app"  # ← 错误
```

**正确值**: `https://uncentury.cn`（见交互框架设计文档第 15 行 `POST https://uncentury.cn/api/integrations/candidate-ingress`）

**影响**: 脚本当前 100% 不可用，所有请求会发到错误地址。

**修复**: 改为 `FLOWMIND_API = "https://uncentury.cn"`

---

#### P0-2: confidence 值语义口径漂移

**位置**: `flowmind_capture.py` 第 92 行

```python
"confidence": 0.8 if record["priority"] == "P0" else 0.6 if record["priority"] == "P1" else 0.4,
```

**问题**: FlowMind schema 定义为 `z.number().min(0).max(100)` — 百分制整数。当前脚本用 0.8/0.6/0.4 小数值，虽然 zod 校验不会拒绝（`0.8` 在 0-100 范围内），但语义口径与现网约定严重漂移。所有从 HermesAgent 同步的 candidate confidence 会远低于正常值，导致排序和优先级判断失效。

**修复**:
```python
"confidence": 80 if record["priority"] == "P0" else 60 if record["priority"] == "P1" else 40,
```

---

#### P0-3: 缺少 instanceId 和 rawText 字段

**位置**: `flowmind_capture.py` 第 77-93 行 `send_to_flowmind()` 构建的 candidate dict

**对比** 交互框架文档第 22-34 行定义的请求体：

| 字段 | 文档要求 | 脚本实际 | 状态 |
|------|---------|---------|------|
| instanceId | `"hermes-agent2"` | ❌ 缺失 | 需补 |
| title | ✅ | ✅ `record["name"]` | OK |
| description | ✅ | ✅ 拼接了优先级/影响/行动 | OK |
| rawText | 紧凑JSON字符串 | ❌ 缺失 | 需补 |
| confidence | 0-100 整数 | 0.8/0.6/0.4 小数 | 需修 |
| sourceContext | ✅ | ✅ | OK |
| sourceAgent | — | `"intel-sentinel"` | OK（显式设置） |

**修复**: 在 candidate dict 中补上：
```python
"instanceId": "hermes-agent2",
"rawText": json.dumps(record, ensure_ascii=False),
```

---

#### P1-4: 接口契约表缺失

交互框架文档列出了 `2.1 已有接口`，但缺少一份**端到端契约对照表**，覆盖：
- 请求字段名、类型、必填/可选
- 返回字段名、类型
- 错误码及含义
- Auth 方式和 token 约定

**建议**: 在文档 §2.1 之后新增 §2.1.1 契约详情表，直接从 FlowMind integration route 源码提取。

---

#### P1-5: Review Decision 状态机描述不完整

**位置**: 交互框架文档第 44-53 行

当前文档描述了状态集合，但不是完整状态机。实际应为：

```
draft → submitted → approved → committed
  ↑                      │
  └── rejected ──────────┘
  └── expired  ──────────┘
```

| 来源状态 | 触发条件 | 目标状态 |
|---------|---------|---------|
| draft | Human Confirm | submitted |
| submitted | Auto/Governance | approved |
| approved | Commit Action | committed |
| draft/any | Human Reject | rejected |
| draft/any | TTL 超时 (24h) | expired |
| rejected | Human Clarify/重提 | draft |
| expired | Human 重新激活 | draft |

**建议**: 在文档 §2.2 或新增 §2.2.1 中补全状态转移表。

---

### 2.2 ⚠️ 需要修正的判断（Codex CLI 复核指出）

#### 修正-1: `result.get("success")` 判断 — 不是 bug

**初审判断**: 认为 `result.get("success")` 一定会失败。
**修正**: 当前 FlowMind integration route 返回 `{success:true, data:{candidateId, status, sourceAgent, instanceId, ingestedAt}}` 包装结构。脚本按 `success` 字段判断是正确的，不构成 bug。

**结论**: 该项从问题清单中移除。代码逻辑 OK。

---

#### 修正-2: sourceAgent fallback — 初审表述不精确

**初审判断**: 认为未注册 instance 会导致 sourceAgent 被归到 openclaw。
**修正**: FlowMind 的 fallback 逻辑是：只有当 request 没显式给 `sourceAgent`、`sourceContext` 也没给、且 instance 未注册时，才 fallback 到 openclaw。`flowmind_capture.py` 显式设置了 `sourceAgent="intel-sentinel"`，因此不会触发 fallback。instance 注册仍然重要，但主要是为了 instance/session/auth 链路完整性，而非 sourceAgent 分类。

**结论**: sourceAgent 分类风险降级为"低"。instance 注册保持 P2 优先级。

---

#### 修正-3: 55% 覆盖度 — 数字有来源，缺脚注

**初审判断**: 质疑 55% 数字无来源。
**修正**: 55% 来自 `docs/06-agent-ops/ops-system-evaluation-20260429.md` 第 147 行：

> **总体覆盖度：约 55%**（从 P0 前的约 20% 提升到 55%）

该数字由当天晚间情报 cron 首次执行后的运营评估得出，是基于文章能力逐项打分后的加权结果。

**结论**: 数字本身没问题，但交互框架文档引用时缺少脚注。建议在首次出现 55% 处添加引用：`[^1]: 来源：ops-system-evaluation-20260429.md §四`

---

#### 修正-4: Cron 注册缺失 — 降级为"自动化缺口"

**初审判断**: 将 cron 注册缺失定性为架构错误。
**修正**: 当前 CrazyAgentsManage 的产品意图是：

```
Bitable（人工确认）→ flowmind_capture.py（手动/按钮触发）→ FlowMind
```

这里故意保留了一道**人类闸门** — 价值点先进入 Bitable，由人工在表格中确认"已确认"状态，再手动触发同步到 FlowMind。这不是架构遗漏，而是有意的治理设计。

**结论**: 降级为"自动化缺口"。若未来目标改为全自动批量同步，再将 cron 注册列为 P1/P2。

---

### 2.3 🆕 Codex CLI 补充建议（采纳）

#### 新增: 双重人工确认入口

当前文档未明确描述的**关键架构决策**是：

```
┌─────────────────────────────────────────────────────────────────┐
│                    双重人工确认模型                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  第一层确认 (CrazyAgentsManage / Bitable)                       │
│  ├─ 决策：这条价值点是否值得进入 FlowMind？                       │
│  ├─ 操作者：运营人员                                             │
│  ├─ 状态：未同步 → 已确认 → 已同步                               │
│  └─ 职责边界：筛选 + 分类 + 优先级标注                            │
│                                                                 │
│  第二层确认 (FlowMind Review Queue)                              │
│  ├─ 决策：这条候选承诺是否进入 truth / committed？                │
│  ├─ 操作者：承诺治理人                                           │
│  ├─ 状态：draft → submitted → approved → committed              │
│  └─ 职责边界：语义审核 + 承诺确认 + 治理归档                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**为什么这很重要**: 这决定了两套产品的职责边界：
- **CrazyAgentsManage** = 情报生产 + 价值筛选（"这个发现值不值得跟进"）
- **FlowMind** = 承诺治理 + 执行追踪（"这个承诺要不要正式化并跟踪"）

**建议**: 在交互框架文档中新增 §3.4 节，明确描述双重确认模型和职责边界。

---

## 三、问题汇总与优先级

### P0 — 阻塞冒烟测试（必须修复）

| # | 问题 | 文件 | 行 | 修复方案 |
|---|------|------|-----|---------|
| 1 | API 地址硬编码错误 | flowmind_capture.py | 25 | `https://flowmind.app` → `https://uncentury.cn` |
| 2 | confidence 口径漂移 | flowmind_capture.py | 92 | `0.8/0.6/0.4` → `80/60/40` |
| 3 | 缺少 instanceId | flowmind_capture.py | 77-93 | 补 `"instanceId": "hermes-agent2"` |
| 4 | 缺少 rawText | flowmind_capture.py | 77-93 | 补 `"rawText": json.dumps(record)` |

### P1 — 影响文档完整性（应在迭代中修复）

| # | 问题 | 修复方案 |
|---|------|---------|
| 5 | 接口契约表缺失 | 新增 §2.1.1 契约详情表 |
| 6 | 状态机描述不完整 | 补全状态转移表（draft→submitted→approved→committed + reject/expired 回路） |
| 7 | 55% 覆盖度缺脚注 | 添加 `[^1]` 引用 ops-system-evaluation-20260429.md |
| 8 | 双重确认模型未描述 | 新增 §3.4 职责边界说明 |

### P2 — 长期优化项

| # | 问题 | 说明 |
|---|------|------|
| 9 | instance 注册 | 当前不阻塞功能，但影响 session/auth 链路完整性 |
| 10 | cron 自动同步 | 当前有意保留人工闸门，全自动为远期目标 |
| 11 | sourceContext 命名规范 | 建议统一 route_id/action 命名标准 |

---

## 四、建议的下一步

**P0 修复 + 冒烟测试优先**:

1. 修复 `flowmind_capture.py` 的 4 个 P0 问题（API 地址、confidence、instanceId、rawText）
2. 在 Bitable 中准备一条测试记录（状态="已确认"，FlowMind同步="未同步"）
3. 执行 `python flowmind_capture.py <test_record_id>` 端到端冒烟
4. 验证返回 `{success:true, data:{candidateId, status, ...}}`
5. 验证 Bitable 记录状态更新为"已同步"
6. 验证 FlowMind review queue 中出现该 candidate

冒烟通过后，再进入正式重构（接口契约表补全、状态机文档化、双重确认模型写入）。

---

## 五、评审修订记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1 | 2026-04-29 | HermesAgent 初审 |
| v2 | 2026-04-29 | 整合 Codex CLI 复核修正：移除 success 判断误判、修正 sourceAgent fallback 定性、补充 55% 来源脚注、降级 cron 缺口定性、新增双重确认模型 |
