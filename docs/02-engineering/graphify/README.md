# Graphify 知识图谱自动查询机制

## 一句话说明

Graphify 是一个将 **代码 AST + 聊天档案 + Tech Radar** 融合为统一知识图谱的系统。它通过 MCP（Model Context Protocol）以常驻服务的方式嵌入 HermesAgent，在执行任何涉及 FlowMind / CrazyAgentsManage 的任务时，Agent 可以**主动**查询图谱来理解架构关系、追踪影响范围、发现隐藏关联。

---

## 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                          HermesAgent                                │
│                                                                     │
│  ┌──────────────┐    MCP Protocol (stdio)     ┌──────────────────┐ │
│  │  MCP Client  │◄──────────────────────────►│  graphify.serve  │ │
│  │              │                             │  (知识图谱服务)    │ │
│  │  自动发现     │                             │                  │ │
│  │  7 个查询工具 │                             │  读取并索引       │ │
│  │              │                             │  knowledge-      │ │
│  │              │                             │  base.json       │ │
│  └──────┬───────┘                             └────────┬─────────┘ │
│         │                                              │           │
│         │  query_graph / get_node /                    │           │
│         │  get_neighbors / shortest_path / ...         │           │
│         ▼                                              ▼           │
│  ┌──────────────────┐                    ┌───────────────────────┐ │
│  │ 常规工具          │                    │  knowledge-base.json   │ │
│  │ search_files     │                    │  (5.1 MB, ~1500 节点) │ │
│  │ read_file        │                    │                       │ │
│  │                  │                    │  ◄── 每周日 02:00      │ │
│  │ 代码级查询        │                    │      cron 自动重建    │ │
│  └──────────────────┘                    └───────────────────────┘ │
│                                                                     │
│                                        ┌─────────────────────────┐ │
│  ┌──────────────────────┐              │  网页可视化               │ │
│  │  data sources:        │              │  http://47.99.217.1      │ │
│  │  ├─ CrazyAgentsManage │              │  /graph/                 │ │
│  │  ├─ FlowMindDeploy    │              │  (vis-network 交互图)    │ │
│  │  ├─ 聊天档案 (双群)    │              └─────────────────────────┘ │
│  │  └─ Tech Radar        │                                         │
│  └──────────────────────┘                                          │
└─────────────────────────────────────────────────────────────────────┘
```

### 数据流

```
聊天消息 (双飞书群) ──┐
代码仓库 (AST 提取) ──┼──► graphify extract ──► knowledge-base.json
Tech Radar 条目 ─────┘                              │
                                                    ▼
                                           graphify.serve (MCP)
                                                    │
                                     ┌──────────────┼──────────────┐
                                     ▼              ▼              ▼
                              HermesAgent    Cron 定时重建    Web 可视化
                              (自动查询)     (每周日 02:00)   (vis-network)
