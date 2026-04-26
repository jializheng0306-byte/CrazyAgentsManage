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

## Required Closeout Updates

At the end of each non-trivial iteration, update:

1. technical PRD if engineering scope changed
2. operations PRD if operator-facing meaning changed
3. roadmap if phase/state/priority changed
4. harness closeout notes if collaboration state changed

## No-Merge Rule

Do not treat a branch as ready for merge until the affected PRD documents and roadmap are updated.

## Boundary Rule

Do not let chat-only conclusions override the PRD system.

If chat and repository differ, repository documents must be updated or the chat conclusion is non-canonical.
