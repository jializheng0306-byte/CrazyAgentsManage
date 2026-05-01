# Harness Infrastructure

CrazyAgentsManage 的 canonical harness core。

本目录中的内容是多 Agent 共用、受 Git 追踪的执行基础设施，不属于任何单一 Agent 的私有状态。

## 目录结构

- `exec-plans/`
  - 执行计划模板与已归档执行计划
- `trace/`
  - `failures/` 结构化失败记录，供 Critic 分析
  - `successes/` 成功模式记录，供流程固化
- `memory/`
  - `situational.md` 情景记忆
  - `procedural.md` 程序记忆
  - `failure-patterns.md` 失败模式注册表

## 使用原则

1. 这里是 canonical harness，不是 Agent 私有目录。
2. `.omx/` 是 runtime-local 辅助层，不得替代 `harness/`。
3. `docs/` 与 `harness/` 才是仓库共享事实层。
4. `Codex ↔ HermesAgent` 协作结论只有落入受追踪工件后才算 durable truth。

## 入口

- 总入口: [HARNESS-ENTRY.md](/home/flowmind/CrazyAgentsManage/docs/02-engineering/harness/HARNESS-ENTRY.md)
- 调度规范: [HAGENT-WORKFLOW.md](/home/flowmind/CrazyAgentsManage/docs/02-engineering/harness/HAGENT-WORKFLOW.md)
- 交叉审查: [CROSS-REVIEW-PROCESS.md](/home/flowmind/CrazyAgentsManage/docs/02-engineering/harness/CROSS-REVIEW-PROCESS.md)
- Worktree 引导: [WORKTREE-BOOTSTRAP.md](/home/flowmind/CrazyAgentsManage/docs/02-engineering/harness/WORKTREE-BOOTSTRAP.md)

## 当前状态

- Phase 1: Canonical harness core 已初始化
- Phase 2: Codex ↔ HermesAgent adapter layer 已落地
- Phase 3: worktree bootstrap 机制已迁入
- Phase 4: Critic / closeout 回写机制已迁入

## Critic 命令

```bash
node scripts/harness-critic.cjs
node scripts/harness-critic.cjs --days 3
node scripts/harness-critic.cjs --write-back
node scripts/harness-critic.cjs --json
node scripts/harness-closeout-writeback.cjs --status success --message "Round completed" --critic-write-back --json
node scripts/harness-closeout-writeback.cjs --status failed --message "Round failed" --stage verification --json
```

## Default Rule

如果当前会话学到的内容只对这一次 runtime 有意义，就放在 `.omx/`。

如果这条经验应该跨会话、跨迭代保留，就提升到 `harness/`。
