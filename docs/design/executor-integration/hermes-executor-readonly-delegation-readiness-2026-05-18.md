# Hermes -> executor 只读 delegation readiness（2026-05-18）

## 1. 目的

在 `Crazy -> executor` 真实 capability 接入验证已经完成之后，本轮继续推进下一个明确阶段：

> `Hermes -> executor` 的 **受控只读 delegation readiness**

这里的目标不是直接让 Hermes 全量把任务委派给 executor，而是先验证：

1. `ALI-HERMES` 宿主机是否已经具备调用 executor 的宿主条件
2. 是否存在一个稳定的、无鉴权的、长期可复用的只读验证 source
3. Hermes 宿主侧是否至少能走通：
   - `discover`
   - `help`
   - `describe`
   - 最终的 `read-only call`

---

## 2. 本轮新增仓库入口

### 2.1 持久只读验证 source

- `scripts/runtime/ensure_executor_validation_source.py`

作用：

- 通过 Crazy 的 operator-facing façade，幂等确保 `petstore-readonly-validation` 存在
- 不要求 Hermes 自己去做 source onboarding
- 保持边界：source onboarding 仍属于 Crazy/Operations

### 2.2 宿主侧只读 probe

- `scripts/runtime/probe_hermes_executor_readonly_path.py`

作用：

- 先确保 validation source 存在
- 再从 `ALI-HERMES` 宿主侧执行：
  - `executor tools sources`
  - `executor call <source> --help`
  - `executor call <source> <tool> --help`
  - `executor tools describe <tool>`
  - 可选真实只读调用

---

## 3. 当前实测结果

### 3.1 已确认成立

#### A. 宿主条件成立

- `executor-sidecar.service` 为 `active`
- `cam.service` 已处于 `http` mode
- `GET /manage/api/operations/integrations/provider-mode` 返回：
  - `mode=http`
  - `executor_url=http://127.0.0.1:4788`
  - `scopeId=executor-sidecar-7b2b4496`

#### B. 长期只读验证 source 已建立

已通过 Crazy façade 创建：

- `petstore-readonly-validation`

当前在 public Crazy `Sources` 中可见：

- `provider=openapi`
- `status=healthy`
- `toolCount=19`

#### C. Hermes 宿主侧 discovery / help / describe 成立

在 `ALI-HERMES` 上已实测：

- `executor tools sources`
- `executor call petstore-readonly-validation --help`
- `executor call petstore-readonly-validation pet findPetsByStatus --help`
- `executor tools describe petstore-readonly-validation.pet.findPetsByStatus`

均能正确返回：

- `petstore-readonly-validation` 已出现在 executor CLI source list
- source 下的 group 结构
- `pet.findPetsByStatus` 的输入 schema
- `outputTypeScript = Pet[]`

这说明：

> **Hermes 宿主侧已经具备“先 discover / 再看 schema / 再决定是否调用”的只读 delegation 前置条件。**

---

## 4. 当前阻塞点

### 4.1 真实只读调用仍未通过

尝试执行：

```bash
executor call petstore-readonly-validation pet findPetsByStatus '{"status":"available"}'
```

当前返回：

- CLI 侧报错：`There was an error processing your request`
- debug stack 指向：`executor-quickjs-runtime.js`
- sidecar 日志显示 `/executions` 请求已成功进入 executor，但执行结果未正常返回给 CLI

这说明问题不在：

- sidecar 服务不存在
- source 不可见
- tool schema 无法解析
- CLI path 错误

当前更合理的宿主侧只读判断链路是：

- `executor tools sources`
- `executor call <source> --help`
- `executor tools describe <tool>`

更像是：

- 当前 executor runtime / OpenAPI invocation 路径的执行层问题
- 或 upstream 在该工具调用上的宿主兼容问题

---

## 5. 当前结论

截至 2026-05-18，这一阶段的状态应被定义为：

### 已完成

- `Phase B discovery readiness`: `是`
- `Hermes-host read-only source bootstrap`: `是`
- `Hermes-host schema-first delegation path`: `是`

### 未完成

- `Phase B invocation readiness`: `否`

所以当前最准确的结论不是“Phase B 已完成”，而是：

> **Hermes -> executor 的受控只读 delegation 已经完成宿主准备、source 准备和 schema/discovery 准备，但真实只读调用仍卡在 executor runtime 执行层。**

---

## 6. 建议的后续顺序

1. 优先把当前 read-only call 失败缩到具体层：
   - executor CLI 适配问题
   - upstream runtime bug
   - 某类 OpenAPI source invocation bug

2. 在 read-only call 路径稳定之前，不要推进：
   - Hermes 受控外部写操作
   - pause/resume/elicitation 回流
   - FlowMind evidence writeback through executor

3. 保持当前边界不变：
   - Crazy 仍负责 source onboarding
   - Hermes 仍只验证 host-side delegation readiness
   - FlowMind 仍不吃 executor 回流结果

---

## 7. 一句话结论

> `Hermes -> executor` 的下一阶段已经不再是“从零设计怎么接”，而是“在已具备 discovery/help/describe 能力和长期只读验证 source 的前提下，修通 read-only invocation 的最后一段 runtime 执行链路”。  
