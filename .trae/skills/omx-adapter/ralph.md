---
name: ralph
description: |
  Persistent single-owner execution loop. Adapted from OMX $ralph for Trae IDE.
  Use when: plan is approved, need sequential execution with verification after each step.
  This is the DEFAULT execution mode for Trae IDE agent in CrazyAgentsManage.
---

# Ralph (Persistent Execution — Trae IDE Adaptation)

## Purpose

Execute an approved plan **sequentially** with persistent ownership, verification after each step, and auto-recovery from failures.

## When to Use

- **Default execution mode** for most tasks
- Single-owner sufficient (no need for parallel `team`)
- Plan already approved via `ralplan`
- L1-L3 complexity tasks

## When NOT to Use

- Need coordinated parallel work → use `team` instead
- No plan yet → use `ralplan` first
- Request is trivial and already scoped → execute directly

## Execution Protocol

### Pre-Execution Checklist

1. Read plan from `.omx/specs/{slug}.md`
2. Verify all prerequisites (dependencies, environment, context)
3. Initialize `TodoWrite` with all plan steps
4. Set `.omx/state.md` phase → `execution`, status → `in_progress`

### Main Loop (Per Step)

For each step in the plan:

```
┌─────────────┐
│  1. EXECUTE  │ ← Implement the step (edit files, write code)
└──────┬──────┘
       ▼
┌─────────────┐
│ 2. VERIFY   │ ← RunCommand: lint, typecheck, test as applicable
└──────┬──────┘
       ▼
   ┌────┴────┐
   │ Pass?   │
   └──┬───┬──┘
     Yes  No
      │   │
      │   ▼
      │ ┌─────────────┐
      │ │ 3. RECOVER  │ ← Diagnose, fix, retry (build-fix cycle)
      │ └──────┬──────┘
      │        │
      │    Retry limit?
      │     ├──Yes → Escalate, mark blocked, ask user
      │     └──No──→ Loop back to EXECUTE
      │
      ▼
┌─────────────┐
│ 4. ADVANCE  │ ← Mark TodoWrite item complete, move to next step
└─────────────┘
```

### Recovery Strategy (Build-Fix Cycle)

When a step fails:

1. **Diagnose**: Read error output, identify root cause
2. **Fix**: Apply targeted fix (not full rewrite)
3. **Verify**: Re-run verification
4. **Loop**: Max 3 recovery attempts per step
5. **Escalate**: After 3 failures → stop, report to user

### Completion

When all steps done:
1. Run final verification (full test suite, lint, typecheck)
2. Write execution trace to `.omx/logs/{timestamp}.md`
3. Trigger closeout flow:
   - `node scripts/record-success.cjs`
   - Update harness memory if lessons learned
   - Generate Hermes handoff if needed
4. Update `.omx/state.md` phase → `closeout`

## Integration with Harness

Each ralph execution round MUST produce:
1. Runtime state updates in `.omx/state.md`
2. Success/failure trace in `harness/trace/` (via record-success/record-failure scripts)
3. Memory promotion if cross-session lesson learned
4. Hermes handoff packet if operations review needed

## State Management During Execution

`.omx/state.md` transitions:
```
init → interview → planning → execution(in_progress) → closeout
                              ↓ (on failure)
                         execution(blocked) → recovery → execution
```
