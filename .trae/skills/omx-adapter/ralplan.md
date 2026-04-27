---
name: ralplan
description: |
  Plan generation and approval workflow. Adapted from OMX $ralplan for Trae IDE.
  Use when: requirements are clear, need an approved implementation plan before coding.
  Triggers Architect/Critic agent review gates. Maps to: SearchCodebase + TodoWrite + plan file output.
---

# Ralplan (Plan Approval — Trae IDE Adaptation)

## Purpose

Generate a **review-quality implementation plan** from clarified requirements, get it approved, then produce an executable specification.

## When to Trigger

- After `deep-interview` completes with clear requirements
- User says "plan this" / "ralplan" / "make a plan"
- L2+ task needs architecture decision before coding
- Need to assess risk and break down work

## Execution Flow

### Input

Read from `.omx/context/{spec-slug}.md` (output of deep-interview) or directly from user request.

### Phase 1: Plan Generation

1. **Explore codebase** using `SearchCodebase`, `Glob`, `Read`:
   - Find existing patterns related to the task
   - Identify affected files and modules
   - Check existing tests, types, configs

2. **Generate plan** with these sections:
   ```markdown
   ## Implementation Plan: {title}

   ### Overview
   {One-liner}

   ### Approach
   {Technical approach, key decisions}

   ### Files to Change
   | File | Change Type | Risk |
   |------|------------|------|
   | ... | modify/create | low/med/high |

   ### Steps
   1. [ ] Step one (dependency)
   2. [ ] Step two (core change)
   3. [ ] Step three (verification)

   ### Verification
   - How to test: ...
   - Lint/typecheck: ...
   - Manual verification: ...

   ### Risks
   | Risk | Mitigation |
   |------|-----------|
   | ... | ... |

   ### Not Doing
   - Explicitly out of scope: ...
   ```

3. **Quality Gate Assessment**:
   - L1: Plan optional, can execute directly
   - L2: Plan recommended, lightweight review
   - L3: Plan **required**, review before execution
   - L4: Plan **mandatory** + formal review + exec-plan document

### Phase 2: Plan Review (Self-Critic / Architect)

For L3+ plans, perform internal review:

**Architect Review**:
- Soundness: Does approach match requirements?
- Boundary conditions: Edge cases covered?
- Layer dependencies: Clean separation?

**Critic Review** (from Harness CROSS-REVIEW-PROCESS):
- Logic correctness
- Codex ↔ HermesAgent boundary preserved?
- `.omx/` vs `harness/` confusion check
- Verification adequacy

### Phase 3: Approval

Present plan to user. Options:
- **Approve**: Proceed to `ralph` (or `team`) execution
- **Request changes**: Revise and re-present
- **Delegate**: For parallel work, dispatch via `team` skill

### Phase 4: Output

Write approved plan to `.omx/specs/{slug}.md`.

Create executable todo list via `TodoWrite` with all steps.

Update `.omx/state.md`:
- phase → `execution-ready`
- current_plan → `{slug}`

## Integration with Harness

- For L4 plans → also create `harness/exec-plans/{id}.md`
- If plan changes shared project truth → note for PRD update on closeout
- If HermesAgent should review → generate handoff packet alongside plan

## Good vs Bad Prompts

**Good**: "Plan the auth system refactoring with these requirements..."
**Bad**: "Fix the null pointer" (too small, just do it — use ralph directly)
