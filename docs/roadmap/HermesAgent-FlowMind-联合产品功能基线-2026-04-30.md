# HermesAgent × FlowMind 联合产品功能基线

> 日期: 2026-04-30  
> 状态: proposed-active-baseline  
> 角色: `CrazyAgentsManage` 侧对联合产品主线的镜像规划入口

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

- `flowmind_capture.py`
- instance registration
- payload/auth/baseURL 契约
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

1. 修 `flowmind_capture.py`
2. 做第一轮 handshake smoke
3. 把 webhook 也纳入 manifest 与 compatibility matrix

### Phase 2 — 运营数据底座

Crazy 侧直接动作：

1. 吸收 `hermes-hud` 的 session collector
2. 建立 Bitable/HUD 数据底座
3. 让反思、情报、运营日报有真实数据输入

### Phase 3 — 治理闭环回写

Crazy 侧直接动作：

1. `decision -> Bitable/Tech Radar` 状态回写
2. feedback/context-pack 消费
3. 双重人工确认入口固定

### Phase 4 — Operator Console 收敛

Crazy 侧直接动作：

1. 五大一级 IA 分区收敛为真实聚合页
2. HUD 只读优先、动作受控
3. 架构页与真实状态互跳

### Phase 5 — 安全自动化升级

Crazy 侧直接动作：

1. 决定 capture 的人工闸门策略
2. 将 `three_state_protocol.py` 与 `task_watcher.py` 推进为默认控制协议
3. 让 webhook 成为正式触发通道，而不是隐式边界

---

## 六、一句话结论

> 从现在开始，CrazyAgentsManage 的活跃产品主线不再是旧的 `v0.1.0 ~ v0.5.0` 顺序，而是“作为 Hermes 侧运营编排系统，与 FlowMind 治理真值层共同演进”的联合产品路线。
