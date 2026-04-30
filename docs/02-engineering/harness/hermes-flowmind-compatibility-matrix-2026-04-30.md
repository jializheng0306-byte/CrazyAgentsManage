# HermesAgent × FlowMind Compatibility Matrix

> 日期: 2026-04-30  
> 状态: initial-baseline  
> 仓库视角: `CrazyAgentsManage`

---

## 1. 当前矩阵

| 维度 | CrazyAgentsManage | FlowMindDeploy | 状态 | 说明 |
|---|---|---|---|---|
| 运营主线 | `PR #11` / 当前运营体系落地 | `main@f9dda9a` | `compatible_with_conditions` | 主方向成立，但 capture 脚本仍需按现网契约修正 |
| Candidate ingress | `scripts/flowmind_capture.py` | `POST /api/integrations/candidate-ingress` | `incompatible_until_p0_fix` | 现脚本 baseURL / body 仍有已知偏差 |
| Truth / Review read | HUD / 运营表面待读取 | `review-queue` / `bridge/truth` | `compatible` | 当前只读边界清晰 |
| Feedback / Context Pack | 上游未形成系统消费逻辑 | `bridge/feedback*` + `context-pack` | `partial` | FlowMind 已提供，但 Crazy 侧未完全吸收 |
| Health / Ops | Hermes 巡检任务 | `ops-health` / `healthz` | `compatible` | 当前最成熟的一条联动链 |
| Webhook route | Hermes webhook runtime | FlowMind ingress / evidence | `partial` | 可以联动，但需要纳入 manifest 与 handshake smoke |

---

## 2. 当前条件项

1. `flowmind_capture.py` 仍未对齐 current direct-path ingress contract
2. `decision -> Bitable/Tech Radar` 状态回写未完成
3. webhook 还是运行时触发通道，尚未纳入正式双仓兼容校验
4. HUD 当前仍是“设计 + webui + 外部 collector 参考实现”的组合，不是单一产品模块

---

## 3. 升级到 `handshake-passed` 的条件

1. `flowmind_capture.py` 修复并完成一次端到端冒烟
2. 运行一次正式 handshake smoke：
   - candidate ingress
   - review queue
   - decision
   - truth
   - feedback/context-pack
3. webhook 路由纳入 manifest 并通过一次联动验证
4. 双边 manifest / compatibility matrix 同步更新

---

## 4. 一句话结论

> 当前 CrazyAgentsManage 与 FlowMindDeploy 已经有可工作的连接，但还没有达到“无需人工额外解释就能稳定演进”的兼容状态；要进入正式协同，必须先通过一轮显式 handshake。
