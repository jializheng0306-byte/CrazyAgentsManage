# 外部 UI 重构团队提示词

请先同步 CrazyAgentsManage 当前活跃分支，再按仓库文档顺序阅读并开始评估。

## 拉取最新版本

```bash
git clone https://github.com/jializheng0306-byte/CrazyAgentsManage.git
cd CrazyAgentsManage
git fetch --all --prune
git checkout feat/auto-capture-trace
git pull --ff-only origin feat/auto-capture-trace
```

## 必读顺序

1. `docs/ui-design/external-ui-redesign-handoff-2026-05-03.md`
2. `docs/prd/hermesagent-hosted-flowmind-product-foundation.md`
3. `docs/prd/technical-implementation-prd.md`
4. `docs/prd/operations-implementation-prd.md`
5. `docs/prd/pages/overview-page-prd.md`
6. `docs/prd/pages/runtime-page-prd.md`
7. `docs/prd/pages/operations-page-prd.md`
8. `docs/prd/pages/governance-page-prd.md`
9. `docs/prd/pages/collaboration-page-prd.md`
10. `docs/prd/pages/architecture-visualization-pages-prd.md`
11. `docs/prd/pages/webui-route-template-alignment.md`
12. `docs/roadmap/HermesAgent-FlowMind-联合产品功能基线-2026-04-30.md`
13. `docs/roadmap/prd-execution-roadmap.md`
14. `docs/roadmap/master-task-plan.md`
15. `docs/ui-design/06-high-fidelity-designs.md`

## 你们需要先理解的事实

1. `CrazyAgentsManage` 当前不是一个通用多 Agent playground，而是：
   - `一个以 HermesAgent 为宿主的 FlowMind 运营产品`
2. UI 的一级 IA 已经固定：
   - `Overview`
   - `Runtime`
   - `Operations`
   - `Governance`
   - `Collaboration`
3. 当前仓库已经存在这些正式产品页和对应过渡模板：
   - `overview.html`
   - `runtime.html`
   - `operations.html`
   - `governance.html`
   - `collaboration.html`
   - `timeline.html`
4. 当前 live 部署副本与仓库基线并非完全一致，因此不要直接把线上页面当唯一真相

## 你们的任务

请基于当前仓库文档和代码，对 Crazy WebUI 做一次正式 UI 重构方案评估，并输出：

1. 现有信息架构是否合理
2. 五个一级 IA 是否还需要调整
3. 当前页面层级、导航、状态表达、布局、交互的主要问题
4. 哪些页面适合先做、哪些页面适合后做
5. 一个分阶段的 UI 重构实施方案
6. 哪些 FlowMind / Hermes 联动契约必须保持不变

## 明确约束

1. 不要把产品重新定义成“另一个智能体控制台”
2. 不要破坏 `/api/bridge/trace/:candidateId` 的 timeline 数据消费主路径
3. 不要破坏 `moduleDetails.handoff` 的 handoff 数据消费主路径
4. 不要破坏 `BASE` 感知的静态资源与链接生成
5. 不要把重构方案建立在“改后端语义”之上，优先做信息架构、视觉和前端交互层重构

## 期望输出格式

请按以下结构回复：

### 1. 总体判断
- 当前产品定位是否清楚
- 当前 IA 是否清楚
- 当前 UI 最大的问题是什么

### 2. 分区评审
- Overview
- Runtime
- Operations
- Governance
- Collaboration
- Architecture Pages

### 3. 分阶段重构建议
- Phase 1
- Phase 2
- Phase 3

### 4. 不可破坏项
- 列出必须保持的产品契约和技术契约

### 5. 进入实施前还缺什么
- 缺失信息
- 需要补看的文档
- 需要确认的运行事实