```

---

## 双层知识基座设计

### 为什么是「双层」

传统的知识库要么是**代码索引**（只能搜符号），要么是**文档库**（只能搜文字）。我们的项目同时存在两种截然不同的「知识」：

| 层次 | 载体 | 特点 | 例子 |
|------|------|------|------|
| **结构层**（代码 AST） | `.py` 源文件 → graphify 提取 | 精确、可执行、有明确依赖关系 | `MemoryCapsule._write()` 调用 `sqlite3.execute()` |
| **语义层**（运营上下文） | 聊天记录 + Tech Radar → 主题提取 | 模糊、叙事性强、承载决策理由 | "上周讨论过 Memory 存储应该用 SQLite 而非 JSON" |

**这两层必须融合才产生价值：**

- 只有代码 → 你看到 `MemoryCapsule` 有 SQLite 调用，但不知道为什么选 SQLite
- 只有聊天 → 你知道"决定用 SQLite"，但找不到对应的代码在哪里
- **两层叠加** → 你点开 `MemoryCapsule` 节点，图谱同时显示它的代码依赖 + 关联的讨论上下文 + 技术雷达中关于存储方案的评估，形成**完整认知**

### 基座如何构建

```
┌──────────────────────────────────────────────────────┐
│                    双层数据注入                        │
│                                                      │
│  结构层（代码）                                       │
│  ┌──────────────────────────────┐                    │
│  │ CrazyAgentsManage/ (Python)  │──┐                 │
│  │ FlowMindDeploy/    (Python)  │  │                 │
│  └──────────────────────────────┘  │                 │
│                                     ▼                 │
│                            graphify extract          │
│                            (AST → 函数/类/文件节点)    │
│                                     │                 │
│  语义层（运营上下文）                  │                 │
│  ┌──────────────────────────────┐  │                 │
│  │ 聊天档案 (每周增量归档)        │──┤                 │
│  │ Tech Radar (技术趋势 JSON)     │──┤                 │
│  └──────────────────────────────┘  │                 │
│                                     ▼                 │
│                             主题提取 + 实体链接        │
│                             (chat_topic / radar_item)  │
│                                     │                 │
│                                     ▼                 │
│                          knowledge-base.json          │
│                          (统一节点-边图，~1500节点)     │
│                                     │                 │
│                    ┌────────────────┼────────────────┐ │
│                    ▼                ▼                ▼ │
│             MCP 查询服务       Web 可视化         cron │
│           (graphify.serve)  (vis-network)    (每周重建)│
└──────────────────────────────────────────────────────┘
```

### 双层之间的连接方式

knowledge-base.json 中，两层节点通过 **边（edge）** 连接：

| 边类型 | 含义 | 示例 |
|--------|------|------|
| `calls` | 函数调用关系 | `router.py` → `capsule.py`（结构层内） |
| `imports` | 模块导入关系 | `governance.py` → `ontology.py`（结构层内） |
| `contains` | 文件包含关系 | `core/` 目录 → 其中的所有文件（结构层内） |
| `discusses` | 聊天涉及某个代码概念 | 聊天节点 → 代码文件/函数节点（跨层） |
| `references` | Radar 条目关联某个模块 | Radar 节点 → 代码文件节点（跨层） |
| `related_to` | 语义关联 | 两个聊天主题因共现关键词而关联（语义层内） |

**关键洞察：** `discusses` 和 `references` 是跨层边——它们让「为什么这样设计」和「代码怎么实现的」连在了一起。当 Agent 调用 `query_graph("ontology")` 时，返回的不仅是 ontology 的代码节点，还包括：
- 讨论过 ontology 的聊天片段（`discusses` 边）
- 技术雷达中对 ontology 的评估（`references` 边）
- 相关文档和 PRD 引用

### 双层基座的典型查询模式

| 用户意图 | 查询入口 | 探测层次 | 典型链路 |
|----------|----------|----------|----------|
| "为什么用 SQLite？" | `query_graph("SQLite memory storage")` | 先从语义层找决策讨论 → 再追踪到结构层代码 | 聊天 `discusses` → `MemoryCapsule` → `calls` → `sqlite3` |
| "ontology 改了什么？" | `query_graph("ontology")` | 先从结构层找代码 → 再回溯到语义层看讨论 | `ontology.py` → `discusses` → 相关聊天 → `references` → Radar 评估 |
| "Memory 系统全貌" | `get_community(memory_社区ID)` | 两层一起拉取 | 社区内所有节点（代码 + 聊天 + Radar 混合） |
| "当前技术栈健康度" | `god_nodes()` + `graph_stats()` | 结构层指标 + 语义层信号 | PageRank 排名 + 社区分布 + 聊天讨论热度交叉分析 |

---

## MCP 工具详解

Graphify 通过 MCP 协议向 HermesAgent 暴露 **7 个原生查询工具**。每个工具都有明确的适用场景。

### 1. `query_graph` — 语义搜索节点

**最常用的入口工具**。用自然语言或关键词搜索图谱中的节点。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | ✓ | 搜索关键词或自然语言描述，如 `"ontology"`、`"promise governance capsule"` |
| `mode` | string | | 搜索模式：`"bfs"`（广度优先，默认）、`"dfs"`（深度优先）、`"semantic"`（语义匹配） |
| `max_depth` | integer | | BFS/DFS 最大遍历深度（默认 3） |
| `top_k` | integer | | 返回结果数量（默认 10） |

**典型调用：**

> Agent 内部调用 `query_graph(query="ontology 本体论 语义模型")`
>
> 返回与 ontology 相关的所有节点及其关联关系：
> - `CrazyAgentsManage/core/ontology/` 下的所有源文件
> - FlowMind 中引用 ontology 的 AST 节点
> - 聊天中提到 ontology 的对话片段
> - Tech Radar 中与 ontology 相关的技术条目

**适用场景：**
- 用户问「xxx 相关的代码有哪些」
- 用户问「哪些模块在处理 yyy」
- 接到任务后想了解某个概念在项目中的分布

---

### 2. `get_node` — 节点详情查询

获取单个节点的完整元数据。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `node_label` | string | ✓ | 节点标签（通常是文件名、函数名或概念名） |
| `include_edges` | boolean | | 是否一并返回该节点的所有边（默认 false） |

**返回信息：**

| 字段 | 说明 |
|------|------|
| `label` | 节点标签 |
| `type` | 节点类型：`file` / `function` / `class` / `chat_topic` / `radar_item` |
| `source_graph` | 来源：`crazy` / `flowmind` / `chat` / `radar` |
| `degree` | 连接度（有多少节点与之关联） |
| `community` | 所属社区编号 |
| `file_path` | 源代码路径（代码节点） |
| `priority` / `action` | Radar 节点的优先级和行动项（Radar 节点） |
| `extracted_topics` | 提取的主题标签（聊天节点） |

**典型调用：**

> `get_node(node_label="router.py")` → 获取 MemRouter 的完整信息
>
> 返回：type=file, source_graph=crazy, degree=47, community=3, file_path=core/router.py

**适用场景：**
- 想了解某个特定节点是什么
- 在搜索结果中看到了一个节点，想获取它的完整信息
- 判断某个文件/函数/概念的来源和重要性

---

### 3. `get_neighbors` — 关联节点遍历

获取某个节点的所有直接邻居（一跳关联节点）。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `node_label` | string | ✓ | 目标节点标签 |
| `direction` | string | | `"both"`（默认）/ `"in"` / `"out"` |
| `edge_types` | array | | 过滤边类型，如 `["calls", "imports", "contains"]` |
| `max_neighbors` | integer | | 最大返回数量（默认 20） |

**典型调用：**

> `get_neighbors(node_label="MemoryCapsule", direction="both", edge_types=["calls", "imports"])`
>
> 返回直接调用或导入 MemoryCapsule 的所有节点，以及 MemoryCapsule 调用或导入的节点。

**适用场景：**
- 修改一个模块前，想知道会影响哪些上下游模块
- 追踪某个函数被谁调用、调用了谁
- 理解一个文件/类的直接依赖关系

---

### 4. `shortest_path` — 最短路径查询

计算两个概念/节点之间的最短关联路径。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `source` | string | ✓ | 起点节点标签 |
| `target` | string | ✓ | 终点节点标签 |
| `max_hops` | integer | | 最大跳数（默认 6） |

**返回：** 路径上的节点序列 + 每跳的边类型。

**典型调用：**

> `shortest_path(source="ontology", target="governance")`
>
> 返回类似：`ontology → TopicExtractor → GovernanceSurface → promise → governance`
>
> 说明 ontology 通过 TopicExtractor 和 GovernanceSurface 间接关联到 governance 模块。

**适用场景：**
- 理解两个看似无关的模块之间的关联
- 追踪一个概念的传播路径
- 做影响分析时追溯间接依赖链

---

### 5. `get_community` — 社区批量获取

获取某个社区（Louvain 算法聚类的关联节点群）中的所有节点。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `community_id` | integer | ✓ | 社区编号（从 get_node 或 god_nodes 获取） |
| `top_k` | integer | | 返回前 K 个最重要的节点（默认 50） |

**典型调用：**

> `get_community(community_id=3)`
>
> 返回社区 3 中的所有节点（路由 + 消息处理相关模块）。

**适用场景：**
- 发现某个节点属于哪个"功能集群"
- 批量获取一个模块群的所有相关文件
- 理解项目的架构分层

---

### 6. `god_nodes` — 核心抽象排名

返回图谱中 **PageRank 最高** 的节点——即整个项目中最核心的抽象概念和关键文件。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `top_k` | integer | | 返回前 K 个（默认 20） |
| `filter_type` | string | | 过滤节点类型：`"file"` / `"function"` / `"class"` / `"chat_topic"` / `"radar_item"` |

**典型调用：**

> `god_nodes(top_k=10)`
>
> 返回类似：
> 1. `router.py` (degree=89, community=3)
> 2. `consume_feedback.py` (degree=76, community=5)
> 3. `capsule.py` (degree=72, community=3)
> ...

**适用场景：**
- 新成员想快速了解项目的核心模块
- 做架构评审时确认核心抽象是否健康
- 想知道哪些文件/函数是"绝对不能动"的

---

### 7. `graph_stats` — 图谱统计

返回全局统计信息。

**参数：** 无

**返回：**

| 字段 | 说明 |
|------|------|
| `total_nodes` | 节点总数 |
| `total_edges` | 边总数 |
| `communities` | 社区数量 |
| `by_type` | 按节点类型统计：`{"file": 800, "function": 400, ...}` |
| `by_source` | 按来源统计：`{"crazy": 600, "flowmind": 300, ...}` |
| `density` | 图密度 |
| `avg_degree` | 平均度 |
| `top_communities` | 最大的社区及其节点数 |

**适用场景：**
- 确认图谱是否是最新数据
- 了解项目规模和复杂度
- 健康检查

---

## 三层次查询体系：工具协同的完整逻辑

### 为什么需要三层

单一工具无法覆盖 Agent 在执行任务时的全部信息需求。不同的信息密度和查询意图，需要不同粒度的工具。三层之间并非互相替代，而是**从具体到抽象、从细节到全景**的递进关系。

### 层次定义

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   信息密度低（具体文件、具体行）                                    │
│   ┌──────────────────────────────────────────────────┐          │
│   │  代码级                                           │          │
│   │  search_files / read_file / execute_code          │          │
│   │                                                   │          │
│   │  输入：文件路径 + 行号                              │          │
│   │  输出：精确的代码内容                                │          │
│   │  Q: "这个函数具体怎么写的？"                         │          │
│   │  A: 第 42 行开始，用了 sqlite3.execute()            │          │
│   └──────────────────────────────────────────────────┘          │
│                         │                                        │
│                         ▼                                        │
│   信息密度中（模块关系、影响范围）                                   │
│   ┌──────────────────────────────────────────────────┐          │
│   │  架构级                                           │          │
│   │  query_graph / get_neighbors / shortest_path      │          │
│   │  get_community / god_nodes / get_node /           │          │
│   │  graph_stats                                      │          │
│   │                                                   │          │
│   │  输入：概念/模块名 + 关系类型                        │          │
│   │  输出：关联节点图谱 + 社区归属 + 影响路径             │          │
│   │  Q: "修改 ontology 会影响哪些模块？"               │          │
│   │  A: governance, capsule, router (通过 discusses    │          │
│   │     和 imports 边关联)，间接影响 17 个文件           │          │
│   └──────────────────────────────────────────────────┘          │
│                         │                                        │
│                         ▼                                        │
│   信息密度高（趋势判断、优先级决策）                                 │
│   ┌──────────────────────────────────────────────────┐          │
│   │  趋势级                                           │          │
│   │  tech-radar.json + radar_item 节点                │          │
│   │  + god_nodes (PageRank) + graph_stats (规模)      │          │
│   │                                                   │          │
│   │  输入：技术领域 + 时间范围                           │          │
│   │  输出：优先级排序 + 成熟度评估 + 行动建议             │          │
│   │  Q: "当前最应该重构的模块是哪个？"                   │          │
│   │  A: MemRouter (PageRank=89 / radar 标记为          │          │
│   │     adopt→reassess / 被 47 个节点依赖)              │          │
│   └──────────────────────────────────────────────────┘          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 三层之间的数据流和触发关系

三层不是静止的分类，而是在 Agent 执行任务时**动态串联**的：

```
用户提问：「promise governance 的实现是否完整？」
  │
  ▼
