# CrazyAgentsManage Agent Adapter

This repository uses a three-layer collaboration model adapted from `FlowMindDeploy`:

1. `dual-cli` is replaced by a **Codex ↔ HermesAgent group-collaboration workflow**
2. `OMX` remains the **runtime/session substrate**
3. `harness/` remains the **repository-owned durable learning layer**

## Entry Rule

For Codex / OMX style agents, this file is an adapter entry, not the full harness.

Read these files in order before substantial work:

1. `docs/02-engineering/harness/HARNESS-ENTRY.md`
2. `docs/02-engineering/harness/CODEX-HERMES-WORKFLOW.md`
3. `docs/02-engineering/harness/CODEX-HERMES-COLLABORATION-MECHANISM.md`
4. `docs/codex-hermes-role-design.md`

If the task explicitly involves `HermesAgent`, Feishu group collaboration, handoff packets, or runtime state sync, also read:

5. `docs/02-engineering/harness/HERMESAGENT-ENTRY.md`
6. `.codex/skills/hermes-group-dual/SKILL.md`

## Working Rules

- Treat `docs/` and `harness/` as the canonical repository fact layer.
- Treat `.omx/` as runtime/session-local state, not as durable shared truth.
- `Codex` owns development, architecture, verification, and code changes.
- `HermesAgent` owns operations framing, runtime inspection, and operational acceptance.
- Cross-role coordination must flow through:
  - repository-tracked docs or harness artifacts
  - generated Hermes handoff packets
  - explicit runtime state snapshots

## Collaboration Boundary

- Do not model HermesAgent as a second coding lane.
- Do not treat group chat history as durable project memory by itself.
- When a Codex task needs HermesAgent participation, Codex must first produce:
  - a runtime state snapshot
  - a handoff packet addressed to HermesAgent
  - any repository artifact HermesAgent must review

## Verification

Before claiming completion for workflow changes:

- validate script syntax
- verify referenced paths exist
- confirm harness and docs layers stay separated from `.omx/`

## PIMO-TMO Domain Boundary (FR109)

Crazy 仓消费 FlowMindDeploy 生成的跨仓契约（`src/integrations/contracts/`），须遵守 PIMO 三层域边界。

**Canonical 源**: FlowMindDeploy `packages/ontology/semantic-dsl/contexts/pimo.domain_boundary.md`（status: canonical, evidence_class: INFERRED）。该条目定义 PIMO（Personal Information Management Ontology）三层域：Canonical / Repo-side / Host-side，及其包容关系 `Host PIMO ⊂ Repo PIMO ⊂ Canonical PIMO`。

### isDefinedBy 协作清单

`isDefinedBy ∈ {flowmind, team, host_pimo}` 封闭集合决定数据主权归属：

| 契约 | isDefinedBy | 权威来源 | Crazy 仓权限 |
|------|-------------|---------|-------------|
| `crazy.agent_task` | flowmind | FMD canonical DSL（Team A 独占写权） | 只读消费 |
| `crazy.promise` | flowmind | FMD canonical DSL（Team A 独占写权） | 只读消费 |
| `crazy.trace_event` | flowmind | FMD canonical DSL（Team A 独占写权） | 只读消费 |

本目录契约全部 `isDefinedBy: flowmind`，归属 FMD canonical 层。Crazy 仓只读消费，不得重定义、改写或裁定（Invariant 3：只读消费，不发明新 truth）。

### 方向不可逆声明

**FMD 生成 → Crazy 消费**（不可逆，FlowMindDeploy AGENTS.md 决策树 7）。Crazy 仓 `src/integrations/contracts/` 为生成物镜像，由 `.generated-marker` 标记禁止手改；字段级一致性由 FMD CI `scripts/governance/check_cross_repo_contract_diff.py` 守卫（Layer 1 self-check + Layer 2 跨仓 diff）。

### 三条跨层跃迁规则

1. **host→repo 须人审**：host_pimo 数据（Agent 个人 PTM：`.learnings/` / task list）须经人类 Review 形成受控 proposal，方可进入 repo_side 层（`docs/` / `changes/` / `releases/` / `harness/`）。
2. **repo→canonical 须 truth promotion**：repo_side 数据须经 truth promotion（approve/commit）方可进入 canonical 层（`packages/ontology/semantic-dsl/`）。
3. **host 直跳 canonical 禁止**：host_pimo 数据不得直接进入 canonical 层，必须先经 repo_side proposal 流程。

> Crazy 仓 Agent 个人执行记录属 host_side 层，`isDefinedBy: host_pimo`，不构成 canonical truth 的替代事实源（Invariant 15）。H4 愿景 / H5 宗旨内容属 canonical 层但只能由人类写入，Agent 不得生成或修改（Invariant 14）。
