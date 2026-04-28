# Failure Patterns

## FP-001 — Chat-only decisions are not durable

- Symptom: important decisions exist only in group messages
- Consequence: future sessions lose rationale and actionability
- Fix: write accepted outcomes to `docs/` or `harness/`

## FP-002 — HermesAgent receives vague asks

- Symptom: Codex asks HermesAgent broad questions without a packet or artifacts
- Consequence: operations feedback is fuzzy and non-actionable
- Fix: always generate a handoff packet first

