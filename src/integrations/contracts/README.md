# FlowMind Cross-Repo Contracts (GENERATED)

> **GENERATED — DO NOT EDIT MANUALLY.** 本目录所有文件由 FlowMindDeploy 仓生成器产出。

## 生成源

- **Canonical 源**: FlowMindDeploy `packages/ontology/semantic-dsl/objects/crazy.*.md`
- **生成器**: `packages/ontology/src/generators/cross-repo-contract-generator.ts`
- **重新生成**: `pnpm --filter @flowmind/ontology build && pnpm --filter @flowmind/ontology generate:contracts`
- **方向**: FMD 生成 → Crazy 消费（不可逆，AGENTS.md 决策树 7）

## 目录结构

```
contracts/
├── schemas/
│   ├── crazy_agent_task.schema.json   # crazy.agent_task JSON Schema
│   ├── crazy_promise.schema.json      # crazy.promise JSON Schema
│   └── crazy_trace_event.schema.json  # crazy.trace_event JSON Schema
├── dataclasses/
│   └── flowmind_contracts.py          # Python @dataclass(kw_only=True) + AccessPolicy 嵌套
├── README.md                           # 本文件（生成物说明 + isDefinedBy 声明）
└── .generated-marker                   # 生成物标记（禁止手改）
```

## isDefinedBy 声明

本目录契约的 `isDefinedBy ∈ {flowmind, team, host_pimo}`：

| 契约 | isDefinedBy | evidence_class |
|------|-------------|----------------|
| `crazy.agent_task` | flowmind | INFERRED |
| `crazy.promise` | flowmind | INFERRED |
| `crazy.trace_event` | flowmind | EXTRACTED |

## 守卫

- **Invariant 1**: 契约不裁定 `truth.status`（crazy.* 为 `cross_repo_reference`，不进 truth kernel）
- **Invariant 2**: `evidence_class` 透传不改写
- **Invariant 3**: 只读消费，不发明新 truth（`.generated-marker` 禁手改）
- **R13**: `accessPolicy.allowStateDecision` 透传（TaskTransmission 守卫）

## 消费方式

```python
from src.integrations.contracts.dataclasses.flowmind_contracts import (
    AgentTask, Promise, TraceEvent, AccessPolicy
)
```

## CI 校验

FMD 仓 CI 通过 `scripts/governance/check_cross_repo_contract_diff.py` 执行字段级 diff：
- Layer 1（常绿 self-check）：FMD DSL vs FMD `generated/` 一致性
- Layer 2（跨仓 diff）：FMD `generated/` vs Crazy `contracts/schemas/` 一致性（counterpart 不可用时 warn 非 fail）

## 消费面现状

Crazy 仓现有 `src/integrations/flowmind_*.py` 为 FlowMind API 调用模块（truth-query / candidate-ingress / review-trigger / webhook）。其 payload 构造属 API 载荷，非 crazy.* 契约结构。`flowmind_*.py` 通过 `TYPE_CHECKING` 守卫导入 dataclass 建立类型层面的消费关系；未来 Crazy 仓需构造 crazy.* 数据时，应直接实例化本目录 dataclass，禁止手写 dict。

## PIMO-TMO 边界引用

本目录契约的 PIMO 三层域边界定义见：
- **Canonical 源**: FMD `packages/ontology/semantic-dsl/contexts/pimo.domain_boundary.md`
- **Crazy 仓总览**: `AGENTS.md` § PIMO-TMO Domain Boundary (FR109)

三条跨层跃迁规则（详细语义见 canonical 源）：
1. host→repo 须人审（host_pimo 数据经人类 Review 形成 proposal）
2. repo→canonical 须 truth promotion（approve/commit）
3. host 直跳 canonical 禁止（必须先经 repo_side）

本目录契约 `isDefinedBy: flowmind`，Crazy 仓只读消费，不参与跨层跃迁裁定。
