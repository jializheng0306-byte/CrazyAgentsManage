# CrazyAgentsManage Loop Surface 页面 PRD

## 版本信息

| 字段 | 值 |
|------|-------|
| 产品 | CrazyAgentsManage |
| 文档类型 | 页面级 PRD / Loop Surface |
| 版本 | v0.1.0 |
| 状态 | Draft |
| Owner | Codex |
| 最后更新 | 2026-05-22 |

## 页面目标

`Loop Surface` 负责把 Crazy 当前分散在 `Governance / Collaboration / Operations / cron output` 之间的闭环状态，表达成一个显式、可审计、具轮次感的 operator surface。

它要回答：

- 当前闭环在第几轮 / 哪个 cycle
- 当前卡在哪个 gate
- 下一步动作归谁
- 哪些反馈待提交
- 哪些 memory candidate 待确认
- 哪个 cron / handoff / closeout 构成了本轮的证据主链

## 页面定位

它**不是**新的一级 IA。

建议定位：

- 主入口：`/collaboration/loops`
- 次入口：
  - `Governance` 中的 loop / gate card
  - `Operations > Cron` 中的 cycle card
  - `Overview` 中的 follow-up / next-hop card

## 继承关系

本文档继承：

- `docs/prd/collaboration-page-prd.md`
- `docs/prd/governance-operator-workflow-prd.md`
- `docs/prd/operations-implementation-prd.md`
- `docs/02-engineering/external-analysis/centaur-loop-reference-value-for-crazyagentsmanage-2026-05-11.md`

## 页面应承载的核心信息

### 1. Loop Stage Panel

内容：

- 当前 stage
- 当前 gate
- stage owner
- 阻塞原因
- next action

最小阶段词表建议：

- `awaiting_handoff_review`
- `awaiting_operational_acceptance`
- `awaiting_feedback`
- `awaiting_memory_confirmation`
- `cycle_closed`

规则：

- 这些 stage 只表达运营闭环，不定义 `truth.status`

### 2. Cycle / Round List

内容：

- cycle id
- cycle type
- source job / source handoff
- round count
- opened at / last updated at
- stage summary

规则：

- cycle 不等于单次 cron 触发
- cycle 应能跨多次反馈 / closeout / follow-up 形成一轮对象

### 3. Evidence Chain Panel

内容：

- 本轮输入
- 本轮输出
- feedback refs
- trace / handoff / closeout refs
- memory candidate refs

规则：

- 只显示 evidence chain，不在这里改写治理 authority

### 4. Feedback Inbox / Input Surface

内容：

- 待提交 feedback
- 最近已提交 feedback
- feedback form / shortcut

规则：

- 该面表达的是运营输入，不反向定义 truth
- 轻量表单优先，OCR 留作后续阶段

### 5. Memory Candidate Queue

内容：

- candidate summary
- source evidence
- confirm / reject status
- target memory layer

规则：

- candidate 不等于 long-term memory
- 必须显式经过 confirm / reject

## 页面信息架构

建议页面结构自上而下为：

1. loop stage summary
2. active cycles / rounds list
3. evidence chain panel
4. feedback inbox / feedback input
5. memory candidate queue

## 页面模块树

- LoopSurfacePage
  - LoopStagePanel
  - CycleListPanel
  - EvidenceChainPanel
  - FeedbackInboxPanel
  - FeedbackInputPanel
  - MemoryCandidateQueuePanel

## 关键交互

- 从 cycle 跳到相关 cron output / handoff / closeout artifact
- 从 gate 跳到 `Governance` / `Collaboration` 的处理面
- 从 feedback 行跳到对应 bridge / local artifact
- 从 memory candidate 跳到 confirm / reject action

## 依赖来源

- `Collaboration` handoff / closeout surfaces
- `Governance` review / feedback surfaces
- `Operations` cron / alerts / health surfaces
- future `memory candidate` governance surface

## 非目标

本文档不定义：

- 新的 truth 状态枚举
- cron 引擎重写
- memory 存储实现细节
- OCR / screenshot 上传协议

## 完成标准

1. Operator 能直接看到“这一轮卡在哪一步”
2. cycle / round 不再只能隐含在 cron output 或 closeout 文本里
3. feedback 与 memory candidate 不再只停留在研究概念
4. 页面可作为 `Collaboration` 与 `Governance` 的闭环表达子表面
