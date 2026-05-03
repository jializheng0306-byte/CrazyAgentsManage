# UI Design — 对外交接入口

> 日期: 2026-05-03  
> 状态: 对外评估启动  
> 仓库视角: `CrazyAgentsManage`（HermesAgent 宿主运营产品）

---

## 这个目录做什么

把 CrazyAgentsManage WebUI 的当前实现状态、一级 IA、数据消费面整理为外部 UI 团队可评估的交接包。

**不是**替代 `docs/prd/` 下的页面 PRD，而是把 PRD 中的页面规格 + 当前 live 验证结果打包成外部可读的评估入口。

---

## 外部 UI 团队应先读哪两份

1. **[external-ui-redesign-handoff-2026-05-03.md](./external-ui-redesign-handoff-2026-05-03.md)**
   - 当前 IA 结构、页面清单、数据消费面、已知缺口

2. **[external-ui-redesign-team-prompt-2026-05-03.md](./external-ui-redesign-team-prompt-2026-05-03.md)**
   - 评估目标、交付要求、判断标准、不做什么

---

## 补充参考（仓库内已有）

| 文档 | 路径 | 用途 |
|---|---|---|
| 页面 PRD（6 页） | `docs/prd/pages/*.md` | 每个页面的正式需求规格 |
| 上位产品基础文档 | `docs/prd/hermesagent-hosted-flowmind-product-foundation.md` | 一级 IA + 产品定位 |
| 运营实现 PRD | `docs/prd/operations-implementation-prd.md` | operator personas + 运营表面 |
| 技术实现 PRD | `docs/prd/technical-implementation-prd.md` | 前后端边界 + 数据契约 |
| WebUI README | `src/webui/README.md` | 设计系统（颜色/字体/断点/无障碍） |
| 联合产品基线 | `docs/roadmap/HermesAgent-FlowMind-联合产品功能基线-2026-04-30.md` | 双仓产品镜像 |

---

## 当前对外评估状态

- **评估启动时间**: 2026-05-03
- **交接文档包**: 本目录下的 handoff + team-prompt
- **评估方**: 外部 UI 团队
- **当前阶段**: 已发出评估请求，等待外部团队反馈
