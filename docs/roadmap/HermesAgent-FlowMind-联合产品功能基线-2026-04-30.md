# HermesAgent × FlowMind 联合产品功能基线

> 日期: 2026-04-30  
> 状态: mirrored-active-baseline  
> 角色: `CrazyAgentsManage` 侧对联合产品主线的镜像规划入口  
> canonical source:
> - `FlowMindDeploy/docs/01-product/HermesAgent-FlowMind-交互框架设计-2026-04-29.md`
> - `FlowMindDeploy/docs/01-product/HermesAgent-FlowMind-产品功能基线与迭代路线图-2026-04-30.md`

---

## 一、为什么需要这份文档

`CrazyAgentsManage` 现在不再只是独立演进的 Hermes 产品壳。

它已经和 `FlowMindDeploy` 形成一个双系统产品：

- `CrazyAgentsManage` 负责运营编排、情报、Bitable、shared-context、HUD、operator workflows
- `FlowMindDeploy` 负责 candidate、review、truth、sessions、feedback、context-pack、部署基线

因此旧的：

- `v0.1.0 ~ v0.5.0` 版本阶梯
- “从零开始搭多智能体平台”的路线图叙事

都不再适合作为当前活跃主线。

---

## 二、当前统一产品基线

当前联合产品应固定为：

**Hermes-hosted FlowMind Operating System**

在 Crazy 侧，这意味着：

- 我们不是单独做一个“更强的 Hermes WebUI”
- 我们是在建设：
  - Hermes 上游运营编排系统
  - 与 FlowMind 下游治理真值系统联动的 operator product

---

## 三、Crazy 侧当前最重要的 4 个方向

### 1. Link Hardening

修好和 FlowMind 的连接：

- `flowmind_capture.py + flowmind_handshake_smoke.py`
- instance registration
- payload/auth 契约
- `control_plane_url / public_url` 双地址配置
- handshake smoke

### 2. Ops Data Plane

把 Hermes 的真实运行态变成运营数据：

- session
- tool call
- token
- estimated cost
- corrections
- patterns
- cron / health

### 3. Governance Roundtrip

让 FlowMind 的治理结果回写 Crazy 的运营状态：

- Bitable
- Tech Radar
- operator task state
- `feedback / truth / context` 分通道消费

### 4. Operator Console Convergence

让 HUD/WebUI 变成统一 operator console，而不是页面堆积。

---

## 四、对旧路线图的重新解释

`docs/roadmap/roadmap.md` 当前更适合作为：

- 历史能力清单
- 已规划模块来源
- backlog catalog

而不是：

- 当前活跃实施顺序

也就是说：

- `v0.1.0 ~ v0.5.0` 依然有参考价值
- 但不再是接下来迭代时的优先执行次序

---

## 五、当前活跃阶段

### Phase 1 — 双仓连接加固

Crazy 侧直接动作：

1. 固定 `flowmind_capture.py + flowmind_handshake_smoke.py` 为当前唯一受支持 ingress 验证对
2. 补齐 `control_plane_url / public_url` 双地址配置
3. 做第一轮 handshake smoke
4. 把 webhook 也纳入 manifest 与 compatibility matrix

### Phase 2 — 轻量本体与数据语义

Crazy 侧直接动作：

1. 对齐联合产品的 ontology / data-semantic 基线
2. 让 Bitable / webhook / 文档输入具备结构化语义草案
3. 保持 ontology 与 truth 的职责分离

### Phase 3 — 反向通道与分层上下文

Crazy 侧直接动作：

1. 对齐 4 条通道：
   - `Push-Candidate`
   - `Pull-Feedback`
   - `Pull-Truth`
   - `Pull-Context`
2. 明确 `approved + committed` 都属于当前可读 truth
3. 让 `feedback` 更新运营状态，`truth/context` 更新运行时决策与长期记忆

### Phase 4 — 运营数据底座

Crazy 侧直接动作：

1. 吸收 `hermes-hud` 的 session collector
2. 建立 Bitable/HUD 数据底座
3. 让反思、情报、运营日报有真实数据输入

### Phase 5 — 治理闭环回写

Crazy 侧直接动作：

