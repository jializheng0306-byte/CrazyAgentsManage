# Handoff Evidence / Cache Refresh Enhancement Backlog

> Date: 2026-05-05  
> Branch: `feat/auto-capture-trace`  
> Scope: Crazy handoff remaining items after operations closeout  
> Baseline: operations fact-layer closeout says:
> - handoffContract = defaultable
> - Execution Boundary = closed
> - latest ops fact closeout commit = `3f833c1`

## 1. Mainline status

These items are no longer treated as mainline blockers:

1. `handoffContract` can be the default handoff-health authority.
2. `Execution Boundary` has already closed as a structured runtime surface.
3. Remaining gaps are enhancement-scope only.

This means Crazy should continue the default operator flow even when a derived replay is not fully evidence-rich.

## 2. Evidence gap downgraded to enhancement

### 2.1 Verified live samples

Two live replay shapes were checked on `http://111.229.194.203:3301`:

1. `recordId = 219a5914-6c85-43df-ad5e-1d1d36241b39`
   - `replayMode = derived`
   - `truth.latestEvidence` exists
   - replay handoff contains:
     - `Latest Evidence Summary`
     - `Latest Evidence Class`
     - `Latest Evidence Source Type`
     - `Latest Evidence Refs`

2. `recordId = a9894493-decf-44c5-a4ed-5efa8e31be51`
   - `replayMode = derived`
   - `truth.status = rejected`
   - `truth.latestEvidence` is absent
   - replay handoff omits the four evidence fields above

The same absence pattern was also confirmed on:

- `recordId = d34e93ea-2ce5-47fe-9a1c-ace5e838d0d2`

### 2.2 Current missing evidence fields on the derived replay path

When replay is derived and upstream truth has no `latestEvidence`, the current handoff packet is missing:

1. `Latest Evidence Summary`
2. `Latest Evidence Class`
3. `Latest Evidence Source Type`
4. `Latest Evidence Refs`

These are enhancement-scope gaps now, not mainline blockers.

### 2.3 Ownership rule

#### Case A: truth already has `latestEvidence`, replay/handoff still omits it

Primary owner: `FlowMind`

Reason:

- operator replay is the canonical producer of `moduleDetails.handoff`
- the four evidence fields belong to the replay-native semantic packet
- Crazy should not invent or paraphrase evidence that replay should already carry

Crazy responsibility in this case:

- keep exposing `handoffContract.missingFields`
- keep fallback field names shape-compatible
- do not synthesize free-text evidence if replay omitted it

#### Case B: truth itself has no `latestEvidence`

Primary owner: `FlowMind`

Reason:

- replay cannot emit evidence fields that upstream truth/provenance has not produced
- Crazy cannot author canonical evidence on behalf of FlowMind

Crazy responsibility in this case:

- surface the missing evidence as an enhancement backlog item
- allow default operator flow to continue
- avoid treating this as a handoff mainline blocker

#### Case C: replay omitted evidence but truth has it and a local bridge-side patch is urgently needed

Secondary fallback owner: `Crazy`

Allowed only as a bridge enhancement:

- Crazy may mirror `truth.latestEvidence` into its normalized `/api/runtime/handoffs` fallback
- field names must remain identical to replay contract naming
- Crazy must not fabricate values beyond what `truth.latestEvidence` already returned

### 2.4 Engineering backlog items

`EVID-1`
- Trigger: replay handoff lacks evidence fields while `truth.latestEvidence` exists
- Owner: `FlowMind`
- Action: populate replay-native `moduleDetails.handoff` evidence fields directly from truth/provenance

`EVID-2`
- Trigger: derived replay has no evidence because truth has no `latestEvidence`
- Owner: `FlowMind`
- Action: improve operator replay / provenance write path so rejected or cleanup decisions can carry first-class evidence when appropriate

`EVID-3`
- Trigger: replay gap remains but Crazy needs a temporary compatibility bridge
- Owner: `Crazy`
- Action: add a non-authoritative bridge fallback that mirrors `truth.latestEvidence` only when upstream truth already has it

## 3. Cache refresh downgraded to enhancement

### 3.1 Current repository fact

The current Crazy repository does **not** contain:

- `scripts/refresh-bitable-cache.sh`
- `scripts/consume_feedback.py`

The current real writeback path is:

- `scripts/daily-promise-review.py`

That script already does all of the following in one run:

1. reads `truth`
2. reads `trace`
3. reads `feedback`
4. writes Promise Overview main-table projections
5. writes Interaction Trace rows
6. writes `last_governance_feedback`

So the repository fact today is:

- feedback consumption is already embedded in the main refresh job
- there is no separate tracked feedback-consumer script to schedule independently

### 3.2 Scheduling recommendation

Recommended near-term scheduling model:

- use one unified refresh job
- do not split feedback and cache refresh yet

Recommended frequency:

- every 30 minutes during operator hours
- suggested window: `08:30-21:30`

Suggested cron shape:

```bash
*/30 8-21 * * * cd /home/flowmind/CrazyAgentsManage && \
PROMISE_BITABLE_CONFIG_PATH=/home/flowmind/CrazyAgentsManage/shared-context/promise-bitable-config.json \
/home/flowmind/CrazyAgentsManage/.venv/bin/python scripts/daily-promise-review.py \
>> /root/.hermes/logs/daily-promise-review.log 2>&1
```

This should be treated as the default enhancement plan unless operations wants a lower-latency feedback loop.

### 3.3 Relation to `consume_feedback.py`

Current answer:

- no standalone `consume_feedback.py` exists in this repository
- therefore the correct near-term relation is: `shared schedule / unified job`

Operational interpretation:

- `daily-promise-review.py` is currently both the cache refresh path and the feedback-consumption path
- no separate feedback cron is required for mainline operation

### 3.4 When to split scheduling later

Only split into independent jobs if one of these becomes true:

1. operators need feedback freshness below 30 minutes
2. feedback volume becomes high enough that main-table refresh should not pay the same cost
3. a real tracked `consume_feedback.py` implementation lands in-repo

If a split is introduced later:

- `consume_feedback.py` should run every 10 minutes
- `refresh-bitable-cache.sh` should run every 30 minutes
- feedback job remains operational-only
- cache refresh job remains projection-only

That split is enhancement backlog, not current delivery scope.

## 4. Final downgrade ruling

As of this closeout:

- evidence richness gaps remain real
- cache refresh automation can still be improved
- neither item should block the default Crazy operator flow

The correct state is:

> handoff remaining work has been downgraded to enhancement backlog, not mainline delivery blocking.
