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

### 2.5 readonly capability probe 也已补齐

新增：

- `shared-context/executor-sources/flowmind-health-readonly-openapi.v1.json`
- `scripts/runtime/ensure_flowmind_health_readonly_source.py`

并把 `scripts/flowmind-health-check.py` 扩为：

- host-owned report read 仍是主判断链
- 同时 best-effort 通过 executor 直读：
  - `/healthz`
  - `/readyz`

宿主实测：

- `flowmind-health-readonly` source 创建成功
- 直跑 `python3 /root/.hermes/scripts/flowmind-health-check.py` 时已出现：
  - `Executor probe: flowmind-health-readonly healthz=ok readyz=ready`

### 2.6 异常通知演练链路已 deterministic 化

新增：

- `scripts/flowmind-health-notify.py`

它负责：

- 读取 `flowmind-health-check.py` 写出的 runtime-local snapshot
- 在 `ABNORMAL / ERROR` 状态下生成固定的 Feishu post payload
- 支持 `--dry-run`，从而在不向正式群发误报的前提下完成异常通知演练

当前 snapshot 默认写入：

- `~/.hermes/cron/state/flowmind-health-check-latest.json`

宿主演练已通过：

- 真实 `OK` snapshot 由 `flowmind-health-check.py` 直接写出
- 用受控 `ABNORMAL` fixture 执行：
  - `python3 /root/.hermes/scripts/flowmind-health-notify.py --snapshot /tmp/flowmind-health-abnormal.json --dry-run`

结果：

- 成功打印待发送 payload
- 摘要中包含：
  - failed check
  - review queue backlog
  - executor probe degraded

## 3. 为什么这轮没有继续把主判断权交给 executor

本轮结论是：

- `flowmind.health-probe` 已经完成 Wave 2 收口
- 但它的完成态也不是“让 executor 接管主判断权”

原因：

1. 当前 blocker 首先是 host governance，而不是 capability gap。
2. 这条链的核心 truth 仍然是 host-owned FlowMind health report。
3. readonly capability probe 有价值，但更适合作为补充验证面，而不是替代 host 主判断链。

因此当前最准确的裁定是：

> `flowmind.health-probe` 已经回到受支持的 repo-tracked host mainline，并补上了 readonly health endpoint probe；但 executor 仍不是这条链的主 authority。

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
6. `python3 scripts/runtime/run_on_ali_hermes.py --cwd /root/CrazyAgentsManage -- 'python3 scripts/runtime/ensure_flowmind_health_readonly_source.py --required-tool getReadyz'`
7. `python3 scripts/runtime/run_on_ali_hermes.py --cwd /root/CrazyAgentsManage -- 'python3 /root/.hermes/scripts/flowmind-health-check.py'`
8. `python3 scripts/runtime/run_on_ali_hermes.py --cwd /root/CrazyAgentsManage -- 'python3 /root/.hermes/scripts/flowmind-health-notify.py --snapshot /tmp/flowmind-health-abnormal.json --dry-run'`

## 5. Wave 2 总状态

本轮之后，Wave 2 应被解释为：

1. `tech-radar.review`
   - readonly evidence enrichment 已落地并 hardened

2. `flowmind.health-probe`
   - repo-tracked host mainline 已落地
   - 历史 paused job 已恢复并手动验证

也就是说：

> Wave 2 不再有“还悬着的第二条候选线”。

## 6. 后续扩展点

1. 若未来要继续增强 executor 参与度，应先证明它比当前 host-owned report read + readonly probe 的组合更有实质收益。
2. 宿主 `/root/CrazyAgentsManage` 当前是 live deploy copy，不等同于 git checkout 基线；这是一条长期边界规则，不再视为 Wave 2 未收口项。
3. 当前生产 job prompt 仍保留旧的 inline `lark-cli` 说明，但异常通知的 deterministic helper 已经落地并完成 dry-run；后续若要把 runtime prompt 也切到 helper，需要先解决 live deploy copy 的 git-tracked prompt guard 约束。

## 7. 一句话结论

> `flowmind.health-probe` 的 Wave 2 完成方式不是让 executor 接管主判断，而是把宿主已有巡检脚本收回 repo fact layer、清掉 AI cron guard、恢复并验证历史 paused job，并补上一条 readonly health endpoint probe；这一步已经在 `ALI-HERMES` 上完成。

## 8. 2026-06-02 恢复备注

2026-06-02 的那次巡检异常最终确认是 `TX-NEWHOST` 先前关机后恢复期内的临时不可达，不是巡检脚本回归。

复核结果：

- `ssh` 到 `111.229.194.203` 已恢复
- `flowmind-newhost.service` 为 `active (running)`
- `nginx` 为 `active (running)`
- `http://127.0.0.1:3301/healthz` 返回 `200`
- `http://127.0.0.1:3301/readyz` 返回 `ready`
- `https://www.uncentury.cn/healthz` 在主机本地 SNI 复核下返回 `200 OK`

因此，这次告警应归类为：

- 主机停机 / 恢复窗口导致的短暂不可达
- 不是 JSON 解析问题
- 不是巡检脚本逻辑问题
