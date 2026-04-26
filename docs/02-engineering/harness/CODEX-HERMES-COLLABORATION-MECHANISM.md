# Codex ↔ HermesAgent Collaboration Mechanism

## Purpose

This document is the execution contract that follows the role-boundary discussion.

It answers one practical question:

How should `Codex` and `HermesAgent` collaborate after the role split is already agreed?

The answer is:

- `Codex` owns implementation and repository truth changes
- `HermesAgent` owns operations review and operational acceptance
- collaboration must move through explicit repository artifacts and structured handoff packets
- group chat remains the coordination transport, not the durable source of truth

## Status

This mechanism is now the working baseline for CrazyAgentsManage.

Role-boundary debate is considered closed unless new evidence contradicts the current model.

## Operating Model

### Lane ownership

- `Codex` lane:
  - domain modeling
  - frontend/backend implementation
  - integration wiring
  - verification
  - repository artifact promotion

- `HermesAgent` lane:
  - operations critique
  - runtime observation
  - operator-facing completeness review
  - operational acceptance / rejection
  - post-delivery feedback to Codex

### Shared rule

Neither lane may treat chat-only conclusions as durable project truth.

Durable truth must be written into:

- `docs/`
- `harness/`
- tracked repository files that define real behavior

## Collaboration Lifecycle

### Phase 1: Kickoff

Codex creates or updates runtime-local execution state in `.omx/`.

Use:

```bash
python3 scripts/runtime/write_runtime_state.py \
  --phase kickoff \
  --status in_progress \
  --actor codex \
  --counterpart HermesAgent \
  --summary "Kickoff for collaboration round"
```

### Phase 2: Handoff

Codex generates a structured packet for HermesAgent.

Use:

```bash
python3 scripts/runtime/generate_hermes_handoff.py \
  --title "Operations review needed" \
  --goal "Review operator-facing impact" \
  --artifacts docs/codex-hermes-role-design.md \
  --questions "What is still missing for operations?"
```

The generated output is what should be sent to `@HermesAgent`.

### Phase 3: Hermes review

HermesAgent reviews from an operations perspective and responds with:

- runtime gap
- operations gap
- missing signal
- missing action
- accept / reject
- follow-up requested from Codex

### Phase 4: Codex implementation or correction

Codex either:

- implements the required changes
- corrects the repository contract
- or explains why a requested change should be deferred

### Phase 5: Closeout

Codex writes durable learning artifacts at round close.

Use:

```bash
python3 scripts/runtime/closeout_writeback.py \
  --status success \
  --stage closeout \
  --message "Completed Codex/HermesAgent round" \
  --artifacts docs/codex-hermes-role-design.md
```

## Escalation Rules

### When Codex must ask HermesAgent

Codex should involve HermesAgent when:

- a new page or API claims to support operations use
- a runtime signal is being exposed for operators
- a workflow or cron surface is being shaped
- a skill/agent/team governance boundary is changing
- a FlowMind integration status surface is introduced or revised

### When HermesAgent should not block Codex

HermesAgent should not reopen role-boundary discussion when:

- the current work is implementation of already accepted responsibilities
- the missing item is clearly a repo-local artifact gap
- the issue is a concrete runtime wiring task rather than a product-boundary dispute

### When role discussion may reopen

Only reopen role-boundary discussion if:

- current server/runtime evidence contradicts the accepted operating model
- a new lane needs ownership that does not fit either Codex or HermesAgent
- Hermes begins doing actual development implementation, or Codex begins acting as the operations controller by default

## Current Execution Priorities

### P0

These are the first items to execute after the role discussion closes:

1. land `scripts/runtime/*`
2. expose real runtime signals
3. connect CrazyAgentsManage to Hermes Cron API
4. add session stuck inference

### P1

These come after P0:

1. add operator task dispatch entry
2. unify skill path scanning
3. expand operational UI controls

### Re-evaluation trigger

After P0 is complete, re-evaluate whether the dispatch entry must move from P1 to immediate-next.

## Artifact Rules

### Repo-local

- `scripts/runtime/*`
- `docs/02-engineering/harness/*`
- `harness/*`
- `.omx/` generated runtime state

### Hermes runtime

- `~/.hermes/memories/`
- `~/.hermes/cron/`
- `state.db`
- `gateway_state.json`

### Future-only

- `~/.hermes/teams/`
- `~/.hermes/shared-context/`

Do not treat future-only items as current-environment defects.

## Done Criteria For The Role Discussion

The role discussion is considered closed when all of the following are true:

1. `docs/codex-hermes-role-design.md` is pushed
2. this collaboration mechanism document is pushed
3. AGENTS / harness entrypoints reference the collaboration mechanism
4. HermesAgent confirms it will engage on operational acceptance, not role-boundary debate, unless new evidence appears

## Current Conclusion

The current collaboration model is:

- stable enough to execute
- no longer in debate mode
- ready to move into implementation and operations acceptance

