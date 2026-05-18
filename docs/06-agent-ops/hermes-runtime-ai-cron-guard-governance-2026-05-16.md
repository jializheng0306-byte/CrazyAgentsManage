# Hermes Runtime AI Cron Guard Governance

> 日期: 2026-05-16  
> 适用宿主: `ALI-HERMES`  
> 范围: Hermes runtime-local AI cron job (`~/.hermes/cron/jobs.json`)  
> 目的: 防止“设计稿/回顾文档中的候选方案”先于实现进入 live runtime

## 1. 背景

2026-05-15 在 `ALI-HERMES` 上排查到一条 runtime-local AI cron job：

- `job_id`: `89317c3146b3`
- `name`: `FlowMind feedback consume poller`
- `schedule`: `every 10m`
- `prompt`: `Run /root/CrazyAgentsManage/scripts/consume_feedback.py ...`

问题在于：

1. 该 job 存在于 `~/.hermes/cron/jobs.json`，不受 git 仓库直接追踪。
2. 它引用了 `/root/CrazyAgentsManage/scripts/consume_feedback.py`。
3. 该脚本并不是当前仓库中的已落地默认实现。
4. 仓库文档当时只在“未来若拆分调度”的候选方案里提到 `consume_feedback.py`，并未授权将其直接创建为 live job。

结果是：

- runtime-local job 先于实现进入 live
- operator 误以为“仓库已经支持这条链”
- 后续故障表现为与真实主链无关的 PAT / provider / skill 运行错误

## 2. 当前裁定

### 2.1 事实层分离

- `~/.hermes/cron/jobs.json` = **runtime-local 调度状态**
- `docs/` + `harness/` + 仓库跟踪脚本 = **repo truth**

二者不能互相替代。

尤其是：

- 文档里出现一个候选脚本名
- backlog 里出现一个未来拆分方案
- chat 中有人提到“以后可以拆成 10 分钟轮询”

都 **不等于** 可以直接在 `jobs.json` 创建 live AI cron job。

### 2.2 Crazy 当前默认主链

对 Crazy/FlowMind 承诺治理而言，当前默认主链是：

- `/root/.hermes/scripts/daily-promise-review.py`

它承担：

1. truth 读取
2. trace 读取
3. feedback 读取
4. Promise Overview 主表写回
5. Interaction Trace 写回
6. `last_governance_feedback` 更新

因此，在一个 **真正受仓库跟踪** 的 `consume_feedback.py` 落地前：

- **不得**创建独立 `FlowMind feedback consume poller`
- **不得**把 feedback split 方案直接写成 live runtime job

## 3. 2026-05-16 已落地的 live guard

live guard 已补到：

- `/root/hermes-agent-v2026.4.30-deepseek/tools/cronjob_tools.py`

仓库内的可追踪安装/审计工件：

- [install_hermes_ai_cron_guard.py](/home/flowmind/CrazyAgentsManage/scripts/runtime/install_hermes_ai_cron_guard.py)
- [audit_hermes_ai_cron_jobs.py](/home/flowmind/CrazyAgentsManage/scripts/runtime/audit_hermes_ai_cron_jobs.py)
- [hermes-script-mirror-manifest.json](/home/flowmind/CrazyAgentsManage/shared-context/hermes-script-mirror-manifest.json)

guard 规则：

1. **AI cron prompt 中引用本地脚本路径时**：
   - 路径必须存在
   - 路径必须是文件
   - 路径必须位于某个 git 仓库内
   - 路径必须是该仓库的 git-tracked 文件
2. **prompt 中使用相对脚本路径时**：
   - 必须同时提供 `workdir`
   - Hermes 才能在创建前解析并验证该路径
3. **`script=` 字段时**：
   - 路径仍必须位于 `~/.hermes/scripts/`
   - 且该文件在创建/更新时必须已存在
   - 且必须在 `~/.hermes/scripts/.mirror-manifest.json` 中声明 repo source-of-truth

这条 guard 的目标不是替代 repo 治理，而是阻止明显越过 repo truth 的 live job 进入运行态。

## 4. Operator 规则

以后在 `ALI-HERMES` 上创建 AI cron job，必须遵守：

### 4.1 创建前校验

若 prompt 或脚本路径指向仓库文件，先校验：

```bash
test -f /root/CrazyAgentsManage/scripts/<name>.py
git -C /root/CrazyAgentsManage ls-files --error-unmatch scripts/<name>.py
```

两条都通过，才允许创建。

### 4.2 不允许的输入来源

以下来源 **不能直接变成 live AI cron job**：

- backlog / handoff 文档中的“候选拆分方案”
- 设计稿里的“未来可新增脚本名”
- issue 评论中的操作建议
- chat 中未落库的临时执行想法

### 4.3 允许创建独立 runtime-local AI cron 的前提

至少同时满足：

1. 脚本或消费面已经在仓库中真实存在
2. 该文件已被 git 跟踪
3. 仓库文档已经明确它是可运行主链，而不是候选方案
4. live sync 路径已确定（repo → host）
5. 该 job 不与现有默认主链形成重复 authority

## 5. 对 `~/.hermes/scripts` mirror 的补充规则

