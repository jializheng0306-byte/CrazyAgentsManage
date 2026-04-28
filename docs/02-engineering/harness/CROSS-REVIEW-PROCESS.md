# Cross Review Process

多 Agent 开发中的交叉审查流程。

## 1. 目的

交叉审查的目标不是增加仪式，而是减少自写自审的盲区。

重点检查：

- 逻辑正确性
- 架构边界
- 运行时与治理语义是否漂移
- 验证是否充分
- durable truth 是否被正确写回

## 2. 何时必须交叉审查

| 场景 | 是否必须 |
|---|---|
| L1 微调 | 否 |
| L2 常规改动 | 视风险而定 |
| L3 多文件改动 | 建议 |
| L4 架构、协作协议、Harness 机制改动 | 必须 |
| 影响 PRD / roadmap / closeout 规则 | 必须 |
| 安全、数据迁移、控制面动作 | 必须 |

## 3. 审查输入

- 任务目标
- 受影响文件
- 关联 PRD / roadmap
- 关联 exec plan
- 验证结果
- 如适用，Hermes handoff 与 closeout evidence

## 4. 审查维度

1. 逻辑正确性
2. 边界条件
3. 分层依赖方向
4. `Codex ↔ HermesAgent` 职责边界是否被破坏
5. 命名与可读性
6. 验证是否覆盖主要声明
7. 是否把 agent 私有状态误当成产品工件
8. 是否把 `.omx/` 与 `harness/` 的职责混淆

## 5. 输出格式

### PASS

- 结论
- 已检查维度
- 剩余小风险

### NEEDS_FIX

- 问题
- 影响
- 建议修复
- 是否需要重新验证

## 6. 与 Harness 记忆的关系

如果相同问题重复出现，应该沉淀到：

- `harness/memory/failure-patterns.md`
- `harness/memory/procedural.md`
- 或转成 lint / doc / template 更新
