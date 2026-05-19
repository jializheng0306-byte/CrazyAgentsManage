# tech-radar.review × executor readonly evidence enrichment closeout（2026-05-19）

> 宿主: `ALI-HERMES`  
> 任务类型: `tech-radar.review`  
> 范围: `Wave 2` 第一条实现  
> 入口脚本: `/root/.hermes/scripts/tech-radar-review.sh`

## 1. 本轮目标

把 `Wave 2` 从“只做适配评估”推进到第一条真正的实现：

- 不整体 executor 化周审查主链
- 只新增 `entry-level evidence enrichment`

## 2. 实际落地内容

### 2.1 新增 helper

- `scripts/fetch-tech-radar-evidence-via-executor.py`

作用：

- 读取 `shared-context/tech-radar.json`
- 选择高优先级条目
- 通过已存在的 readonly sources 做外部补证据

### 2.2 tech-radar 周审查脚本已接入新分区

`scripts/tech-radar-review.sh` 现在在本地 summary 主链之后，新增：

- `P0/P1 Pending Radar 条目只读补证据（via executor）`

行为：

1. best-effort 确保 `crossref-readonly` / `hn-readonly` 存在
2. 对 radar 条目做 readonly enrichment
3. 结果写回同一份周审查 markdown

### 2.3 当前数据口径修正

实际运行中发现：

- 当前 radar 条目不是以 `pending` 为主要状态口径
- 现实中大量条目使用 `adopt / trial / assess`

因此 helper 已补 fallback 逻辑：

- 优先 `pending`
- 若无结果，回退到 `adopt / trial / assess` 中的 `P0/P1` 条目

### 2.4 宿主同步口径补齐

后续验证又发现一个宿主事实层缺口：

- `crazy-runtime-live` 同步清单此前未包含 `shared-context/tech-radar.json`
- 这会导致 `ALI-HERMES` 上的 `tech-radar-review.sh` 继续读取旧版 radar truth

因此同步清单已补齐：

- `shared-context/tech-radar.json`

这样宿主周审查与仓库当前 radar truth 才能保持同一口径。

## 3. 宿主实测结果

在 `ALI-HERMES` 上运行：

- `bash /root/.hermes/scripts/tech-radar-review.sh`

结果：

- 生成 `tech-radar-review-2026-05-19.md`
- 报告中出现 `P0/P1 Pending Radar 条目只读补证据（via executor）`
- 报告中出现多条 `Executor evidence source: crossref-readonly`
- 已对 `Memanto / RecursiveMAS / OxyGent / FSFM / S2G-RAG` 等条目追加只读外部补证据

## 4. 结论

本轮之后，`Wave 2` 不再只是一个适配建议，而是已经拥有第一条真实实现：

> `tech-radar.review` 已经开始在不让渡 `tech-radar.json` authority 的前提下，使用 executor 做 entry-level readonly evidence enrichment。

## 5. 下一步

最自然的后续不是再改同一脚本框架，而是二选一：

1. 优化 enrichment 的匹配质量与结果去重
2. 扩展下一批 source 类型（例如 `github` entry 的 readonly enrichment）
