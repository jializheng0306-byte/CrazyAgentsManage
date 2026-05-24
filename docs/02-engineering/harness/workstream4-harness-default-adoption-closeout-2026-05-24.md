# Workstream 4 · Harness Default Adoption Closeout（2026-05-24）

> 范围: Crazy `Workstream 4 Harness Productization`  
> 状态: `completed-published`  
> 宿主: `ALI-HERMES`

## 1. 目标

把 Workstream 4 从：

- 已有 starter visibility
- 已有 closeout artifact / lane traceability / governance chain check
- 但 non-trivial round 仍可能 direct 写 trace，绕过默认 closeout 入口

推进到：

- non-trivial round 默认只能走 canonical closeout 链
- `Operations > Harness` 明确展示默认入口与 direct trace policy
- Workstream 4 可以从 `completed-in-lane` 升格为 `completed-published`

## 2. 本轮落地

### 2.1 Default adoption enforcement

`scripts/record-success.cjs` 与 `scripts/record-failure.cjs` 现在默认拒绝 non-trivial direct 调用：

- 允许：`harness-closeout-writeback.cjs` 内部调用
- 允许：`HARNESS_TRACE_TRIVIAL=true` 的 trivial local probe
- 拒绝：把 direct trace 脚本当作 non-trivial round 的主 closeout 入口

### 2.2 Operations > Harness policy visibility

`GET /api/operations/harness` 现在额外暴露：

- `defaultEntry`
- `directTracePolicy`

页面侧同步把这两条规则显示在 `Harness Summary`。

### 2.3 Canonical command list

`Operations > Harness` 的默认命令链现已收紧为：

- `harness-closeout-writeback`
- `harness-critic`
- `check_harness_closeout_chain.py`
- `create-agent-worktree.sh`

不再把 `record-success.cjs` / `record-failure.cjs` 作为默认主入口展示。

## 3. 验证

### 本地

- `pytest tests/test_sprint4.py`
- `python -m py_compile src/webui/api.py src/webui/app.py`
- `node --check src/webui/static/js/operations.js`
- `node --check scripts/record-success.cjs`
- `node --check scripts/record-failure.cjs`
- `node --check scripts/harness-closeout-writeback.cjs`
- `bash scripts/check_harness_governance_all.sh`

本地 closeout evidence：

- `trace.id = S-20260524-001`
- `closeout.id = C-20260524-001`
- `lane = shared`
- `topic = workstream4-default-adoption`

### 宿主

固定顺序：

1. `python3 scripts/governance/sync_live_deploy_copy.py --workspace-root . --profile crazy-runtime-live --skip-verify --json`
2. `python3 scripts/runtime/run_on_ali_hermes.py --cwd /root/CrazyAgentsManage -- 'python3 scripts/runtime/sync_hermes_script_mirror.py'`
3. `python3 scripts/governance/sync_live_deploy_copy.py --workspace-root . --profile crazy-webui-live --skip-verify --json`

宿主 smoke 关注：

- direct `record-success.cjs` 对 non-trivial round 必须失败
- `harness-closeout-writeback.cjs` 仍可成功写出 canonical trace + closeout
- `/api/operations/harness` 返回新的 policy 字段

宿主 evidence：

- direct trace rejection:
  - `record-success.cjs only supports trivial direct traces; non-trivial rounds must use node scripts/harness-closeout-writeback.cjs`
- canonical closeout:
  - `trace.id = S-20260524-002`
  - `closeout.id = C-20260524-002`
  - `lane = shared`
  - `topic = host-default-adoption-smoke`

## 4. 裁定

当前 Workstream 4 已不再只是“脚本存在 + starter 可见”，而是具备：

1. canonical closeout 入口
2. default adoption enforcement
3. `Operations` 上的可见 policy
4. 宿主可复验的行为约束

因此本条线从：

- `completed-in-lane`

升级为：

- `completed-published`

## 5. 后续

下一条自然工作不再是继续补 Harness 基础设施，而是：

- 把 reviewer / Hermes acceptance / PRD closeout 进一步贴到同一条 evidence 链
- 在后续 productization 中继续利用 `pending closeout` 做巡检与复盘入口
