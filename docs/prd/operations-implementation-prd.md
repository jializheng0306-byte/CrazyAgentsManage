# CrazyAgentsManage 运营实现 PRD

## 版本信息

| 字段 | 内容 |
|------|------|
| 产品 | CrazyAgentsManage |
| 文档类型 | 运营实现 PRD |
| 版本 | v0.1.0 |
| 状态 | 当前主基线 |
| 文档管理者 | Codex |
| 运营复核方 | HermesAgent |
| 最后更新 | 2026-04-26 |

## 范围

本 PRD 定义的是：为了让 Hermes 侧运营真正可用，系统必须向运营者暴露什么、支持什么、以及怎样才算达到运营可接受状态。

覆盖内容包括：

- 运营角色视角
- 必须可见的运行时对象
- 运营工作流
- 告警、报告、动作入口
- 运营验收标准

它不负责后端实现细节，后端与前端实现细节由以下文档定义：

- `docs/prd/technical-implementation-prd.md`

## 运营基线

### 已接受的角色模型

- `HermesAgent` 是运营 lane
- `Codex` 是开发 lane
- 运营工作应输出结构化反馈，而不是直接重写架构方案

### 运营最核心的 5 个问题

运营者必须能快速回答：

1. 现在什么在运行？
2. 什么卡住了？
3. 什么失败了？
4. 哪里需要介入？
5. 哪些 FlowMind 关联状态正在漂移？

## 运营必须可见的运行时对象

控制台至少要显式展示：

- sessions
- delegated tasks / child runs
- skills
- cron jobs
- runtime alerts
- gateway / platform connection state
- FlowMind bridge state
- token / cost usage

## 必需的运营视图

### 1. Session 视图

运营者需要看到：

- active / completed / suspect sessions
- 父子任务 lineage
- message / tool / token 摘要
- stuck 指示器

### 2. Task / Delegation 视图

运营者需要看到：

- pending / running / done / failed 状态
- 依赖关系
- 子智能体归属
- 下一步可操作入口

### 3. Skills 视图

运营者需要看到：

- 已安装 skills
- 缺失 / 失效 skills
- 角色 / 领域分组
- 哪些 skill 故障会阻断真实工作

### 4. Cron 视图

运营者需要看到：

- 已配置任务
- 上次运行 / 下次运行
- 成功 / 失败状态
- pause / resume / trigger 入口（前提是真有后端能力）

### 5. Alerts 视图

运营者需要看到：

- 明确异常记录
- 严重级别
- 受影响运行时对象
- 建议下一步动作

## 必需的运营动作

系统最终必须支持以下结构化动作：

- 确认告警
- 打开受影响对象
- 发起或重新发起任务
- 检查 session / task 证据
- 触发 review 例行流程
- 在有真实后端支持时操作 cron job

如果某个动作当前还不存在，UI 不得假装它存在。

## FlowMind 侧运营需求

从运营视角，CrazyAgentsManage 必须清楚区分：

- Hermes 运行时真相
- FlowMind 治理真相
- 尚未确认的 candidate 状态

### 对 FlowMind 关联状态的运营要求

- candidate 状态必须与 canonical truth 区分开
- review / feedback 闭环必须可见
- drift 或 blockage 必须以运营问题的形式暴露，而不是藏在日志里

## 报告需求

运营侧需要固定输出，例如：

- 每日运行摘要
- 每周运营审计
- pending / stuck review 清单
- failed task / failed cron 汇总

这些报告可以从半自动开始，但在 PRD 层必须被视为显式产品要求。

## 运营验收门槛

### P0

- 运营者无需 shell 访问即可判断 runtime 健康
- stuck / failed 状态清晰可见
- FlowMind 关联状态不会被误标成 canonical truth
- 关键运营视图不再是 mock-only

### P1

- 运营者能执行基本的结构化后续动作
- 报告与 review 流程稳定
- skill / cron / session 表面互相关联

### P2

- 更丰富的自动化
- 预测式告警
- 治理辅助与优化闭环

## 非目标

本运营 PRD 不授权：

- 让 HermesAgent 直接承担代码实现责任
- 用聊天结论替代仓库真相
- 把任何未来能力都误写成当前运行时承诺

## 运营体系差距审计（2026-04-29，基于 OpenClaw 实战文章对照）

> **审计来源**：对照《OpenClaw 实战：一个人、一台 Mac、六个 AI Agent》文章描述的完整运营体系，
> 逐项审查当前 CrazyAgentsManage 运营实现的实际状态。
>
> **结论**：当前运营体系仅覆盖文章描述能力的约 20%。情报链路只有"采集"没有"评估→决策→落地"，
> 记忆系统缺少自主迭代循环，Cron 任务全部处于计划开发状态，Harness 配置未落地。

### 差距 1：情报链路断在"采集"环节

**文章描述的完整链路**：
```
采集 → 5星评估 → 影响分析(对现有系统) → P0/P1/P2行动建议 → 更新 Tech Radar → Zoe 审查 → 用户确认 → ACP 编码落地
```

**当前实际状态**：
```
采集(RSS/arxiv) → 推送群消息（原始新闻列表）→ 结束
```

