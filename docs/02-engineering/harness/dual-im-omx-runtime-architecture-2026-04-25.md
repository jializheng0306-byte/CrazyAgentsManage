# CrazyAgentsManage Group-Collaboration Runtime Architecture

> Date: 2026-04-25
> Source lineage: adapted from FlowMindDeploy `dual-cli + OMX + harness`

## Summary

The original three-layer model remains valid, but the orchestration lane changes:

- old: `codebuddy` + `qodercli` dual external CLI lanes
- new: `Codex` development lane + `HermesAgent` operations lane via Feishu group `@` collaboration

## Layer Mapping

### Layer 1: Orchestration

Old:

- `dual-cli`
- PR comments
- Team A / Team B lane ordering

New:

- Codex handoff packets
- HermesAgent operational review
- group-chat coordination using `@HermesAgent`

### Layer 2: Runtime substrate

Unchanged in principle:

- OMX runtime state
- local session trace
- runtime notepad/memory

### Layer 3: Durable learning

Unchanged in principle:

- `harness/exec-plans/`
- `harness/trace/failures/`
- `harness/trace/successes/`
- `harness/memory/`

## Explicit Rules

1. Runtime state stays under `.omx/`
2. Repository learning stays under `harness/`
3. HermesAgent receives structured packets, not implicit context
4. Chat is the transport surface, not the durable memory layer

## Recommended Current Entry Points

- runtime state writer:
  - `scripts/runtime/write_runtime_state.py`
- Hermes handoff generator:
  - `scripts/runtime/generate_hermes_handoff.py`
- closeout writer:
  - `scripts/runtime/closeout_writeback.py`

## Expected Outcome

This gives CrazyAgentsManage the same architectural separation that worked in FlowMindDeploy:

- runtime remains lightweight and local
- repository facts remain durable and reviewable
- collaboration remains explicit and role-shaped

