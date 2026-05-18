# executor 阿里云部署评估（2026-05-18）

## 1. 结论

当前版本下，`executor` **不应立即被当成 CrazyAgentsManage 的独立产品底座部署**，  
但**可以在需要真实 capability plane 时，以 sidecar / local capability service 的方式部署到阿里云宿主环境**。

一句话：

> **当前推荐的是“按需部署 sidecar”，不是“先上共享 executor 平台”。**

---

## 2. 是否现在就必须部署？

### 2.1 不必须立即部署的理由

当前仓库已经具备：

- `Operations` → executor façade API
- sample mode / http mode 自动切换
- `Sources / Tool Catalog / Credential Health / Provider Health` 的 UI 接入
- source / credential 写操作的本地回归测试

也就是说：

- 对于当前产品设计评审
- 对于本地实现与页面接线
- 对于 capability plane 的对象模型验证

**不需要先在阿里云部署 executor，当前分支也能继续推进。**

### 2.2 什么时候需要部署

当以下任一目标成为当前任务时，建议开始部署：

1. 需要在 Crazy `Operations` 页面看到**真实** source/tool/provider/credential 数据，而不是 sample mode
2. 需要让 HermesAgent 在真实运行环境里调用 executor 做外部能力编排
3. 需要把 executor 的结果作为 FlowMind 的真实 candidate / evidence 上游
4. 需要验证 provider / credential / binding 在真实环境中的健康态与操作闭环

所以结论是：

- **评审阶段**：不必强制部署
- **真实 capability 接入阶段**：应部署

---

## 3. 推荐部署方式

## 3.1 推荐：阿里云 sidecar 模式

当前最稳的部署方式不是单独立一个 executor 产品环境，而是：

```text
ALI-HERMES / Crazy 宿主机
├─ HermesAgent runtime host
├─ CrazyAgentsManage WebUI / Flask
└─ executor local HTTP server (sidecar)
```

推荐原因：

1. 当前 Crazy 代码已经按 **HTTP capability bridge** 实现：
   - `EXECUTOR_API_BASE_URL`
   - `EXECUTOR_SCOPE_ID`
   - `get_executor_provider()`
2. 当前文档也明确第一阶段接入方式是：
   - `sidecar / capability service`
3. 这样不会过早把 executor 升级成“共享平台真相源”

### 推荐环境变量

```bash
EXECUTOR_API_BASE_URL=http://127.0.0.1:4788
EXECUTOR_SCOPE_ID=<executor scope id>
```

这意味着：

- Crazy 通过 localhost HTTP 访问 executor
- 不依赖额外公网暴露
- provider / secret / source 的能力面保留在宿主机侧

## 3.2 当前不推荐：先做共享 executor service

即不推荐一开始就做成：

- 远端独立 executor cluster
- 多租户共享 capability plane
- Crazy / Hermes 远程跨机访问 executor

原因：

1. 现在 `Hermes -> executor delegation spec` 还没冻结
2. `FlowMind evidence enrichment pipeline` 还没正式实现
3. `Closeout writeback integration` 还没明确哪些动作该交给 executor
4. 过早平台化会把部署、权限、secret、provider 故障面放大

---

## 4. HermesAgent 如何适配 executor

## 4.1 不变的边界

HermesAgent 继续保持：

- runtime host
- session / trace / token / tool call 现场真相源
- 任务生命周期持有者

executor 不替代 Hermes 的：

- session model
- trace model
- runtime telemetry
- operator closeout truth

## 4.2 当前阶段的适配方式

### Phase A：Crazy → executor

先由 Crazy 接入 executor：

```text
Crazy Operations UI
  -> Crazy façade API
    -> executor HTTP API
```

这一阶段 Hermes 不需要直接改成“通过 executor 跑所有任务”，只需允许 Crazy 在同一宿主机上看到真实 capability plane。

### Phase B：Hermes → executor delegation

在需要真实 external orchestration 时，再补 Hermes 适配：

```text
Hermes runtime task
  -> executor capability / execution
    -> external system result
      -> FlowMind candidate / evidence
```

适配原则：

1. **Hermes 持有任务生命周期**
   - 开始
   - 中断
   - 恢复
   - 失败
   - trace

2. **executor 只执行能力步骤**
   - source access
   - tool invoke
   - external orchestration

3. **FlowMind 只消费结果**
   - candidate
   - evidence
   - provenance

## 4.3 建议的 Hermes 适配顺序

1. 先只让 Hermes 感知 executor 健康态
2. 再允许 Hermes 调 executor 做只读外部查询
3. 再允许 Hermes 调 executor 做受控外部写操作
4. 最后才考虑 execution delegation / pause / resume / elicitation 回流

---

## 5. 部署前检查单

在阿里云上真正部署 executor 之前，至少应满足：

1. Crazy `Operations` 已经在 http mode 下可稳定读取：
   - sources
   - tools
   - credentials
   - providers
   - summary
2. source create / delete / refresh / bind / unbind 已有定向回归保护
3. executor provider / credential 健康态语义已经收口
4. 明确 executor 结果是否会进入 FlowMind evidence/candidate
5. 明确 executor secrets 由谁运维、放在哪层
6. 明确 Hermes 遇到 executor 不可达时的降级策略

---

## 6. 当前推荐决策

### 当前阶段建议

- **继续在当前分支完成 Crazy 侧 capability plane 收口**
- **暂不强制要求立即在阿里云部署 executor**

### 下一阶段建议

如果要进入真实 capability 集成验证：

- **在阿里云宿主机上部署 executor local HTTP sidecar**
- **Crazy 先消费**
- **Hermes 后委派**
- **FlowMind 最后消费结果**

---

## 7. 一句话给总控方

> 现在最合理的做法不是“马上把 executor 部署成独立平台”，而是等 Crazy 当前 capability-plane 接口和对象语义收口后，再在阿里云宿主机上以 localhost sidecar 的方式部署 executor；接入顺序保持 `Crazy 先消费 -> Hermes 后委派 -> FlowMind 最后吃结果`。  