【架构级 — 先了解全局】
  query_graph("promise governance")
  → 返回 23 个相关节点（代码 14 个 + 聊天 7 个 + Radar 2 个）
  → 发现核心文件是 governance/surface.py
  │
  ▼
【趋势级 — 判断优先级背景】
  get_node("governance-surface") → type=radar_item, priority=P0, action=adopt
  get_node("promise-capsule")     → type=radar_item, priority=P1, action=hold
  → 结论：governance 是高优推动中，promise 在观望
  │
  ▼
【架构级 — 追踪影响范围】
  get_neighbors("governance/surface.py", edge_types=["calls", "imports", "discusses"])
  → 直接依赖：capsule.py, consume_feedback.py, router.py
  → 聊天讨论：3 条（讨论过 surface 的 API 设计）
  │
  ▼
【代码级 — 深入验证】
  search_files(pattern="class GovernanceSurface", path="/root/CrazyAgentsManage")
  read_file(path="governance/surface.py", offset=1, limit=100)
  → 确认实现：有 __init__, process, validate 三个方法
  │
  ▼
【架构级 — 交叉验证】
  shortest_path("governance/surface.py", "promise/capsule.py")
  → 路径：surface → consume_feedback → promise → capsule (3 hops)
  → 证实：修改 surface 会通过 consume_feedback 间接影响 promise
  │
  ▼
