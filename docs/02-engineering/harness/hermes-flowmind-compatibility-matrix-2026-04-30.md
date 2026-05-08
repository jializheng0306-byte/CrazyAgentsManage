# HermesAgent × FlowMind Compatibility Matrix

> 日期: 2026-05-08（更新自 2026-04-30 initial-baseline）  
> 状态: updated-post-mirror-sync  
> 仓库视角: `CrazyAgentsManage`  
> 触发更新: 真实 handoff generator round + PR #17 mirror sync landed + feedback/context-pack 消费判面纠偏

---

## 1. 当前矩阵

| 维度 | CrazyAgentsManage | FlowMindDeploy | 状态 | 说明 |
|---|---|---|---|---|
| 运营主线 | `feat/auto-capture-trace@3c5815d` | `main@f9dda9a` | `compatible_with_conditions` | 主方向成立；capture 管道仍有条件项（见 §2） |
| Candidate ingress | `scripts/flowmind_capture.py` | `POST /api/integrations/candidate-ingress` | `partially_compatible` | 接口可达（2026-05-03 冒烟 201 created），但 capture 脚本的 baseURL/body 对齐未在真实 Bitable→FlowMind 链路上闭合验证 |
| Truth / Review read | `scripts/runtime/generate_hermes_handoff.py` + HUD/webui | `review-queue` + `bridge/truth` | `compatible` ✅ | **已真实跑通**：2026-05-03 通过 `bridge/truth` 成功读取 `semanticContext` + `latestEvidence`，直接注入 Hermes handoff packet |
| Hermes handoff packet | `scripts/runtime/generate_hermes_handoff.py` | `bridge/truth` | `compatible` ✅ | **真实 round 已验证**：packet 包含 semantic refs、field mappings、consumer hints、latestEvidence，HermesAgent 无需人工补充即可完成运营 review |
| Action-family interpretation | Crazy PRD/roadmap/semantic-first 入口 | `治理动作分层口径-v1-2026-05-07.md` | `compatible` ✅ | **已镜像到 Crazy 入口层**：现在明确区分 `review decision actions / truth promotion actions / operational feedback events`，不再把三类动作混写成同一种状态推进 |
| Execution packet field layering | Crazy PRD/roadmap/semantic-first 入口 | `执行包字段对照与消费顺序-v1-2026-05-07.md` | `compatible` ✅ | **已镜像到 Crazy 入口层**：现在明确区分 `moduleDetails.handoff / semanticContext / latestEvidence / executionBoundary / handoffContract` 五层职责 |
| Governance evidence reading order | Crazy PRD/roadmap/semantic-first 入口 | `治理证据资产索引-v1-2026-05-07.md` | `compatible` ✅ | **已镜像到入口层**：Crazy 侧已承认 `change record -> deploy fact -> acceptance/eval -> closeout seed -> governance report` 的 shared 读取顺序；更深对等 shared 入口仍可后续增强 |
| Handshake smoke | `docs/02-engineering/harness/handshake-smoke-status-2026-05-03.md` | (全覆盖) | `partial_pass_with_evidence` | 仓库证据已补；当前 5/8 通过、3/8 仅接口可达，尚未形成全链路 `handshake-passed` |
| Feedback | **脚本级部分消费** | `bridge/feedback/:instanceId` | `partially_consumed` | `scripts/daily-promise-review.py` 已读取、归一化并把 feedback 投影到承诺审查主表/Trace 子表；但还没有统一页面/产品化消费面。`GET /bridge/feedback/:instanceId` 当前代码口径允许 `ui_bearer` 或 `x-instance-token` |
| Context Pack | **仅 probe 调用** | `bridge/context-pack` | `probe_only` | 当前只在 `scripts/flowmind_handshake_smoke.py` 中做 handshake 级探测；没有 durable 主线消费入口，`POST /bridge/context-pack` 仍要求 `x-instance-token`。**下一优先补强 lane 已冻结为 Crazy `/api/runtime/handoffs` 的 page-facing `contextSummary`，而不是直连 `context-pack` 或先开新 instance surface。** |
| Health / Ops | Hermes 巡检任务 | `healthz` | `compatible` ✅ | 当前最成熟的一条联动链 |
| Webhook route | Hermes webhook runtime | FlowMind ingress / evidence | `partial` | 可以联动，但需要纳入 manifest 与 handshake smoke |

