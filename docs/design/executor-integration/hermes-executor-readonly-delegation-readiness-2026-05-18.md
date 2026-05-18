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
- `executor call petstore-readonly-validation pet getPetById --help`
- `executor tools describe petstore-readonly-validation.pet.getPetById`
- `executor call petstore-readonly-validation pet getPetById '{"petId":1}'`

均能正确返回：

- `petstore-readonly-validation` 已出现在 executor CLI source list
- source 下的 group 结构
- `pet.getPetById` 的输入 schema
- `outputTypeScript = Pet`
- 真实只读调用已成功返回数据

这说明：

> **Hermes 宿主侧已经具备“先 discover / 再看 schema / 再决定是否调用”的只读 delegation 前置条件。**

---

## 4. 当前阻塞点

### 4.1 第一版样本工具曾误判为 blocker

尝试执行：

```bash
executor call petstore-readonly-validation pet findPetsByStatus '{"status":"available"}'
```

以及：

- `executor call petstore-readonly-validation store getInventory`

这两条路径最初都失败，看起来像 executor invocation blocker。
但进一步直连上游 Petstore API 后确认：

- `GET /api/v3/pet/findByStatus?status=available` → 上游返回 `500`
- `GET /api/v3/store/inventory` → 上游返回 `500`

当前更合理的宿主侧只读判断链路是：

- `executor tools sources`
- `executor call <source> --help`
- `executor tools describe <tool>`
- 选择一个上游稳定的只读 GET tool 做真实 invocation

因此第一版 blocker 已被修正为：

> **不是 executor runtime 整体失效，而是最初选中的 Petstore 验证端点本身不稳定。**

---

## 5. 当前结论

截至 2026-05-18，这一阶段的状态应被定义为：

### 已完成

- `Phase B discovery readiness`: `是`
- `Hermes-host read-only source bootstrap`: `是`
- `Hermes-host schema-first delegation path`: `是`
- `Phase B invocation readiness`: `是`

所以当前最准确的结论是：

> **Hermes -> executor 的受控只读 delegation readiness 已经完成：宿主准备、source 准备、schema/discovery 准备，以及至少一条真实只读 tool invocation 都已经在 `ALI-HERMES` 上通过。**

---

## 6. 建议的后续顺序

1. 下一步不再需要优先修“只读调用是否可用”，而是应该开始定义：
   - Hermes 什么时候允许自动调用 executor
   - 哪些 task 类型先开放只读 delegation
   - 结果如何进入 Crazy / FlowMind 的后续链路

2. 在明确 delegation spec 前，仍不要推进：
   - Hermes 受控外部写操作
   - pause/resume/elicitation 回流
   - FlowMind evidence writeback through executor

3. 保持当前边界不变：
   - Crazy 仍负责 source onboarding
   - Hermes 先只开放只读 delegation
   - FlowMind 仍不吃 executor 回流结果

---

## 7. 一句话结论

> `Hermes -> executor` 的下一阶段已经不再是“修只读调用能不能通”，而是“在只读 invocation 已通过的前提下，冻结第一版 delegation spec，并决定哪类 Hermes task 先开放只读 capability 调用”。
