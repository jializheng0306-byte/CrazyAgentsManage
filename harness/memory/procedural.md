# Procedural Memory

## Initial rules

1. Codex writes a runtime snapshot before asking HermesAgent to act.
2. Codex generates a structured handoff packet before any `@HermesAgent` collaboration step.
3. Durable process lessons must be promoted from `.omx/` to `harness/`.
## 20260426T004218Z — validated round

- Stage: role-discussion-closeout
- Message: Role split and collaboration mechanism fully accepted; future work moves to implementation and operational acceptance
- Artifacts: docs/codex-hermes-role-design.md, docs/02-engineering/harness/CODEX-HERMES-COLLABORATION-MECHANISM.md

## 20260502T090000Z — auto-capture-trace post-hook deployed

- Stage: implementation
- Artifacts added:
  - `~/.hermes/rules/intent-analysis-rules.json` — 意图分析规则文件
  - `scripts/auto-trace-to-bitable.py` — 自动捕获分析入口
  - `scripts/send-capture-trace-to-feishu.py` — 飞书三通道留痕函数
  - `docs/06-agent-ops/auto-capture-config-guide.md` — 配置指南
- Changed: `AGENTS.md` — 增加 Auto-Capture Trace 后置步骤
- Contract: 自动化边界在 Bitable value item，FlowMind ingress 保留人工闸门
- Follow-up: 配置 BITABLE_APP_TOKEN/TABLE_ID 环境变量后激活 Bitable 写入
