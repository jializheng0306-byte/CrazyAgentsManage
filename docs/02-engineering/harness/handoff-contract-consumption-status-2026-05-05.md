# Handoff Contract Consumption Status

> Date: 2026-05-05  
> Branch: `feat/auto-capture-trace`  
> Scope: Crazy handoff consumer surface (`/api/runtime/handoffs` + `/timeline`)

## Verified repository change

This round upgrades Crazy from:

- consuming `moduleDetails.handoff` only
- locally inferring whether the handoff surface is blocked

to:

- consuming FlowMind replay `handoffContract`
- using upstream `ready / blockingIssues / missingFields / executionBoundaryMissingFields`
  as the default handoff health authority

## Consumer path now implemented

Crazy handoff consumption order is now:

1. `moduleDetails.handoff`
2. `semanticContext`
3. `latestEvidence`
4. `handoffContract.ready`
5. `handoffContract.blockingIssues`

If upstream replay does not yet provide `handoffContract`, Crazy still returns a
normalized local fallback object with the same shape, so the UI does not invent
another free-text readiness rule.

## Fields now exposed by `/api/runtime/handoffs`

The normalized handoff API now returns:

- `handoffContract.version`
- `handoffContract.primarySource`
- `handoffContract.fallbackOrder`
- `handoffContract.ready`
- `handoffContract.blockingIssues`
- `handoffContract.missingFields`
- `handoffContract.executionBoundarySource`
- `handoffContract.executionBoundaryMissingFields`

Existing fields remain available:

- `fieldMap`
- `missingFields`
- `gaps`
- `executionBoundary`
- `executionBoundarySource`
- `executionBoundaryMissingFields`

## UI behavior now frozen

`timeline.js` now treats handoff state as:

- `契约就绪` when `handoffContract.ready = true`
- `契约阻塞` when `handoffContract.ready = false`

The page also renders:

- upstream `blockingIssues`
- normalized missing-field details
- execution-boundary gaps

It no longer treats:

- `source === moduleDetails.handoff`

as sufficient proof that the handoff surface is healthy.

## Regression coverage

Repository verification passed:

```bash
/home/flowmind/CrazyAgentsManage/.venv/bin/python -m pytest -q \
  /home/flowmind/CrazyAgentsManage/tests/test_sprint4.py \
  -k "runtime_handoffs or timeline_js_reachable"

/home/flowmind/CrazyAgentsManage/.venv/bin/python -m py_compile \
  /home/flowmind/CrazyAgentsManage/src/webui/api.py \
  /home/flowmind/CrazyAgentsManage/tests/test_sprint4.py
```

Observed result:

- `6 passed, 36 deselected`
- `py_compile` passed

## Operational conclusion

From this point forward, Crazy development and operations lanes should use the
same rule:

- whether a handoff surface is blocked is decided by `handoffContract`
- not by local page heuristics
- not by manually judging whether a few visible fields “look complete”

## One-line conclusion

> Crazy now treats `handoffContract` as the default handoff-health contract, so
> “is this handoff usable?” is no longer a front-end opinion but a shared
> cross-repo contract decision.
