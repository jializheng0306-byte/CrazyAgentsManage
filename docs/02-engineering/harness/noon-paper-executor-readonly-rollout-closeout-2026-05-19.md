# noon-paper × executor readonly rollout closeout（2026-05-19）

> 宿主: `ALI-HERMES`  
> 任务类型: `intel.noon-paper`  
> capability source: `crossref-readonly`  
> wrapper path: `/root/.hermes/scripts/noon-paper-review.sh`

## 1. 本轮目标

把 `Wave 1` 中已经冻结允许的任务类型里，真正挑一条落地成首个端到端实现。

本轮选择：

- `intel.noon-paper`

原因：

- 天然是外部只读资料检索任务
- 不直接写 FlowMind truth / promise truth / closeout truth
- 相比 `morning-intel / evening-intel`，依赖链更短、实现风险更小

## 2. 实际落地内容

### 2.1 新增 capability source

通过 Crazy façade 在 `ALI-HERMES` 上创建：

- `crossref-readonly`

当前状态：

- `kind=openapi`
- `toolCount=1`
- tool path = `crossref-readonly.works.searchWorks`

### 2.2 新增 repo-tracked helper

- `shared-context/executor-sources/crossref-works-openapi.v1.json`
- `scripts/runtime/ensure_crossref_readonly_source.py`
- `scripts/fetch-crossref-papers-via-executor.py`
- `scripts/runtime/sync_hermes_script_mirror.py`

### 2.3 noon-paper collector 已接入 executor

`scripts/noon-paper-collector.sh` 现在会先执行：

- `fetch-crossref-papers-via-executor.py`

生成新分区：

- `Crossref 最新 AI Agent / Multi-Agent 论文（via executor）`

随后仍保留原有 arXiv 采集分区。

### 2.4 noon-paper wrapper 已 repo-tracked

新增：

- `scripts/noon-paper-review.sh`

并同步到：

- `/root/.hermes/scripts/noon-paper-review.sh`

当前 wrapper 行为：

1. 调用 repo-tracked collector
2. 生成 `~/.hermes/intel/noon-paper-YYYY-MM-DD.md`
3. 复制为 review / knowledge 副本
4. best-effort 发送飞书摘要

## 3. 实测结果

### 3.1 source 可见

`executor tools sources` 中已出现：

- `crossref-readonly`

### 3.2 helper 可调用

在 `ALI-HERMES` 上已实测：

- `python3 /root/.hermes/scripts/fetch-crossref-papers-via-executor.py --heading "Crossref Test" --query "AI agent" --rows 2`

可正常返回 markdown 结果。

### 3.3 noon-paper wrapper 跑通

已实测：

- `/root/.hermes/scripts/noon-paper-review.sh`

结果：

- 生成 `REPORT_FILE=/root/.hermes/intel/noon-paper-2026-05-19.md`
- 生成 `REVIEW_FILE=/root/.hermes/papers/review-20260519.md`
- 日志中出现：
  - `Crossref 最新 AI Agent / Multi-Agent 论文（via executor）`
  - `collector 完成`
  - `飞书摘要发送成功`

## 4. 结论

本轮之后，可以明确认定：

> `intel.noon-paper` 已经成为 `Hermes -> executor` readonly delegation spec v1 下的第一条真实端到端实现链路。

它证明的不只是“只读调用能通”，而是：

1. Crazy façade 可预置 readonly source
2. repo-tracked helper 可经 executor 拉取外部数据
3. host mirror 脚本可消费该能力
4. Hermes runtime 主链仍保持 wrapper / report / message 的 ownership

## 5. 下一步

现在再往下推进时，不该重复实现另一条同类能力，而应该优先二选一：

1. 把 `intel.morning` 的一个外部 read step 接到 executor
2. 抽象出 `Wave 1` 通用 readonly delegation helper contract，减少脚本各自拼装 executor call
