# morning-intel × executor readonly step closeout（2026-05-19）

> 宿主: `ALI-HERMES`  
> 任务类型: `intel.morning`  
> capability source: `hn-readonly`  
> collector path: `/root/.hermes/scripts/morning-intel-collector.sh`

## 1. 本轮目标

在 `noon-paper` 已经成为首条 Wave 1 端到端链路之后，继续推进第二条允许类型：

- `intel.morning`

本轮已经继续推进到：

- `morning-intel-v2.py` authority 收口到 repo-tracked source-of-truth
- 并让其中一段 external read step 接到 executor

## 2. 实际落地内容

### 2.1 新增 capability source

通过 Crazy façade 在 `ALI-HERMES` 上创建：

- `hn-readonly`

当前状态：

- `kind=openapi`
- `toolCount=1`
- tool path = `hn-readonly.stories.searchStoriesByDate`

### 2.2 新增通用 helper contract

新增：

- `scripts/executor_readonly_helper.py`

作用：

- 统一 Wave 1 的 readonly executor call glue
- 让 `morning-intel` 与 `noon-paper` 不再各自重复拼装 executor CLI

### 2.3 新增 HN wrapper

新增：

- `scripts/fetch-hn-stories-via-executor.py`

当前由 `scripts/morning-intel-collector.sh` 调用，生成：

- `Hacker News AI / Agent Stories（via executor）`

### 2.4 repo-tracked authority 已建立

新增：

- `scripts/morning-intel-v2.py`

并同步到：

- `/root/.hermes/scripts/morning-intel-v2.py`

当前 system crontab 继续指向同一路径：

- `30 8 * * * /usr/bin/python3 /root/.hermes/scripts/morning-intel-v2.py`

但其 source-of-truth 已从宿主机本地副本切回仓库。

## 3. 实测结果

### 3.1 source 可见

`executor tools sources` 中已出现：

- `hn-readonly`

### 3.2 helper 可调用

在 `ALI-HERMES` 上，Hacker News Algolia API 可通过 executor source 返回结果。

### 3.3 morning collector 已产生 executor 段落

在 `ALI-HERMES` 上运行：

- `/root/.hermes/scripts/morning-intel-collector.sh`

预期结果已落地为：

- `~/.hermes/intel/morning-intel-YYYY-MM-DD.md` 中新增 executor 段落
- 原有 arXiv / RSS / GitHub 逻辑仍保留

### 3.4 authority 主链已通过新实现跑通

在 `ALI-HERMES` 上运行：

- `/root/.hermes/scripts/morning-intel-v2.py`

结果：

- stdout 明确出现 `Hacker News (executor): 5 条`
- 生成 `summary-YYYYMMDD-v2.md`
- 生成 `intel-data-YYYYMMDD-v2.json`
- 生成 `knowledge/intel-YYYYMMDD-v2.md`
- 飞书群推送成功

## 4. 结论

本轮之后，`Wave 1` 已经不是只有一条 executor 读链：

- `intel.noon-paper`：完整 wrapper 链已落地
- `intel.morning`：collector 级 external read step 已落地，且 authority 已回到 repo

这意味着后续真正需要决策的，不再是“能不能接第二条”，而是：

1. 是否继续把 `intel.evening` 加一段 executor-backed read step
2. 是否进一步统一 `morning-intel / noon-paper / evening-intel` 的 readonly delegation helper contract
