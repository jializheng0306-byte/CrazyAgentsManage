# Hermes × executor 只读 Delegation Spec v1（2026-05-19）

## 1. 目的

在 `ALI-HERMES` 上，`Hermes -> executor` 的只读 capability 调用已经完成 readiness 验证：

- source 可见
- schema/help/describe 可见
- 至少一条真实只读 invocation 已通过

下一步不再是继续证明“能不能调”，而是冻结：

1. **Hermes 什么时候允许自动调用 executor**
2. **第一批开放哪些 Hermes task 类型**
3. **哪些类型继续禁止**
4. **只读结果如何回到 Hermes / Crazy，而不越过 FlowMind 边界**

---

## 2. 边界

### 2.1 所有权不变

- `CrazyAgentsManage`
  - 拥有 operator-facing product shell
  - 拥有 source onboarding / provider health / capability visibility

- `HermesAgent`
  - 拥有 runtime lifecycle
  - 拥有 session / trace / task state
  - 拥有是否发起 delegation 的判断权

- `FlowMind`
  - 拥有 candidate / truth / review / provenance
  - 不直接接收 executor 内部执行态

- `executor`
  - 只承接 capability plane
  - 只负责 external read capability execution
  - 不拥有 runtime truth / governance truth / closeout truth

### 2.2 v1 范围

本 spec 只覆盖：

- `readonly`
- `external capability step`
- `Hermes host-side consumption`

本 spec 不覆盖：

- 外部写操作
- source / credential / binding 变更
- pause / resume / elicitation 回流
- FlowMind writeback through executor
- closeout / repo writeback through executor

---

## 3. 只读 delegation 前置条件

Hermes 只有在以下条件同时满足时，才允许把某个 external step 委派给 executor：

1. `ALI-HERMES` 上 `executor-sidecar.service` 为 `active`
2. Crazy live `provider-mode == http`
3. 目标 source 已由 Crazy/Operations 预先创建
4. 目标 tool 已可通过 `executor tools describe <path>` 读取 schema
5. 该 tool 属于只读调用，不触发外部写操作
6. 该 task 的主 authority 仍然在 Hermes，而不是把整个任务托管给 executor

---

## 4. Delegation 单元

v1 冻结的 delegation 单元不是“整个任务”，而是：

> **task 内的 external read capability step**

也就是说：

- Hermes 仍然启动任务
- Hermes 仍然记录 trace / state / errors
- Hermes 只把“去外部系统读数据”这一步交给 executor
- 结果回到 Hermes 后，再由 Hermes 决定：
  - 写本地报告
  - 更新共享上下文
  - 是否提交给 FlowMind
  - 是否给 operator 发消息

---

## 5. 第一批开放的 task 类型（Wave 1）

这批任务满足三个条件：

1. 现实中已经存在稳定入口脚本 / job
2. 任务的核心价值是“读取外部资料”
3. 即使 delegation 失败，也不会直接污染 FlowMind / promise / closeout truth

### 5.1 `intel.morning`

现有入口：

- `scripts/morning-intel-v2.py`
- `scripts/morning-intel-collector.sh`

当前落地状态：

- **collector 级 external read step 已接入 executor**
- **repo-tracked wrapper authority 已建立**
- capability source: `hn-readonly`
- repo-tracked helper: `scripts/fetch-hn-stories-via-executor.py`

允许 delegation 的步骤：

- arXiv / RSS / GitHub 等外部数据拉取
- 外部只读摘要查询

不允许 delegation 的步骤：

- 写 Tech Radar JSON
- 发 Feishu 群消息
- 改 Hermes 本地记忆

### 5.2 `intel.noon-paper`

现有入口：

- `system crontab` `noon-paper-review.sh`
- `scripts/noon-paper-collector.sh`

当前落地状态：

- **已作为 Wave 1 首条端到端链路实现**
- capability source: `crossref-readonly`
- host wrapper: repo-tracked `scripts/noon-paper-review.sh`

允许 delegation 的步骤：

- 学术论文元数据只读查询
- 外部只读摘要获取

不允许 delegation 的步骤：

