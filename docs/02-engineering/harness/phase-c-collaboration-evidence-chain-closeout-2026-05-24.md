# Phase C · Collaboration Evidence Chain Closeout（2026-05-24）

> 范围: Crazy `Phase C · Harness × Hermes 协作层对齐` 第二切片  
> 状态: `in-progress / second-slice-landed`  
> 宿主: `ALI-HERMES`

## 1. 目标

把 `Phase C` 从：

- 只有 `handoff / snapshot / closeout / repo truth` 的第一版聚合
- 但 reviewer / Hermes acceptance / PRD closeout 仍主要停留在口头要求

推进到：

- `/api/collaboration/summary` 显式暴露统一 evidence chain
- `/collaboration` 明确显示 `next actor / next action`
- `/api/collaboration/graph-projection` 与 `/architecture/tech` 继续细化链路节点

## 2. 本轮落地

### 2.1 Collaboration Summary 第二切片

在保留第一切片 `triage + evidence jumps` 的基础上，新增：

- `reviewer-state`
- `hermes-acceptance`
- `prd-closeout`

每个阶段都显式给出：

- `status`
- `summary`
- `nextActor`
- `nextAction`
- `evidenceRefs`

### 2.2 Collaboration Page 统一证据链

`/collaboration` 新增单独的 evidence-chain 区块，不再让 operator 只从四张 triage 卡倒推协作阶段。

当前页面会直接回答：

- reviewer 还是否有 open handoff
- Hermes acceptance 是否已经在 runtime snapshot 中形成明确状态
- PRD / roadmap / tracker closeout 是否已有 closeout governance evidence 支撑

### 2.3 Tech Collaboration Projection 继续细化

`/api/collaboration/graph-projection` 继续从第一切片的粗粒度节点扩展为：

- `Reviewer`
- `Hermes Acceptance`
- `PRD Closeout`

这样 `TechArchitecturePreviewPage` 展示的不再只是“有一条协作链”，而是能看见当前卡在哪个中间阶段。

## 3. 文档回写

本轮同步更新：

- `docs/roadmap/master-task-plan.md`
- `docs/prd/collaboration-workflow-implementation-prd.md`
- `docs/prd/collaboration-operator-workflow-prd.md`
- `docs/prd/pages/collaboration-page-prd.md`

## 4. 验证

### 本地

- `.venv/bin/python -m pytest tests/test_sprint4.py -q`
- `python3 -m py_compile src/webui/api.py src/webui/app.py`
- `node --check src/webui/static/js/collaboration.js`
- `node --check src/webui/static/js/architecture-tech.js`
- `bash scripts/check_harness_governance_all.sh`
- local closeout evidence:
  - `trace.id = S-20260524-005`
  - `closeout.id = C-20260524-005`
  - `lane = shared`
  - `topic = phase-c-collaboration-evidence-chain`

### 宿主

固定顺序：

1. `python3 scripts/governance/sync_live_deploy_copy.py --workspace-root . --profile crazy-runtime-live --skip-verify --json`
2. `python3 scripts/runtime/run_on_ali_hermes.py --cwd /root/CrazyAgentsManage -- 'python3 scripts/runtime/sync_hermes_script_mirror.py'`
3. `python3 scripts/governance/sync_live_deploy_copy.py --workspace-root . --profile crazy-webui-live --skip-verify --json`

附加动作：

- `systemctl restart cam.service`

宿主应复验：

- `GET http://47.99.217.1/manage/api/collaboration/summary`
- `GET http://47.99.217.1/manage/api/collaboration/graph-projection`
- focused browser gate:
  - `/manage/collaboration`
  - `/manage/architecture/tech`

## 5. 当前裁定

`Phase C` 现在处于：

- `in-progress / second-slice-landed`

也就是说：

1. 第一切片的 summary aggregation + evidence jumps + graph projection 仍成立
2. reviewer / Hermes acceptance / PRD closeout 已进入 canonical collaboration summary 主链
3. `TechArchitecturePreviewPage` 已读取更细粒度的阶段节点

但它还不是：

- `completed-published`

剩余重点仍是：

- 把 triage 继续贴到更明确的处理动作与 writeback path
- 判断是否需要更细粒度的 acceptance artifact / handoff contract 回写
