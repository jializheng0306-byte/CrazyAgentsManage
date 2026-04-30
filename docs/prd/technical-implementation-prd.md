# CrazyAgentsManage Technical Implementation PRD

## Version

| Field | Value |
|------|-------|
| Product | CrazyAgentsManage |
| Document Type | Technical Implementation PRD |
| Version | v0.1.0 |
| Status | Active baseline |
| Owner | Codex |
| Operations Reviewer | HermesAgent |
| Last Updated | 2026-04-26 |

## Scope

This PRD defines the engineering work required to turn CrazyAgentsManage into a real Hermes-side operator console.

It covers:

- runtime data ingestion
- API and adapter surfaces
- frontend/backend implementation scope
- technical acceptance criteria
- phased implementation ordering

It does not define operator policy in detail. That belongs in:

- `docs/prd/operations-implementation-prd.md`

## Product Boundary

### Current shared boundary

- `CrazyAgentsManage` is the Hermes runtime/operator console
- `FlowMind` is the governance engine and canonical truth layer
- `CrazyAgentsManage` may display, relay, and operationalize FlowMind-facing state
- `CrazyAgentsManage` must not redefine FlowMind semantics ad hoc

### Technical implication

Implementation must keep three seams explicit:

1. Hermes runtime and session substrate
2. CrazyAgentsManage operator console and adapters
3. FlowMind governance and truth interfaces

## Current Technical Baseline

### Runtime facts already available

- Hermes runtime data sources already exist and are readable:
  - `state.db`
  - `gateway_state.json`
  - `~/.hermes/skills/`
  - `~/.hermes/memories/`
  - cron / runtime process state
- CrazyAgentsManage already has a WebUI/API demo for runtime observation
- Codex/Hermes role split is already accepted and should not be re-argued in implementation work

### Known gaps still relevant

- session stuck / zombie inference needs stronger technical treatment
- runtime signals still need normalization before they are operator-ready
- some control surfaces remain mock or incomplete
- FlowMind-facing interfaces must align to actual bridge contracts, not imagined endpoints

## Implementation Areas

### 1. Runtime State Adapters

Build and harden read adapters for:

- session state
- message / token accounting
- task/delegation lineage
- skills inventory
- cron job state
- alerts and anomaly indicators

Acceptance criteria:

- adapters tolerate partial/missing runtime files
- adapters distinguish “not configured” from “broken”
- adapter outputs are normalized for frontend consumption

### 2. Task / Delegation Substrate

Implement or finish the substrate required for:

- role-aware delegation
- shared context/task state files
- task graph lineage
- cross-session task tracking

Acceptance criteria:

- delegated tasks produce durable status artifacts
- parent/child lineage can be queried and rendered
- failure state is explicit, not inferred from silence alone

### 3. Team / Memory Substrate

Implement the repository-side pieces for:

- team memory
- shared context directories
- role memory loading
- post-iteration memory writeback

Acceptance criteria:

- team and shared-context structures are created predictably
- read/write boundaries are explicit
- memory updates are reviewable and attributable

### 4. Runtime Controls

Implement real operator controls for:

- cron visibility and actions
- session inspection
- task dispatch entry
- bridge status inspection
- runtime alert acknowledgement

Acceptance criteria:

- every control exposed in the UI is backed by a real action or a documented non-action
- mock endpoints are either replaced or clearly labeled

### 5. Observability UI

Implement the operator-facing UI for:

- sessions
- task graph / lineage
- runtime health
- skills inventory
- cron surfaces
- token/cost visibility
- alerts and exceptions

Acceptance criteria:

- source/runtime state is visible without shell access
- root cause breadcrumbs exist for abnormal states
- high-frequency pages remain usable with large data sets

## FlowMind Integration Contract

CrazyAgentsManage must align to the real FlowMind-facing interfaces already established in `FlowMindDeploy`.

### Current bridge-aligned surfaces

- candidate ingress
- truth query
- context compilation
- truth change feedback

### Rule

Do not invent new API names in implementation planning unless they are explicitly marked as proposed and separated from already implemented bridge surfaces.

## Non-Goals

This PRD does not authorize:

- redefining FlowMind product semantics
- treating Hermes as the source of canonical truth
- making HermesAgent a second coding lane
- chat-only architectural decisions without repository artifacts

## Technical Acceptance Gates

### P0

- runtime state adapters are reliable
- real runtime signals are exposed
- session/task anomalies are identifiable
- non-mock critical operator surfaces exist

### P1

- task dispatch entry is usable
- skill scanning is consistent
- memory/team substrate is functional
- key UI pages are operationally navigable

### P2

- advanced automation and optimization layers
- long-tail dashboards
- secondary integrations and convenience tooling

## Change Control

When a task changes technical scope, update:

1. this PRD
2. `docs/roadmap/prd-execution-roadmap.md`
3. harness closeout artifacts if role coordination changed