**缺失环节**：

| 环节 | 文章描述 | 当前状态 | 运营影响 |
|------|---------|---------|---------|
| 5 星评估 | 每条情报按重要性评分 | 🔴 无 | 运营者无法区分重要/噪声 |
| 影响分析 | 评估对现有系统的影响 | 🔴 无 | 发现了有价值的技术也不知道跟自己有什么关系 |
| P0/P1/P2 行动建议 | 按影响程度分级建议 | 🔴 无 | 无法驱动技术发现→方案落地 |
| Tech Radar | `shared-context/tech-radar.json` Adopt/Trial/Assess 三级 | 🔴 无 | 没有技术趋势的结构化跟踪 |
| 评估→决策→委派编码 | Zoe 评估 → 用户确认 → ACP 委派 | 🔴 无 | 情报和代码落地完全脱节 |

**运营验收要求**：
- P0：情报 cron 必须输出评估后的结构化摘要（不是原始新闻列表）
- P0：必须有 Tech Radar 文件，每次情报 cron 运行时更新
- P1：情报发现有价值技术时，必须能给出对现有系统的影响分析和行动建议
- P2：行动建议确认后，必须能自动委派编码探索

### 差距 2：记忆系统缺少自主迭代循环

**文章描述的 6 步循环**：
```
触发事件 → .learnings/ 即时记录 → 每日反思 Cron → ≥3次 promote 到 MEMORY.md → bootstrap hook 注入 → 行为改进
```

**当前实际状态**：
- `.learnings/` 目录：🔴 不存在
- 即时记录机制：🔴 不存在（Agent 犯错/被纠正时不会自动记录）
- 反思 cron：🟡 刚建立（2026-04-29），能看实际活动但不能审查 .learnings/
- promote 逻辑：🔴 不存在（没有 ≥3 次提升到 MEMORY.md 的机制）
- bootstrap hook：🔴 不存在（新 session 不会自动加载历史经验）

**运营验收要求**：
- P0：`.learnings/` 目录结构必须存在（ERRORS.md / LEARNINGS.md / FEATURE_REQUESTS.md）
- P0：反思 cron 必须能审查 .learnings/ 中的 pending 条目并决定是否 promote
- P1：新 session 启动时必须能加载 MEMORY.md 和 .learnings/ 历史
- P1：MEMORY.md 必须有容量管理（<3000 tokens 硬上限，超限时自动精简）

### 差距 3：Cron 任务体系未建立

**文章描述**：52 个 cron 任务覆盖全天自动轮转

**当前实际运行的 cron**：

| 任务 | 调度 | 状态 |
|------|------|------|
| FlowMind 巡检 | 08:00/20:00 | 🟢 运行中 |
| 每日反思 | 23:30 | 🟢 刚建立 |

**PRD 中规划但未实施的 14 个 cron**：全部 🔴

**运营验收要求**：
- P0：至少 5 个核心 cron 必须运行（晨报/午间/晚间/巡检/反思）
- P1：cron 任务必须有成功/失败/产出为空的可观测性
- P1：cron 零产出必须被标记为失败（不能反思说"一切正常"就过关）

### 差距 4：Harness 配置未落地

**文章描述的 Harness 配置**（每个参数背后都是真实事故）：

```json
{
  "compaction": { "mode": "safeguard", "memoryFlush": { "softThresholdTokens": 40000 } },
  "contextPruning": { "mode": "cache-ttl", "ttl": "6h", "keepLastAssistants": 3 },
  "session": { "reset": { "atHour": 5, "idleMinutes": 30 }, "maintenance": { "pruneAfter": "7d", "maxDiskBytes": 104857600 } }
}
```

**当前 HermesAgent 配置状态**：未配置以上任何参数。文章描述的四个真实事故（P0 全团队瘫痪 8 小时、P1 报告被压缩、P2 规则失效、session 膨胀）在当前系统中均有复现风险。

**运营验收要求**：
- P0：session idleMinutes 必须 ≤ 30 分钟
- P0：session pruneAfter 必须 ≤ 7 天
- P0：maxDiskBytes 必须 ≤ 100MB
- P1：memoryFlush 必须启用，阈值 ≤ 40K tokens

### 差距 5：没有"情报→编码"的完整落地链路

**文章描述的 Tech Radar 落地案例**：
```
ainews 发现 ReMe → Zoe 评估(源码级对比) → 给出"参考设计自研"建议 → 用户确认 → ACP 委派 Claude Code 做 PoC → 分阶段落地
```

**当前状态**：完全没有这条链路。情报采集和代码开发是两个完全独立的世界。

**运营验收要求**：
- P1：Tech Radar 中 Assess/Trial 级别的技术必须有评估报告
- P1：评估报告必须包含"对我们系统的影响"和"建议行动"
- P2：用户确认后必须能自动委派编码探索（通过 delegate_task/ACP）

---

## 变更控制

当某轮迭代改变了运营语义时，必须同步更新：

1. 本运营 PRD
2. `docs/roadmap/prd-execution-roadmap.md`
3. 若协作状态变化，再更新对应 harness closeout 记录
