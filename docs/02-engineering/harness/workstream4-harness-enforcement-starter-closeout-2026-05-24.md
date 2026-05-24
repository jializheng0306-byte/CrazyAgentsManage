# Workstream 4 · Harness Enforcement Starter Closeout（2026-05-24）

> 范围: Crazy `Workstream 4 Harness Productization Starter`  
> 状态: `completed-in-lane`  
> 宿主: `ALI-HERMES`

## 1. 目标

把 Crazy `Workstream 4` 从：

- Harness 脚本和文档已经存在，但默认使用链不可见、不可追踪

推进到：

- `Operations` 可直接巡检 Harness readiness
- `closeout artifact` 成为显式仓库工件
- `check_harness_governance_all.sh` 会继续检查 closeout chain
- worktree lane 信息可被 closeout 工件追踪

## 2. 本轮落地内容

### 2.1 Operations > Harness

已接入：

- success trace count
- failure trace count
- closeout count
- pending closeout count
- critic readiness
- closeout readiness
- worktree bootstrap readiness
- runbooks / default commands

### 2.2 Closeout artifact

新增目录：

- `harness/closeouts/`

closeout payload 现在绑定：

- trace id / kind
- governance result
- governance reports
- critic result
- critic write-back 是否触发
- worktree path
- lane
- lane source
- topic

### 2.3 Worktree lane traceability

`scripts/worktree/create-agent-worktree.sh` 现在会写：

- `.omx/worktree-context.json`

用于让后续 closeout 记录 lane / topic / branch / worktree metadata。

### 2.4 Governance enforcement

新增检查：

- `python3 scripts/check_harness_closeout_chain.py`

并接入：

- `scripts/check_harness_governance.sh`
- `scripts/check_harness_governance_all.sh`

当前检查目标：

1. enforced trace 必须绑定 closeout
2. success closeout 必须带 governance 结果
3. failed closeout 必须带 critic 分析
4. non-trivial closeout 必须带 lane / worktree traceability

## 3. 宿主验证

按固定顺序执行：

1. `python3 scripts/governance/sync_live_deploy_copy.py --workspace-root . --profile crazy-runtime-live --skip-verify --json`
2. `python3 scripts/runtime/run_on_ali_hermes.py --cwd /root/CrazyAgentsManage -- 'python3 scripts/runtime/sync_hermes_script_mirror.py'`
3. `python3 scripts/governance/sync_live_deploy_copy.py --workspace-root . --profile crazy-webui-live --skip-verify --json`

随后宿主 smoke：

- `node scripts/harness-closeout-writeback.cjs --status success --message 'Host harness smoke' --lane shared --topic host-harness-smoke --skip-governance-check --json`

宿主结果：

- `trace.id = S-20260524-001`
- `closeout.id = C-20260524-001`
- `lane = shared`
- `laneSource = cli-arg`

部署副本 `GET /api/operations/harness` 已可见：

- `closeoutCount`
- `pendingCloseoutCount`

部署副本 `GET /api/operations/control-room-summary` 已包含：

- `harness`

## 4. 当前裁定

`Workstream 4` 现已进入：

> `completed-in-lane` 的 starter 状态

也就是说：

1. 可见性已经成立
2. closeout artifact 已成为仓库事实
3. lane traceability 已进入工件
4. governance check 已能拦截明显缺链

但它还不是：

> `completed-published`

因为当前还缺：

- 默认强制 adoption
- 非平凡迭代全面改走这条默认 closeout 链

## 5. 下一跳

下一条最自然的工作，不再是补新的 Harness 卡片，而是：

1. 让非平凡迭代默认走 `harness-closeout-writeback`
2. 让 success / failure trace + closeout artifact 变成默认习惯
3. 让 reviewer / Hermes acceptance / PRD closeout 都沿同一条链收口
