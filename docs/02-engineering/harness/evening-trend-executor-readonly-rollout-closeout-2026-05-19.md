# evening-trend × executor readonly rollout closeout（2026-05-19）

> 宿主: `ALI-HERMES`  
> 任务类型: `intel.evening`  
> capability source: `hn-readonly`  
> wrapper path: `/root/.hermes/scripts/evening-trend-analysis.py`

## 1. 本轮目标

把 `Wave 1` 的第三条允许类型也落成真实链路：

- `intel.evening`

这次不只是在 collector 里补一个 external read step，而是同时把宿主机当前晚间主链 authority 也收回仓库。

## 2. 实际落地内容

### 2.1 新增 repo-tracked authority

新增：

- `scripts/evening-trend-analysis.py`

并同步到：

- `/root/.hermes/scripts/evening-trend-analysis.py`

它继续保留：

- ai-builders-digest 读取
- 趋势报告写入 `~/.hermes/trends/`
- 飞书云盘上传
- 飞书群推送

### 2.2 collector 已接入 executor

`scripts/evening-intel-collector.sh` 现在新增：

- `Hacker News Agent / Builder Trends（via executor）`

通过：

- `hn-readonly`
- `fetch-hn-stories-via-executor.py`

### 2.3 host mirror 已纳入 authority

`shared-context/hermes-script-mirror-manifest.json` 与 `sync_hermes_script_mirror.py` 现在都包含：

- `evening-trend-analysis.py`

因此 `~/.hermes/scripts/evening-trend-analysis.py` 不再是宿主机私有实现，而是 repo-tracked mirror。

## 3. 实测结果

### 3.1 source 可见

`executor tools sources` 中仍可见：

- `hn-readonly`

### 3.2 collector 已产出 executor 段落

在 `ALI-HERMES` 上运行：

- `bash /root/.hermes/scripts/evening-intel-collector.sh`

结果：

- 生成 `REPORT_FILE=/root/.hermes/intel/evening-intel-2026-05-19.md`
- 文件中出现 `Hacker News Agent / Builder Trends（via executor）`

### 3.3 authority 主链已跑通

在 `ALI-HERMES` 上运行：

- `/root/.hermes/scripts/evening-trend-analysis.py`

结果：

- stdout 出现 `✅ collector 完成`
- 生成 `/root/.hermes/trends/trend-2026-05-19.md`
- `trend-2026-05-19.md` 中保留 `Hacker News Agent / Builder Trends（via executor）`
- 飞书云盘上传成功
- 飞书群推送成功

## 4. 结论

本轮之后，`Wave 1` 三条允许链都已经完成真实落地：

- `intel.morning`
- `intel.noon-paper`
- `intel.evening`

这意味着主线已经不再是“再补第三条一样的 read step”，而是要开始考虑：

1. 把三条链中重复的 wrapper / report / upload / message 进一步抽象
2. 决定是否进入 `Wave 2`
