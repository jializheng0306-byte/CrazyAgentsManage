---
name: trace
description: |
  Session timeline and summary display. Adapted from OMX $trace for Trae IDE.
  Shows the complete agent flow trace: which hooks fired, keywords used,
  skills invoked, agents dispatched, modes transitioned, tools called.
  Auto-generated from session activity, not manually invoked.
---

# Trace (Session Timeline — Trae IDE Adaptation)

## Purpose

Display the **complete session flow timeline** showing how the agent arrived at the current state.

## What It Shows

### Timeline View (chronological)

```
[TIME] MODE: {mode}  PHASE: {phase}
  ├─ Keyword/Tool: {what triggered}
  ├─ Skill: {which skill activated}
  ├─ Agent: {sub-agent if dispatched}
  ├─ Files: {read/written}
  └─ Note: {brief outcome}
```

### Summary View (aggregated)

- **Mode transitions**: How many times each mode was entered
- **Skills activated**: Which skills were invoked and their outcomes
- **Tools called**: Frequency and purpose of tool usage
- **Flow patterns**: keyword → skill → agent chain

## How Trace Data Is Collected

In Trae IDE adaptation, trace data comes from:

1. **`.omx/state.md`** — Phase/mode transitions recorded at each state change
2. **`.omx/logs/{date}.md`** — Manual trace entries written at significant steps
3. **`TodoWrite` history** — Task completion timeline
4. **Harness trace records** — `harness/trace/successes/*.json` at closeout

## Trace Entry Format

Append to `.omx/logs/{YYYYMMDD}.md`:

```markdown
## [{ISO_TIMESTAMP}] {EVENT_TYPE}

- **Phase**: {init|interview|planning|execution|closeout}
- **Mode**: {deep-interview|ralplan|ralph|team|...}
- **Trigger**: {user_input or automatic}
- **Action**: {what the agent did}
- **Files**: {affected files}
- **Outcome**: {success|failure|partial|pending}
- **Next**: {what happens next}
```

## When to Write Trace Entries

| Event | Write Trace? |
|-------|-------------|
| Phase transition | **Always** |
| Skill invocation start | Yes |
| Skill invocation end | **Always** (with outcome) |
| Sub-agent dispatch | Yes |
| Sub-agent result received | **Always** |
| Error/Failure | **Always** (with diagnosis) |
| User interruption | Yes |
| Closeout | **Always** (final summary) |

## Output Example

When user or system requests `$trace` or session summary:

```markdown
## Session Trace Summary

**Session ID**: {uuid}
**Duration**: {start} → {end}
**Final Phase**: {phase}
**Final Status**: {status}

### Mode Timeline
| Time | Mode | Duration | Events |
|------|------|----------|--------|
| T+0 | init | 3s | Session started |
| T+3 | deep-interview | 2min | 3 rounds, converged |
| T+123 | ralplan | 45s | Plan generated, approved |
| T+168 | ralph | 15min | 7/8 steps completed |
| T+1068 | closeout | 10s | Success traced |

### Skills Used
| Skill | Invocations | Avg Duration | Success Rate |
|-------|-------------|-------------|--------------|
| deep-interview | 1 | 2m | 100% |
| ralplan | 1 | 45s | 100% |
| ralph | 1 | 15m | 87.5% |

### Tools Used
| Tool | Calls | Primary Purpose |
|------|-------|----------------|
| Read | 23 | Code inspection |
| Write/Edit | 8 | Implementation |
| RunCommand | 12 | Test/lint/verify |
| SearchCodebase | 5 | Pattern finding |
| AskUserQuestion | 3 | Clarification |
| TodoWrite | 4 | Progress tracking |

### Bottlenecks
1. Step 5 (integration test) — 3 retries needed
2. Interview Round 2 — user ambiguity on scope
```
