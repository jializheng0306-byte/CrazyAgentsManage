# Phase 5 Feedback Reverification — Crazy Main Table Writeback

> Date: 2026-05-03  
> Branch: `feat/auto-capture-trace`  
> Type: real writeback reverification  
> Scope: Crazy Promise Overview main table + Interaction Trace table

## Verified live objects

| Field | Value |
|---|---|
| candidateId | `219a5914-6c85-43df-ad5e-1d1d36241b39` |
| recordId | `219a5914-6c85-43df-ad5e-1d1d36241b39` |
| instanceId | `hermes-agent` |
| promise_id | `promise-phase5-c1-approved` |
| main table record_id | `recviza1xpm9BI` |
| main table app | `EpeXbhpF9a0s0wsh6axce9PknFg` |
| main table id | `tblJRMmjbyKEDZY1` |
| trace table id | `tbltwMndeV5O2YkR` |

## Read order used

1. `GET /api/bridge/truth/:candidateId`
2. `GET /api/bridge/trace/:candidateId`
3. `GET /api/bridge/feedback/:instanceId`
4. `GET /api/operator/records/:recordId/replay`

This round explicitly kept:

- `flowmind_status` sourced from `truth.status`
- `feedback` sourced into operational notes / trace rows only
- `moduleDetails.handoff` used as interpretation support, not as the primary status source

## Main table result

The live main table row for candidate `219a5914-6c85-43df-ad5e-1d1d36241b39` was updated to:

- `flowmind_status = approved`
- `trace_event_count = 7`
- `last_trace_summary = Crazy 验收已确认 Bitable 主表与时序图页面可用`
- `last_trace_at = 2026-05-03 08:55:59`
- `trace_summary = Crazy 验收已确认 Bitable 主表与时序图页面可用`
- `备注` now contains the feedback summaries:
  - `clarified`
  - `confirmed`

## Feedback handling result

The live feedback endpoint returned `200` and exposed two real events for `instanceId=hermes-agent`:

1. `clarified`
2. `confirmed`

These were consumed in two places:

- appended into main table `备注`
- written into the interaction trace table with:
  - `module = feedback`
  - `action = clarified / confirmed`

They did **not** overwrite `flowmind_status`.

## Trace table result

The live trace table now contains candidate-specific rows for:

- `create`
- `clarify`
- `confirm`
- `approve`
- `update`
- `clarified` (`module = feedback`)
- `confirmed` (`module = feedback`)

This confirms feedback is now consumed as a separate operational loop rather than being folded into the main candidate status field.

## Additional field repair completed

The live Promise Overview main table had been missing these fields:

- `flowmind_status`
- `last_trace_at`
- `trace_summary`

They were created before the writeback run, and then populated by the real run.

## Conclusion

`feedback` has moved from a runtime gap to a consumable read surface for Crazy main-table writeback.

What is now true:

- truth decides `flowmind_status`
- trace decides `trace_event_count / last_trace_summary / last_trace_at`
- feedback updates operational notes / trace rows
- handoff remains interpretation-only

This is sufficient to treat Crazy as having entered the minimum Phase 5 writeback loop for the verified candidate.
