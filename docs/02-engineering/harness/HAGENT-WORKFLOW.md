# HAGENT Workflow

多 Agent 协作的调度规范。

## 1. 角色

| 角色 | 职责 | 是否写代码 |
|---|---|---|
| Coordinator | 规划、拆分、汇总、裁决 | 视情况，默认否 |
| Executor | 实施、验证、修复 | 是 |
| Reviewer | 交叉审查与风险识别 | 否 |
| Operator Reviewer | 运营视角复核与验收 | 否 |

在 CrazyAgentsManage 中，默认映射为：

- `Codex` 常同时承担 `Coordinator + Executor`
- `HermesAgent` 承担 `Operator Reviewer`
- 如需额外审查，可引入 `Reviewer`

## 2. 核心规则

1. 协调者必须先明确任务边界，再决定是否拆分。
2. 不同执行 Agent 不共享同一 worktree。
3. 每个执行输出都要回写成受追踪工件或可验证代码变更。
4. 审查视角不能与实现上下文完全重叠。
5. HermesAgent 不作为第二编码 lane，而作为运营验收 lane。

## 3. 复杂度分级

| 级别 | 特征 | 建议 |
|---|---|---|
| L1 | 单文件、小改动 | 单 Agent 可完成 |
| L2 | 单模块、少量文件 | 单 Agent + 轻量 review |
| L3 | 多文件或跨层改动 | 独立 worktree + review |
| L4 | 架构、协作协议、跨边界高风险改动 | 独立 worktree + exec plan + 强制 review |

## 4. 推荐流程

1. 读取需求、PRD、roadmap 与 harness 边界
2. 判断是否需要新增或更新 `harness/exec-plans/`
3. 判断任务级别 L1-L4
4. 如需并行执行，为不同执行 Agent 分配独立 worktree
5. 执行实现并完成验证
6. 通过 `harness-closeout-writeback` 写入 success / failure trace 与 closeout artifact，并记录 worktree lane
7. 不要把 `record-success.cjs` / `record-failure.cjs` 当成非平凡迭代的 direct closeout 入口
8. 必要时由 HermesAgent 做运营验收或由 Reviewer 做交叉审查
9. closeout 时更新 `docs/`、`harness/` 与 roadmap
10. 如失败模式重复出现，回写 `harness/memory/`

## 5. CrazyAgentsManage 特殊要求

### Codex

- 通过 `AGENTS.md` 进入
- 再转到 canonical harness core
- 负责实现、验证、仓库事实更新

### HermesAgent

- 通过 `HERMESAGENT-ENTRY.md` 接收 handoff
- 从运营视角反馈 runtime gap、operations gap、missing signal、missing action

### 其他 CLI Agent

- 必须先进入仓库级 adapter，再进入 canonical harness core
- 不得把私有状态目录当成共享事实来源

## 6. 禁止模式

- 多个开发 Agent 共用一个 worktree
- 把 `.omx/`、`.codex/` 等私有目录当成共享事实来源
- HermesAgent 直接改写实现架构作为常规路径
- 未 closeout 就把 chat-only 结论当成仓库事实
