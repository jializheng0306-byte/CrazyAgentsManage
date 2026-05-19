# Hermes × executor 只读 Delegation Spec Freeze Closeout（2026-05-19）

> 范围: `Hermes -> executor` readonly delegation v1  
> 宿主: `ALI-HERMES`  
> 上位文档: `docs/design/executor-integration/hermes-executor-readonly-delegation-spec-v1-2026-05-19.md`

## 1. 本轮完成了什么

本轮没有继续停留在“只读 capability 调用能不能通”的验证层，而是把下一步真正需要的策略冻结成了仓库事实：

1. 明确 `readonly delegation` 的边界仍然是 **external read capability step**
2. 明确 `Crazy` 继续负责 source onboarding
3. 明确 `Hermes` 继续负责 lifecycle / trace / runtime truth
4. 明确 `FlowMind` 继续不接 executor 内部执行态
5. 明确第一批开放的 task 类型、第二批候选、当前禁止项

## 2. 第一批开放（Wave 1）

已冻结为：

- `intel.morning`
- `intel.noon-paper`
- `intel.evening`

它们的共同特征：

- 已有真实 repo-tracked 主链入口
- 核心价值是读取外部资料
- delegation 失败不会直接污染 FlowMind / promise / closeout truth

## 3. 第二批候选（Wave 2）

当前只列为候选，不作为 v1 默认开放：

- `tech-radar.review`
- `flowmind.health-probe`

原因：

- 前者对 external capability plane 的收益还不如情报采集链明显
- 后者当前不在受支持的 repo-tracked 主链里，容易与 live guard / source-of-truth 规则冲突

## 4. 当前明确禁止

v1 明确不开放的类型包括：

- `promise.review`
- `promise.capture-clarify`
- `flowmind.capture`
- `closeout.writeback`
- `cron.health`
- `memory.maintenance`

这些类型要么会写治理状态，要么写 closeout truth，要么主要是宿主本地运维，不适合进入第一批 readonly delegation。

## 5. 产物

### 规范性文档

- `docs/design/executor-integration/hermes-executor-readonly-delegation-spec-v1-2026-05-19.md`

### 机器可读策略

- `shared-context/hermes-executor-readonly-delegation-policy.v1.json`

## 6. 结论

本轮之后，主线不再需要继续讨论“先开放哪类 Hermes task 类型”。

这件事已经冻结为仓库事实。

下一轮主线应直接进入：

1. 选择一个 Wave 1 任务
2. 把其 external read step 真正接到 executor
3. 保持 Hermes lifecycle / trace ownership 不变
