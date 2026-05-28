# Phase C · Collaboration Acceptance Artifact Closeout（2026-05-25）

> 范围: Crazy `Phase C · Harness × Hermes 协作层对齐` 第五切片  
> 状态: `complete / fifth-slice-landed`  
> 宿主: `ALI-HERMES`

## 1. 目标

收掉上一轮留下的主风险：

- `accept / reject / defer` 仍只是 runtime snapshot status
- reviewer / Hermes acceptance 还没有独立 acceptance artifact

把 `Hermes Acceptance` 从：

- confirmation projection

推进到：

- repo-owned acceptance artifact
- 明确的 `accepted / rejected / deferred` 决策对象
- Collaboration evidence chain 对 acceptance artifact 的优先消费

## 2. 本轮落地

### 2.1 新增 acceptance artifact 层

当前新增：

- `harness/acceptance/TEMPLATE.json`
- `scripts/write_acceptance_artifact.py`

脚本支持：

- `--decision accepted`
- `--decision rejected`
- `--decision deferred`

并会把：

- handoff path / title
- runtime snapshot phase / status / updated_at
- artifacts
- actor / counterpart / summary / notes

写成独立 acceptance artifact。

### 2.2 Collaboration summary 优先消费 acceptance artifact

`/api/collaboration/summary` 现在对 `Hermes Acceptance` 的判断顺序是：

1. 优先看最新 acceptance artifact
2. 只有 artifact 缺失时，才回退到 runtime snapshot status

因此：

- `accepted` -> `healthy`
- `rejected / deferred` -> `degraded`

不再只靠 snapshot status 推断 acceptance 结论。

### 2.3 Writeback confirmation 收口到 acceptance artifact

`Hermes Acceptance` 的 `writebackConfirmation` 现在显式检查：

- runtime snapshot
- latest acceptance artifact
- snapshot.artifacts
- latest closeout 是否已追平 snapshot

并且 playbook 会直接给出：

- `python3 scripts/write_acceptance_artifact.py --decision accepted ...`
- `python3 scripts/write_acceptance_artifact.py --decision deferred ...`
- `python3 scripts/write_acceptance_artifact.py --decision rejected ...`

### 2.4 可见性补齐

`Collaboration` 右侧 evidence 面板现在也会展示：

- latest acceptance artifact

不再只有 snapshot / closeout。

## 3. 文档回写

本轮同步更新：

- `docs/roadmap/master-task-plan.md`
- `docs/prd/collaboration-workflow-implementation-prd.md`
- `docs/prd/collaboration-operator-workflow-prd.md`

FlowMind 侧仍只更新 canonical tracker / roadmap / change record。

## 4. 验证

### 本地

- `.venv/bin/python -m pytest tests/test_sprint4.py -q`
- `python3 -m py_compile src/webui/api.py scripts/write_acceptance_artifact.py`
- `node --check src/webui/static/js/collaboration.js`
- `bash scripts/check_harness_governance_all.sh`
- `python3 /home/flowmind/FlowMindDeploy/scripts/governance/check_cross_repo_prd_sync.py --source-repo-root /home/flowmind/FlowMindDeploy --counterpart-repo-root /home/flowmind/CrazyAgentsManage`
- local closeout evidence:
  - `trace.id = S-20260525-002`
  - `closeout.id = C-20260525-002`

### 宿主

固定顺序：

1. `python3 scripts/governance/sync_live_deploy_copy.py --workspace-root . --profile crazy-runtime-live --skip-verify --json`
2. `python3 scripts/runtime/run_on_ali_hermes.py --cwd /root/CrazyAgentsManage -- 'python3 scripts/runtime/sync_hermes_script_mirror.py'`
3. `python3 scripts/governance/sync_live_deploy_copy.py --workspace-root . --profile crazy-webui-live --skip-verify --json`

随后：

- `python3 scripts/runtime/run_on_ali_hermes.py -- 'systemctl restart cam.service'`
- `python3 scripts/runtime/run_on_ali_hermes.py -- 'systemctl is-active cam.service'`
- `python3 scripts/runtime/run_on_ali_hermes.py -- 'python3 /root/CrazyAgentsManage/scripts/write_acceptance_artifact.py --help'`
- `python3 scripts/runtime/run_on_ali_hermes.py -- 'curl -s http://127.0.0.1/manage/api/collaboration/summary'`
- `python3 scripts/runtime/run_phase_c_collaboration_live_gate.py --output-dir /tmp/phase-c-live-gate`

## 5. 当前裁定

`Phase C` 现在处于：

- `in-progress / fifth-slice-landed`

也就是说：

1. action playbook 已成立
2. object-level writeback confirmation 已成立
3. acceptance artifact 已成为独立 repo-owned 对象

## 6. 结论

Phase C 的第五切片已经完成收口。

当前结论是：

- `accept / reject / defer` 已经是独立 repo-owned acceptance artifact
- `writebackConfirmation` 已经对 acceptance artifact 做对象级收口
- reviewer / Hermes acceptance 不再构成新的 FlowMind contract gap
- 如果后续还要细化 handoff contract writeback，只属于增强项，不再是 Phase C 主线尾巴
