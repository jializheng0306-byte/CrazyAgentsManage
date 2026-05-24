# Harness Infrastructure

CrazyAgentsManage 的 canonical harness core。

## One-Page Summary

### 这个目录解决什么问题

- 固定 Crazy 的 repository-owned harness 事实层
- 给 Codex ↔ HermesAgent 协作提供可复验的 closeout、critic、记忆与治理入口
- 避免 `.omx/`、群聊、临时状态替代仓库事实

### 谁应该读

- 需要做 closeout、cross-review、critic write-back 的人
- 需要判断哪些信息必须进入仓库事实层的人
- 需要沿着双仓治理线补脚本和规则的人

### 先读哪三份

1. [HARNESS-ENTRY.md](/home/flowmind/CrazyAgentsManage/docs/02-engineering/harness/HARNESS-ENTRY.md)
2. [CROSS-REVIEW-PROCESS.md](/home/flowmind/CrazyAgentsManage/docs/02-engineering/harness/CROSS-REVIEW-PROCESS.md)
3. [SEMANTIC-FIRST-READING-RULE.md](/home/flowmind/CrazyAgentsManage/docs/02-engineering/harness/SEMANTIC-FIRST-READING-RULE.md)

### 典型工作流

1. 先跑 `./scripts/check_harness_governance_all.sh`
2. 再做 cross-review / closeout
3. 最后把成功、失败、critic 和 PRD/roadmap 回写到仓库

### 常见误区

- 只跑本地局部脚本，不跑全量治理入口
- 把 `.omx/` runtime state 当成 durable truth
- 让 evidence 文档、兼容矩阵、消费状态三者口径分裂

本目录中的内容是多 Agent 共用、受 Git 追踪的执行基础设施，不属于任何单一 Agent 的私有状态。

## 目录结构

- `exec-plans/`
  - 执行计划模板与已归档执行计划
- `trace/`
  - `failures/` 结构化失败记录，供 Critic 分析
  - `successes/` 成功模式记录，供流程固化
- `closeouts/`
  - 非平凡迭代的结构化 closeout 记录，绑定 trace / critic / governance / worktree lane
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
./scripts/check_harness_governance.sh
./scripts/check_harness_governance.sh --with-cross-repo
./scripts/check_harness_governance.sh --local-only
./scripts/check_harness_governance_all.sh
./scripts/check_harness_governance_all.sh --skip-cross-repo
python3 scripts/check_harness_closeout_chain.py
node scripts/harness-closeout-writeback.cjs --status success --message "Round completed" --critic-write-back --json
node scripts/harness-closeout-writeback.cjs --status failed --message "Round failed" --stage verification --json
```

## Governance Gate

- PR / cross-review 前，先运行 `./scripts/check_harness_governance.sh`
- 如果 FlowMind 双仓同步检查器已就位，再运行 `./scripts/check_harness_governance.sh --with-cross-repo`
- 推荐默认入口：`./scripts/check_harness_governance_all.sh`
- `status=success` 的 closeout 会默认执行全量治理检查；失败则直接阻断 closeout
- `status=failed` 的 closeout 默认不阻断，便于记录失败现场；如需强制执行可加 `--governance-check`
- 当前治理检查会回写报告到 `docs/02-engineering/harness/harness-governance-report.md`
- closeout writeback 会把当前 harness 治理报告与 FlowMind 的 architecture drift 报告摘要一起写入 `governanceReports`

## Default Rule

如果当前会话学到的内容只对这一次 runtime 有意义，就放在 `.omx/`。

如果这条经验应该跨会话、跨迭代保留，就提升到 `harness/`。