1. `candidate approved / committed / rejected` 后按规则回写 Bitable / Tech Radar
2. 固定 `feedback pull -> Bitable / operator task state` 最小规则
3. 双重人工确认入口固定

### Phase 6 — Operator Console 与外部执行平面升级

Crazy 侧直接动作：

1. 五大一级 IA 分区收敛为真实聚合页
2. HUD 只读优先、动作受控
3. 架构页与真实状态互跳
4. 将 `three_state_protocol.py` 与 `task_watcher.py` 推进为默认控制协议
5. 给 Codex 外部执行平面补：
   - `task registry`
   - `handoff packet`
   - `runtime heartbeat`
6. 让 webhook 成为正式触发通道，而不是隐式边界

Phase 6 当前默认口径还必须与 FlowMind canonical docs 保持一致：

- `FlowMindDeploy/docs/01-product/Operator-Console-最小职责边界-2026-05-04.md`
- `FlowMindDeploy/docs/01-product/handoff-packet-contract-v1-2026-05-04.md`
- `FlowMindDeploy/docs/01-product/Phase6-默认SOP与提示词同步-2026-05-04.md`
- `FlowMindDeploy/docs/01-product/外部执行面-读写边界-v1-2026-05-04.md`
- `FlowMindDeploy/docs/01-product/治理动作分层口径-v1-2026-05-07.md`
- `FlowMindDeploy/docs/01-product/执行包字段对照与消费顺序-v1-2026-05-07.md`
- `FlowMindDeploy/docs/05-version-control/治理证据资产索引-v1-2026-05-07.md`
- `FlowMindDeploy/docs/01-product/运营Follow-Up最小默认解释-v0-2026-05-14.md`
- `FlowMindDeploy/docs/01-product/Slice1-read-model-projection-任务分解-v0-2026-05-14.md`
- `FlowMindDeploy/docs/01-product/Slice1-read-model-projection-验收证据骨架-v0-2026-05-14.md`

Crazy 侧不得自行改写以下默认规则：

- `truth.status` 是主状态唯一来源
- `feedback.eventType` 只进入运营动作层
- `timeline` 默认消费 `traceEvents[]`
- `handoff` 默认消费 `moduleDetails.handoff + semanticContext + latestEvidence`
- `confirm / reject / clarify` 属于 review decision actions，而不是运营反馈
- `approve / commit` 属于 truth promotion actions，而不是 review decision 或本地 done 投影
- `moduleDetails.handoff / semanticContext / latestEvidence / executionBoundary / handoffContract` 应按执行包五层解释
- 双仓 closeout / governance 结论应参考 `FlowMindDeploy/docs/05-version-control/治理证据资产索引-v1-2026-05-07.md`
- `operational follow-up` 默认消费同一 Slice 1 projection，不在 Crazy / Hermes 侧本地改写 `needsFollowUp / followUpKind / nextActor`

当前 cross-repo mirror 补记：

1. `operational follow-up` 已同步到 Crazy mirror 与 Hermes 协同入口
2. Crazy 页面、handoff 摘要与 Hermes prompt context 默认直接消费同一 projection
3. 若后续要继续扩 `nextActor` 或 follow-up kind，必须先改 FlowMind canonical docs，再跑 mirror / sync check

---

## 六、镜像同步规则

这份文档不是第二套母本。

只要 `FlowMindDeploy` 中以下 canonical docs 变化：

- `docs/01-product/HermesAgent-FlowMind-交互框架设计-2026-04-29.md`
- `docs/01-product/HermesAgent-FlowMind-产品功能基线与迭代路线图-2026-04-30.md`

就必须同步更新：

1. 本文档
2. `docs/prd/README.md`
3. `docs/roadmap/prd-execution-roadmap.md`
4. `docs/02-engineering/harness/SEMANTIC-FIRST-READING-RULE.md`

检查命令：

```bash
scripts/check_cross_repo_prd_sync.sh
```

---

## 七、一句话结论

> 从现在开始，CrazyAgentsManage 的活跃产品主线不再是旧的 `v0.1.0 ~ v0.5.0` 顺序，而是“作为 Hermes 侧运营编排系统，与 FlowMind 治理真值层共同演进”的联合产品路线。