Agent 最终回答：
「promise governance 的实现情况：
  1. governance/surface.py 已有基础实现（process + validate）
  2. Radar 标记为 P0-adopt，属于当前最高优
  3. 修改 surface 会通过 consume_feedback 间接影响 17 个文件
  4. 聊天中有 3 条讨论过 API 设计，建议参考后再动工」
```

### 工具选择决策树

当 Agent 接到任务后的内部决策逻辑：

```
接到任务
  │
  ├── 涉及「找具体代码行」？
  │     └── YES → search_files / read_file（代码级）
  │
  ├── 涉及「理解模块间关系」？
  │     ├── 不知道有哪些相关模块 → query_graph（语义搜索）
  │     ├── 知道目标模块，想看影响范围 → get_neighbors
  │     ├── 想知道两个概念怎么关联 → shortest_path
  │     ├── 想知道模块属于哪个功能集群 → get_community
  │     ├── 想了解项目核心是什么 → god_nodes
  │     └── 想看全局统计数据 → graph_stats
  │
  ├── 涉及「技术方向决策」？
  │     ├── 某个技术的优先级 → get_node(radar_item) → priority/action
  │     ├── 全局优先级排名 → god_nodes(filter_type="radar_item")
  │     └── 技术栈健康度 → graph_stats + god_nodes 交叉分析
  │
  └── 涉及「理解设计决策原因」？
        ├── 先在架构级搜索相关聊天节点 → query_graph + edge_types=["discusses"]
        ├── 再在代码级查看实际实现 → read_file
        └── 最后趋势级看该决策的 Radar 评价 → get_node(radar_item)
