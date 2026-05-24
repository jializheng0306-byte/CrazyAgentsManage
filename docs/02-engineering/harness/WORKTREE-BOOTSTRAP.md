# Worktree Bootstrap

将“每个开发 Agent 独立 worktree”从原则变成可执行流程。

## 1. 原则

- `branch` 表示 lane
- `worktree` 表示 agent runtime
- 同一时刻不要让多个开发 Agent 共用同一个执行 worktree

## 2. 适用对象

- `codex`
- `claude`
- `qoder`
- `codebuddy`
- 其他兼容 CLI agent

## 3. 推荐映射

| Agent | 推荐 lane | 推荐 branch 形态 |
|---|---|---|
| codex | `codex/*`、`shared/*`、`docs/*` | `codex/<topic>` |
| claude | `shared/*`、`docs/*` | `shared/<topic>` |
| 其他 CLI agent | `shared/*`、`docs/*`、`ops/*` | `<lane>/<topic>` |

说明：

- `HermesAgent` 不是常规编码 lane，因此通常不需要独立开发 worktree
- 如果需要为运营复核准备独立工件整理环境，可使用 `ops/<topic>` 或 `shared/<topic>`

## 4. 脚本入口

使用脚本：

[scripts/worktree/create-agent-worktree.sh](/home/flowmind/CrazyAgentsManage/scripts/worktree/create-agent-worktree.sh)

### 示例

```bash
scripts/worktree/create-agent-worktree.sh --agent codex --lane codex --topic runtime-alignment
scripts/worktree/create-agent-worktree.sh --agent claude --lane shared --topic harness-review
scripts/worktree/create-agent-worktree.sh --agent qoder --lane docs --topic page-prd-pass
```

## 5. 命名约定

脚本默认生成：

- branch: `<lane>/<topic>`
- worktree path: `../CrazyAgentsManage-<agent>-<lane>-<topic>`
- runtime-local metadata: `.omx/worktree-context.json`

## 6. 进入顺序

### Codex / OMX

1. 进入 worktree
2. 读取 `AGENTS.md`
3. 再转入 canonical harness core

### 其他 Agent

1. 进入 worktree
2. 读取对应 adapter 入口
3. 再转入 canonical harness core

## 7. 私有状态规则

每个 worktree 内允许存在 Agent 私有目录，例如：

- `.codex/`
- `.omx/`
- `.claude/`
- `.codebuddy/`

但这些目录：

1. 只能服务于当前 worktree 的当前 Agent
2. 不能作为跨 Agent 协作接口
3. 不得替代受追踪仓库工件

## 8. 共享输出规则

需要被别的 Agent 或团队消费的内容必须写入：

- `docs/`
- `harness/`
- 受追踪源码与配置

而不是留在 Agent 私有目录中。
