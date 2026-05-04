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

## 三层次查询体系

Graphify MCP 工具与 HermesAgent 现有的代码搜索工具形成 **三层互补结构**：

```
┌──────────────────────────────────────────────────────┐
│  层次          工具                  解决的问题       │
├──────────────────────────────────────────────────────┤
│  代码级    search_files / read_file   这个函数在哪？  │
│           grep / find                 具体怎么写的？  │
├──────────────────────────────────────────────────────┤
│  架构级    query_graph                哪些模块相关？  │
│           get_neighbors               谁依赖谁？       │
│           shortest_path               概念怎么关联？   │
│           get_community               功能集群在哪？   │
│           god_nodes                  核心抽象是什么？ │
├──────────────────────────────────────────────────────┤
│  趋势级    tech-radar.json            技术应该往哪走？│
│           (已存在的 Radar 机制)       当前优先级？     │
└──────────────────────────────────────────────────────┘
```

### 典型工作流示例

**场景：用户说「我想修改 ontology 模块的序列化方式」**

Agent 的自动查询链路：

1. **`query_graph("ontology serialization")`** → 找到所有与 ontology 序列化相关的节点
2. **`get_neighbors("ontology.py", edge_types=["calls", "imports"])`** → 列出直接依赖方
3. **`get_node("ontology.py")`** → 获取完整文件元数据（路径、社区、度）
4. **`shortest_path("ontology.py", "governance")`** → 检查是否会影响 governance 模块
5. 结合 `search_files` 读取实际代码 → 开始修改

**场景：用户问「FlowMind 和 CrazyAgentsManage 之间有哪些数据通道？」**

1. **`query_graph("data flow channel pipe")`** → 语义搜索数据通道相关节点
2. **`get_community(community_id=N)`** → 看数据通道所属集群
3. **`shortest_path("FlowMind", "CrazyAgentsManage")`** → 追踪双仓间关联路径

---

## 配置与部署

### MCP 服务配置

配置文件：`~/.hermes/config.yaml`

```yaml
mcp:
  servers:
    graphify:
      command: /root/.hermes/scripts/graphify-mcp-server.sh
      enabled: true
      tools:
        get_community: true
        get_neighbors: true
        get_node: true
        god_nodes: true
        graph_stats: true
        query_graph: true
        shortest_path: true
```

### MCP 服务脚本

文件：`/root/.hermes/scripts/graphify-mcp-server.sh`

```bash
#!/bin/bash
exec python3 -m graphify.serve \
  /root/.hermes/chat-archive/CrazyAgentsManage/graphify-out/knowledge-base.json
```

### 生效机制

```
HermesAgent 启动
  │
  ├── 读取 ~/.hermes/config.yaml
  │     └── 发现 mcp.servers.graphify
  │
  ├── 启动 graphify-mcp-server.sh
  │     └── 通过 stdio 建立 MCP 连接
  │     └── 加载 knowledge-base.json 到内存
  │
  ├── 协议握手，发现 7 个工具
  │
  └── 工具自动注册到 Agent 的工具集
        └── Agent 可根据任务上下文自主调用
```

**重要：** MCP 服务器在 Agent **会话启动时**加载。配置修改后，需要 `/new`（新会话）才能生效。

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
