# executor 真实 capability 接入验证收口（2026-05-18）

> 宿主: `ALI-HERMES`  
> live WebUI root: `/opt/crazyagentsmanage`  
> live runtime root: `/root/CrazyAgentsManage`  
> Crazy service: `cam.service`  
> executor sidecar: `executor-sidecar.service`

## 1. 本轮目标

把 `CrazyAgentsManage` 从：

- executor façade 本地回归完成
- `ALI-HERMES` live 面仍停留在旧版本 / `sample` mode

推进到：

- live Crazy 面已同步到当前 reconciled 分支
- `executor` 已在 `ALI-HERMES` 作为 localhost sidecar 运行
- public `/manage` 面已经通过 Crazy façade 消费真实 capability plane

## 2. 实际动作

### 2.1 同步 live 副本

已将以下当前分支文件同步到 `/opt/crazyagentsmanage`：

- `src/webui/api.py`
- `src/webui/executor_bridge.py`
- `src/webui/templates/operations.html`
- `src/webui/static/js/operations.js`
- `src/webui/templates/ia-nav.html`
- `src/webui/templates/overview.html`
- `src/webui/templates/architecture-philosophy.html`
- `src/webui/templates/architecture-product.html`
- `src/webui/templates/architecture-tech.html`
- 以及 timeline 相关文件

同时已将以下 runtime helper 同步到 `/root/CrazyAgentsManage`：

- `scripts/runtime/install_executor_sidecar_on_ali_hermes.sh`
- `scripts/runtime/enable_crazy_executor_http_mode_on_ali_hermes.sh`
- `scripts/runtime/run_on_ali_hermes.py`
- `scripts/runtime/smoke_executor_live_mode.py`

### 2.2 启动 sidecar

已在 `ALI-HERMES` 上执行：

- `bash scripts/runtime/install_executor_sidecar_on_ali_hermes.sh`

结果：

- `executor-sidecar.service` 启动成功
- `http://127.0.0.1:4788/api/scope` 可达
- scope id 生成为 `executor-sidecar-7b2b4496`

### 2.3 切换 Crazy 到 HTTP mode

已在 `ALI-HERMES` 上执行：

- `bash scripts/runtime/enable_crazy_executor_http_mode_on_ali_hermes.sh`

结果：

- `cam.service` 已注入 `EXECUTOR_API_BASE_URL=http://127.0.0.1:4788`
- public `GET /manage/api/operations/integrations/provider-mode` 已从 `sample` 变为 `http`

## 3. 关键验证

### 3.1 public Operations 页面

- `http://47.99.217.1/manage/operations` → `200`

### 3.2 public provider-mode

返回：

- `mode=http`
- `executor_url=http://127.0.0.1:4788`
- `scopeId=executor-sidecar-7b2b4496`

### 3.3 真实 smoke

已执行：

- `python3 scripts/runtime/smoke_executor_live_mode.py`

smoke 行为：

1. 通过 public Crazy façade 读取 `provider-mode`
2. 拉取 `https://petstore3.swagger.io/api/v3/openapi.json`
3. 创建临时 source：`petstore-validation-20260518131829`
4. 验证 source 出现在 `Sources`
5. 验证 `Tool Catalog` 返回 `19` 个真实工具
6. 验证 `Provider Health` / `Summary` 已更新
7. 删除临时 source，cleanup 成功

## 4. 结论

本轮之后，可以明确认定：

> `CrazyAgentsManage` 已经从“本地 executor 接线与回归阶段”，推进到“ALI-HERMES live 面上的真实 capability 接入验证阶段”。

当前仍保持的边界：

- `Crazy` 只消费 capability plane
- `Hermes` 仍持有 runtime lifecycle
- `FlowMind` 仍未在本轮承担 executor 结果回流
- 当前完成的是 `Phase A: Crazy -> executor`

## 5. 下一步

进入下一轮时，优先顺序应是：

1. 固化 live 同步和 sidecar 启停的日常操作入口
2. 决定是否保留一组长期测试 source，还是继续全部使用临时 smoke source
3. 开始设计 `Hermes -> executor delegation` 的受控只读路径
