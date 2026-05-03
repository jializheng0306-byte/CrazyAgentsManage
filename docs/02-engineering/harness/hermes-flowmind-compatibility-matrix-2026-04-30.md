# HermesAgent × FlowMind Compatibility Matrix

> 日期: 2026-05-03（更新自 2026-04-30 initial-baseline）  
> 状态: updated-post-real-round  
> 仓库视角: `CrazyAgentsManage`  
> 触发更新: 真实 handoff generator round (candidate `219a5914`, instance `hermes-agent`)

---

## 1. 当前矩阵

| 维度 | CrazyAgentsManage | FlowMindDeploy | 状态 | 说明 |
|---|---|---|---|---|
| 运营主线 | `feat/auto-capture-trace@3c5815d` | `main@f9dda9a` | `compatible_with_conditions` | 主方向成立；capture 管道仍有条件项（见 §2） |
| Candidate ingress | `scripts/flowmind_capture.py` | `POST /api/integrations/candidate-ingress` | `partially_compatible` | 接口可达（2026-05-03 冒烟 201 created），但 capture 脚本的 baseURL/body 对齐未在真实 Bitable→FlowMind 链路上闭合验证 |
| Truth / Review read | `scripts/runtime/generate_hermes_handoff.py` + HUD/webui | `review-queue` + `bridge/truth` | `compatible` ✅ | **已真实跑通**：2026-05-03 通过 `bridge/truth` 成功读取 `semanticContext` + `latestEvidence`，直接注入 Hermes handoff packet |
| Hermes handoff packet | `scripts/runtime/generate_hermes_handoff.py` | `bridge/truth` | `compatible` ✅ | **真实 round 已验证**：packet 包含 semantic refs、field mappings、consumer hints、latestEvidence，HermesAgent 无需人工补充即可完成运营 review |
| Handshake smoke | (待固化到仓库) | (全覆盖) | `pending_evidence` | 各端点接口可达已验证，但缺少仓库内固化记录（见 §2 条件项 #5） |
| Feedback | **未消费** | `bridge/feedback/:instanceId` | `endpoint_only` | FlowMind 端点存在（HTTP 401 → endpoint 可达，需 x-instance-token），Crazy 侧无消费入口 |
| Context Pack | **未消费** | `bridge/context-pack` | `endpoint_only` | FlowMind 端点存在（HTTP 401 → endpoint 可达，需 x-instance-token），Crazy 侧无消费入口 |
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

5. **handshake smoke 记录未固化到仓库**  
   - 各端点接口可达已在本轮验证，但未输出仓库内 `handshake-smoke-status-*.md`
   - 本轮补收口会输出该记录

6. **feedback/context-pack 消费证据仍不足**  
   - 两个端点均存在且可达（HTTP 401 证明端点存活），但 Crazy 侧无消费脚本/流程
   - 本轮补收口会输出 `feedback-context-consumption-status-*.md`

---

## 3. 升级到 `handshake-passed` 的条件

1. `flowmind_capture.py` 完成一次 Bitable"已确认"记录 → FlowMind candidate 的端到端闭合验证
2. 运行一次正式 handshake smoke（本轮已验证各端点可达，见 handshake-smoke-status）：
   - ✅ candidate ingress — 接口可达
   - ✅ review queue — 接口可达
   - ⚠️ decision — 接口可达但未在真实 review 轮次中触发
   - ✅ truth — 已通过 handoff generator 真实消费
   - ⚠️ feedback — 接口可达，但 Crazy 侧未消费
   - ⚠️ context-pack — 接口可达，但 Crazy 侧未消费
3. webhook 路由纳入 manifest 并通过一次联动验证
4. 双边 manifest / compatibility matrix 同步更新
5. **feedback/context-pack 至少一侧形成可运行的消费入口（P2）**

---

## 4. 一句话结论

> 2026-05-03 更新：**Truth read + handoff packet 链已真实跑通**，`semanticContext` + `latestEvidence` 可自动注入 Hermes review。Capture 管道接口层可达，但端到端闭合验证仍缺；feedback/context-pack 仍停留在"端点存在但无人消费"状态。
