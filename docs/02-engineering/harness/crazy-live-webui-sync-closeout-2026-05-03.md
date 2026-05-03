# Crazy Live WebUI Sync Closeout

> Date: 2026-05-03  
> Scope: `ALI-HERMES` live Crazy WebUI deploy copy  
> Live root: `/opt/crazyagentsmanage`

## Why this sync was needed

FlowMind live deploy sync governance confirmed that the tracked repository baseline
and the live Crazy WebUI copy had drifted.

The drift was not in the product contract itself, but in the deployed copy on
`/opt/crazyagentsmanage`, which still lagged behind the repository baseline for
the timeline / handoff consumer surface.

## Files synced

1. `src/webui/templates/timeline.html`
2. `src/webui/static/js/timeline.js`
3. `src/webui/static/css/timeline.css`
4. `tests/test_sprint4.py`

## Expected live behavior after sync

- Timeline page should continue to consume `GET /api/bridge/trace/:candidateId`
- Handoff summary should continue to prefer `moduleDetails.handoff`
- The live page should not regress to the old `events[]`-only error-shape path
- The live deploy copy should match the current repository baseline for the four drifted files

## Validation note

This closeout record is completed only after:

1. live file backup is taken
2. the four files are copied into `/opt/crazyagentsmanage`
3. `/timeline` is re-checked on the live surface
4. deployed static/template files are confirmed to match the repo baseline

## Live backup taken

- Backup directory:
  - `/opt/crazyagentsmanage/.deploy-backups/timeline-sync-20260503_191608`

## Validation completed

- Local service route:
  - `http://127.0.0.1:5002/timeline` → `200`
- Public route:
  - `http://47.99.217.1/manage/timeline` → `200`
- Timeline main consumer path:
  - deployed `timeline.js` still calls local wrapper `/api/promise-review/trace/:candidateId`
  - deployed `api.py` still proxies that wrapper to FlowMind `/api/bridge/trace/:candidateId`
- Live trace payload check:
  - `candidateId = 219a5914-6c85-43df-ad5e-1d1d36241b39`
  - `traceCount = 7`
  - `traceEvents` exists
  - legacy `events` key is absent in the normalized live response
- Live handoff payload check:
  - `recordId = 219a5914-6c85-43df-ad5e-1d1d36241b39`
  - source = `moduleDetails.handoff`
  - `Truth Status = approved`
  - `missingFields = []`

## Result

- The four drifted live files were synced to `/opt/crazyagentsmanage`
- The live deploy copy now matches the current repository baseline for the sync-governed timeline files
- Timeline and handoff main consumer paths still hold after live sync
