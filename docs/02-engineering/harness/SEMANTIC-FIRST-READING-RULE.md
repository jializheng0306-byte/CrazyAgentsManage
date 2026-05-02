# Semantic-First Reading Rule

## 目的

当任务涉及以下任一对象或流程时：

- `candidate`
- `promise`
- `truth`
- `trace`
- `review`
- `feedback`

不要直接从页面代码、脚本、Bitable 字段或群聊记录开始。  
先进入语义与协同规则层，再决定是否下钻到宿主平台运行态和原始实现。

这条规则要解决的不是“搜索太慢”，而是三类偏差：

1. 双仓与宿主平台之间对同一对象口径不一致
2. runtime truth、operations truth、canonical truth 被混写
3. 直接在原始实现中找答案，跳过了语义主键、契约边界与宿主平台事实层

## 三层读取顺序

### 第 1 层：语义与契约层

优先读取：

1. [轻量本体DSL规范-v0-2026-05-02.md](/home/flowmind/FlowMindDeploy/docs/01-product/轻量本体DSL规范-v0-2026-05-02.md)
2. [下一阶段任务规划-2026-05-02.md](/home/flowmind/FlowMindDeploy/docs/01-product/下一阶段任务规划-2026-05-02.md)
3. [Graphify-轻量本体方案借鉴评估-2026-05-02.md](/home/flowmind/FlowMindDeploy/docs/01-product/Graphify-轻量本体方案借鉴评估-2026-05-02.md)
4. [hermes-flowmind-compatibility-matrix-2026-04-30.md](/home/flowmind/CrazyAgentsManage/docs/02-engineering/harness/hermes-flowmind-compatibility-matrix-2026-04-30.md)
5. [hermes-flowmind-link-manifest-v1.json](/home/flowmind/CrazyAgentsManage/docs/02-engineering/harness/hermes-flowmind-link-manifest-v1.json)

这一层回答：

- 该对象的稳定名字与边界是什么
- 哪些状态只是 candidate，哪些已经进入 truth 可读面
- 哪些通道是正式支持的，哪些仍是 partial/incompatible

### 第 2 层：双仓产品与协同层

优先读取：

1. [HermesAgent-FlowMind-联合产品功能基线-2026-04-30.md](/home/flowmind/CrazyAgentsManage/docs/roadmap/HermesAgent-FlowMind-联合产品功能基线-2026-04-30.md)
2. [prd-execution-roadmap.md](/home/flowmind/CrazyAgentsManage/docs/roadmap/prd-execution-roadmap.md)
3. [hermesagent-hosted-flowmind-product-foundation.md](/home/flowmind/CrazyAgentsManage/docs/prd/hermesagent-hosted-flowmind-product-foundation.md)
4. [HERMES-FLOWMIND-双仓协同治理方案-2026-04-30.md](/home/flowmind/CrazyAgentsManage/docs/02-engineering/harness/HERMES-FLOWMIND-双仓协同治理方案-2026-04-30.md)

这一层回答：

- 当前产品主线怎样解释这些对象
- 双仓里哪一侧是语义、治理、展示或回写的权威方
- 当前 UI/运营面到底在消费什么状态

### 第 3 层：Hermes 宿主平台运行与运营层

如果任务还涉及 HermesAgent 实际运行、技能、cron、Bitable 留痕或运营流程，再读：

1. [operations-manual.md](/home/flowmind/CrazyAgentsManage/docs/06-agent-ops/operations-manual.md)
2. [daily-workflow.md](/home/flowmind/CrazyAgentsManage/docs/06-agent-ops/daily-workflow.md)
3. [agent-ops-skill-taxonomy.md](/home/flowmind/CrazyAgentsManage/docs/06-agent-ops/agent-ops-skill-taxonomy.md)
4. [hermes-agent-operations-design.md](/home/flowmind/CrazyAgentsManage/docs/06-agent-ops/hermes-agent-operations-design.md)
5. [HERMESAGENT-ENTRY.md](/home/flowmind/CrazyAgentsManage/docs/02-engineering/harness/HERMESAGENT-ENTRY.md)

这一层回答：

- Hermes 宿主平台真正有哪些运行入口与技能
- 哪些事实来自 cron、skills、Bitable、runtime 目录
- 哪些只是设计稿，而不是现网运行事实

### 第 4 层：原始实现层

只有前三层不足以回答问题时，再读：

- WebUI 页面代码
- Python/脚本实现
- API route
- runtime snapshot
- logs
- 群聊消息

## 触发规则

出现以下任一情况时，必须使用这条顺序：

1. 任务提到 `candidate / promise / truth / trace / review / feedback`
2. 任务涉及 HermesAgent × CrazyAgentsManage × FlowMind 的跨端状态判断
3. 任务要区分 runtime truth、operations truth、canonical truth
4. 任务需要决定是否应更新 Bitable、timeline、Tech Radar、review queue 或 feedback 状态

## 允许直接读原始实现的情况

以下情况可以跳过前置层：

1. 纯前端视觉改动，不涉及上述语义对象
2. 纯脚本语法修复，不涉及状态边界
3. 孤立机械性测试修复

## 一句话规则

> 涉及 `candidate / promise / truth / trace / review / feedback` 时，先读语义与契约，再读双仓产品事实，再读 Hermes 宿主平台运行层，最后才读原始实现。
