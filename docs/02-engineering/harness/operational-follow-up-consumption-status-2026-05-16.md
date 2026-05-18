# Operational Follow-Up Consumption Status

> Date: 2026-05-16
> Status: actual-consumer-evidence
> Scope: CrazyAgentsManage consumer surfaces for the FlowMind Slice 1 `operationalFollowUp` projection

## What is now actually consumed

1. `src/webui/api.py`
   - `/api/runtime/handoffs?recordId=...` now exposes `operationalFollowUp` in the normalized response.
   - Priority order:
     - upstream `replay.operationalFollowUp`
     - fallback to `moduleDetails.handoff` -> `Operational Follow-Up` section
   - Constraint: Crazy does not derive a new local follow-up interpretation when FlowMind already emitted a projection.

2. `scripts/runtime/generate_hermes_handoff.py`
   - Hermes handoff packets now include an `Operational follow-up` block when `bridge/truth` payloads contain the projection.
   - The packet carries upstream fields directly so HermesAgent can review the same Slice 1 projection without re-parsing prose.

3. `src/webui/static/js/timeline.js` + `src/webui/templates/timeline.html`
   - Crazy timeline / handoff page now renders an `Operational Follow-Up` block inside the existing handoff summary card.
   - The page only displays API-returned projection fields and shows an explicit gap box when replay omitted the projection.
   - Constraint: the page does not infer `needsFollowUp`, `followUpKind`, or `nextActor` locally.

4. `scripts/daily-promise-review.py`
   - Promise-side review runtime now consumes `truth.operationalFollowUp` during scheduled review aggregation.
   - The review digest includes `follow_up_kind`, `next_actor`, `needs_follow_up`, and `last_governance_feedback`, so follow-up changes now count as review-state changes.
   - Bitable main-table sync now writes follow-up summary fields and appends follow-up status into the promise remark path.

5. Regression coverage
   - `tests/test_sprint4.py`
     - verifies runtime handoff API exposes upstream projection
     - verifies fallback extraction from `moduleDetails.handoff` when top-level projection is absent
     - verifies timeline page assets expose the new follow-up rendering surface
   - `tests/test_generate_hermes_handoff.py`
     - verifies Hermes handoff packet renders follow-up fields when truth payload includes them
   - `tests/test_daily_promise_review_contract.py`
     - verifies promise review digest changes when operational follow-up changes
     - verifies promise review normalization reads the upstream projection directly

## What is still not done

1. Promise-side consumption is now proven at scheduled-review / Bitable-sync level, but not yet at a dedicated Hermes writeback endpoint with its own explicit read/write contract.
2. Any future expansion of `followUpKind` or `nextActor` still has to start from FlowMind canonical docs and mirror sync, not local Crazy changes.

## Current conclusion

The mirror / compatibility sync is no longer docs-only.
Crazy now has two real consumer surfaces for the shared Slice 1 projection:

- runtime handoff API
- Hermes handoff packet
- Crazy timeline / handoff page
- promise-side scheduled review + Bitable main-table sync

This is enough to keep Slice 2 gated while still proving that the mirrored operational follow-up model is consumed outside FlowMind.
