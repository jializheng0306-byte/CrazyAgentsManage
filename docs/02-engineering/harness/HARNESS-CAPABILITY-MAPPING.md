# Harness Capability Mapping

## 文档目的

说明从 `FlowMindDeploy` 迁入的 Harness 机制，在 `CrazyAgentsManage` 中如何落地，以及它与当前 `Codex ↔ HermesAgent` 协作模型如何分层。

## 一、分层关系

当前项目的执行治理分为三层：

### 1. 通用 Harness 层

这是从 `FlowMindDeploy` 迁入并适配后的共享执行基础设施，包括：

- `harness/`
- `docs/02-engineering/harness/HARNESS-ENTRY.md`
- `docs/02-engineering/harness/HAGENT-WORKFLOW.md`
- `docs/02-engineering/harness/CROSS-REVIEW-PROCESS.md`
- `docs/02-engineering/harness/WORKTREE-BOOTSTRAP.md`
- `scripts/record-success.cjs`
- `scripts/record-failure.cjs`
- `scripts/harness-critic.cjs`
- `scripts/harness-closeout-writeback.cjs`
- `scripts/worktree/create-agent-worktree.sh`

### 2. CrazyAgentsManage 专用协作层

这是当前项目原有且继续保留的 `Codex ↔ HermesAgent` 专用机制，包括：

- `docs/02-engineering/harness/CODEX-HERMES-WORKFLOW.md`
- `docs/02-engineering/harness/CODEX-HERMES-COLLABORATION-MECHANISM.md`
- `docs/02-engineering/harness/HERMESAGENT-ENTRY.md`
- `docs/codex-hermes-role-design.md`
- `scripts/runtime/write_runtime_state.py`
- `scripts/runtime/generate_hermes_handoff.py`
- `scripts/runtime/closeout_writeback.py`

### 3. OMX runtime-local 层

这是会话级、运行期、非 durable 的辅助层：

- `.omx/state/`
- `.omx/notepad.md`
- `.omx/context/`
- `.omx/interviews/`

## 二、能力落地映射

## 1. 执行计划能力

### 来源能力

FlowMindDeploy 的 `harness/exec-plans/` 与 Harness 入口规则。

### 当前项目落地

- `harness/exec-plans/TEMPLATE.md`
- `docs/roadmap/master-task-plan.md`
- 非平凡任务可在 `harness/exec-plans/` 下继续落地切片执行计划

### 当前意义

让 PRD、路线图、具体执行切片之间形成可追踪关系，而不是只靠聊天推进。

## 2. 结构化成功/失败记录能力

### 来源能力

- `record-success.cjs`
- `record-failure.cjs`

### 当前项目落地

- `scripts/record-success.cjs`
- `scripts/record-failure.cjs`
- 输出目录：
  - `harness/trace/successes/`
  - `harness/trace/failures/`

### 当前意义

每一轮非平凡迭代可以有结构化 closeout，而不是只靠口头说明完成。

## 3. Critic 自学习能力

### 来源能力

`harness-critic.cjs`

### 当前项目落地

- `scripts/harness-critic.cjs`
- 回写目标：
  - `harness/memory/failure-patterns.md`
  - `harness/memory/procedural.md`

### 当前意义

当前项目可以把重复失败模式沉淀成仓库级经验，而不是留在单次会话里。

## 4. Closeout writeback 能力

### 来源能力

`harness-closeout-writeback.cjs`

### 当前项目落地

- `scripts/harness-closeout-writeback.cjs`
- 可统一完成：
  - success/failure trace 写入
  - critic 触发
  - critic write-back

### 当前意义

把“完成一轮工作”从一句话，变成一个可审阅的、可回放的仓库流程。

## 5. Worktree bootstrap 能力

### 来源能力

`scripts/worktree/create-agent-worktree.sh`

### 当前项目落地

- `scripts/worktree/create-agent-worktree.sh`
- 文档：
  - `docs/02-engineering/harness/WORKTREE-BOOTSTRAP.md`

### 当前意义

当前项目正式具备“不同执行 Agent 使用不同 worktree”的可执行入口，减少多 Agent 互相踩工作区的风险。

## 6. 交叉审查能力

### 来源能力

`CROSS-REVIEW-PROCESS.md`

### 当前项目落地

- `docs/02-engineering/harness/CROSS-REVIEW-PROCESS.md`

### 当前意义

对 L3/L4、Harness 机制改动、PRD/roadmap/closeout 规则改动建立正式审查要求。

## 7. 通用多 Agent 调度能力

### 来源能力

`HAGENT-WORKFLOW.md`

### 当前项目落地

- `docs/02-engineering/harness/HAGENT-WORKFLOW.md`

### 当前意义

把“如何拆分、谁负责、何时 review、何时 closeout”固化为仓库规则，并明确 HermesAgent 是运营验收 lane，而不是第二开发 lane。

## 三、与 Hermes 专用机制的结合方式

通用 Harness 迁入后，当前项目形成如下执行顺序：

1. 从 `AGENTS.md` 进入
2. 读取 `docs/02-engineering/harness/HARNESS-ENTRY.md`
3. 根据任务需要，遵守：
   - `HAGENT-WORKFLOW.md`
   - `CROSS-REVIEW-PROCESS.md`
   - `WORKTREE-BOOTSTRAP.md`
4. 如果任务涉及 HermesAgent 协作：
   - 写 runtime state snapshot
   - 生成 Hermes handoff packet
   - 由 HermesAgent 做运营复核
5. closeout 时：
   - 更新 PRD / roadmap / docs
   - 写 success/failure trace
   - 必要时运行 critic

## 四、当前项目中的实际落点

这套机制在当前项目里不再是抽象规则，而是实际对应到以下产品工作：

- PRD 与路线图维护
- WebUI IA 收敛
- 架构展示页接入
- `Codex ↔ HermesAgent` 交接
- runtime signal 暴露
- operator-facing 能力验收

## 五、当前结论

`FlowMindDeploy` 的 Harness 机制已经在当前项目中完成“共享执行基础设施”的迁移。

当前 CrazyAgentsManage 具备了：

- repository-owned 的执行计划层
- repository-owned 的 success/failure trace 层
- critic 自学习层
- closeout writeback 层
- worktree bootstrap 层
- 与 `Codex ↔ HermesAgent` 专用协作层并存的清晰分层

下一步重点不再是“有没有 Harness”，而是“是否强制在每轮非平凡迭代中真正使用这套 Harness”。
