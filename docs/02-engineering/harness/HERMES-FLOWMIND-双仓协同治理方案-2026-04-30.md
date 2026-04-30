# HermesAgent × FlowMind 双仓协同治理方案

> 日期: 2026-04-30  
> 状态: proposed-baseline  
> 仓库视角: `CrazyAgentsManage` 侧镜像治理包

---

## 一、为什么 CrazyAgentsManage 需要这份文档

`CrazyAgentsManage` 与 `FlowMindDeploy` 已经不是一个仓库内的模块关系，而是：

1. 两个独立仓库
2. 两组不同主线
3. 两套不同宿主平台
4. 两类不同产品职责

如果没有显式治理机制，这两个系统之间会持续出现 4 类偏差：

- 功能边界漂移
- 接口契约漂移
- 部署入口漂移
- 发布节奏漂移

所以本仓不再把 FlowMind 看成“某个脚本调用的外部服务”，而要把它看成：

- 一个需要共同版本治理的**下游真值系统**

---

## 二、系统分工

### CrazyAgentsManage / HermesAgent

角色：

- 运营编排层
- 情报采集
- Bitable / Tech Radar / shared-context
- cron / task watcher / 三态通信协议
- operator HUD / WebUI

### FlowMindDeploy

角色：

- 治理真值层
- candidate ingress
- review queue
- truth
- sessions
- feedback / context-pack

### 核心分工原则

- `CrazyAgentsManage` 负责“发现、筛选、编排、运营”
- `FlowMindDeploy` 负责“治理、审查、固化 truth”
- `CrazyAgentsManage` 不能演化出第二套 truth

---

## 三、共同治理包（Cross-Repo Governance Pack）

以后双仓共同管理，统一依赖 4 个工件：

1. **双仓协同治理方案**
2. **兼容矩阵**
3. **机器可读 link manifest**
4. **双仓 handshake smoke**

这意味着：

- 单仓里某个脚本改了，不等于双仓机制就仍然有效
- 只有治理包同步更新后，才算完成跨仓变更

---

## 四、CrazyAgentsManage 视角下的连接方式

### 4.1 主数据流

```text
情报 / 运营事件
  -> Tech Radar / Bitable / shared-context
  -> 人工确认或策略确认
  -> FlowMind candidate ingress
  -> review / truth / sessions
  -> feedback / context-pack
  -> CrazyAgentsManage 更新运营状态
```

### 4.2 标准接口边界

CrazyAgentsManage 不允许绕过以下标准边界直接“猜测”对接：

| 对象 | 接口 |
|---|---|
| Candidate ingress | `POST /api/integrations/candidate-ingress` |
| Review queue | `GET /api/integrations/review-queue` |
| Review decision | `POST /api/integrations/candidates/:id/confirm|reject|clarify` |
| Truth read | `GET /api/bridge/truth` |
| Feedback record/pull | `POST /api/bridge/feedback` / `GET /api/bridge/feedback/:instanceId` |
| Context pack | `POST /api/bridge/context-pack` |
| Health | `ops-health` / `healthz` / `readyz` |

---

## 五、共同管理方式

### 5.1 Source of Truth

| 维度 | 事实源 |
|---|---|
| 运营计划 / 情报 / Bitable / HUD | `CrazyAgentsManage` |
| candidate / review / truth / sessions | `FlowMindDeploy` |
| 双仓契约 | Governance Pack |
| 宿主拓扑 | Governance Pack |
| 发布兼容性 | Compatibility Matrix |

### 5.2 何时必须触发双仓治理动作

只要出现以下任一变更，就必须更新治理包：

1. capture payload 变化
2. sourceAgent / instanceId 语义变化
3. feedback/context-pack 结构变化
4. auth 方式变化
5. webhook route 语义变化
6. baseURL / 宿主拓扑变化
7. HUD 直接读写 FlowMind 的入口变化

### 5.3 双仓发布状态

统一使用 4 个状态：

- `single-repo-ready`
- `awaiting-handshake`
- `handshake-passed`
- `released-with-conditions`

任何一边都不允许只因为“本仓完成了”就宣称双仓链路已经稳定。

---

## 六、与现有 webhook 机制的关系

### 6.1 基本判断

**可以联动，但角色不同。**

- 双仓协同治理机制 = **控制层 / 治理层**
- webhook 机制 = **运行时触发层**

它们不是替代关系，而是：

- webhook 受治理包约束
- 治理包不依赖 webhook 才存在

### 6.2 当前 webhook 应该扮演的角色

webhook 更适合做：

1. GitHub PR / 外部事件进入 Hermes
2. Hermes 根据路由规则做编排
3. 如有必要再把结构化结果送进 FlowMind

webhook 不适合直接承担：

1. 双仓兼容性判断
2. 版本基线判断
3. 发布是否通过的最终裁定

### 6.3 推荐联动方式

建议把 webhook 纳入治理包的方式是：

1. **在 manifest 中登记**
   - route_id
   - source system
   - deliver mode
   - executor path
2. **在 compatibility matrix 中标记**
   - 当前 webhook 路由是否仍兼容 FlowMind 当前 contract
3. **在 handshake smoke 中验证**
   - 触发 1 次 webhook
   - 看是否能稳定形成 candidate / feedback / evidence

换句话说：

- webhook 是连接管道
- governance pack 是管道规则

---

## 七、CrazyAgentsManage 当前最小落地要求

### M1

保留本镜像治理文档

### M2

保留兼容矩阵镜像

### M3

保留 link manifest 镜像

### M4

后续修改以下内容时，必须同步检查 `FlowMindDeploy` 侧：

- `scripts/flowmind_capture.py`
- `bitable_sync.py`
- 与 FlowMind 相关的 cron/job
- HUD 中的 FlowMind 状态面板

### M5

在本仓的 handoff / closeout / runtime state 文档里，后续涉及 FlowMind 的部分，都必须附上：

- 对应 FlowMind baseline
- 对应 compatibility 状态

---

## 八、下一步

1. 对齐 `flowmind_capture.py` 与当前 FlowMind direct-path ingress 契约
2. 把 `hermes-hud` 的 session / corrections / patterns collector 语义吸收到 CrazyAgentsManage
3. 建立 `FlowMind decision -> Bitable/Tech Radar` 状态回写
4. 把 webhook 路由正式纳入 manifest 和 handshake smoke

---

## 九、一句话结论

> CrazyAgentsManage 与 FlowMindDeploy 现在必须按“双仓协同治理”来管理：CrazyAgentsManage 负责运营编排，FlowMindDeploy 负责治理真值，而 webhook 只是运行时触发通道，必须被兼容矩阵、manifest 和发布握手机制约束，不能再作为隐式连接边界。