`~/.hermes/scripts/*` 可以继续存在，但它只是宿主机 mirror，不是 authority。

如果某个 AI cron / no-agent cron 使用了 `~/.hermes/scripts/*`：

1. repo 中必须有对应 source-of-truth 文件
2. 文档必须写明 mirror 来源
3. 变更后必须同步到宿主机副本
4. 不允许只改 `~/.hermes/scripts/*` 而不回写仓库

## 6. 2026-05-16 现场处置

本次已执行：

1. 暂停 runtime-local job `89317c3146b3`
2. 将承诺治理调度收口到统一链 `daily-promise-review.py`
3. 给 Hermes runtime 增加创建前 guard
4. 将 guard 的安装器、审计器和 mirror manifest 写回仓库
5. 暂停当前仍无 repo source-of-truth 的启用中 AI cron job
6. 将承诺治理统一链改成 `only-if-changed` 模式
7. 暂停与 `system crontab` 重复的 AI cron job
8. 将 Hermes 默认 provider 从失效的 `copilot/claude-opus-4.6` 回切为 `xiaomi/mimo-v2.5-pro`

对应 live 行为验证：

- 坏 prompt：
  - `Run /root/CrazyAgentsManage/scripts/consume_feedback.py ...`
  - **被拦截**
- 好 prompt：
  - `Run /root/CrazyAgentsManage/scripts/daily-promise-review.py ...`
  - **允许创建**
- 统一刷新链：
  - 继续按 `*/30 8-21` 触发
  - 但只有状态摘要变化时才写回/发消息

### 6.0 `only-if-changed` 口径

当前 `ALI-HERMES` 上的承诺治理统一链，不再等同于“每 30 分钟都做一次完整审查并发群消息”。

实际语义是：

1. 每 30 分钟做一次轻量探测
2. 读取承诺 + truth/trace/feedback 形成状态摘要
3. 若摘要和上次相同，则直接退出
4. 只有摘要变化时，才执行：
   - Bitable 写回
   - 本地报告落盘
   - 飞书群消息发送

状态摘要文件默认位于：

- `~/.hermes/promises/reviews/daily-promise-review-state.json`

### 6.1 2026-05-16 已暂停的遗留 AI cron

以下 job 因“仍无 repo-tracked source-of-truth”已在 `ALI-HERMES` 上暂停：

1. `c262d04dd857` — `FlowMind巡检-每日一次`
2. `1a78710a5ee4` — `午间论文-情报哨兵`
3. `a4113733d984` — `每周聊天归档+图谱更新`
4. `52b9717907fd` — `kanban-web-refresh`

暂停原因统一写入：

- `AI cron guard: Missing repo-tracked source-of-truth ...`

在这些脚本回到受 git 跟踪的 repo fact layer 前，不得恢复。

### 6.1b 2026-05-16 已暂停的重复 AI cron

以下 job 虽然有 source-of-truth，但因与 `system crontab` 重复，已被暂停：

1. `2740994773ec` — `晨间情报-情报哨兵agent模式`
2. `d1ba7a14ad58` — `晚间趋势-情报哨兵agent模式`
3. `7102c72fdf8b` — `每日反思-基于实际活动`
4. `839db2992cc9` — `记忆系统维护-每周日`

统一暂停原因格式：

- `Runtime dedupe: Duplicate of system cron ...`

裁定理由：

- `system crontab` 已承载同一业务链
- AI cron 与 system cron 并行只会制造“双重 authority + 双重告警 + 双重失败表象”

### 6.1c 当前保留的 AI cron

2026-05-16 收口后，仍保留启用中的 AI cron 仅限**非重复**任务：

1. `f77e10821b97` — `Cron健康检查-每日两次`
2. `06afc0fecead` — `Tech Radar周审查-每周日`

它们已额外 pin 到：

- `provider = xiaomi`
- `model = mimo-v2.5-pro`

### 6.2 审计口径

仓库内审计脚本：

- [audit_hermes_ai_cron_jobs.py](/home/flowmind/CrazyAgentsManage/scripts/runtime/audit_hermes_ai_cron_jobs.py)

默认只审计 **启用中的** AI cron job。

理由：

- 已暂停 job 是“待治理存量”，不是当前运行态风险
- operator 需要优先看到“现在还在跑、但没有 source-of-truth 的 job”

### 6.3 Provider 收口

2026-05-16 前，`ALI-HERMES` 的默认配置曾漂移为：

- `provider: copilot`
- `model: claude-opus-4.6`

这会导致 runtime-local AI cron 在执行时统一报：

- `checking third-party user token: bad request: Personal Access Tokens are not supported for this endpoint`

因此本轮已把 Hermes 默认 provider 回切到：

- `provider: xiaomi`
- `model: mimo-v2.5-pro`

并通过本地交付 smoke job 验证该 provider 链可正常完成一次 cron run。

## 7. 一句话规则

> `jobs.json` 里的 AI cron job 只是 runtime-local state，不是 repo truth。任何引用本地脚本的 AI cron，在进入 live 前都必须先证明：脚本真实存在、被 git 跟踪、并且已被仓库文档授权为可运行主链，而不是设计稿中的未来方案。
