# tech-radar.review × executor Wave 2 评估（2026-05-19）

## 1. 评估目标

在 `Wave 1` 三条只读链都已经真实落地后，正式进入 `Wave 2` 的优先评估对象：

- `tech-radar.review`

这里要回答的不是“能不能也接 executor”，而是更精确的三个问题：

1. 当前 `tech-radar.review` 的主价值到底是什么
2. executor 接入后，应该替代哪一段，还是只增强哪一段
3. 这件事现在值不值得进入下一条实现主线

---

## 2. 当前现实

### 2.1 当前入口

仓库当前入口是：

- `scripts/tech-radar-review.sh`

它现在做的事情很克制：

1. 读取 `shared-context/tech-radar.json`
2. 汇总 `adopt / trial / assess`
3. 扫描最近 7 天 `intel/*.md` 中的高星/P0/P1 线索
4. 生成周审查 markdown

也就是说：

> 当前 `tech-radar.review` 本质上是 **本地共享上下文与情报产物的汇总审查脚本**。

### 2.2 当前数据构成

`shared-context/tech-radar.json` 当前共有 28 条 entry。

来源分布：

- `arxiv`: 19
- `x/twitter`: 2
- `techcrunch`: 2
- `hn`: 2
- `github`: 2
- `podcast`: 1

优先级分布：

- `P0`: 4
- `P1`: 14
- `P2`: 10

这说明：

- 绝大多数条目来自 **外部资料**
- 但当前周审查脚本本身几乎不做外部读取
- 它只是消化已落库的本地 `tech-radar.json + intel/*.md`

---

## 3. 是否值得接 executor

## 3.1 结论

> **值得接，但不值得把当前 `tech-radar-review.sh` 整体替换成 executor 驱动脚本。**

更准确地说：

> **值得把 `tech-radar.review` 的“entry-level evidence enrichment” 子步骤接入 executor，而不是把“weekly summary generation” 主流程交给 executor。**

---

## 3.2 为什么不是整条替换

当前 `tech-radar.review` 的主 authority 是：

- `shared-context/tech-radar.json`
- 最近一周的 `intel/*.md`

这两者都已经是 repo / host 本地事实层。

如果把整条周审查主流程交给 executor：

- 收益不大
- 还会增加外部 capability 依赖
- 反而模糊当前脚本作为“本地审查器”的职责

所以：

- **不值得**把当前周审查主链整体 executor 化

---

## 3.3 为什么仍然值得接一段 executor

`tech-radar.review` 真正缺的不是“再汇总一遍本地文件”，而是：

### A. 对高优先级条目的外部证据补拉

例如：

- `arxiv` 条目：补拉最新摘要/版本/引用线索
- `github` 条目：补拉仓库元数据、活跃度、issue/PR 线索
- `hn` 条目：补拉讨论热度
- `techcrunch` / `podcast` 条目：补拉相关文章或补充上下文

### B. 对 `pending` 高优先级条目的再确认

当前很多条目停留在：

- `status=pending`

但没有一条系统化的“定期补证据再判断是否 promote 到 trial/adopt”的机制。

executor 正适合承接：

- 只读 evidence refresh
- schema-first 外部查询
- 对单个 radar entry 的补充抓取

### C. 这与当前 Wave 1 已落地能力天然衔接

现在宿主上已经稳定有：

- `crossref-readonly`
- `github-repo-readonly`
- `x-syndication-readonly`
- `hn-readonly`

也就是说，`tech-radar.review` 可以直接复用现有 capability plane 做：

- 论文类条目的补证据
- GitHub 仓库类条目的元数据与 recent activity 补证据
- X/Twitter 单条 signal 的 syndication 只读补证据
- HN 类条目的热度/内容补证据

所以：

- **值得接 executor**
- 但目标是 `evidence enrichment step`

---

## 4. Wave 2 的推荐接法

### 4.1 推荐模式

```text
tech-radar weekly summary
  -> keep local and repo-owned

tech-radar entry evidence refresh
  -> delegate readonly external enrichment to executor
```

### 4.2 推荐的第一条实现

不要先改 `scripts/tech-radar-review.sh` 的周报框架。

先新增一个更小、更可验证的子步骤，例如：

- `scripts/fetch-tech-radar-evidence-via-executor.py`

输入：

- 某个 radar entry

输出：

- 针对该 entry 的最新外部补充证据

支持的第一批 source 类型：

- `arxiv`
- `hn`
- `github`
- `x/twitter`

### 4.3 推荐的执行顺序

1. 只挑 `P0/P1 + pending` 的 radar entry
2. 只做 readonly enrichment
3. 结果回到本地 markdown / JSON review artifact
4. 由 Crazy / Hermes 决定是否修改 `tech-radar.json`

---

## 5. 当前不推荐的做法

### 不推荐 1：整条 `tech-radar-review.sh` executor 化

原因：

- 主体仍然是本地 facts 汇总
- executor 只会增加复杂度

### 不推荐 2：直接让 executor 改 `shared-context/tech-radar.json`

原因：

- `tech-radar.json` 仍属于 repo truth
- executor 不应直接拥有这一层 authority

### 不推荐 3：现在就把 `podcast` / `techcrunch` 全部统一接入

原因：

- 当前高优先级分布最值当的 source 已经覆盖到 `arxiv / github / x/twitter`
- `podcast` / `techcrunch` 仍缺同等级稳定 readonly capability，且当前条目优先级仍以 `P2` 为主

---

## 6. 最终裁定

### 值得接 executor 吗？

- `是`

### 值得现在就做吗？

- `是`

### 应该接哪一段？

- `entry-level evidence enrichment`

### 不应该接哪一段？

- `weekly summary generation`
- `tech-radar.json authority write path`

---

## 7. 一句话结论

> `tech-radar.review` 进入 `Wave 2` 的正确方式，不是把周审查脚本整体 executor 化，而是新增一个面向 `P0/P1 + pending` 条目的 readonly evidence enrichment 子步骤，让 executor 负责补拉外部证据，Crazy/Hermes 仍负责本地审查与最终 truth promotion。  

## 8. 当前状态

截至 2026-05-19，本评估已进入实现态：

- readonly evidence enrichment 子步骤已在宿主 `ALI-HERMES` 上跑通
- `tech-radar-review-YYYY-MM-DD.md` 中已出现 executor 补证据分区
- `github` 条目已补到 recent commit activity，不再只停留在静态 repo metadata
- `x/twitter` 的高优先级条目已可通过 `x-syndication-readonly` 做 syndication 只读补证据
- 当前仍保持：
  - 周报主体为本地 summary 主链
  - `tech-radar.json` authority 仍不交给 executor
