---
name: hermes-group-dual
description: Use when work in CrazyAgentsManage requires adapting the old dual-cli workflow into Codex ↔ HermesAgent collaboration over Feishu group @mentions, with Codex owning development, HermesAgent owning operations, OMX storing runtime-local state, and harness/docs storing durable repository facts.
---

# Hermes Group Dual

This skill is the CrazyAgentsManage-local replacement for the old `dual-cli` workflow.

## What changed

Old model:

- Team A / Team B
- external CLI lanes
- PR comment driven rhythm

New model:

- `Codex` = development lane
- `HermesAgent` = operations lane
- Feishu group `@HermesAgent` handoff packets replace CLI dispatches

## Required files

Read these before using the workflow:

1. `docs/02-engineering/harness/HARNESS-ENTRY.md`
2. `docs/02-engineering/harness/CODEX-HERMES-WORKFLOW.md`
3. `docs/codex-hermes-role-design.md`

If HermesAgent needs explicit guidance, also read:

4. `docs/02-engineering/harness/HERMESAGENT-ENTRY.md`

## Non-negotiable rules

1. `.omx/` is runtime-local only.
2. `harness/` and `docs/` are the durable fact layer.
3. HermesAgent is not a second coding lane.
4. Codex must generate a structured handoff packet before asking HermesAgent to act.

## Default workflow

### Kickoff

Write runtime state:

```bash
python3 scripts/runtime/write_runtime_state.py \
  --phase kickoff \
  --status in_progress \
  --actor codex \
  --counterpart HermesAgent \
  --summary "Kickoff for CrazyAgentsManage round"
```

### Handoff

Generate a packet:

```bash
python3 scripts/runtime/generate_hermes_handoff.py \
  --title "Operations review needed" \
  --goal "Review the operator-facing impact" \
  --artifacts docs/codex-hermes-role-design.md \
  --questions "What is still missing for operations?"
```

Send or paraphrase that output to `@HermesAgent`.

### Closeout

Write a harness trace:

```bash
python3 scripts/runtime/closeout_writeback.py \
  --status success \
  --stage closeout \
  --message "Completed collaboration round" \
  --artifacts docs/codex-hermes-role-design.md
```

## When to use this skill

Use this skill when the task includes any of:

- `HermesAgent`
- Feishu group collaboration
- `@` mention based coordination
- CrazyAgentsManage runtime/handoff design
- adapting old `dual-cli` behavior for this repository

## What this skill should produce

- runtime snapshot
- Hermes handoff packet
- durable harness write-back when the round ends

