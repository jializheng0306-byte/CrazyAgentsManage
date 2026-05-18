# Hermes -> executor 只读 delegation readiness 收口（2026-05-18）

> 宿主: `ALI-HERMES`  
> executor sidecar: `executor-sidecar.service`  
> Crazy live mode: `http`  
> 验证 source: `petstore-readonly-validation`

## 1. 本轮意图

在 `Crazy -> executor` 真实 capability 接入验证完成后，继续向下一阶段推进：

- 不直接做写操作 delegation
- 不直接做 FlowMind 结果回流
- 先验证 `Hermes -> executor` 的 **只读 delegation readiness**

## 2. 本轮新增事实

### 2.1 长期只读验证 source 已固定

已通过 Crazy façade 固定一个长期可复用的无鉴权验证 source：

- `petstore-readonly-validation`

当前状态：

- `provider=openapi`
- `status=healthy`
- `toolCount=19`

### 2.2 宿主侧 source / help / describe 成立

在 `ALI-HERMES` 上，以下链路已经成立：

- `executor tools sources`
- `executor call petstore-readonly-validation --help`
- `executor call petstore-readonly-validation pet getPetById --help`
- `executor tools describe petstore-readonly-validation.pet.getPetById`
- `executor call petstore-readonly-validation pet getPetById '{"petId":1}'`

这说明宿主侧已经能做到：

1. 看见 capability source
2. 先看 group/path
3. 再看 input/output schema
4. 按 schema 组织调用参数
5. 至少完成一条真实只读 tool invocation

### 2.3 第一版 blocker 已被修正

最初失败的样本是：

```bash
executor call petstore-readonly-validation pet findPetsByStatus '{"status":"available"}'
executor call petstore-readonly-validation store getInventory
```

继续核对后确认：

- `GET https://petstore3.swagger.io/api/v3/pet/findByStatus?status=available` 本身返回 `500`
- `GET https://petstore3.swagger.io/api/v3/store/inventory` 本身返回 `500`

因此原来的“runtime invocation blocker”不是 executor 总体故障，而是验证样本选择问题。

## 3. 结构化结论

### 已完成

- `discoveryReady = true`
- `schemaHelpReady = true`
- `hostReadiness = true`
- `invocationReady = true`

因此本轮收口应定义为：

> `Hermes -> executor` 的只读 delegation readiness 已经完成，且至少一条真实 read-only invocation 已在 `ALI-HERMES` 上通过。

## 4. 对下一轮的约束

在 delegation spec 冻结前，不应继续推进：

- Hermes 受控外部写操作
- pause/resume/elicitation 回流
- FlowMind 通过 executor 吃 evidence writeback

下一轮最优先事项应是：

1. 定义第一版只读 delegation spec
2. 决定 Hermes 哪类 task 先开放只读 capability 调用
3. 决定结果如何向 Crazy / FlowMind 继续传递
