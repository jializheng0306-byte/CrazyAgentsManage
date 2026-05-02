# PRD Document Governance

## Why This Exists

CrazyAgentsManage no longer uses a single monolithic PRD as its only planning surface.

The repository now uses:

1. a technical implementation PRD
2. an operations implementation PRD
3. a canonical execution roadmap

This document defines how those artifacts must be maintained inside the Codex ↔ HermesAgent harness workflow.

## Canonical Files

- `docs/prd/technical-implementation-prd.md`
- `docs/prd/operations-implementation-prd.md`
- `docs/roadmap/prd-execution-roadmap.md`
- `docs/prd/README.md`

For Hermes × FlowMind joint planning, also treat these as upstream canonical inputs:

- `FlowMindDeploy/docs/01-product/HermesAgent-FlowMind-交互框架设计-2026-04-29.md`
- `FlowMindDeploy/docs/01-product/HermesAgent-FlowMind-产品功能基线与迭代路线图-2026-04-30.md`

## Ownership

- `Codex` owns document version management and sequencing updates
- `HermesAgent` owns operations review and acceptance comments

## Update Triggers

Update the PRD system when an iteration changes:

- technical scope
- operator-facing scope
- implementation phase ordering
- merge/readiness status
- role/handoff implications that affect execution
- cross-repo canonical planning truth

## Required Closeout Updates

At the end of each non-trivial iteration, update:

1. technical PRD if engineering scope changed
2. operations PRD if operator-facing meaning changed
3. roadmap if phase/state/priority changed
4. harness closeout notes if collaboration state changed

If the iteration changed FlowMind-side canonical joint planning docs, also update:

5. `docs/roadmap/HermesAgent-FlowMind-联合产品功能基线-2026-04-30.md`
6. run `scripts/check_cross_repo_prd_sync.sh`

## No-Merge Rule

Do not treat a branch as ready for merge until the affected PRD documents and roadmap are updated.

If FlowMind-side canonical planning changed, do not treat the branch as ready for merge until the cross-repo PRD sync checker passes.

## Boundary Rule

Do not let chat-only conclusions override the PRD system.

If chat and repository differ, repository documents must be updated or the chat conclusion is non-canonical.
