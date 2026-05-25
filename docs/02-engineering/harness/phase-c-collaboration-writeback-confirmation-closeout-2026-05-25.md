# Phase C · Collaboration Writeback Confirmation Closeout（2026-05-25）

> 范围: Crazy `Phase C · Harness × Hermes 协作层对齐` 第四切片  
> 状态: `in-progress / fourth-slice-landed`  
> 宿主: `ALI-HERMES`

## 1. 目标

把上一切片的：

- `action playbook`
- `context-aware landing`
- `route / command / writeback path`

继续推进到：

- `reviewer-state / hermes-acceptance / prd-closeout`
- 三段 evidence chain 都显式投影 `writeback confirmation`
- operator 不再需要自己比对路径，页面直接显示哪些 artifact 已就位、哪些仍缺口

## 2. 本轮落地

### 2.1 Evidence chain 加入 object-level writeback confirmation

`/api/collaboration/summary` 的三段 evidence chain 现在都会返回：

- `writebackConfirmation.status`
- `writebackConfirmation.summary`
- `writebackConfirmation.items[]`

当前覆盖：

- `Reviewer`
  - runtime snapshot
  - open handoff artifact
  - handoff 引用的 repo artifact
- `Hermes Acceptance`
  - runtime snapshot
  - snapshot.artifacts
  - latest closeout 是否已追平 snapshot
- `PRD Closeout`
  - latest closeout artifact
  - cross-repo governance evidence
  - Crazy / FlowMind 侧关键文档锚点

### 2.2 Collaboration UI 直接显示 confirmation

`/collaboration` 的 evidence chain 卡片现在除了：

- next actor
- next action
- canonical commands
- writeback paths

还会直接展示：

- writeback confirmation summary
- per-artifact ready / missing 状态

### 2.3 口径约束

本轮仍然没有让 Crazy 越权改写 FlowMind canonical truth。

当前只是：

- 投影和核验 repo-tracked / runtime-local artifact
- 帮 operator 判断 acceptance / closeout 是否已经具备闭环前提

并没有：

- 新增 FlowMind 写入口
- 让 executor 直接接管 repo truth

## 3. 文档回写

本轮同步更新：

- `docs/roadmap/master-task-plan.md`

FlowMind 侧只更新 canonical tracker / roadmap 口径，不进入实现补偿开发。

## 4. 验证

### 本地

- `.venv/bin/python -m pytest tests/test_sprint4.py -q`
- `python3 -m py_compile src/webui/api.py`
- `node --check src/webui/static/js/collaboration.js`
- `bash scripts/check_harness_governance_all.sh`
- `python3 /home/flowmind/FlowMindDeploy/scripts/governance/check_cross_repo_prd_sync.py --source-repo-root /home/flowmind/FlowMindDeploy --counterpart-repo-root /home/flowmind/CrazyAgentsManage`
- local closeout evidence:
  - `trace.id = S-20260525-001`
  - `closeout.id = C-20260525-001`

### 宿主

固定顺序：

1. `python3 scripts/governance/sync_live_deploy_copy.py --workspace-root . --profile crazy-runtime-live --skip-verify --json`
2. `python3 scripts/runtime/run_on_ali_hermes.py --cwd /root/CrazyAgentsManage -- 'python3 scripts/runtime/sync_hermes_script_mirror.py'`
3. `python3 scripts/governance/sync_live_deploy_copy.py --workspace-root . --profile crazy-webui-live --skip-verify --json`

随后：

- `python3 scripts/runtime/run_on_ali_hermes.py -- 'systemctl restart cam.service'`
- `python3 scripts/runtime/run_on_ali_hermes.py -- 'systemctl is-active cam.service'`
- `python3 scripts/runtime/run_on_ali_hermes.py -- 'curl -s http://127.0.0.1/manage/api/collaboration/summary'`
- `python3 scripts/runtime/run_on_ali_hermes.py -- 'curl -s http://127.0.0.1/manage/api/collaboration/graph-projection'`
- `python3 scripts/runtime/run_phase_c_collaboration_live_gate.py --output-dir /tmp/phase-c-live-gate`

## 5. 当前裁定

`Phase C` 现在处于：

- `in-progress / fourth-slice-landed`

也就是说：

1. canonical evidence chain 已成立
2. action playbook 与 context-aware landing 已成立
3. evidence chain 已进入 object-level writeback confirmation

## 6. 下一步

剩余主问题已从“能否看见和跳转”收窄到更具体的两件事：

1. 是否要把 `accept / reject / defer` 明确落成独立 acceptance artifact，而不只是 runtime snapshot status
2. 是否要让 reviewer / Hermes acceptance 对 handoff contract 形成更细粒度的回写对象，而不只做 confirmation projection
