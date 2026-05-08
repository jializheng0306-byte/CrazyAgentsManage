# CrazyAgentsManage Collaboration 页面 PRD

## 版本信息

| 字段 | 值 |
|------|-------|
| 产品 | CrazyAgentsManage |
| 文档类型 | 页面级 PRD / Collaboration |
| 版本 | v0.1.0 |
| 状态 | Draft |
| Owner | Codex |
| 最后更新 | 2026-04-27 |

## 页面目标

`Collaboration` 页面负责让用户看见 Codex / HermesAgent 协作链路是否真正闭环。

它要回答：

- handoff 发起了什么
- HermesAgent 是否完成 review / acceptance
- closeout 是否形成仓库事实
- 哪条协作链路还没有闭环

## 继承关系

本文档继承：

- `docs/prd/collaboration-workflow-implementation-prd.md`
- `docs/prd/collaboration-operator-workflow-prd.md`

## 页面应承载的核心信息

### 1. Handoff 列表

内容：

- handoff 标题
- 目标
- artifacts
- 状态

### 2. Runtime Snapshot

内容：

- phase
- status
- actor
- summary

### 3. Closeout Evidence

内容：

- closeout 记录
- 是否回写 PRD / roadmap / 文档
- 缺失 writeback 提示
- 如需组合治理结论，按 shared 治理证据顺序展示：
  - change record
  - deploy fact
  - acceptance / eval
  - closeout seed
  - governance report

### 4. 协作链路图

内容：

- handoff
- snapshot
- closeout
- repo truth
- 闭环缺口

## 页面信息架构

建议页面结构自上而下为：

1. handoff 列表区
2. runtime snapshot 区
3. closeout evidence 区
4. 协作链路图区

## 页面模块树

- CollaborationPage
  - HandoffListPanel
  - RuntimeSnapshotPanel
  - CloseoutEvidencePanel
  - CollaborationGraphPanel

## 关键交互

- 从 handoff 跳到相关 artifact
- 从 snapshot 跳到当前轮次详情
- 从 closeout 跳到仓库事实文档
- 从链路图跳到技术架构展示页

## 依赖来源

- handoff surface
- runtime snapshot surface
- closeout evidence surface
- collaboration operator workflow

## 非目标

本文档不定义：

- 群聊消息格式
- tmux 操作细节
- 页面字段级原型

## 完成标准

1. 协作闭环可以作为页面级体验被直接检查
2. 用户能发现“做了但没闭环”的链路
3. 页面可作为 `TechArchitecturePreviewPage` 的协作详情依托
