# Hermes 真实运行面 Authority 审计

> 日期：2026-05-02
> 范围：`ALI-HERMES` (`47.99.217.1`)
> 目标：固定真实调度 authority、活跃入口脚本与遗留脚本的关系，避免后续继续把“旧文档入口”误认成“当前运行事实”

---

## 一、结论先行

当前 `ALI-HERMES` 不是“没有 scheduler”，而是**存在两类 scheduler authority**：

1. root `crontab`
   - 负责晨间/午间/晚间/反思/承诺等 shell/python 定时任务
2. Hermes `~/.hermes/cron/jobs.json`
   - 负责 Hermes 内部提醒类任务
   - 当前已确认承载 `flowmind-health-check.py`

因此，后续所有修复都必须避免再使用“Cron 系统”这种混称，而要明确：

- `root crontab` authority
- `Hermes jobs.json` authority

---

## 二、实测 authority

### 2.1 root crontab

当前实测条目：

```cron
30 8 * * * /usr/bin/python3 /root/.hermes/scripts/morning-intel-v2.py >> /root/.hermes/logs/cron.log 2>&1
0 9 * * * /root/.hermes/scripts/daily-promise-review.py >> /root/.hermes/logs/cron.log 2>&1
0 12 * * * /root/.hermes/scripts/noon-paper-review.sh >> /root/.hermes/logs/cron.log 2>&1
0 20 * * * /root/.hermes/scripts/evening-trend-analysis.py >> /root/.hermes/logs/cron.log 2>&1
0 23 * * * /root/.hermes/scripts/daily-reflection.sh >> /root/.hermes/logs/cron.log 2>&1
30 23 * * * /root/.hermes/scripts/auto-reflection.sh >> /root/.hermes/logs/cron.log 2>&1
0 10 * * 0 /root/.hermes/scripts/weekly-memory-maintenance.sh >> /root/.hermes/logs/cron.log 2>&1
```

判定：

- 当前 root `crontab` 是 shell/python 运营任务的真实 authority
- `morning-intel-v2.py`、`daily-promise-review.py`、`evening-trend-analysis.py` 已经取代旧 `.sh` 版本作为现行入口

### 2.2 Hermes jobs.json

当前已确认任务：

1. `FlowMind巡检-每日两次`
   - 脚本：`flowmind-health-check.py`
   - 调度：`0 8,20 * * *`
2. `每日反思-基于实际活动`
   - Hermes 内部任务面

判定：

- `flowmind-health-check.py` 的 authority 在 Hermes `jobs.json`
- 它不应再被写成 root `crontab` 任务，否则会重新引入双 authority

---

## 三、活跃入口与遗留入口

### 3.1 当前活跃入口

| 任务 | 当前活跃入口 | authority |
|---|---|---|
| 晨间情报 | `/root/.hermes/scripts/morning-intel-v2.py` | root `crontab` |
| 承诺审查 | `/root/.hermes/scripts/daily-promise-review.py` | root `crontab` |
| 午间论文 | `/root/.hermes/scripts/noon-paper-review.sh` | root `crontab` |
| 晚间趋势 | `/root/.hermes/scripts/evening-trend-analysis.py` | root `crontab` |
| 每日反思 | `/root/.hermes/scripts/daily-reflection.sh` | root `crontab` |
| 自动反思 | `/root/.hermes/scripts/auto-reflection.sh` | root `crontab` |
| 记忆维护 | `/root/.hermes/scripts/weekly-memory-maintenance.sh` | root `crontab` |
| FlowMind 巡检 | `/root/.hermes/scripts/flowmind-health-check.py` | Hermes `jobs.json` |

### 3.2 已确认遗留但未主动调度的入口

| 路径 | 当前状态 | 风险 |
|---|---|---|
| `/root/.hermes/scripts/morning-intel.sh` | 遗留旧版 shell 脚本 | 内容为旧采集逻辑，占位输出风险高 |
| `/root/.hermes/scripts/daily-promise-review.sh` | 遗留旧版 shell 脚本 | 内容为骨架统计，和现行 `.py` 入口冲突 |
| `/root/.hermes/scripts/evening-trend-analysis.sh` | 遗留旧版 shell 脚本 | 内容为模拟数据/占位输出，不应再被当成现行事实 |

---

## 四、为什么现在不能直接删除旧 `.sh`

这 3 个旧入口虽然已经不在主动调度面里，但审计发现它们仍被以下内容引用：

1. `~/.hermes/skills/devops/*` 下的 live skill 文档
2. 部分历史运营文档
3. 旧的手工操作说明

因此当前直接删除会带来两个问题：

1. 运行面 guidance 与实际入口再次脱节
2. 仍按旧文档手工操作的人会直接撞到 “file not found”

当前更合理的收口顺序是：

1. 先更新仓库与 live skill 中的入口说明
2. 再决定把旧 `.sh` 归档、替换成兼容 wrapper，还是删除

---

## 五、与 FlowMind 相关的裁定

### 5.1 已成立

1. `flowmind_capture.py + flowmind_handshake_smoke.py` 是当前唯一受支持的 ingress 验证对
2. direct-path handshake 已通过
3. `flowmind-health-check.py` 是最成熟的一条跨系统健康链路

### 5.2 仍待裁定

1. `flowmind_capture.py` 是否从人工闸门进入正式调度
2. `bitable_sync.py` 是否单独调度，还是继续作为上游任务中的显式步骤
3. `task_watcher.py` 如何恢复为默认控制协议，而不是仅有代码存在

---

## 六、下一步收口动作

1. 更新双仓文档，把 `Candidate ingress` 状态从“待修”改为“已握手，待策略裁定”
2. 更新 Crazy/Hermes 的入口说明，把 `.py` 入口写成现行事实
3. 对旧 `.sh` 采取兼容收口方案：
   - 要么改成 wrapper
   - 要么更新全部引用后归档
4. 在 closeout 中明确写清：
   - 哪些任务归 root `crontab`
   - 哪些任务归 Hermes `jobs.json`
   - 哪些任务仍是人工闸门

---

## 七、一句话结论

> `ALI-HERMES` 当前真正的问题已经不是“有没有 cron”，而是“root crontab 与 Hermes jobs.json 各自负责什么，以及旧 `.sh` 入口何时退出事实源”。这属于 authority 收口问题，不再是 transport 或基础脚本可用性问题。
