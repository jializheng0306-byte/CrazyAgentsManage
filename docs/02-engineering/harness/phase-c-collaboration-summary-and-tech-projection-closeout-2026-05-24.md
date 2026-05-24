# Phase C · Collaboration Summary + Tech Projection Closeout（2026-05-24）

> 范围: Crazy `Phase C · Harness × Hermes 协作层对齐` 第一切片  
> 状态: `in-progress / first-slice-landed`  
> 宿主: `ALI-HERMES`

## 1. 目标

把 `Phase C` 从：

- 只有路线图和 PRD 明确要求
- 但 `Collaboration` 页面还没有 canonical summary aggregation
- `TechArchitecturePreviewPage` 也还没有协作链动态投影

推进到：

- `Collaboration` 有正式的 summary aggregation
- `Evidence Jumps` 成为页面级产品对象
- `TechArchitecturePreviewPage` 复用同一条协作链状态源

## 2. 本轮落地

### 2.1 Collaboration Summary Aggregation

新增：

- `GET /api/collaboration/summary`

当前聚合：

- `open handoff`
- `pending closeout`
- `missing writeback`
- `unreviewed artifact`

并给出：

- `briefing`
- `nextHop`
- `handoffs`
- `runtimeSnapshot`
- `harness`
- `evidenceJumps`

### 2.2 Collaboration Evidence Jumps

`/collaboration` 现在不再只显示交接包与 trace 卡片，而是显式提供：

- task workspace
- loop surface
- runtime sessions
- governance graph
- operations > harness

### 2.3 Tech collaboration-chain projection

新增：

- `GET /api/collaboration/graph-projection`

并接到：

- `/architecture/tech`

当前节点：

- `Codex`
- `HermesAgent`
- `handoff`
- `runtime snapshot`
- `closeout`
- `repo truth`

## 3. 额外修正

### 3.1 runtime/handoff/harness richer-root fallback

`runtime/state`、`runtime/handoffs`、`runtime/harness-summary` 现在会优先选取更有证据的 root，而不是在 deploy copy 中因为空壳目录导致 summary 退化。

### 3.2 public `/manage` API compatibility

本轮还利用了此前补好的：

- `/manage/api/...` compatibility

确保 public `/manage/collaboration` 与 `/manage/architecture/tech` 能真实加载页面级 API，而不是只剩静态壳层。

## 4. 验证

### 本地

- `pytest tests/test_sprint4.py`
- `python -m py_compile src/webui/api.py src/webui/app.py`
- `node --check src/webui/static/js/collaboration.js`
- `node --check src/webui/static/js/architecture-tech.js`
- `node --check tests/phase_c_collaboration_live_gate_check.js`
- `bash scripts/check_harness_governance_all.sh`
- local closeout evidence:
  - `trace.id = S-20260524-003`
  - `closeout.id = C-20260524-003`
  - `lane = shared`
  - `topic = phase-c-collaboration-summary-tech-projection`

### 宿主

固定顺序：

1. `python3 scripts/governance/sync_live_deploy_copy.py --workspace-root . --profile crazy-runtime-live --skip-verify --json`
2. `python3 scripts/runtime/run_on_ali_hermes.py --cwd /root/CrazyAgentsManage -- 'python3 scripts/runtime/sync_hermes_script_mirror.py'`
3. `python3 scripts/governance/sync_live_deploy_copy.py --workspace-root . --profile crazy-webui-live --skip-verify --json`

附加动作：

- `systemctl restart cam.service`

宿主结果：

- `GET http://47.99.217.1/manage/api/collaboration/summary` → `200`
- `GET http://47.99.217.1/manage/api/collaboration/graph-projection` → `200`
- focused Playwright gate 通过：
  - `/manage/collaboration`
  - `/manage/architecture/tech`
- artifacts:
  - `/tmp/phase-c-collaboration-gate.json`
  - `/tmp/phase-c-collaboration.png`
  - `/tmp/phase-c-architecture-tech.png`

## 5. 当前裁定

`Phase C` 现在已经进入：

- `in-progress / first-slice-landed`

也就是说：

1. canonical summary aggregation 已成立
2. evidence jumps 已成为正式页面对象
3. architecture collaboration-chain projection 已接入

但它还不是：

- `completed-published`

因为下一步还要继续收：

- reviewer / Hermes acceptance / PRD closeout 的统一 evidence 链
- 更显式的 writeback / unresolved artifact 处理动作
