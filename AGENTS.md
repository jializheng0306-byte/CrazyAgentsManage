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
5. `docs/02-engineering/harness/SEMANTIC-FIRST-READING-RULE.md` for `candidate / promise / truth / trace / review / feedback` work

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

## Semantic-First Trigger

When the task involves `candidate`, `promise`, `truth`, `trace`, `review`, or `feedback`, do not start from page code, scripts, runtime snapshots, or chat history.

Read in this order:

1. semantic/contract layer
2. cross-repo product and collaboration layer
3. Hermes host-platform operations layer
4. raw implementation only after the first three layers

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

## Auto-Capture Trace Post-Hook

When a HermesAgent task completes and its type is one of:
- `external-intel-collect`
- `morning-intel`
- `evening-trend`

The agent MUST run the auto-capture trace script as a post-processing step:
- Script: `scripts/auto-trace-to-bitable.py`
- Input: JSON with `source_task` and `raw_content` (the full task output text)
- Failure behavior: log warning, do NOT block the main task
- Log: `~/.hermes/logs/auto-capture-trace.log`
