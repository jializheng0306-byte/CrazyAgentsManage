# TX-NEWHOST 架构部署环境完整性与角色验证测试方案（2026-06-28）

> 这份方案替换上一版以 `provider-mode` / executor capability 为中心的口径。
> 当前重点是：整套架构部署环境是否完整，以及每个应用是否仍只承担自己的角色。

## 1. 方案目标

在 `FlowMindDeploy` 和 `CrazyAgentsManage` 的最新版本都已经发布到服务器之后，验证当前 `TX-NEWHOST` 架构是否满足下面四件事：

1. 版本真相已经对齐，远端副本没有漂移。
2. 本地仓库健康，脚本、单测、静态检查都能通过。
3. 主机上的各个应用都存活，且入口、角色、回滚锚点都符合当前基线。
4. `Crazy -> Hermes -> FlowMind` 的协作链路可闭环，且角色边界没有混淆。
5. 人工可以介入协作、治理和运行态三个入口，并完整跑通至少几条端到端链路。

## 2. 参考基线

### CrazyAgentsManage 侧

- [docs/codex-hermes-role-design.md](/home/flowmind/CrazyAgentsManage/docs/codex-hermes-role-design.md)
- [docs/roadmap/HermesAgent-FlowMind-联合产品功能基线-2026-04-30.md](/home/flowmind/CrazyAgentsManage/docs/roadmap/HermesAgent-FlowMind-联合产品功能基线-2026-04-30.md)
- [docs/06-agent-ops/operations-manual.md](/home/flowmind/CrazyAgentsManage/docs/06-agent-ops/operations-manual.md)

### FlowMindDeploy 侧

- [三台服务器环境部署总览](/home/flowmind/FlowMindDeploy/docs/04-deploy/三台服务器环境部署总览-2026-04-25.md)
- [第三阶段控制面角色裁定与切换回滚方案](/home/flowmind/FlowMindDeploy/docs/04-deploy/真实部署环境-第三阶段-控制面角色裁定与切换回滚方案-2026-04-26.md)
- [live 副本同步治理](/home/flowmind/FlowMindDeploy/docs/04-deploy/真实部署环境-live副本同步治理-2026-05-03.md)
- [Pilot scripts 入口](/home/flowmind/FlowMindDeploy/scripts/pilot/README.md)

## 3. 当前基线

| 对象 | 当前定位 | 关键事实 | 不负责 |
|---|---|---|---|
| `TX-NEWHOST (111.229.194.203)` | 当前正式主控制面 | 现在承载 `CrazyAgentsManage` 和 `FlowMind host-mode 3301` | 不是历史回滚锚点 |
| `CrazyAgentsManage` | operator control room / façade | 对外正式入口是 `/manage/` | 不做 canonical truth 裁定 |
| `HermesAgent runtime` | 运行时宿主 / 运营执行面 | 负责 session、trace、cron、gateway 等运行态 | 不替代 FlowMind truth |
| `Hermes-Webui` | Hermes 运行态观测面 | 属于当前主机上的运行面之一 | 不充当 Crazy 主入口 |
| `Graphify` | 只读图谱 / MCP 辅助面 | 通过 Hermes 配置加载并提供图谱查询能力 | 不写运营状态 |
| `cron` | 定时任务执行面 | 承载巡检、汇总、周边自动化 | 不定义产品 truth |
| `FlowMind host-mode 3301` | canonical truth / review / feedback 面 | 负责 truth、review、feedback、context 等基线能力 | 不充当 operator console |
| `TX-PRIMARY (49.232.158.82)` | 历史回滚锚点 | 已退役，只保留为回滚与历史事实 | 不承载当前主生产面 |
| `ALI-HERMES (47.99.217.1)` | 辅助 / 验证位 | 只用于验证、webhook 或辅助探针 | 不进入主链路 |

## 4. 执行门槛

这份方案按 4 个执行门槛推进，但落地时展开成 6 个验证阶段：

1. 版本真相对齐
2. 本地健康
3. 主机烟测
4. 端到端链路
5. 角色边界
6. 回滚 / 观测

