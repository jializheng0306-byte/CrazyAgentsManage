# FlowMind -> Crazy -> Hermes -> Executor 职责边界摘要

> 日期: 2026-05-18  
> 作用: 用中文把当前版本关于 `FlowMind / CrazyAgentsManage / HermesAgent / executor` 的职责边界收敛成一页摘要，供总控、评审方、实现方快速对齐。  
> 上游阅读基线:
> - `README.md`
> - `docs/design/executor-integration/README.md`
> - `docs/design/executor-integration/crazy-hermes-flowmind-executor-embedding-analysis.md`
> - `docs/design/executor-integration/decision-summary.md`
> - `docs/design/executor-integration/operations-integration-plan.md`

## 1. 一句话结论

当前版本的合理关系是：

> **FlowMind 管治理真值，Hermes 管运行时真值，Crazy 管 operator-facing 产品壳，executor 管外部能力平面。**

这四者是上下游协作关系，不是四个同层平台。

---

## 2. 四者各自回答什么问题

### 2.1 FlowMind

FlowMind 是：

- 治理引擎
- canonical truth 层
- candidate / review / truth / provenance 的持有者

FlowMind 回答的问题：

- 哪些内容还只是 candidate
- 哪些内容已经成为 truth
- 哪些对象需要 review
- 哪些对象出现 blocked / drift

一句话：

> **FlowMind 负责 governance truth。**

### 2.2 HermesAgent

HermesAgent 是：

- runtime host
- session / trace / token / tool 调用现场的持有者
- 任务执行与协作分发入口

Hermes 回答的问题：

- 当前任务是否在运行
- 哪些任务卡住了
- 哪些工具被调用了
- 当前运行代价和状态如何

一句话：

> **HermesAgent 负责 runtime truth。**

### 2.3 CrazyAgentsManage

CrazyAgentsManage 是：

- operator-facing product shell
- Hermes 运行态、FlowMind 治理闭环、外部 capability plane 的统一产品表面
- 一级 IA 的拥有者：
  - Overview
  - Runtime
  - Operations
  - Governance
  - Collaboration

Crazy 回答的问题：

- operator 看到什么
- operator 在哪里操作
- 哪些对象是运营对象
- 哪些治理/协作结果需要沉淀成产品表面

一句话：

> **Crazy 负责 product shell / operator façade。**

### 2.4 executor

executor 是：

- AI execution + integration platform
- source / tool / secret / plugin / execution 的能力底座

executor 回答的问题：

- 外部 source 怎么接入
- tool catalog 怎么生成
- secrets / connection / binding 怎么管理
- 受控代码执行怎么跑

一句话：

> **executor 负责 capability substrate，而不是 Crazy 的主产品模型。**

---

## 3. 当前版本的正确嵌入方式

当前版本不应把 executor 当成 Crazy 的产品底座，而应采用：

> **Adopt capabilities, not identity**

也就是：

- Crazy 保持产品壳
- Hermes 保持 runtime host
- FlowMind 保持治理真值层
- executor 下沉为 `Operations / Integrations capability plane`

当前最合理的接入面：

- Sources
- Tool Catalog
- Credential Health
- Provider Health
- 未来可选的 external execution

---

## 4. 哪些边界不能越过

### executor 不应接管

- Crazy 的一级 IA
- Hermes 的 session / trace / token telemetry
- FlowMind 的 candidate / truth / review / provenance
- Crazy / Hermes 的 handoff / closeout / repo writeback 事实层

### Crazy 不应重造

- source substrate
- tool registry substrate
- secret / provider substrate
- plugin substrate

### Hermes 不应替代

- FlowMind 的治理判断
- executor 的外部能力底座

### FlowMind 不应直接承担

- executor 的外部能力执行
- Crazy 的 operator-facing UI 编排

---

## 5. 当前推荐的数据流

### 场景 A：Operations / Integrations 控制台

```text
Crazy UI
  -> Crazy Operations façade API
    -> executor capability API
```

职责：

- Crazy：渲染 operator-facing 语言与工作台
- executor：提供 source / tool / credential / provider 数据

### 场景 B：Hermes 发起外部能力编排

```text
Hermes runtime task
  -> executor execution / tool capability
    -> 外部系统结果
      -> FlowMind candidate / evidence
```

职责：

- Hermes：任务生命周期与 runtime trace
- executor：拿能力、跑受控执行
- FlowMind：判断这些结果是否构成 truth

### 场景 C：协作与 closeout

```text
Crazy / Hermes closeout
  -> 可选 external action 交给 executor 执行
  -> repo writeback / handoff / closeout truth 仍保留在 Crazy / Hermes / 仓库工件
```

---

## 6. 当前最稳的实施顺序

1. 先完成 Crazy 的统一 shell 与一级 IA 稳定化
2. 再把 executor 接入 `Operations`
3. 先接：
   - source onboarding
   - tool catalog
   - credential / provider health
4. 暂不把 execution engine 提到主产品面
5. 后续再让 Hermes 在需要时委派 executor 做外部能力编排
6. 最终再把 executor 结果以 evidence/candidate 方式回流 FlowMind

---

## 7. 当前版本的推荐判断

### 合理的判断

- `executor` 作为 capability plane 接入：`是`
- `Crazy` 继续作为 operator-facing façade：`是`
- `Hermes` 继续作为 runtime host：`是`
- `FlowMind` 继续作为治理真值层：`是`

### 不合理的判断

- 把 executor 直接当 Crazy 的产品底座：`否`
- 让 executor 接管 Hermes runtime truth：`否`
- 让 executor 接管 FlowMind governance truth：`否`
- 让 Crazy 自己重做 source/tool/secret substrate：`否`

---

## 8. 评审时重点盯的 3 个风险

1. **Execution Delegation 漂移**
   Hermes 未来若委派 executor 跑外部能力，必须保持 Hermes 持有任务生命周期与 trace。

2. **Evidence 回流漂移**
   executor 可以拿外部结果，但 FlowMind 才能判断这些结果是否足以成为 truth。

3. **Closeout 漂移**
   executor 可以执行外部写回动作，但 Crazy / Hermes / repository artifact 才能构成最终 closeout truth。

---

## 9. 一句话给总控方

> 当前版本最合理的理解方式，不是“Crazy 融合了一个新的底座”，而是“Crazy 先完成 operator-facing 壳层重构，再把 executor 作为外部 capability plane 接到 Operations，同时保持 Hermes 和 FlowMind 各自的 truth 边界不被吞并”。  
