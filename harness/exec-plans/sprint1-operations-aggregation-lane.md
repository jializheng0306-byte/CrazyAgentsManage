## Background

Sprint 1 aggregation lane starts from the existing `Operations` workbench.
The page already has real object-family APIs and executor integration APIs,
but it still behaves like a tool surface with count-only metrics instead of
the page-level aggregation layer required by the PRD and gate checks.

Relevant product + engineering anchors:

- `docs/prd/operations-surface-implementation-prd.md`
- `docs/prd/pages/operations-page-prd.md`
- `docs/roadmap/master-task-plan.md`
- `docs/roadmap/prd-execution-roadmap.md`

## Goal

Land the first complete `Operations` aggregation slice by:

1. adding a reusable `Operations` summary API
2. surfacing page-level briefing + summary framing on `/operations`
3. keeping the existing workbench intact underneath the new aggregation layer

## Scope

- `src/webui/api.py`
  - add a reusable operations summary aggregation endpoint/helper
- `src/webui/templates/operations.html`
  - add briefing, summary grid, and subpage framing
- `src/webui/static/js/operations.js`
  - switch summary rendering to the shared aggregation payload
- `tests/test_executor_integration.py`
  - cover the new API and UI asset expectations

## Non-goals

- redesigning other IA pages in the same pass
- changing executor provider semantics
- adding new operator write actions
- rewriting the existing three-column workbench structure

## Verification

- targeted pytest for operations/executor API coverage
- validate the operations template/JS contract via existing asset tests
- ensure no regression in existing integrations summary behavior

## Closeout Notes

If implementation scope expands beyond the existing PRD contract, update:

- `docs/prd/operations-surface-implementation-prd.md`
- `docs/prd/pages/operations-page-prd.md`
- `docs/roadmap/prd-execution-roadmap.md`

If the scope remains inside the current contract, keep docs stable and record
the iteration through code + test evidence only.
