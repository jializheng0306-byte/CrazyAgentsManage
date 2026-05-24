# Phase C · Collaboration Action Playbooks Closeout（2026-05-24）

> 范围: Crazy `Phase C · Harness × Hermes 协作层对齐` 第三切片  
> 状态: `in-progress / third-slice-landed`  
> 宿主: `ALI-HERMES`

## 1. 目标

把 `Phase C` 从：

- 已能看见 reviewer / Hermes acceptance / PRD closeout 三段 evidence chain
- 但 operator 还需要自己判断“跳去哪、跑什么、写回哪里”

推进到：

- `Collaboration` 直接给出 action playbook
- `Tasks` / `Operations` 接收 action context 并落到对应工作面
- triage 继续贴近真实处理动作与 writeback path

## 2. 本轮落地

### 2.1 Collaboration action playbooks

`/api/collaboration/summary` 里的 degraded `actionItems` 与 `evidenceChain` 现在都会显式给出：

- `routeHref`
- `routeLabel`
- `commands`
- `writebackPaths`

当前已覆盖：

- `reviewer-state`
- `hermes-acceptance`
- `prd-closeout`

### 2.2 Context-aware landing

`/collaboration` 的 action link 不再只是裸跳转，而是带 context 的入口：

- `Tasks`
  - `?action=...&focus=request-bus&stage=...`
- `Operations`
  - `?family=harness&action=prd-closeout&focus=commands`

### 2.3 Tasks / Operations 接收上下文

当前页面行为：

- `Tasks` 会显示 action banner，并把视线聚焦到 `request-bus / DAG / task list`
- `Operations` 会根据 query param 直接切到对应 family，并显示 context banner

## 3. 文档回写

本轮同步更新：

- `docs/roadmap/master-task-plan.md`

本轮没有新增 FlowMind contract/read-surface gap，因此 FlowMind 侧仍只需要更新 canonical tracker，不需要进入实现补偿开发。

## 4. 验证

### 本地

- `.venv/bin/python -m pytest tests/test_sprint4.py -q`
- `.venv/bin/python -m pytest tests/test_phase_c_live_gate_runner.py tests/test_sprint4.py -q`
- `python3 -m py_compile src/webui/api.py src/webui/app.py`
- `python3 -m py_compile scripts/runtime/run_phase_c_collaboration_live_gate.py`
- `node --check src/webui/static/js/collaboration.js`
- `node --check src/webui/static/js/tasks.js`
- `node --check src/webui/static/js/operations.js`
- `bash scripts/check_harness_governance_all.sh`
- `python3 /home/flowmind/FlowMindDeploy/scripts/governance/check_cross_repo_prd_sync.py --source-repo-root /home/flowmind/FlowMindDeploy --counterpart-repo-root /home/flowmind/CrazyAgentsManage`
- local closeout evidence:
  - `trace.id = S-20260524-007`
  - `closeout.id = C-20260524-007`
  - `lane = shared`
  - `topic = phase-c-collaboration-action-playbooks`

### 宿主

固定顺序：

1. `python3 scripts/governance/sync_live_deploy_copy.py --workspace-root . --profile crazy-runtime-live --skip-verify --json`
2. `python3 scripts/runtime/run_on_ali_hermes.py --cwd /root/CrazyAgentsManage -- 'python3 scripts/runtime/sync_hermes_script_mirror.py'`
3. `python3 scripts/governance/sync_live_deploy_copy.py --workspace-root . --profile crazy-webui-live --skip-verify --json`

随后：

- `systemctl restart cam.service`
- `GET http://47.99.217.1/manage/api/collaboration/summary`
- `GET http://47.99.217.1/manage/api/collaboration/graph-projection`
- focused Playwright gate:
  - `/manage/collaboration`
  - `/manage/architecture/tech`
  - canonical command:
    - `python3 scripts/runtime/run_phase_c_collaboration_live_gate.py --output-dir /tmp/phase-c-live-gate`
  - optional non-blocking public probe:
    - `python3 scripts/runtime/run_phase_c_collaboration_live_gate.py --output-dir /tmp/phase-c-live-gate --probe-public-url http://47.99.217.1/manage`

## 5. 当前裁定

`Phase C` 现在处于：

- `in-progress / third-slice-landed`

也就是说：

1. canonical evidence chain 已成立
2. triage 已继续贴到 action playbook 与 writeback path
3. `Tasks` / `Operations` 已能接住协作上下文跳转

## 6. 剩余风险收口（2026-05-24 补记）

此前 focused Playwright gate 的主要不稳定点，不在页面实现本身，而在“公网直连入口”缺乏稳定性。

当前已明确收口为：

- `SSH tunnel -> localhost -> /manage/*` 是 canonical live gate 路径
- `public URL` 只保留为附加探针，不再作为 blocker
- 仓库内已有脚本 `scripts/runtime/run_phase_c_collaboration_live_gate.py` 负责：
  - 建立和清理 ALI-HERMES tunnel
  - 当默认本地端口被占用时自动切到空闲端口
  - 运行 focused Playwright gate
  - 可选附带 public probe，但 public 失败不会推翻 canonical gate 结果
- 本轮收口证据：
  - `trace.id = S-20260524-008`
  - `closeout.id = C-20260524-008`
  - canonical gate passed
  - public probe remained `ERR_EMPTY_RESPONSE`, but no longer blocks release judgment

剩余主问题变成：

- 是否需要更细粒度的 handoff contract / acceptance artifact 回写
- 是否需要把 action playbook 继续升级成对象级 writeback confirmation
