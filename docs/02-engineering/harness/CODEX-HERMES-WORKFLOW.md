# Codex ↔ HermesAgent Workflow

## Goal

Replace the old `codebuddy ↔ qodercli` dual-lane model with a role-split model:

- `Codex` = development lane
- `HermesAgent` = operations lane

The collaboration surface is a Feishu group conversation using `@` mentions, but the durable truth must live in repository artifacts.

## Role Contract

### Codex

- owns implementation
- owns schema and interface design
- owns verification
- owns generation of Hermes handoff packets
- owns promotion of accepted outcomes into repo facts

### HermesAgent

- owns operations framing
- owns runtime monitoring and daily operational interpretation
- owns operational acceptance criteria
- owns follow-up requests back to Codex from an operator perspective

## Collaboration Protocol

### 1. Kickoff

Codex creates a runtime snapshot:

```bash
python3 scripts/runtime/write_runtime_state.py \
  --phase kickoff \
  --status in_progress \
  --actor codex \
  --counterpart HermesAgent \
  --summary "Kickoff for CrazyAgentsManage collaboration round"
```

### 2. Produce handoff packet

Before asking HermesAgent to act, Codex generates a handoff packet:

```bash
python3 scripts/runtime/generate_hermes_handoff.py \
  --title "Need operations review" \
  --goal "Review runtime and operations impact" \
  --artifacts docs/codex-hermes-role-design.md \
  --questions "What operator view is still missing?"
```

The generated packet is what Codex sends or paraphrases in group chat to `@HermesAgent`.

### 3. HermesAgent review

HermesAgent responds with:

- missing operator-facing fields
- missing runtime signals
- missing operational actions
- acceptance or rejection from operations perspective

### 4. Codex closeout

After the round ends, Codex writes:

- runtime closeout snapshot in `.omx/`
- harness success/failure trace in `harness/trace/`
- optional memory update when the lesson is durable

## Durable Outputs

Use repository artifacts for:

- accepted workflow rules
- stable role contracts
- stable architecture decisions
- repeatable failure/success patterns

Use `.omx/` only for:

- current phase
- current summary
- current in-flight handoff context

## Anti-Patterns

Do not:

- treat group chat messages as the only collaboration log
- skip the handoff packet and ask HermesAgent vague questions
- write durable project truth only into `.omx/`
- let HermesAgent directly redefine development architecture without a repo artifact

