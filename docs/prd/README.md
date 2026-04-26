# PRD System

## Purpose

CrazyAgentsManage now uses a split PRD system instead of relying on a single monolithic product document.

The split exists because the project has already converged on two different but tightly coupled implementation lanes:

1. technical implementation
2. operations implementation

This keeps repository truth aligned with the accepted Codex/HermesAgent role model:

- `Codex` owns development planning, implementation sequencing, and document version management
- `HermesAgent` owns operations framing, runtime review, and operational acceptance

## Consensus Baseline

The current shared product understanding is:

- `CrazyAgentsManage` is the Hermes-side operator console and runtime host management surface
- `FlowMind` is the governance engine and canonical truth layer, not the operator console itself
- `Codex` remains the development lane
- `HermesAgent` remains the operations lane

This baseline should not be reopened casually. Update it only when repository evidence changes.

## Canonical Documents

### Technical PRD

File:

- `docs/prd/technical-implementation-prd.md`

Use this for:

- architecture boundaries
- backend/frontend implementation scope
- data contracts
- runtime integration surfaces
- technical acceptance criteria

### Operations PRD

File:

- `docs/prd/operations-implementation-prd.md`

Use this for:

- operator personas
- runtime signals and dashboards
- operator workflows
- action surfaces
- operational acceptance criteria

### Execution Roadmap

File:

- `docs/roadmap/prd-execution-roadmap.md`

Use this for:

- phase ordering
- implementation sequence
- document update cadence
- release and merge gates

## Legacy Documents

The following files remain useful as background inputs, but they are no longer the only canonical PRD surface:

- `docs/prd/product-requirements.md`
- `docs/prd/multi-agent-architecture-design.md`
- `docs/prd/observability-design.md`
- `docs/06-agent-ops/hermes-agent-operations-design.md`

When conflicts appear, the split PRD set plus the roadmap should be treated as the active planning baseline.

## Update Rules

After every non-trivial iteration, update all affected documents before calling the round complete:

1. technical PRD
2. operations PRD
3. execution roadmap
4. harness closeout / handoff artifacts when collaboration state changed

If an iteration changes only runtime operations, the operations PRD and roadmap still need updates.
If an iteration changes only engineering implementation, the technical PRD and roadmap still need updates.

## Merge Rule

No merge to a shared branch should be treated as complete until:

1. affected PRD documents are updated
2. roadmap status is updated
3. Codex/HermesAgent handoff state is consistent with repository truth
