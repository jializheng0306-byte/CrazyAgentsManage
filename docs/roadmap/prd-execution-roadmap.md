# PRD Execution Roadmap

## Purpose

This roadmap is the single execution tracker for the split PRD system.

It coordinates:

- technical implementation work
- operations implementation work
- document version management
- Codex/HermesAgent closeout updates

## Canonical Inputs

This roadmap must stay aligned with:

1. `docs/prd/technical-implementation-prd.md`
2. `docs/prd/operations-implementation-prd.md`
3. `docs/codex-hermes-role-design.md`
4. `docs/02-engineering/harness/CODEX-HERMES-COLLABORATION-MECHANISM.md`

## Ownership

- `Codex` owns roadmap edits, sequencing, and document version management
- `HermesAgent` reviews roadmap changes from an operations-acceptance perspective

## Current Product Consensus

The project has reached baseline agreement on product direction:

- `CrazyAgentsManage` is the Hermes-side operator console
- `FlowMind` is the governance engine / canonical truth layer
- `Codex` drives implementation planning and delivery
- `HermesAgent` drives operations framing and acceptance

## Workstreams

### Workstream A — Technical Implementation

Source:

- `docs/prd/technical-implementation-prd.md`

Focus:

- adapters
- task/delegation substrate
- team/shared-context substrate
- runtime controls
- observability UI

### Workstream B — Operations Implementation

Source:

- `docs/prd/operations-implementation-prd.md`

Focus:

- operator views
- operator actions
- alerts/reports
- FlowMind-linked operational states
- acceptance gates

## Execution Phases

### Phase 0 — Documentation Baseline

Status: in progress

Goals:

- split PRD into technical and operations documents
- establish roadmap as canonical execution tracker
- bind document updates into harness workflow

Done when:

- split PRD files exist
- roadmap exists
- harness entrypoints point at the new governance flow

### Phase 1 — Runtime / Substrate Readiness

Goals:

- stabilize technical substrate
- expose real runtime signals
- define operator-visible runtime objects

Primary outputs:

- adapter hardening
- task/delegation visibility
- runtime signal exposure

### Phase 2 — Operator Surface Readiness

Goals:

- align UI and API surfaces to real runtime actions
- expose operator workflows without mock ambiguity

Primary outputs:

- session/task/cron/alert views
- structured operator actions
- cross-linking between runtime objects

### Phase 3 — Governance / FlowMind Readiness

Goals:

- align CrazyAgentsManage to real FlowMind bridge surfaces
- separate Hermes runtime truth from FlowMind canonical truth

Primary outputs:

- bridge-aware operator UX
- candidate/truth distinction
- review and feedback visibility

## Iteration Closeout Rule

After every non-trivial iteration, update:

1. the technical PRD if implementation scope changed
2. the operations PRD if operator-facing meaning changed
3. this roadmap with phase/status changes
4. harness closeout artifacts if the Codex/Hermes collaboration state changed

## Merge Gate

An iteration is not considered complete for a shared branch until:

1. affected PRD documents are updated
2. roadmap status is updated
3. repository artifacts reflect the accepted truth
4. HermesAgent acceptance comments are resolved or explicitly deferred

## Immediate Next Actions

1. keep the split PRD set as the planning baseline
2. route new work items into technical vs operations lanes explicitly
3. require document updates during every iteration closeout