```

### 协同反模式：什么不该做

| 反模式 | 为什么不好 | 正确做法 |
|--------|------------|----------|
| 跳过架构级直接 `search_files` | 搜索 "ontology" 返回 200+ 结果，无法判断哪些是核心 | 先 `query_graph("ontology")` 定位核心节点，再用 `search_files` 深度查看 |
| 用 `query_graph` 查函数签名 | 图谱不存储代码体，只能返回节点标签和边 | 从 `query_graph` 拿到文件路径 → 用 `read_file` 查看具体代码 |
| 每个任务都 `god_nodes()` | 成本高（全图 PageRank），且大部分任务不需要全局排名 | 仅在架构评审、新人上手、全局健康检查时使用 |
| 修改代码前不做 `get_neighbors` | 改了表面暴露的接口，不知道下游谁在用 | 改接口前必做 `get_neighbors` 检查影响范围 |
| 只看代码不看 Radar | 技术方向判断缺少趋势依据，可能做出与路线图冲突的决策 | `get_neighbors` 后追加 `get_node` 查询相关 Radar 条目 |

### 组合查询速查表

| 任务类型 | 推荐工具链 | 预期时间 |
|----------|------------|----------|
| 新人上手项目 | `graph_stats` → `god_nodes(top_k=15)` → 选核心模块 `get_neighbors` | ~30 秒 |
| 修改函数前的影响分析 | `query_graph("目标概念")` → `get_neighbors` → `shortest_path(目标, 关键下游)` | ~20 秒 |
| 追踪 Bug 根源 | `query_graph("bug相关关键词")` → `shortest_path(症状, 可能的根源)` → `read_file` | ~45 秒 |
| 架构健康评审 | `graph_stats` → `god_nodes` → 对每个核心模块 `get_neighbors` → 检查 Radar 评价 | ~2 分钟 |
| 技术选型决策 | `query_graph("候选方案A")` + `query_graph("候选方案B")` → 对比 `get_node` 查看 Radar 状态 | ~30 秒 |
| 理解设计决策历史 | `query_graph("模块名", mode="semantic")` → 过滤 `type=chat_topic` 节点 → 读取聊天上下文 | ~40 秒 |

---

## 配置与部署

### 在 HermesAgent 配置体系中的位置

Graphify MCP 是 HermesAgent 的 **原生 MCP 客户端** 通过 `mcp.servers` 配置块管理的常驻服务之一。完整的 `~/.hermes/config.yaml` 中，Graphify 配置位于 `mcp.servers` 节点下，与其他 MCP 服务器并列：

```yaml
# ~/.hermes/config.yaml (Graphify 相关节选)
_config_version: 22

agent:
  max_turns: 60
  reasoning_effort: xhigh
  # ... 其他 Agent 配置 ...

mcp:                                          # ← MCP 配置根节点
  servers:                                     # ← 所有 MCP 服务器列表
    graphify:                                  # ← Graphify 知识图谱服务
      command: /root/.hermes/scripts/graphify-mcp-server.sh
      enabled: true                            # ← 会话启动时自动拉起
      tools:                                   # ← 显式声明启用的工具
        get_community: true
        get_neighbors: true
        get_node: true
        god_nodes: true
        graph_stats: true
        query_graph: true
        shortest_path: true
    # 其他 MCP 服务器可在此并列添加 ...
