# Phase 6 HandoffContract 开发团队提示词

下面这版直接发给 Crazy 开发团队。

---

你现在处理的是 Crazy handoff 消费面开发，不要再按旧口径判断“handoff 是否可用”。

从本轮开始，默认规则已经切换为：

- handoff 主体仍优先读 `moduleDetails.handoff`
- handoff 是否就绪、是否阻塞，统一读 `handoffContract`

## 你必须遵守的开发规则

1. 默认消费 `/api/runtime/handoffs?recordId=...`
2. 页面状态灯直接使用 `handoffContract.ready`
3. 页面阻塞说明直接展示 `handoffContract.blockingIssues`
4. 缺口说明直接展示：
   - `handoffContract.missingFields`
   - `handoffContract.executionBoundaryMissingFields`
5. 如果 replay 上游暂时没有 `handoffContract`，允许消费 Crazy 归一后的 fallback 结构，但字段名必须保持一致
6. 不要在前端或本地 API 再新增另一套“本地 handoff 健康规则”

## 明确禁止

- 因为页面上“看起来有 handoff 内容”就判定可用
- 因为 `source = moduleDetails.handoff` 就判定通过
- 手工拼一段自由文本去替代结构化阻塞原因
- 在前端本地推断另一套 ready / blocked 逻辑

## 开发完成后的最小自检

1. `recordId` 正常时，页面能展示：
   - `handoffContract.ready`
   - `handoffContract.blockingIssues`
   - `handoffContract.missingFields`
   - `handoffContract.executionBoundaryMissingFields`
2. 上游 ready=true 时，页面状态为“契约就绪”
3. 上游 ready=false 时，页面状态为“契约阻塞”
4. 如果上游没给 `handoffContract`，Crazy fallback 仍返回同形状字段

## 建议回报模板

```PLAIN_TEXT
开发侧 handoffContract 接线结果：
- recordId:
- handoffContract.ready 是否已接线:
- blockingIssues 是否已展示:
- missingFields 是否已展示:
- executionBoundaryMissingFields 是否已展示:
- 是否仍存在本地自定义 handoff 健康规则:
- 结论: 已切到统一契约 / 仍有阻塞
```

## 事实层引用

- `docs/02-engineering/harness/handoff-contract-consumption-status-2026-05-05.md`

如果你的结论与事实层文档不一致，先核对代码与接口，不要沿用旧口径。
