# HermesAgent → FlowMind Capture 集成方案

> 状态: 方案讨论中 | 日期: 2026-04-28 | 发起人: Codex CLI
> 评审报告: [hermes-flowmind-interaction-framework-review.md](hermes-flowmind-interaction-framework-review.md) (2026-04-29)

## 1. 需求

用户在 HermesAgent 执行某个动作输出内容后（例如晚间情报搜集），希望对感兴趣的内容触发 FlowMind capture（候选承诺捕捉），让内容进入 FlowMind 的 governance 流水线进行后续处理。

## 2. 现状分析

### 2.1 已有接口（真实可用的）

| 接口 | 端点 | 说明 |
|------|------|------|
| Candidate Ingress | `POST https://uncentury.cn/api/integrations/candidate-ingress` | 外部系统向 FlowMind 提交候选承诺 |
| Human Decision | `POST /api/integrations/candidates/:id/confirm|reject|clarify` | 人类对候选做决策 |
| Review Queue | `GET /api/integrations/review-queue` | 查看待审批队列 |
| Pilot Metrics | `GET /api/integrations/pilot-metrics` | 查看 pilot 指标 |
| Sessions | `POST/GET /api/integrations/sessions` | 管理集成会话 |

**Candidate Ingress 请求体结构**:
```json
{
  "instanceId": "hermes-agent2",
  "title": "情报摘要标题",
  "description": "详细描述",
  "rawText": "紧凑JSON字符串，包含关键原始数据",
  "confidence": 80,
  "sourceContext": {
    "route_id": "hermes-intel-capture",
    "action": "evening-trend-analysis",
    "source": "hermes-agent"
  }
}
```
- Auth: `Bearer flowmind-dev-token`
- 返回: `{candidateId, status:"draft", sessionId, sourceAgent, ingestedAt}`

### 2.2 Candidate 进入 FlowMind 后会发生什么

```
HermesAgent → candidate-ingress API → FlowMind
  │
  ├─ 1. Candidate 创建，状态 = "draft"，TTL = 24h
  ├─ 2. SSE 事件 "candidate.inferred" 发射
  ├─ 3. Provenance 记录（创建动作）
  ├─ 4. Session 统计更新
  ├─ 5. 进入 Human Review Queue
  │     ├─ HumanReviewPage（前端页面）
  │     ├─ 人类可以: Confirm → submitted → approved → committed
  │     ├─          Reject  → rejected
  │     └─          Clarify → draft（回退澄清）
  └─ 6. 通过 governance-runtime 进行后续编排
        (clarification-sessions, mutation-orchestration, context-compilation)
```

**关键点**: 当前 capture 之后是**纯人类审核**流程。Candidate 进入 `draft` 状态后等待人类在 `HumanReviewPage` 上做 Confirm/Reject/Clarify 决策。没有自动推进逻辑。

### 2.3 已有集成模式

| 模式 | 实现 | 特点 |
|------|------|------|
| Auto-ingress Plugin | `scripts/pilot/openclaw-auto-ingress-plugin/index.js` | OpenClaw 原生插件，每次回复自动 mirror 到 FlowMind |
| Webhook Executor | `hermes-webhook-fixed-executor.mjs` | GitHub PR webhook 触发，固定 executor 脚本 |
| Pilot Workflow | `pilot-workflow.mjs` | 合成 pilot 数据，批量创建 candidate + session |
| Crontab Script | `evening-trend-analysis.sh` | 晚间趋势脚本（模拟数据），**无 FlowMind 集成** |

### 2.4 关键差距

- ❌ 现有 auto-ingress 是**全量 mirror**，无法对特定内容做选择性 capture
- ❌ Hermes cron 任务执行后**没有 FlowMind 集成链路**
- ❌ 缺少「Hermes 上下文 → FlowMind candidate」的语义桥接层

## 3. 方案设计

### 3.1 核心思路：Hermes 内建 "Capture 指令" + 语义标记

让用户在 Hermes 的输出中通过**自然语言指令**或**结构化标记**告诉 Hermes「这段内容我感兴趣，capture 到 FlowMind」。

#### 方式 A：对话指令式（推荐优先实现）

用户在群聊中对 Hermes 回复追加指令：
```
@HermesAgent 把上面这段晚间趋势中关于 "Multi-Agent" 的部分 capture 到 FlowMind
```

Hermes 解析指令 → 调用 FlowMind candidate-ingress API。

**优点**: 无需改 cron 脚本，灵活，随时可用
**缺点**: 每次需要手动触发

#### 方式 B：Cron 后处理钩子

在 Hermes cron 任务完成后，增加一个「后处理」阶段：
- cron 执行晚间情报采集 → 输出到群 → 同时生成结构化摘要
- 摘要中标记「可 capture 的条目」（带 `[CAPTURE]` 标记或独立 JSON）
- 用户可配置「感兴趣的话题关键词」
- 自动匹配 → 自动调用 candidate-ingress

**优点**: 自动化，批量
**缺点**: 需要改造 cron 脚本，匹配精度依赖关键词

#### 方式 C：混合模式（长期方案）

- Cron 输出带结构化标记
- 用户可即时指令追加 capture
- 建立「capture 策略」配置（哪些话题自动 capture、哪些需人工确认）

### 3.2 技术实现

#### Hermes 侧

1. **新增工具或 skill**: `flowmind-capture`
   - 封装 `POST /api/integrations/candidate-ingress` 调用
   - 参数: `title`, `description`, `rawText`, `sourceContext`
   - 固定: `instanceId="hermes-agent2"`, `bearer="flowmind-dev-token"`, `baseURL="https://uncentury.cn"`

2. **Cron 后处理脚本**: 
   - 在 `evening-trend-analysis.sh` 之后追加 capture 逻辑
   - 或者改为 Hermes cronjob（而非系统 crontab），利用 Hermes 的 skill 能力

3. **语义标记格式**:
   ```markdown
   ## 晚间趋势 - Multi-Agent
   
   摘要: Multi-Agent 架构正在成为主流...
   
   [FLOWMIND_CAPTURE: confidence=75, topic="multi-agent"]
   ```

#### FlowMind 侧（现状即可，无需改动）

当前 FlowMind 的 candidate-ingress + HumanReviewPage 已经足够支撑 capture 后的处理流程。

### 3.3 实施优先级

| 阶段 | 内容 | 预估 |
|------|------|------|
| P0 | 实现 `flowmind-capture` skill（对话指令式） | 一次性开发 |
| P1 | 改造晚间趋势 cron → Hermes cronjob + 后处理钩子 | 半天 |
| P2 | 建立 capture 策略配置 + 关键词自动匹配 | 待定 |

## 4. 待讨论问题

1. **capture 粒度**: 每次 capture 是一条趋势/一篇论文，还是整份报告作为一个 candidate？
2. **自动 confirm**: capture 后要不要自动 confirm？还是始终等人工？
3. **sourceContext 规范**: 需要约定统一的 route_id、action 命名标准
4. **会话管理**: 是否每次 cron 执行创建一个新 session？还是复用？
5. **confidence 计算**: 自动 capture 的 confidence 如何确定？（关键词匹配度？源可信度？）
