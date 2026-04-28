---
name: omx-adapter
description: |
  Core OMX (oh-my-codex) adapter for Trae IDE. Maps the OMX workflow layer
  (deep-interview → ralplan → ralph/team) to Trae IDE native capabilities
  while maintaining full integration with CrazyAgentsManage Harness mechanism.
  Use this when: any development task in CrazyAgentsManage needs structured workflow,
  plan-then-execute discipline, runtime state tracking, or Harness closeout integration.
---

# OMX Adapter for Trae IDE

## What This Is

This is the **Trae IDE adaptation layer** for [oh-my-codex](https://github.com/Yeachan-Heo/oh-my-codex) (OMX).

OMX was designed as a workflow layer for **OpenAI Codex CLI**. This adapter maps its core concepts to **Trae IDE**'s native agent capabilities while preserving full integration with the **CrazyAgentsManage Harness** system.

## Architecture Mapping

```
┌─────────────────── OMX Original ──────────────────┐    ┌──────────────── Trae IDE Adaptation ────────────────┐
│ $deep-interview   → Clarification via AskUserQuestion │    │ interview mode  → Structured clarification      │
│ $ralplan          → Plan approval with Architect/Critic │    │ plan mode       → TodoWrite + explicit approval  │
│ $ralph            → Persistent execution loop            │    │ Agent Mode      → Default continuous execution  │
│ $team             → Task tool with sub-agent dispatch   │    │ Task tool       → Parallel sub-agent execution   │
│ $trace            → Timeline/summary display             │    │ TodoWrite       → Progress tracking              │
│ .omx/state.md     → Runtime state JSON                 │    │ .omx/state.md   → Same (runtime-local)           │
│ AGENTS.md         → Operating contract                  │    │ SKILL.md + rules→ Operating contract             │
└────────────────────────────────────────────────────┘    └────────────────────────────────────────────────────┘
                            │                                              │
                            ▼                                              ▼
              ┌─────────────────────────────────────────────────────────────┐
              │        CrazyAgentsManage Harness Layer (Git-tracked)        │
              │  harness/trace/  harness/memory/  harness/exec-plans/       │
              │  scripts/runtime/*.py  scripts/harness-*.cjs               │
              └─────────────────────────────────────────────────────────────┘
```

## The OMX Workflow in Trae IDE

### Phase 1: Deep Interview (Clarification)

**Trigger**: User request is broad, ambiguous, or lacks clear boundaries.

**What happens**:
1. Use `AskUserQuestion` to gather structured requirements
2. Write context snapshot to `.omx/context/{slug}.md`
3. Update `.omx/state.md` phase → `interview`
4. Produce a structured requirement spec

**Output**: Clear, bounded, agreed-upon task definition.

### Phase 2: Ralplan (Plan Approval)

**Trigger**: Requirements are clear, need an approved execution plan.

**What happens**:
1. Analyze codebase using `SearchCodebase` / `Glob` / `Read`
2. Generate implementation plan with:
   - Steps (ordered)
   - Files affected
   - Risk assessment
   - Verification approach
3. Use `TodoWrite` to create tracked task list
4. Write approved plan to `.omx/specs/{slug}.md`
5. Update `.omx/state.md` phase → `planning`

**Plan Quality Gates (from OMX)**:
- L1 (single file): Single Agent, direct execution
- L2 (single module): Plan + lightweight review
- L3 (multi-file): Independent worktree + review
- L4 (architecture change): Exec plan + **mandatory review**

### Phase 3: Ralph / Team (Execution)

**Trigger**: Plan is approved, ready to implement.

**Two paths**:

#### Path A: Ralph (Single-owner persistent loop)
- Execute steps sequentially from the plan
- Verify each step before moving on
- Use `RunCommand` for build/test/lint
- Update progress via `TodoWrite`
- Auto-recover from failures (build-fix cycle)

#### Path B: Team (Coordinated parallel)
- Use `Task` tool with `search` or `browser_use` subagent type
- Dispatch independent work items in parallel
- Collect results and integrate
- For L3/L4 tasks, coordinate through worktrees

### Phase 4: Closeout & Harness Integration

**Trigger**: All tasks completed or decision to stop.

**What happens**:
1. Run verification (lint, typecheck, tests)
2. Write success/failure trace:
   ```bash
   node scripts/record-success.cjs   # or record-failure.cjs
   ```
3. If HermesAgent involvement needed:
   ```bash
   python3 scripts/runtime/generate_hermes_handoff.py ...
   ```
4. Promote durable lessons:
   - Process lessons → `harness/memory/procedural.md`
   - Failure patterns → `harness/memory/failure-patterns.md`
5. Update `.omx/state.md` phase → `closeout`

## Runtime State Management

The agent MUST maintain `.omx/state.md` with current session info:

```json
{
  "mode": "active",
  "session_id": "<uuid>",
  "phase": "init|interview|planning|execution|closeout",
  "status": "idle|in_progress|blocked|completed",
  "actor": "trae-agent",
  "counterpart": null,
  "summary": "...",
  "current_plan": "<spec-slug-or-null>",
  "handoff_context": {}
}
```

## Harness Integration Rules

1. **Before any significant work**: Read `AGENTS.md` → `HARNESS-ENTRY.md` → relevant docs
2. **When HermesAgent needed**: Generate handoff packet first, never ask vague questions
3. **On closeout**: Always write trace to `harness/trace/`, not just `.omx/`
4. **Durable truth**: Only `docs/` + `harness/` count; `.omx/` is session-local
5. **Complexity check**: Always assess L1-L4 before starting execution

## Anti-Patterns (from OMX + Harness)

- Do NOT skip clarification for vague requests (OMX FP)
- Do NOT execute without a plan for L3+ tasks (Harness rule)
- Do NOT write durable truth only into `.omx/` (Harness canonical rule)
- Do NOT treat chat conclusions as repository facts (Harness FP-001)
- Do NOT ask HermesAgent without a handoff packet (Harness FP-002)

## Available Sub-Skills

This adapter coordinates these workflow skills (all in `.trae/skills/omx-adapter/`):

| Skill | OMX Equivalent | Purpose |
|-------|----------------|---------|
| `deep-interview` | `$deep-interview` | Structured requirement clarification |
| `ralplan` | `$ralplan` | Plan generation with quality gates |
| `ralph` | `$ralph` | Persistent single-owner execution loop |
| `team` | `$team` | Coordinated parallel dispatch |
| `trace` | `$trace` | Session timeline and summary |
| `build-fix` | `$build-fix` | Build error recovery cycle |

## When to Use Each Path

```
Request received
    │
    ├─ Vague? ───→ deep-interview ──→ Clear requirements
    │
    ├─ Clear but complex? ──→ ralplan ──→ Approved plan
    │
    ├─ Plan approved?
    │    ├─ Single owner sufficient? ──→ ralph (sequential)
    │    └─ Needs parallel work? ──→ team (coordinated)
    │
    └─ Done? ──→ closeout ──→ Harness trace writeback
```