```

**配置要点：**

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `command` | 脚本路径 | MCP 服务器的启动命令。HermesAgent 通过 `stdio`（标准输入/输出）与之通信 |
| `enabled` | `true` / `false` | 设为 `false` 可临时禁用图谱查询，不影响其他功能 |
| `tools` | 工具名 → 布尔值 | 精细控制每个工具的启用状态。可单独关闭某个工具（如 `god_nodes: false`） |
| 加载时机 | 会话启动 | MCP 服务随 HermesAgent 会话一起启动/销毁 |

### 快速验证配置

```bash
# 1. 确认配置语法正确
hermes config validate

# 2. 确认 graphify 配置块存在且 enabled=true
grep -A 12 "graphify:" ~/.hermes/config.yaml

# 3. 手动启动 MCP 服务测试（会列出可用的工具和 schema）
/root/.hermes/scripts/graphify-mcp-server.sh
# 按 Ctrl+C 退出后，可在日志中看到类似输出：
#   tools/list: 7 tools available
#   - query_graph (semantic search)
#   - get_node (node details)
#   ...

# 4. 检查数据文件完整性
python3 -c "
import json
kb = json.load(open('/root/.hermes/chat-archive/CrazyAgentsManage/graphify-out/knowledge-base.json'))
print(f'Nodes: {len(kb[\"nodes\"])}  |  Edges: {len(kb[\"links\"])}  |  Size: {len(json.dumps(kb))//1024} KB')
"
```

### MCP 协议生命周期

Graphify 与 HermesAgent 之间的通信遵循标准的 MCP（Model Context Protocol）规范：

```
┌─────────────────────────────────────────────────────────────┐
│                     会话生命周期                              │
│                                                             │
│  HermesAgent 启动                                           │
│    │                                                        │
│    ├── 1. 读取 config.yaml                                  │
│    │      → 遍历 mcp.servers，过滤 enabled=true             │
│    │                                                        │
│    ├── 2. 为每个 server fork 子进程                          │
│    │      → 执行 command 字段指定的脚本                      │
│    │      → 通过 stdin/stdout 建立双向管道                   │
│    │                                                        │
│    ├── 3. MCP 握手 (initialize)                             │
│    │      → HermesAgent 发送 initialize 请求                │
│    │      → graphify.serve 返回 server_info + capabilities  │
│    │                                                        │
│    ├── 4. 工具发现 (tools/list)                             │
│    │      → HermesAgent 查询可用工具列表                     │
│    │      → graphify 返回 7 个工具 + JSON Schema             │
│    │      → 工具自动注册到 HermesAgent 的工具集              │
│    │                                                        │
│    ├── 5. 运行时调用                                        │
│    │      → Agent 决策 → 调用 tools/call → graphify 执行    │
│    │      → 结果通过 MCP 协议返回 → Agent 继续推理          │
│    │                                                        │
│    └── 6. 会话结束                                          │
│           → HermesAgent 发送 shutdown                       │
│           → 子进程优雅退出 (SIGTERM → 3s → SIGKILL)         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**关键行为：**

- **热加载：** 会话启动时一次性加载 `knowledge-base.json` 到内存。之后所有查询都在内存中完成，无需反复读盘。
- **数据不 hot-reload：** 如果 cron 在会话运行期间更新了 `knowledge-base.json`，当前会话看不到新数据。需 `/new` 重启会话。
- **单会话单实例：** 每个 HermesAgent 会话只启动一个 graphify 进程。多个会话各自拥有独立实例。
- **工具 Schema 自描述：** graphify 通过 MCP 协议的 JSON Schema 向 Agent 描述每个工具的参数类型、必填项和返回值结构。Agent 据此自主决策调用方式。

### 环境依赖

Graphify MCP 服务运行时依赖以下 Python 环境：

| 依赖 | 版本要求 | 用途 |
|------|----------|------|
| Python | ≥ 3.10 | graphify.serve 运行环境 |
| graphify | ≥ 0.7.4 | 核心库：图谱加载、查询执行 |
| networkx | ≥ 3.0 | 图算法（BFS/DFS/PageRank/Louvain） |
| scipy | ≥ 1.10 | 最短路径、社区检测的数学计算 |

**依赖健康检查命令：**

```bash
python3 -c "
import graphify; print(f'graphify: {graphify.__version__}')
import networkx; print(f'networkx: {networkx.__version__}')
import scipy;   print(f'scipy:   {scipy.__version__}')
"
```