任一门槛失败，都先修复当前层，不要跳过该层继续往下测。

## 5. 六阶段检查表

| 阶段 | 验证什么 | 通过标准 | 推荐命令 |
|---|---|---|---|
| 1. 事实对齐 | 文档、配置、角色矩阵、部署副本是否一致 | 默认值都指向 `111.229.194.203`，旧 IP 只出现在历史段落；两仓 live sync 报告均为 `PASS` | `cd /home/flowmind/FlowMindDeploy && pnpm governance:live-deploy-sync -- --profile flowmind-tx-newhost && pnpm governance:live-deploy-report`；`cd /home/flowmind/CrazyAgentsManage && python3 scripts/governance/check_live_deploy_sync.py --workspace-root . --profile crazy-webui-live --profile crazy-runtime-live --json` |
| 2. 本地健康 | 脚本语法、单测、静态检查 | `pytest` / 语法检查 / governance checks 无新增报错 | `cd /home/flowmind/CrazyAgentsManage && ./scripts/run-local-tests.sh`；`cd /home/flowmind/CrazyAgentsManage && ./scripts/check_harness_governance_all.sh`；`cd /home/flowmind/FlowMindDeploy && pnpm governance:architecture-drift && pnpm governance:phase6-acceptance` |
| 3. 主机烟测 | `TX-NEWHOST` 上各应用是否都活着 | `HermesAgent runtime`、`Hermes-Webui`、`Graphify`、`cron`、`FlowMind host-mode` 都可达 | `cd /home/flowmind/FlowMindDeploy && pnpm pilot:ops-health`；`systemctl status flowmind-newhost.service`；`curl -fsS http://127.0.0.1:3301/healthz`；`systemctl status cron`；`systemctl status hermes-webui`；`hermes config validate`；`grep -A 12 "graphify:" ~/.hermes/config.yaml`；`python3 -m graphify.serve /root/.hermes/chat-archive/CrazyAgentsManage/graphify-out/knowledge-base.json` |
| 4. 端到端链路 | `Crazy -> Hermes -> FlowMind` 是否闭环 | 能生成 handoff，能读 truth，能拉 feedback / context-pack | `cd /home/flowmind/FlowMindDeploy && pnpm pilot:smoke` |
| 5. 角色边界 | 应用是否只做自己该做的事 | Crazy 只做控制面；FlowMind 只做 truth；Hermes 只做运行态；Graphify 只读；退役/验证面不进主链路 | `curl -I http://127.0.0.1/manage/`；`curl -I http://127.0.0.1:5002/manage/`（应为 404）；`curl -fsS http://127.0.0.1:5002/`；`curl -fsS http://47.99.217.1:8644/health` |
| 6. 回滚 / 观测 | 出问题能不能定位和退回 | 有明确日志、指标、回滚步骤，且回退不破坏当前 truth | `cd /home/flowmind/FlowMindDeploy && pnpm pilot:rollback-readiness`；`curl http://49.232.158.82:3301/healthz`；`journalctl -u flowmind-newhost.service -n 200 --no-pager`；`tail -n 200 /root/.hermes/logs/cron.log`；`tail -n 200 /var/log/flowmind/ops-health.log` |

版本核对说明：

- 如果远端副本保留 `.git`，再额外记录一次 `git rev-parse HEAD` 作为二级证据。
- 如果远端是非 git worktree 副本，则以 sync report + sha256 为正式版本证据，不强行要求 HEAD 可读。

## 6. 角色验证要点

### CrazyAgentsManage

- 只负责 operator-facing control room 和 façade。
- 正式入口应是 `/manage/`，不是内网后端直连路径。
- 任何 truth / review / feedback 的最终裁定都不应在 Crazy 本地重写。

### FlowMind host-mode

- 只负责 canonical truth / review / feedback / context。
- 需要能被 `pilot:smoke` 读到，不需要承担 operator console 的职责。
- `truth.status` 继续是主状态唯一来源。

### HermesAgent runtime / Hermes-Webui / cron / Graphify

