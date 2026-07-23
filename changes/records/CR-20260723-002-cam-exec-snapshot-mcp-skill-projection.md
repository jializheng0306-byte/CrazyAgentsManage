# CR-20260723-002

**日期:** 2026-07-23
**类型:** Capability Absorption (Cross-Repo, OpenBKN)
**范围:** CAM-P0 执行时配置快照 + CAM-P1 MCP/Skill 只读投影

## 摘要

CrazyAgentsManage 吸收 OpenBKN ActionTypeSnapshot 能力：task 进入执行状态时冻结配置快照（append-only 不可变），并新增 Operations façade 只读投影 MCP instance + Skill registry（对齐 bkn-sdk skill 查询面）。

## 跨仓引用

- **正向引用**: FMD CR-20260723-003（A2 执行时 DSL 快照）— CAM-P0 的执行时配置快照对齐 A2 的证据锚点模式
- **正向引用**: FMD CR-20260723-004（A3 声明式风险 Pre-checks）— CAM-P0 的 automation_state 对齐 A3 的 Pre-Execution Gate 模式
- FMD A2 PR #48 (SHA 605da09e) + A3 PR #49 (SHA c9a34d12) 已 merged

## 变更内容

### CAM-P0：执行时配置快照

1. **`src/core/execution_snapshot.py`**（新增）
   - `capture_execution_snapshot(task_id, task_config, automation_state, permission_hooks, duplicate_hooks)` — 组装不可变快照（含 sha256 checksum + frozen_at）
   - `append_snapshot(snapshot, storage_path)` — append-only JSON Lines 持久化
   - `load_snapshots(storage_path)` — 读取历史快照
   - `verify_snapshot(snapshot)` — 校验 checksum 不变性（防篡改）

### CAM-P1：Operations façade 只读投影

2. **`src/webui/api.py`**（新增端点）
   - `/api/operations/integrations` — 投影 MCP instance + Skill registry
   - 只读，无写操作（`read_only: true`）
   - Skill registry 复用现有 `_scan_local_skills` / `_scan_remote_skills` 扫描逻辑
   - MCP instance 从 `mcp_servers.json` 配置只读投影
   - 对齐 bkn-sdk skill 查询面，不内聚编排

### 测试

3. **`src/core/test_execution_snapshot.py`**（新增，unittest）
   - checksum 生成 + 确定性 + 差异性
   - append-only round-trip + 多快照顺序
   - verify 防篡改
   - **R13 守卫**: 断言快照不含 owner 字段（不转移承诺 ownership）

## 边界

- **R13 (GTD)**: 快照不含 owner 字段，不转移承诺 ownership
- **append-only**: 一旦写入不可修改
- **Invariant 1 (对偶)**: 快照是证据锚点，不是 truth 源（对齐 FMD A2 dslSnapshot 边界）
- **只读投影**: CAM-P1 不内聚编排，仅投影查询面

## 设计决策

- **CAM 与 FMD 异构语言栈**: CAM=Python/Flask，FMD=TypeScript。CAM 走自身 harness；跨仓只 CR 互引，不混合运行时
- **automation_state 渐进治理**: prototype→rehearsed→approved-for-automation→automated（对齐 CAM task-bus 渐进治理模型）
- **不迁全 taxonomy**: CAM-P0 只实现快照机制，不预定义全部 automation_state 转换规则

## 关联

- 跨仓对偶: FMD CR-20260723-003 (A2 DSL 快照) + CR-20260723-004 (A3 Pre-checks)
- 执行计划: FMD `harness/exec-plans/EP-20260724-openbkn-absorption-resumption.md`
- OpenBKN 源: ActionTypeSnapshot (bkn-engineering) + bkn-sdk skill 查询面

## 验证

- [x] `python3 -m unittest src/core/test_execution_snapshot.py` 全绿（13 tests）
- [x] R13 守卫: 快照不含 owner 字段
- [x] checksum 不变性: verify 检测篡改
- [x] append-only: 多快照顺序保持

## 下一步

- PR merge 后 accepted SHA 冻结
- Step Final: 跨仓 CR 互引验证（FMD CR-003/004 ↔ CAM CR-002）
