# Sprint 2 · Control Plane Hardening Closeout（2026-05-23）

> 范围: Crazy `Sprint 2 Control Plane Hardening`  
> 状态: `completed-published`  
> 宿主: `ALI-HERMES`

## 1. 目标

把 Crazy `Sprint 2` 从：

- 一组已落但仍需继续拼接的 control-plane slices

推进到：

- 一个有 published baseline 的 operator-facing control room
- 一个在 `ALI-HERMES` 部署副本上可直接巡检的产品面
- 一个在双仓 PRD / roadmap / tracker / change-record 中口径一致的完成态

## 2. 已完成的对象族

### Collaboration / Loop Surface

- `promise-review-cycle`
- `morning-intel-cycle`
- memory candidate confirm / reject / defer
- feedback input local queue

### Tasks control plane

- task bus 四条 lane
  - `inbox`
  - `working`
  - `outbox`
  - `archive`
- status transition
- automation promotion gate

### Operations control room 第一批

- `Sources`
- `Tool Catalog`
- `Credential Health`
- `Provider Health`
- `Readonly Boundary`
- `Isolation`
- `Task Registry`
- `Automation Maturity`
- `Host Health`
- `Runbooks`

### Operations control room 第二批

- `Env Map`
- `Backup / Recovery`
- `Recovery Paths`

## 3. 宿主验证顺序

本轮继续遵守固定顺序：

1. `python3 scripts/governance/sync_live_deploy_copy.py --workspace-root . --profile crazy-runtime-live --skip-verify --json`
2. `python3 scripts/runtime/run_on_ali_hermes.py --cwd /root/CrazyAgentsManage -- 'python3 scripts/runtime/sync_hermes_script_mirror.py'`
3. `python3 scripts/governance/sync_live_deploy_copy.py --workspace-root . --profile crazy-webui-live --skip-verify --json`

之后再做只读宿主验证。

## 4. 宿主最终状态

### 4.1 Operations 页面

部署副本 `/operations` 已出现：

- `Task Registry`
- `Automation Maturity`
- `Host Health`
- `Env Map`
- `Isolation`
- `Readonly Boundary`
- `Backup / Recovery`
- `Recovery Paths`
- `Runbooks`

### 4.2 Control-room summary

部署副本 `GET /api/operations/control-room-summary` 已包含：

- `taskRegistry`
- `automationMaturity`
- `hostHealth`
- `envMap`
- `backupRecovery`
- `recoveryPaths`
- `runbooks`

### 4.3 Recovery path readiness

部署副本 `GET /api/operations/recovery-paths` 最终结果：

- `pathCount = 4`
- `readyCount = 4`
- `degradedCount = 0`
- `envDriftCount = 0`

### 4.4 Backup coverage evidence

部署副本 `GET /api/operations/recovery-paths` 最终结果：

- `deployCopyBackups = 3`
- `hostBackupSnapshots = 1`
- `memoryEditBackups = 14`
- `mirrorManifestPresent = true`
- `runbookCoverage = 2`

并已在宿主创建：

- `/root/backups/20260523-sprint2-closeout`

## 5. 双仓治理结论

治理检查结果：

- cross-repo PRD sync: `OK`
- Crazy harness governance all: `OK`

双仓口径已对齐：

- Crazy PRD / roadmap
- FlowMind canonical roadmap / tracker
- FlowMind change records
- Crazy harness closeout evidence

## 6. 裁定

`Sprint 2 Control Plane Hardening` 现可正式视为：

> `completed-published`

原因：

1. 第一批 control-plane objects 已全部进入产品面
2. 第二批 `env map / backup-recovery / recovery paths` 已进入产品面
3. 宿主部署副本已完成只读验证
4. 双仓文档系统与 change-record 已同步
5. 当前不再存在必须留在 Sprint 2 核心范围内的开放主风险

## 7. 后续边界

后续如继续扩 `Operations`，应视为：

- second-batch 深化

而不是继续把工作挂在 Sprint 2 核心缺口下。

当前自然下一跳只剩：

1. `env drift` 深化
2. `backup coverage` 深化
3. `recovery path` 更细粒度证据化

这些都不再改变 Sprint 2 已完成的主裁定。