- HermesAgent runtime 负责运行态、任务和巡检。
- Hermes-Webui 负责运行态观测，不是 Crazy 的主入口。
- cron 负责调度与自动化，不是 truth authority。
- Graphify 只提供只读知识图谱能力，不写运营状态。

### TX-PRIMARY / ALI-HERMES

- `TX-PRIMARY` 只允许作为回滚锚点和历史事实。
- `ALI-HERMES` 只允许作为辅助 / 验证位。
- 这两个环境不应出现在主生产路径里。

## 7. 通过标准

满足以下条件时，认为当前架构部署环境通过本测试方案：

1. 两仓 live sync 报告都为 `PASS`。
2. 本地测试与治理检查都无新增失败。
3. `TX-NEWHOST` 上的主应用都处于可达状态。
4. `Crazy -> Hermes -> FlowMind` 的链路可以完整跑通。
5. 角色边界成立，公众入口和回滚锚点没有混淆。
6. 观测与回滚信息齐全，且回退不会污染 truth。

## 8. 失败时的回溯顺序

1. 先查事实对齐和版本同步。
2. 再查本地测试与治理检查。
3. 再查主机烟测和服务状态。
4. 再查端到端链路。
5. 再查角色边界。
6. 最后查回滚与观测链路。

## 9. 人工参与链路补充用例

> 下面这组用例专门用来验证“人参与交互”的能力。它们不追求全自动，而是要把人工决策点、协作面、治理面、运行态这几层真正走通。

| 用例 | 覆盖项目 | 人工参与点 | 执行链路 | 通过标准 |
|---|---|---|---|---|
| 9.1 协作 handoff 演练 | `CrazyAgentsManage` + `HermesAgent` + `FlowMindDeploy` | 在 Crazy 的 `Collaboration` 页面手工发起一个需要 review 的 handoff，并在 Hermes 侧确认接收 | 1) 打开 `/manage/` -> `Collaboration` 2) 选择一个 candidate / session / runtime issue 3) 生成 handoff packet 4) HermesAgent 侧人工确认并补足 runtime signal 5) 在 FlowMindDeploy review queue 中确认进入待审 | handoff、review queue、Crazy 摘要三处状态一致；Crazy 只展示，不直接改写 truth |
| 9.2 truth promotion 演练 | `FlowMindDeploy` + `CrazyAgentsManage` | 人工在 FlowMindDeploy 上对候选执行 `approve / reject / defer` | 1) 在 FlowMindDeploy review queue 中人工决策 2) 记录理由 3) 刷新 Crazy 的 `Governance` / `Collaboration` 页面 4) 核验状态投影 | FlowMindDeploy 的决策成为唯一 truth；Crazy 只同步展示，不出现本地覆盖 |
| 9.3 运行态异常介入 | `HermesAgent runtime` + `CrazyAgentsManage` | 人工在 Runtime 页面确认异常并选择恢复动作 | 1) 在 Crazy `Runtime` 页面挑一个异常 session / trace 2) 到 Hermes runtime 或服务状态页确认来源 3) 在可回滚窗口执行恢复 / 重启 / 补救 4) 回到 Crazy 看告警是否消退 | 异常可定位到具体 session / service / tool；恢复后仍能追踪到闭环证据 |
| 9.4 反馈回流闭环 | `CrazyAgentsManage` + `FlowMindDeploy` | 人工在 Crazy 侧提交 feedback / note，再由 FlowMind 侧接收并回写 | 1) 在 Crazy `Governance` / `Collaboration` 页面提交反馈 2) 在 FlowMindDeploy 侧确认 review / feedback 记录 3) 回到 Crazy 观察最新摘要 4) 检查是否进入后续跟踪 | feedback 在两侧都可追踪；状态变化有证据，不依赖口头约定 |

建议的实际演练顺序：

1. 先跑 `9.1`，确认协作 handoff 能发出去。
2. 再跑 `9.2`，确认治理层的真值裁定能回流。
3. 然后跑 `9.4`，确认反馈能回到协作面形成后续动作。
4. 最后在维护窗口跑 `9.3`，确认异常恢复链路和回滚观察都成立。
