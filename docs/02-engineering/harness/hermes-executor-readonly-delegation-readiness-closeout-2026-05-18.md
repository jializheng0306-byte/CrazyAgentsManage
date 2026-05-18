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
- `executor call petstore-readonly-validation pet findPetsByStatus --help`
- `executor tools describe petstore-readonly-validation.pet.findPetsByStatus`

这说明宿主侧已经能做到：

1. 看见 capability source
2. 先看 group/path
3. 再看 input/output schema
4. 按 schema 组织调用参数

### 2.3 真实只读调用仍失败

尝试执行：

```bash
executor call petstore-readonly-validation pet findPetsByStatus '{"status":"available"}'
```

当前结果：

- CLI 返回 runtime error
- debug stack 指向 `executor-quickjs-runtime.js`
- sidecar 日志显示 `/executions` 已成功进入 executor，但执行结果没有正常回到 CLI

## 3. 结构化结论

### 已完成

- `discoveryReady = true`
- `schemaHelpReady = true`
- `hostReadiness = true`

### 未完成

- `invocationReady = false`

因此本轮收口应定义为：

> `Hermes -> executor` 的只读 delegation 已经完成宿主准备与 schema-first 准备，但真实 read-only invocation 仍卡在 executor runtime 执行层。

## 4. 对下一轮的约束

在修通 `read-only invocation` 前，不应继续推进：

- Hermes 受控外部写操作
- pause/resume/elicitation 回流
- FlowMind 通过 executor 吃 evidence writeback

下一轮最优先事项应是：

1. 缩小 `executor-quickjs-runtime.js` 调用失败范围
2. 判断是 upstream invocation bug 还是当前 OpenAPI source runtime 兼容问题
3. 修通至少一条真正的 read-only tool invocation