- 本地报告写回
- Feishu 推送
- FlowMind candidate ingress

### 5.3 `intel.evening`

现有入口：

- `scripts/evening-trend-analysis.py`
- `scripts/evening-intel-collector.sh`

当前落地状态：

- **collector 级 external read step 已接入 executor**
- **repo-tracked wrapper authority 已建立**
- capability source: `hn-readonly`
- repo-tracked helper: `scripts/fetch-hn-stories-via-executor.py`

允许 delegation 的步骤：

- 外部新闻 / feed / API 的只读查询
- 趋势相关只读 capability 聚合

不允许 delegation 的步骤：

- 更新 `shared-context/tech-radar.json`
- 运行 `bitable_sync.py`
- 发送运营消息

---

## 6. 第二批候选（Wave 2，暂不默认开放）

这批任务不是禁止，而是需要在 Wave 1 跑稳后再开放。

### 6.1 `tech-radar.review`

现有入口：

- `scripts/tech-radar-review.sh`

为什么不先开：

- 当前主逻辑更多是本地 `shared-context` 汇总，而不是强依赖外部 capability
- executor 对它的收益不如 intel 采集链明显

可开放的未来方向：

- 对已进入 radar 的条目做外部证据补拉
- 对某个 technology / paper / repo 做补充只读查询

### 6.2 `flowmind.health-probe`

现有历史 job：

- `FlowMind巡检-每日一次`（当前 paused）

为什么不先开：

- 它现在不在受支持的 repo-tracked 主链里
- 容易和现有 live guard / source-of-truth 规则冲突

---

## 7. 当前明确禁止的 task 类型

### 7.1 `promise.review`

现有入口：

- `scripts/daily-promise-review.py`

禁止原因：

- 写 Bitable 主表 / trace 子表
- 拉 FlowMind truth / trace / feedback 后会形成治理输出
- 已越过“只读 external step”的边界

### 7.2 `promise.capture-clarify`

现有入口：

- `scripts/promise-governance/promise_capture_clarify.py`

禁止原因：

- 创建本地 promise
- 写 trace
- 可选进入 FlowMind candidate ingress

### 7.3 `flowmind.capture`

现有入口：

- `scripts/flowmind_capture.py`

禁止原因：

- 直接写 candidate ingress
- 属于 governance write path

### 7.4 `closeout.writeback`

现有入口：

- `scripts/runtime/closeout_writeback.py`
- 各类 handoff / closeout flow

禁止原因：

- 属于 closeout truth
- 不能交给 executor 持有 authority

### 7.5 `cron.health`

现有入口：

- `scripts/cron-health-check.sh`

禁止原因：

- 当前是本地宿主健康与日志检查
- 不属于外部 capability 优先收益场景

### 7.6 `memory.maintenance` / `reflection`

现有入口：

- `memory-maintenance.sh`
- `auto-reflection.sh`

禁止原因：

- 核心是本地记忆/学习工件维护
- 不是 external read capability 问题

---

## 8. v1 执行协议

当 Wave 1 任务需要 readonly delegation 时，Hermes 应按以下顺序执行：

1. 先确定 task 仍由 Hermes 持有生命周期
2. 只选择 external read step 做 delegation
3. 先看 `executor tools describe` 获取 schema
4. 再执行 readonly call
5. 把结果回收到 Hermes runtime trace
6. 后续本地写回 / 报告 / 推送 / governance 动作仍由 Hermes 或 Crazy 主链负责

---

## 9. 失败处理

如果 readonly delegation 失败：

1. Hermes 记录失败到 runtime trace
2. Hermes 不自动升级成外部写动作
3. Hermes 可回退到现有 repo-tracked 本地脚本路径
4. 失败不能直接污染：
   - promise truth
   - FlowMind truth
   - closeout artifacts

---

## 10. 一句话结论

> v1 冻结的策略是：**只把 `morning-intel / noon-paper / evening-intel` 这三类以外部读取为主的任务，开放“external read step”级别的 readonly delegation；所有治理写回、承诺写回、closeout 写回、宿主本地运维类任务继续禁止。**
