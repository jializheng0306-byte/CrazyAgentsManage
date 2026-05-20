# flowmind.health-probe × Wave 2 closeout（2026-05-20）

> 宿主: `ALI-HERMES`  
> 任务类型: `flowmind.health-probe`  
> 范围: `Wave 2` 收尾  
> 历史 job: `FlowMind巡检-每日一次` / `c262d04dd857`

## 1. 本轮结论

`flowmind.health-probe` 的核心缺口不是“没有 executor capability”，而是：

- 宿主上已经有真实巡检脚本
- 但它不在 repo-tracked fact layer
- 因此被 AI cron guard 以 `Missing repo-tracked source-of-truth` 暂停

所以本轮的正确收口不是继续给它补 executor source，而是：

> 先把 FlowMind 巡检脚本正式纳入仓库主链，清掉 source-of-truth blocker，再恢复宿主运行态。

## 2. 实际落地

### 2.1 新增 repo-tracked wrapper

新增：

- `scripts/flowmind-health-check.py`

它把宿主上原有巡检逻辑正式收回仓库：

- 通过 SSH 读取 FlowMind 新主控面的 health report JSON
- 按顺序尝试：
  - current report
  - latest-run report
  - `ops-health.log` 最后一个完整 JSON block
- 产出稳定的：
  - `STATUS: OK`
  - `STATUS: ABNORMAL`
  - `STATUS: ERROR`

### 2.2 接入宿主同步链

已接入：

- `scripts/governance/live-deploy-sync.manifest.json`
- `shared-context/hermes-script-mirror-manifest.json`

这样 `sync_live_deploy_copy` 会把仓库脚本同步到：

- `/root/CrazyAgentsManage/scripts/flowmind-health-check.py`

`sync_hermes_script_mirror.py` 会再同步到：

- `/root/.hermes/scripts/flowmind-health-check.py`

### 2.3 AI cron guard blocker 已清掉

宿主上执行 include-disabled 审计：

- `python3 /root/CrazyAgentsManage/scripts/runtime/audit_hermes_ai_cron_jobs.py --jobs /root/.hermes/cron/jobs.json --manifest /root/.hermes/scripts/.mirror-manifest.json --hermes-home /root/.hermes --include-disabled`

结果：

- `ok: true`
- `count: 0`

说明：

- `FlowMind巡检-每日一次` 不再因为 source-of-truth 缺失被判违规

### 2.4 历史 paused job 已恢复并手动触发

在宿主上执行：

- `hermes cron resume c262d04dd857`
- `hermes cron run --accept-hooks c262d04dd857`
- `hermes cron tick --accept-hooks`

结果：

- job 重新进入 `enabled=true`
- `state=scheduled`
- `last_status=ok`
- `last_error=null`
- `repeat.completed` 从 `31` 增加到 `32`

并生成新的 cron output：

- `~/.hermes/cron/output/c262d04dd857/2026-05-20_10-40-13.md`

其中记录：

- script output = `STATUS: OK`
- final response = `FlowMind巡检正常`

## 3. 为什么这轮没有继续 executor 化

本轮结论是：

- `flowmind.health-probe` 已经完成 Wave 2 收口
- 但它的完成态不是“继续补 executor source”

原因：

1. 当前 blocker 是 host governance，不是 capability gap。
2. 这条链的核心读取对象是 host-owned FlowMind health report，而不是一个需要先接 capability plane 才能访问的外部资料面。
3. 在 source-of-truth 没闭合前继续谈 executor 只会把问题绕开，不会把主线做完。

因此当前最准确的裁定是：

> `flowmind.health-probe` 已经回到受支持的 repo-tracked host mainline，但暂不进入 executor default lane。

## 4. 验证

### 4.1 本地

已通过：

- `.venv/bin/python -m pytest tests/test_flowmind_health_check.py tests/test_hermes_ai_cron_guard_audit.py -q`
- `bash scripts/check_harness_governance_all.sh`

### 4.2 宿主

按固定顺序执行：

1. `python3 scripts/governance/sync_live_deploy_copy.py --workspace-root . --profile crazy-runtime-live --skip-verify --json`
2. `python3 scripts/runtime/run_on_ali_hermes.py --cwd /root/CrazyAgentsManage -- 'python3 scripts/runtime/sync_hermes_script_mirror.py'`
3. `python3 scripts/runtime/run_on_ali_hermes.py --cwd /root/CrazyAgentsManage -- 'python3 /root/.hermes/scripts/flowmind-health-check.py'`

补充宿主验证：

4. include-disabled AI cron guard audit
5. `hermes cron resume/run/tick` 恢复并手动触发历史 job

## 5. Wave 2 总状态

本轮之后，Wave 2 应被解释为：

1. `tech-radar.review`
   - readonly evidence enrichment 已落地并 hardened

2. `flowmind.health-probe`
   - repo-tracked host mainline 已落地
   - 历史 paused job 已恢复并手动验证

也就是说：

> Wave 2 不再有“还悬着的第二条候选线”。

## 6. 剩余注意项

1. `flowmind.health-probe` 当前恢复的是 host health lane，不是 executor source lane。
2. 若未来要继续 executor 化，应先证明它比当前 host-owned report read 方案更有实质收益。
3. 宿主 `/root/CrazyAgentsManage` 当前是 live deploy copy，不等同于 git checkout 基线；不要把 host runtime-local 状态误读为 repo truth。

## 7. 一句话结论

> `flowmind.health-probe` 的 Wave 2 正确完成方式不是继续追 executor，而是先把宿主已有巡检脚本收回 repo fact layer、清掉 AI cron guard、恢复并验证历史 paused job；这一步已经在 `ALI-HERMES` 上完成。
