# Agent Constitution Pattern 落地记录

> 来源：Garry Tan (YC CEO) 的 agent 三层文件结构
> Tech Radar 条目：Agent Constitution Pattern (SOUL.md/USER.md/AGENTS.md)
> 优先级：P1
> 状态：✅ 已落地

---

## 原始发现

Garry Tan 将 agent 人格拆分为三层文件：
- **SOUL.md** — 声音/价值观（agent 的核心身份）
- **USER.md** — 用户模型（agent 对用户的理解）
- **AGENTS.md** — 执行规则（agent 的操作规范）

此模式直接适用于 HermesAgent 记忆系统的分层架构，可替代当前单一 prompt 堆叠方式。

## 我们的落地方式

### 1. 创建 Agent 独立身份目录

```
soul/agents/
├── README.md                          — Agent 注册表
├── intel-sentinel/
│   ├── SOUL.md                        — 情报哨兵身份定义
│   └── learnings/
│       ├── ERRORS.md                  — 错误记录
│       ├── LEARNINGS.md               — 经验教训
│       └── FEATURE_REQUESTS.md        — 功能需求
├── promise-keeper/
│   ├── SOUL.md                        — 承诺管家身份定义
│   └── learnings/ (同上)
└── ops-guardian/
    ├── SOUL.md                        — 运维卫士身份定义
    └── learnings/ (同上)
```

### 2. 每个 SOUL.md 的结构

对齐 Garry Tan 的三层模式：

| Garry Tan 层 | 我们的实现 | 文件 |
|-------------|-----------|------|
| SOUL.md (声音/价值观) | 身份定义 + 核心职责 + 绝对禁止 | `soul/agents/{agent}/SOUL.md` |
| USER.md (用户模型) | 决策框架（如何响应用户输入） | 内嵌在 SOUL.md 的"决策框架"章节 |
| AGENTS.md (执行规则) | 协作协议（与其他 Agent 的通信规则） | 内嵌在 SOUL.md 的"协作协议"章节 |

### 3. 与之前架构的对比

| 维度 | 之前 | 现在 |
|------|------|------|
| Agent 身份 | 唯一的 MEMORY.md，无角色区分 | 每个 Agent 有独立 SOUL.md |
| 学习空间 | 共享 .learnings/ | 每个 Agent 有独立 learnings/ |
| 协作规则 | 隐式（靠 prompt 切换） | 显式（SOUL.md 中的协作协议章节） |
| 注册表 | 不存在 | soul/agents/README.md |

### 4. 受影响的文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `soul/agents/README.md` | 新建 | Agent 注册表，定义职责边界 |
| `soul/agents/intel-sentinel/SOUL.md` | 新建 | 情报哨兵身份（情报采集+评估+Tech Radar） |
| `soul/agents/intel-sentinel/learnings/*.md` | 新建 | 情报哨兵学习空间 |
| `soul/agents/promise-keeper/SOUL.md` | 新建 | 承诺管家身份（承诺治理+状态追踪） |
| `soul/agents/promise-keeper/learnings/*.md` | 新建 | 承诺管家学习空间 |
| `soul/agents/ops-guardian/SOUL.md` | 新建 | 运维卫士身份（系统运维+Cron可观测性） |
| `soul/agents/ops-guardian/learnings/*.md` | 新建 | 运维卫士学习空间 |
| `scripts/memory_promote.py` | 新建 | 扫描所有 Agent 的 learnings/ 并 promote |

### 5. 下一步

- [ ] 评估是否需要独立的 USER.md 文件（当前内嵌在 SOUL.md 中）
- [ ] 评估是否需要独立的 AGENTS.md 文件（当前内嵌在 SOUL.md 中）
- [ ] 在实际 cron 运行中验证 Agent 独立身份的效果

---

落地日期：2026-04-29
执行者：HermesAgent