### 内存与性能

| 指标 | 典型值 | 说明 |
|------|--------|------|
| knowledge-base.json 大小 | ~5.1 MB | 磁盘占用 |
| 内存占用（图加载后） | ~80–120 MB | networkx 图对象 + 邻接矩阵 |
| query_graph 延迟 | < 50ms | 语义匹配 + BFS 在内存中完成 |
| get_neighbors 延迟 | < 5ms | 邻接表直接索引 |
| god_nodes (PageRank) 延迟 | ~200ms | 全图计算，首次执行后缓存 |
| MCP 进程 CPU 空闲 | < 0.1% | 查询时才消耗 CPU |
| 内存泄漏风险 | 极低 | 纯函数式查询，无状态累积 |

### 安全与隔离

- **进程隔离：** graphify 作为独立子进程运行，崩溃不影响 HermesAgent 主进程
- **只读数据：** graphify 不写任何文件。查询纯内存执行，不修改 `knowledge-base.json`
- **无网络访问：** graphify.serve 不发起任何外部网络请求（纯本地计算）
- **受限文件系统访问：** 仅读取启动时指定的 `knowledge-base.json`，不访问其他路径
- **工具权限：** 所有 MCP 工具需要用户在 `config.yaml` 中显式声明 `true` 才能启用

### 多 MCP 服务器共存

HermesAgent 支持同时运行多个 MCP 服务器。Graphify 与其他 MCP 服务（如飞书 API、浏览器自动化等）在同一会话中共存，工具命名空间隔离：

```
HermesAgent 工具集
├── search_files          ← 原生工具
├── read_file             ← 原生工具
├── query_graph           ← MCP: graphify
├── get_node              ← MCP: graphify
├── get_neighbors         ← MCP: graphify
├── ...                   ← MCP: graphify (其他 4 个)
├── feishu_send_message   ← MCP: feishu (示例)
└── browser_navigate      ← MCP: browser (示例)
```

Agent 根据工具名称和 Schema 自动选择合适的工具调用，无需手动路由。

### 备份与恢复

```bash
# 备份 knowledge-base.json
cp /root/.hermes/chat-archive/CrazyAgentsManage/graphify-out/knowledge-base.json \
   /root/.hermes/chat-archive/CrazyAgentsManage/graphify-out/knowledge-base.json.bak.$(date +%Y%m%d)

# 恢复备份
cp /root/.hermes/chat-archive/CrazyAgentsManage/graphify-out/knowledge-base.json.bak.20260504 \
   /root/.hermes/chat-archive/CrazyAgentsManage/graphify-out/knowledge-base.json

# 重新生成（如果备份也不可用）
python3 /root/.hermes/scripts/weekly-archive-rebuild.py --force
```

---

## 数据管线

### 数据源

| 来源 | 路径 | 内容 |
|------|------|------|
| CrazyAgentsManage 代码 | `/root/CrazyAgentsManage/` | AST 提取的类/函数/文件节点 |
| FlowMindDeploy 代码 | `/root/FlowMindDeploy/` | AST 提取的类/函数/文件节点 |
| CraigAgentsManage 聊天 | `~/.hermes/chat-archive/CrazyAgentsManage/2026_W*.md` | 对话主题提取 |
| FlowMind 聊天 | `~/.hermes/chat-archive/FlowMind/2026_W*.md` | 对话主题提取 |
| Tech Radar | `~/.hermes/shared-context/tech-radar.json` | 技术趋势条目 |

### 更新节奏

| 触发方式 | 频率 | 说明 |
|----------|------|------|
| Cron 定时重建 | 每周日 02:00 CST | Cron job `a4113733d984`，执行 `weekly-archive-rebuild.py` + `regenerate-graph-html.py` |
| 手动重建 | 按需 | `python3 /root/.hermes/scripts/weekly-archive-rebuild.py` |
| Agent 重启 | 每次会话启动 | MCP 服务重新加载 knowledge-base.json → 数据自动刷新 |

### 产物文件

| 文件 | 大小参考 | 用途 |
|------|----------|------|
| `knowledge-base.json` | ~5.1 MB | Graphify MCP 服务的唯一数据源 |
| `merged-graph.json` | ~4.4 MB | 用于生成网页可视化 |
| `/var/www/hermes/graph/index.html` | ~2.7 MB | 网页端 vis-network 交互图 |

### Web 可视化

访问 `http://47.99.217.1/graph/` 可查看交互式知识图谱，支持：
- 节点点击查看详情
- 搜索下拉框实时定位
- 社区筛选（Legend 面板）
- 边标签悬停显示
- ForceAtlas2 物理布局

