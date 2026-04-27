---
name: deep-interview
description: |
  Structured deep interview for requirement clarification. Adapted from OMX $deep-interview
  for Trae IDE. Use when: request is broad, ambiguous, lacks clear boundaries,
  or user says "interview me" / "clarify" / "deep-interview".
  Maps to: AskUserQuestion tool + .omx/context/ writeback.
---

# Deep Interview (Trae IDE Adaptation)

## Purpose

Turn vague, broad, or ambiguous user requests into **explicit, bounded, actionable specifications** before any implementation begins.

## When to Trigger

- User request is broad ("fix the dashboard", "improve performance")
- Request has unclear boundaries or missing constraints
- User explicitly asks for clarification/interview
- L3/L4 complexity task that needs solid foundation first
- Multiple valid interpretations exist

## When NOT to Trigger

- Request is already a concrete, specific coding task
- User provides a detailed PRD/ticket with clear acceptance criteria
- Simple L1 bug fix with obvious scope

## Interview Profiles (from OMX)

| Profile | Depth | Target | Rounds | Best For |
|--------|-------|--------|--------|----------|
| `quick` | Shallow | Fast pre-PRD pass | ≤3 | Quick tasks, already-has-some-context |
| `standard` | Full | Thorough requirements | ~5-12 | Default for new features |
| `deep` | High-rigor | Exhaustive exploration | ≤20 | Architecture, complex systems |

## Execution Steps

### Step 0: Preflight Context Intake

1. Parse `{ARGUMENTS}` from the task description
2. Detect project context:
   - Run `explore` to classify *brownfield* vs *greenfield*
   - Check `.omx/context/` for existing interview snapshots
   - Load relevant context if snapshot exists
3. Initialize state via `state_write(mode="deep-interview")`

### Step 1: Initialize Interview State

Write to `.omx/context/{slug}.md`:

```json
{
  "active": true,
  "current_hash": "deep-interview",
  "profile": "<quick|standard|deep>",
  "type": "greenfield|brownfield",
  "initial_idea": "<user input>",
  "rounds": [],
  "current_ambiguity": 1.0,
  "current_confidence": {"codex": 1.0, "user": 0},
  "context": { "slug": "<slug>", "type": "...", ... },
  "codebase_context": null,
  "stage": "intent-first"
}
```

### Step 2: Social Interview Loop

For each round, use `AskUserQuestion` with these dimensions:

**Round 1 — Intent Clarity** (always required):
- Intent: What does the user want?
- Outcome Clarity: What does "done" look like?
- Scope Clarity: How big/wide is this?
- Context Clarity: Existing codebase understanding?

**Round 2 — Feasibility & Boundaries** (if ambiguity remains):
- Constraints: Technical, business, time?
- Known Facts: What exists already?
- Decision Boundaries: What decisions can I make vs need approval?

**Round 3 — Challenge Modes** (for standard/deep):
- Contrarian: What if we did the opposite?
- Simplifier: What's the minimal version?
- Ontologist: What are the core entities and relationships?

### Step 3: Crystallize Artifacts

When interview converges, write execution-ready spec:

```markdown
## Task Specification: {slug}

### Intent
{what + why}

### Non-goals
{explicitly out of scope}

### Scope Classification
- Level: L1|L2|L3|L4
- Type: greenfield|brownfield
- Risk: low|medium|high

### Requirements
#### Functional
- RF-001: ...
- RF-002: ...

#### Non-Functional
- NFP-001: ...
- NFP-002: ...

### Constraints
- Technical: ...
- Business: ...
- Timebox: ...

### Acceptance Criteria
- AC-001: ...
- AC-002: ...

### Artifacts Needed
- Files to modify: ...
- New files: ...
- Docs to update: ...
```

### Step 4: Update State

Update `.omx/state.md`:
- phase → `planning-ready`
- summary → interview completed
- current_spec → `{slug}`

## Integration with Harness

After interview completes:
1. If task involves HermesAgent operations review → flag for handoff
2. Write spec to both `.omx/specs/{slug}.md` AND consider `harness/exec-plans/` for reusable patterns
3. For L3/L4 tasks → automatically trigger `ralplan` next

## Cancellation Conditions

- User says stop/cancel → persist state, write partial spec
- Ambiguity stuck after Round 5+ → propose best-guess spec for approval
- Max rounds reached → crystallize with explicit assumptions noted
