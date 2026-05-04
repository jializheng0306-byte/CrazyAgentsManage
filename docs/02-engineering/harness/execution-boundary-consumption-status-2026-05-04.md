# Execution Boundary Consumption Status

> Date: 2026-05-04  
> Branch: `feat/auto-capture-trace`  
> Scope: Crazy handoff / review consumer surface

## Verified live record

| Field | Value |
|---|---|
| recordId | `219a5914-6c85-43df-ad5e-1d1d36241b39` |
| candidateId | `219a5914-6c85-43df-ad5e-1d1d36241b39` |
| page path | `/timeline?recordId=219a5914-6c85-43df-ad5e-1d1d36241b39` |
| consumer API | `/api/runtime/handoffs?recordId=...` |

## Consumer path now implemented

Crazy now consumes execution boundary information in this order:

1. `moduleDetails.handoff`
2. `Execution Boundary` section inside the handoff packet
3. fallback: `semanticContext.executionBoundary`

No local fallback rule set is synthesized when these fields are absent.

## Fields wired into the consumer

When upstream provides boundary data, Crazy will display:

- `Canonical Authority`
- `Local Writable Targets`
- `Human Gate Actions`
- `Forbidden Mutations`

The normalized handoff API now returns:

- `executionBoundary`
- `executionBoundarySource`
- `executionBoundaryMissingFields`

## Current live result

For the verified live record:

- `moduleDetails.handoff` → present
- `Execution Boundary` section → **missing**
- `semanticContext.executionBoundary` → **missing**

Normalized live result:

- `executionBoundary = null`
- `executionBoundarySource = null`
- `executionBoundaryMissingFields = [Canonical Authority, Local Writable Targets, Human Gate Actions, Forbidden Mutations]`

The live page therefore renders a structured gap state instead of inventing a local boundary interpretation.

## What is already enforced

Even with the boundary payload missing, Crazy still keeps these behaviors:

- `truth.status` remains the only main status source
- `feedback.eventType` remains an operational signal only
- `traceEvents[]` remains the timeline main chain
- no page logic implicitly triggers `Human Gate Actions`

## Remaining upstream gap

Still missing from the verified live record:

1. `moduleDetails.handoff -> Execution Boundary`
2. or `semanticContext.executionBoundary`

Until one of those appears in live payloads, Crazy can only show a structured “boundary missing” state, not the boundary values themselves.
