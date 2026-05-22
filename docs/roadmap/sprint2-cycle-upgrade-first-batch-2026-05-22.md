# Sprint 2 Cycle 升级首批实施拆解

> 日期: 2026-05-22  
> 状态: completed-in-lane / verified  
> 所属主线: `Sprint 2 Control Plane Hardening`  
> 来源判断:
> - `docs/02-engineering/external-analysis/centaur-loop-reference-value-for-crazyagentsmanage-2026-05-11.md`
> - `docs/roadmap/master-task-plan.md`
> - `docs/prd/pages/loop-surface-page-prd.md`

## 一、目标

把 `Centaur Loop` 借鉴线中的“cron job 先升级成 cycle”从分析结论推进成可实施批次。

本批次不追求一次性把所有 cron 都 cycle 化，而是先选两条：

1. 一条治理闭环最强的
2. 一条情报闭环最清晰的

用于验证：

- cycle object 是否值得引入
- `Loop Surface` 的第一批真实数据源是什么
- stage / feedback / memory candidate 的关系是否能在不改动 truth authority 的前提下表达清楚

## 二、选择原则

首批候选必须满足：

1. 已有 repo-tracked source-of-truth
2. 已有明确输入和输出产物
3. 至少存在一个可识别的人工 gate 或后续 follow-up
4. 不需要先重写底层运行时
5. 对 operator 的收益高于实现成本

## 三、首批裁定

### 3.1 第一条：`daily-promise-review.py`

选择结果：**入首批**

理由：

1. 它已经有明确的治理闭环属性：
   - `truth.status`
   - `feedback.eventType`
   - Bitable 主表状态投影
   - closeout / runtime verified 证据
2. 它天然适合表达：
   - 当前 review round
   - 当前是否 awaiting feedback
   - 当前是否 awaiting memory confirmation
3. 它已经是 operator 高频查看对象，cycle 化收益最高

建议 cycle type：

- `promise-review-cycle`

建议首批 stage：

- `collecting_governance_inputs`
- `awaiting_operational_review`
- `awaiting_feedback`
- `awaiting_memory_confirmation`
- `cycle_closed`

### 3.2 第二条：`morning-intel-v2.py`

选择结果：**入首批**

理由：

1. 它已经是 repo-tracked cron 主链
2. 已有稳定输出产物与 operator 消费路径
3. 已完成 executor readonly rollout，对“闭环表达”更具代表性
4. 和 `daily-promise-review.py` 互补：
   - 前者偏治理 / follow-up
   - 后者偏情报 / digest / operator review

建议 cycle type：

- `morning-intel-cycle`

建议首批 stage：

- `collecting_sources`
- `awaiting_operational_acceptance`
- `awaiting_follow_up_decision`
- `awaiting_memory_confirmation`
- `cycle_closed`

## 四、未入首批的对象

### 4.1 `evening-trend-analysis.py`

当前裁定：**第二批候选**

原因：

- 与 `morning-intel-v2.py` 在情报循环结构上高度相似
- 当前首批先做一条情报线即可验证 cycle 模型

### 4.2 `daily-reflection.sh`

当前裁定：**暂不入首批**

原因：

- 运行态质量历史上暴露过骨架输出问题
- 更适合作为 `memory candidate` 线的下游消费者，而不是先当 cycle 主试点

### 4.3 `flowmind-health-check.py`

当前裁定：**暂不入首批**

原因：

- 更偏 probe / health lane
- 当前重点是让 operator 看懂“人类 gate 的闭环对象”，而不是 probe 执行轮次

## 五、首批最小数据面

首批 cycle 对象至少需要：

- `cycleId`
- `cycleType`
- `sourceJobId`
- `sourceJobName`
- `roundNumber`
- `stage`
- `stageOwner`
- `openedAt`
- `updatedAt`
- `evidenceRefs`
- `feedbackStatus`
- `memoryCandidateStatus`
- `nextAction`

## 六、与 Loop Surface 的关系

`Loop Surface` 第一版不需要覆盖全部 cron。

它只要先能稳定消费：

1. `promise-review-cycle`
2. `morning-intel-cycle`

就足够证明：

- stage object 有用
- cycle object 可落地
- feedback / memory candidate 可以挂在真实轮次上

## 七、后续顺序

完成首批后，再按以下顺序推进：

1. `evening-trend-analysis.py`
2. `memory candidate -> confirm/reject` 最小数据面
3. `feedback` 表单化输入面
4. OCR / screenshot 反馈

## 八、一句话结论

> Sprint 2 的 cycle 首批不求面面俱到，只先把 `daily-promise-review.py` 和 `morning-intel-v2.py` 升成可追踪的 cycle 对象，用来证明 `Loop Surface` 和 `feedback / memory candidate` 这条 `Centaur Loop` 借鉴线值得进入主产品面。  

## 九、当前落地结果（2026-05-22）

1. `Loop Surface` 已统一消费 `promise-review-cycle` 与 `morning-intel-cycle` 两条首批 cycle 对象。
2. `Loop Surface` 已支持对 `reflection_learning -> MEMORY.md` 候选记录 `confirm / reject / defer` 本地留痕，并持久化到 `shared-context/loop-surface/memory-candidate-decisions.jsonl`。
3. `Loop Surface` 已支持 manual-form-first 的 feedback input 本地 operator queue，并持久化到 `shared-context/loop-surface/feedback-inputs.jsonl`。
4. 上述两条写面都只作用于 Crazy / Hermes 的本地 operator plane，不直接改写 FlowMind truth / feedback authority，也不把 Crazy 提升为 repo-side canonical memory accept 面。
