# Phase 6 HandoffContract 运营团队提示词

下面这版直接发给 Crazy 运营团队。

---

你现在做的是 Crazy handoff 消费面的真实 round 验收，不要再按旧口径判断“handoff 是否可用”。

从本轮开始，默认规则已经切换为：

- handoff 主体仍优先读 `moduleDetails.handoff`
- 但 handoff 是否就绪、是否阻塞，统一读 `handoffContract`

## 你必须遵守的验收规则

1. 先看 `handoffContract.ready`
   - `true` = 可按默认流程消费
   - `false` = 上游契约阻塞

2. 阻塞原因只看：
   - `handoffContract.blockingIssues`
   - `handoffContract.missingFields`
   - `handoffContract.executionBoundaryMissingFields`

3. 不再允许：
   - 因为页面上“看起来有 handoff 内容”就判定可用
   - 因为 `source = moduleDetails.handoff` 就判定通过
   - 写“虽然字段不全，但人工看起来还能用”这类结论
   - 手工拼一段自由文本去替代结构化阻塞原因

## 运营验收时最少要核对的内容

1. `recordId`
2. `source`
3. `handoffContract.ready`
4. `handoffContract.blockingIssues`
5. `handoffContract.missingFields`
6. `handoffContract.executionBoundaryMissingFields`

## 建议回报模板

```PLAIN_TEXT
运营侧 handoffContract 验收结果：
- recordId:
- source:
- handoffContract.ready: true / false
- blockingIssues:
- missingFields:
- executionBoundaryMissingFields:
- 结论: 可按默认流程继续 / 上游契约阻塞
```

## 事实层引用

- `docs/02-engineering/harness/handoff-contract-consumption-status-2026-05-05.md`

如果你的结论与事实层文档不一致，先核对页面和接口返回，不要沿用旧口径。