---

## 故障排查

### 问题：MCP 工具不可用

**症状：** Agent 的工具列表中没有 `query_graph` 等 Graphify 工具

**排查步骤：**

1. **检查配置是否启用：**
   ```bash
   grep -A 10 "graphify" ~/.hermes/config.yaml
   ```
   确认 `enabled: true`

2. **检查 MCP 脚本是否可执行：**
   ```bash
   ls -la /root/.hermes/scripts/graphify-mcp-server.sh
   ```

3. **手动测试 MCP 服务：**
   ```bash
   python3 -m graphify.serve \
     /root/.hermes/chat-archive/CrazyAgentsManage/graphify-out/knowledge-base.json
   ```
   如果能正常启动并显示工具列表，说明服务本身正常。

4. **重启会话：** MCP 服务器在会话启动时加载。修改配置后执行 `/new` 或重新连接飞书即可生效。

### 问题：查询结果过时

**症状：** 图谱中缺少最近添加的文件或对话

**原因：** 数据重建是每周进行的（周日 02:00），期间的新增内容不会反映在图谱中。

**解决方案：**

```bash
# 手动触发重建
python3 /root/.hermes/scripts/weekly-archive-rebuild.py

# 然后重启 Agent 会话加载新数据
# 或等待下次 cron（每周日 02:00）自动重建
```

### 问题：knowledge-base.json 损坏

**症状：** MCP 服务启动失败，报 JSON 解析错误

**解决方案：**

```bash
# 1. 验证 JSON 有效性
python3 -c "import json; json.load(open('/root/.hermes/chat-archive/CrazyAgentsManage/graphify-out/knowledge-base.json'))"

# 2. 如果验证失败，强制重建
python3 /root/.hermes/scripts/weekly-archive-rebuild.py --force
```

### 问题：MCP 服务器进程僵死

**症状：** 工具调用超时或返回空结果

**解决方案：**

```bash
# 杀死残留进程
pkill -f "graphify.serve"

# 重启 Agent 会话（/new）即可自动拉起新进程
```

---

## 维护手册

### 日常操作

| 操作 | 命令 |
|------|------|
| 查看图谱状态 | 调用 `graph_stats` 工具（或让 Agent 代查） |
| 手动重建 | `python3 /root/.hermes/scripts/weekly-archive-rebuild.py` |
| 重启 MCP 服务 | `/new`（新会话） |
| 查看 cron 状态 | `hermes cron list`（找到 job `a4113733d984`） |
| 验证数据完整性 | `python3 -c "import json; kb=json.load(open('.../knowledge-base.json')); print(len(kb['nodes']), len(kb['links']))"` |

### 新增数据源

如需将新的数据源纳入图谱（如新的代码仓、新的聊天群），编辑 `/root/.hermes/scripts/weekly-archive-rebuild.py`：

1. 在 `GROUPS` 字典中添加新的 group_name → chat_id 映射（聊天数据）
2. 在 graphify extract 阶段添加新的代码仓路径（代码数据）
3. 手动运行一次重建以验证

### 语义优先级过滤

当节点数超过限制（默认 1500），`regenerate-graph-html.py` 使用语义优先级过滤保留关键节点。当前优先级关键词：

```
ontology, governance, promise, deploy, memory, router,
capsule, feedback, consume, truth, gate, graph,
flow, topic, extract, signal, agent, capsule
```

如需添加新的优先级关键词，编辑 `/root/.hermes/scripts/regenerate-graph-html.py`，在 `SEMANTIC_KEYWORDS` 集合中添加。

---

## 相关文档

- [Tech Radar 周审查机制](../../../hermes-agent/tech-radar-review.md)（待补充）
- [每周聊天归档 cron 配置](../../../hermes-agent/cron-jobs.md)（待补充）
- [Graphify 官方文档](https://github.com/jializheng0306-byte/graphify)（项目仓库）
- [vis-network 交互图说明](https://visjs.github.io/vis-network/docs/network/)（前端可视化引擎）

---

## 变更记录

| 日期 | 变更内容 | 作者 |
|------|----------|------|
| 2026-05-04 | 初始版本：MCP 集成完成，7 个工具全部启用，cron 定时重建已配置 | HermesAgent |
| 2026-05-04 | v1.1：新增「双层知识基座设计」章节；三层次查询体系深度扩展（决策树、反模式、组合速查表）；配置章节大幅补充（生命周期、性能、安全、多MCP共存、备份恢复） | HermesAgent |
