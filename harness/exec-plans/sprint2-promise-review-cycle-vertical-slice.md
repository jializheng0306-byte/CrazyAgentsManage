## Background

Sprint 2 `Control Plane Hardening` needs one thin vertical slice that proves
the control-plane story in code, not just in PRDs. The current best candidate
is `daily-promise-review.py` because it already owns a repo-tracked review
state, projects `truth / feedback / operational follow-up`, and is operator
facing.

Relevant product + engineering anchors:

- `docs/prd/pages/loop-surface-page-prd.md`
- `docs/roadmap/sprint2-cycle-upgrade-first-batch-2026-05-22.md`
- `docs/roadmap/master-task-plan.md`
- `docs/roadmap/prd-execution-roadmap.md`

## Goal

Land the first real Sprint 2 cycle slice by:

1. turning `daily-promise-review-state.json` into a minimal `promise-review-cycle`
2. exposing that cycle through `/api/collaboration/loops`
3. mounting a minimal `/collaboration/loops` page as the first `Loop Surface`

## Scope

- `src/webui/api.py`
  - read promise review state / reports and build a minimal cycle object
- `src/webui/app.py`
  - mount `/collaboration/loops`
- `src/webui/templates/loop-surface.html`
  - render a thin Loop Surface page
- `src/webui/static/js/loop-surface.js`
  - fetch and render the cycle
- `src/webui/templates/collaboration.html`
  - add a link to the new Loop Surface subpage
- `tests/test_sprint4.py`
  - cover the new route and API shape

## Non-goals

- implementing memory-candidate confirmation
- implementing feedback input forms
- introducing a second cycle object in the same pass
- claiming a full task-bus productization in the same pass

## Verification

- `.venv/bin/python -m pytest tests/test_sprint4.py tests/test_daily_promise_review_contract.py -q`
- `.venv/bin/python -m py_compile src/webui/api.py src/webui/app.py`
- `node --check src/webui/static/js/loop-surface.js`

## Closeout Notes

If this slice lands successfully, the next default step is not another page
shell but:

1. decide whether `morning-intel-v2.py` is the second cycle object
2. then open `memory candidate` / `feedback input` only after the cycle object
   is stable
