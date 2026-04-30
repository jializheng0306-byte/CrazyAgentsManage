# CrazyAgentsManage Operations Implementation PRD

## Version

| Field | Value |
|------|-------|
| Product | CrazyAgentsManage |
| Document Type | Operations Implementation PRD |
| Version | v0.1.0 |
| Status | Active baseline |
| Owner | Codex (document management) |
| Operations Reviewer | HermesAgent |
| Last Updated | 2026-04-26 |

## Scope

This PRD defines what the operator-facing system must expose so Hermes-side operations are real, usable, and reviewable.

It covers:

- operator personas
- runtime objects that must be visible
- operator workflows
- alerts, reports, and action surfaces
- operational acceptance criteria

It does not define backend implementation details. Those belong in:

- `docs/prd/technical-implementation-prd.md`

## Operator Baseline

### Accepted role model

- `HermesAgent` is the operations lane
- `Codex` is the development lane
- operations work should result in structured feedback, not ad hoc architecture rewrites

### Primary operator questions

Operators must be able to answer:

1. What is running?
2. What is stuck?
3. What failed?
4. What requires intervention?
5. Which FlowMind-linked states are drifting?

## Primary Runtime Objects

The operator console must make the following objects explicit:

- sessions
- delegated tasks / child runs
- skills
- cron jobs
- runtime alerts
- gateway/platform connection state
- FlowMind bridge state
- token/cost usage

## Required Operator Views

### 1. Session view

Operators need:

- active vs completed vs suspect sessions
- parent/child task lineage
- message/tool/token summaries
- stuck indicators

### 2. Task/delegation view

Operators need:

- pending/running/done/failed states
- dependency visibility
- child agent ownership
- actionable follow-up path

### 3. Skills view

Operators need:

- installed skills
- missing/invalid skills
- role or domain grouping
- which skill failures block real work

### 4. Cron view

Operators need:

- configured jobs
- last run / next run
- success/failure state
- pause/resume/trigger entry when actually supported

### 5. Alerts view

Operators need:

- explicit anomaly records
- severity
- affected runtime object
- suggested next action

## Required Operator Actions

The system must eventually support structured actions for:

- acknowledge an alert
- open the affected runtime object
- dispatch or re-dispatch a task
- inspect session/task evidence
- trigger a review routine
- operate cron jobs when backed by real runtime capability

If an action does not yet exist, the UI must not imply that it does.

## FlowMind-Side Operator Needs

From the operator perspective, CrazyAgentsManage must distinguish:

- Hermes runtime truth
- FlowMind governance truth
- pending or unconfirmed candidate state

### Operator expectations for FlowMind-linked state

- candidate state must be distinguishable from canonical truth
- review and feedback loops must be visible
- drift or blockage should be surfaced as operator questions, not hidden in logs

## Reporting Expectations

Operators need recurring outputs such as:

- daily runtime digest
- weekly operational audit
- pending/stuck review list
- failed task / failed cron summaries

These reports may start as manual or semi-manual, but the PRD should treat them as explicit product requirements.

## Operational Acceptance Criteria

### P0

- operators can identify runtime health without shell access
- stuck or failed states are visible
- FlowMind-linked runtime states are not mislabeled as canonical truth
- operator-facing critical views are not mock-only

### P1

- operators can perform basic structured follow-up actions
- reports and recurring review workflows are consistent
- skill/cron/session surfaces are cross-linked

### P2

- richer automation
- predictive alerts
- governance assistance and optimization loops

## Non-Goals

This PRD does not authorize:

- direct code implementation ownership by HermesAgent
- replacing repository truth with chat-only operations decisions
- turning every conceptual future capability into a current runtime commitment

## Change Control

When an iteration changes operator-facing meaning, update:

1. this operations PRD
2. `docs/roadmap/prd-execution-roadmap.md`
3. the relevant harness closeout records if collaboration state changed
