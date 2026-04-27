---
name: team
description: |
  Coordinated parallel execution dispatch. Adapted from OMX $team for Trae IDE.
  Use when: approved plan has independent parallel work items, L3+ task needing
  coordinated multi-agent execution. Maps to: Task tool sub-agent dispatch.
---

# Team (Coordinated Parallel Execution — Trae IDE Adaptation)

## Purpose

Dispatch **independent work items to multiple sub-agents** executing in parallel, then collect and integrate results.

## When to Use

- Approved plan has clearly independent parallel tracks
- L3+ task with separable work items
- Need coordinated multi-file/multi-module changes
- Performance-critical path benefits from parallelism

## When NOT to Use

- Sequential dependencies between steps → use `ralph`
- Single simple task → execute directly
- No clear parallel boundaries → don't force it

## Canonical Pipeline

```
team-plan → team-exec → team-verify → team-fix → (loop) → team-closeout
```

### 1. Team Plan

Analyze the approved plan and identify parallelizable work streams:

```yaml
team-name: "{task-slug}-team"
tracks:
  - name: "track-a"
    agent: "search"          # or browser_use
    goal: "..."
    spec: "specific instruction for this track"
    inputs: [...]
    outputs: [...]
  - name: "track-b"
    agent: "search"
    goal: "..."
    spec: "..."
```

**Constraints**:
- Max 6 concurrent agents (OMX default)
- Each track must have clear goal, spec, and expected outputs
- Tracks must be truly independent (no file conflicts)

### 2. Team Execute

Use `Task` tool to dispatch each track:

- **agent type**: `search` for code research/review tasks, `browser_use` for web tasks
- **query**: Detailed instruction including goal, scope, files to read/modify, expected output format
- **response_language**: Consistent language for result integration

### 3. Team Verify

After all tracks complete:

1. Collect results from each track
2. Verify no conflicts (file overlaps, logical contradictions)
3. Run integration verification:
   ```bash
   # Full project-level verification
   <lint command>
   <typecheck command>
   <test command>
   ```
4. Document what each track produced

### 4. Team Fix (if needed)

If verification fails:
- Identify which track(s) caused the issue
- Dispatch targeted fix task(s)
- Re-verify

### 5. Team Closeout

1. Write team execution summary to `.omx/logs/`
2. Record success/failure trace per track
3. If any track failed → record failure with track attribution
4. Promote lessons to harness memory if reusable pattern discovered

## Integration with Harness

Team execution produces **multiple traces**:
- One overall team trace in `harness/trace/successes/` or `failures/`
- Per-track annotations within the trace JSON
- Team coordination lessons in `harness/memory/procedural.md` if pattern emerges

## Failure Mode Handling

| Mode | Action |
|------|--------|
| Single track fails | Fix that track, others keep results |
| Integration conflict | Resolve in ralph loop, don't re-dispatch |
| All tracks fail | Full rollback, record failure, escalate |
| Timeout | Partial results saved, decision point for user |