---

## 2. 当前条件项

1. **`flowmind_capture.py` direct-path 对齐未闭合验证**  
   - 接口层面：candidate-ingress endpoint 可达（2026-05-03 冒烟 201 ✓）  
   - 脚本层面：`send_to_flowmind()` 使用 `POST /api/integrations/candidate-ingress`，路径正确  
   - 仍缺失：Bitable 真实"已确认"记录 → FlowMind candidate 的端到端闭合验证

2. **`decision → Bitable/Tech Radar` 状态回写未完成**  
   - 兼容矩阵条件项原 #2，状态无变化

3. **webhook 还是运行时触发通道，尚未纳入正式双仓兼容校验**  
   - 兼容矩阵条件项原 #3，状态无变化

4. **HUD 当前仍是"设计 + webui + 外部 collector 参考实现"的组合，不是单一产品模块**  
   - 兼容矩阵条件项原 #4，状态无变化

5. **feedback/context-pack 判面已分叉，旧口径需要拆开维护**
   - `feedback` 已有脚本级消费与运营字段投影，但还缺统一页面/产品化消费面与持续运行证据
   - `context-pack` 目前仍停留在 handshake/probe 调用，尚无 durable 主线消费入口
   - `feedback-context-consumption-status-2026-05-03.md` 与 link manifest 已按本轮结论纠偏，后续不能再把两者并列写成“都只是 endpoint_only”
   - `context-pack` 的下一优先补强顺序也已冻结：先补 Crazy `runtime/handoffs` 的 page-facing `contextSummary`，再决定是否收紧上游 gate，当前不立项 instance-level context surface

6. **shared 治理证据资产目前只是入口层镜像，不是 Crazy 的对等 shared 证据系统**  
   - 这不阻塞当前 mirror / sync gate 基线
   - 但后续若 Crazy 侧需要自己的 governance-report 汇总面，应单独扩设计

---

## 3. 升级到 `handshake-passed` 的条件

1. `flowmind_capture.py` 完成一次 Bitable"已确认"记录 → FlowMind candidate 的端到端闭合验证
2. 运行一次正式 handshake smoke（本轮已验证各端点可达，见 handshake-smoke-status）：
   - ✅ candidate ingress — 接口可达
   - ✅ review queue — 接口可达
   - ⚠️ decision — 接口可达但未在真实 review 轮次中触发
   - ✅ truth — 已通过 handoff generator 真实消费
   - ⚠️ feedback — 已有脚本级消费，但仍缺统一产品化入口与持续运行证据
   - ⚠️ context-pack — 当前仅 probe 调用，仍缺 durable 主线消费入口
3. webhook 路由纳入 manifest 并通过一次联动验证
4. 双边 manifest / compatibility matrix 同步更新
5. **context-pack 形成至少一条 durable 可运行消费入口（P2），且默认优先路径是 Crazy `runtime/handoffs` page-facing `contextSummary`，feedback 则补齐契约/运行证据面**

---

## 4. 一句话结论

> 2026-05-08 更新：**Truth read + handoff packet 链已真实跑通，且第一轮 mirror sync 已合并到 Crazy 主开发线。** Crazy 入口层现在已经承认动作分层、执行包字段分层与 shared 证据读取顺序；`feedback` 已进入脚本级消费，`context-pack` 仍缺 durable 主线消费入口，但下一优先补强 lane 已冻结为 `runtime/handoffs` 的 page-facing `contextSummary`，capture 管道端到端闭合验证也仍待补齐。
