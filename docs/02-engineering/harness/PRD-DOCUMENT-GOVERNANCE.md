# PRD 文档治理规则

## 为什么需要这个文件

`CrazyAgentsManage` 不再把单一的大 PRD 当作唯一规划面。

当前仓库采用的是：

1. 技术实现 PRD
2. 运营实现 PRD
3. 统一执行路线图

本文件定义的是：这些文档如何被纳入 `Codex ↔ HermesAgent` 的 harness 流程。

## 规范文档

- `docs/prd/technical-implementation-prd.md`
- `docs/prd/operations-implementation-prd.md`
- `docs/roadmap/prd-execution-roadmap.md`
- `docs/prd/README.md`

## 责任归属

- `Codex` 负责文档版本管理与节奏更新
- `HermesAgent` 负责运营视角复核与验收意见

## 触发条件

当一次迭代改变以下任意内容时，必须更新 PRD 体系：

- 技术范围
- 运营语义
- 实施阶段排序
- merge / readiness 状态
- 影响执行流程的角色/交接约束

## 强制收口更新

每次非平凡迭代结束时，必须至少检查并更新：

1. 技术 PRD（若工程范围变化）
2. 运营 PRD（若运营语义变化）
3. 路线图（若阶段/状态/优先级变化）
4. harness closeout 记录（若协作状态变化）

## 不得合并规则

如果受影响的 PRD 文档和路线图没有更新，就不得把当前分支视为 ready for merge。

## 边界规则

聊天中的结论不能覆盖 PRD 文档体系。

如果聊天结论与仓库文件不一致，则以仓库文档为准，或者立即补文档；否则该聊天结论不具备 canonical 地位。
