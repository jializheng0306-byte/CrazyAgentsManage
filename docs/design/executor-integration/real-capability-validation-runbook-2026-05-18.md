# executor 真实 capability 接入验证 Runbook（2026-05-18）

## 1. 目标

把 `CrazyAgentsManage` 从：

- 本地回归通过
- executor façade 语义收口

推进到：

- `ALI-HERMES` live Crazy 面已经部署当前分支
- `cam.service` 已切到 `executor` HTTP mode
- 通过一个真实临时 source 完成 `create -> list -> tools -> summary -> delete` 的最小闭环

这标志着项目已进入 **真实 capability 接入验证阶段**。

---

## 2. 当前阶段边界

本 runbook 只做 **Phase A: Crazy -> executor**：

```text
Crazy Operations UI
  -> Crazy façade API
    -> executor HTTP sidecar
```

当前不做：

- Hermes 任务生命周期委派给 executor
- FlowMind evidence/candidate 正式回流
- 多机共享 executor platform

---

## 3. 仓库内入口

### 3.1 live 副本同步

- `scripts/governance/live-deploy-sync.manifest.json`
- `scripts/governance/check_live_deploy_sync.py`
- `scripts/governance/sync_live_deploy_copy.py`

### 3.2 ALI-HERMES 远端执行

- `scripts/runtime/run_on_ali_hermes.py`

### 3.3 executor sidecar / http mode / smoke

- `scripts/runtime/install_executor_sidecar_on_ali_hermes.sh`
- `scripts/runtime/enable_crazy_executor_http_mode_on_ali_hermes.sh`
- `scripts/runtime/smoke_executor_live_mode.py`

---

## 4. 推荐执行顺序

### Step 1. 检查 live 副本是否漂移

```bash
python3 scripts/governance/check_live_deploy_sync.py \
  --workspace-root . \
  --profile crazy-webui-live \
  --json \
  --batch-mode no
```

### Step 2. 同步 WebUI live 副本

```bash
python3 scripts/governance/sync_live_deploy_copy.py \
  --workspace-root . \
  --profile crazy-webui-live \
  --skip-verify
```

### Step 3. 同步 runtime helper 到 ALI-HERMES

```bash
python3 scripts/governance/sync_live_deploy_copy.py \
  --workspace-root . \
  --profile crazy-runtime-live \
  --skip-verify
```

### Step 4. 在 ALI-HERMES 安装 executor sidecar

```bash
python3 scripts/runtime/run_on_ali_hermes.py \
  --cwd /root/CrazyAgentsManage \
  -- bash scripts/runtime/install_executor_sidecar_on_ali_hermes.sh
```

### Step 5. 让 cam.service 切到 executor HTTP mode

```bash
python3 scripts/runtime/run_on_ali_hermes.py \
  --cwd /root/CrazyAgentsManage \
  -- bash scripts/runtime/enable_crazy_executor_http_mode_on_ali_hermes.sh
```

### Step 6. 执行真实 smoke

```bash
python3 scripts/runtime/smoke_executor_live_mode.py
```

默认 smoke 会：

1. 确认 `provider-mode == http`
2. 拉取 `petstore3` OpenAPI 文档
3. 通过 Crazy façade 创建临时 `openapi` source
4. 验证 source 出现在 `Sources`
5. 验证 `Tool Catalog` 可读取到真实工具
6. 验证 `Provider Health` / `Summary` 已更新
7. 默认删除临时 source，避免污染 live 面

---

## 5. 通过标准

以下条件同时满足时，可认定已进入真实 capability 接入验证阶段：

1. `http://47.99.217.1/manage/operations` 可打开
2. `GET /manage/api/operations/integrations/provider-mode` 返回 `mode=http`
3. `executor` sidecar 在 `127.0.0.1:4788` 健康
4. smoke 可以走完 `create -> list -> tools -> summary -> delete`
5. `Runtime / Governance / Collaboration` 没有因为 executor 接入而被侵入

---

## 6. 失败时先看什么

### 6.1 provider-mode 仍是 `sample`

先看：

```bash
python3 scripts/runtime/run_on_ali_hermes.py -- systemctl status executor-sidecar.service --no-pager
python3 scripts/runtime/run_on_ali_hermes.py -- systemctl status cam.service --no-pager
python3 scripts/runtime/run_on_ali_hermes.py -- curl -fsS http://127.0.0.1:4788/api/scope
python3 scripts/runtime/run_on_ali_hermes.py -- curl -fsS http://127.0.0.1:5002/api/operations/integrations/provider-mode
```

### 6.2 `/manage/operations` 仍然异常

优先复查：

- `crazy-webui-live` profile 是否已同步
- `cam.service` 是否已重启
- `/opt/crazyagentsmanage/src/webui/api.py`
- `/opt/crazyagentsmanage/src/webui/executor_bridge.py`
- `/opt/crazyagentsmanage/src/webui/templates/operations.html`
- `/opt/crazyagentsmanage/src/webui/static/js/operations.js`

---

## 7. 一句话结论

这个 runbook 的意义不是“把 executor 平台化上线”，而是：

> **先把当前 Crazy 分支部署到 `ALI-HERMES` live 面，再把 executor 作为 localhost sidecar 接到 `Operations`，用一个真实临时 source 证明 capability plane 已经可被 live Crazy 消费。**
