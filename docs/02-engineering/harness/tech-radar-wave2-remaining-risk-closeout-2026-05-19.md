# tech-radar.review × Wave 2 remaining-risk closeout（2026-05-19）

> 宿主: `ALI-HERMES`  
> 任务类型: `tech-radar.review`  
> 范围: `Wave 2` remaining risks  
> 入口脚本: `/root/.hermes/scripts/tech-radar-review.sh`

## 1. 本轮目标

收掉上一轮 closeout 中明确留下的三条剩余风险：

1. `x/twitter` 的 1 条 `P1` 条目仍未覆盖
2. `max_entries=5` 可能挤掉第二条 `P1 github`
3. GitHub public API 的宿主侧 rate-limit 稳定性未验证

## 2. 实际落地

### 2.1 `x/twitter` 已补 readonly source

新增：

- `shared-context/executor-sources/x-publish-readonly-openapi.v1.json`
- `scripts/runtime/ensure_x_publish_readonly_source.py`

虽然最初先看了官方 `publish.twitter.com/oembed` 路径，但在 `ALI-HERMES` 上实测出现 TLS handshake timeout，不适合作为宿主主线。

本轮最终落地为：

- source id: `x-syndication-readonly`
- tool path: `x-syndication-readonly.tweets.getTweetResult`
- host-accessible base API: `https://cdn.syndication.twimg.com/tweet-result`

这样 `x/twitter` 的高优先级条目现在能补到：

- author / handle
- created_at
- tweet text
- favorite_count
- lang

### 2.2 选择逻辑不再把第二条 GitHub 挤掉

更新：

- `scripts/fetch-tech-radar-evidence-via-executor.py`
- `scripts/tech-radar-review.sh`

当前选择策略改为三段：

1. 每个 source 先保 1 条 base coverage
2. 对紧凑型非 paper source（当前主要是 `github` / `x/twitter`）优先补全
3. 剩余名额再回到全局按优先级填充

同时把：

- `--max-entries` 从 `5` 提到 `6`

这样当前真实分布下，宿主报告可以同时覆盖：

- 全部 4 条 `P0`
- `x/twitter` 的 `P1`
- 第二条 `github` 的 `P1`

### 2.3 GitHub rate-limit 风险收敛为 runtime-local cache

更新：

- `scripts/fetch-tech-radar-evidence-via-executor.py`

当前对 GitHub evidence 增加：

- runtime-local cache
- stale fallback
- report-visible cache status

默认缓存位置：

- `~/.hermes/cache/tech-radar-evidence/github/*.json`

行为：

- fresh cache: 直接命中，不再重复打 GitHub
- stale cache + remote read 失败: 回退到缓存
- 报告中显式显示 `Executor evidence cache: hit|miss|fallback`

这保持了边界不变：

- cache 是 runtime-local
- 不是 repo truth
- 不回写 `tech-radar.json`

## 3. 验证

### 3.1 本地

已通过：

- `.venv/bin/python -m pytest tests/test_fetch_tech_radar_evidence_via_executor.py tests/test_ensure_github_repo_readonly_source.py tests/test_ensure_x_publish_readonly_source.py -q`
- `bash scripts/check_harness_governance_all.sh`

新增覆盖包括：

- `x/twitter` syndication 解析
- compact source 选择逻辑
- GitHub fresh cache 命中
- GitHub stale cache fallback
- X readonly source recreate 路径

### 3.2 宿主

按固定顺序执行：

1. `python3 scripts/governance/sync_live_deploy_copy.py --workspace-root . --profile crazy-runtime-live --skip-verify --json`
2. `python3 scripts/runtime/run_on_ali_hermes.py --cwd /root/CrazyAgentsManage -- 'python3 scripts/runtime/sync_hermes_script_mirror.py'`
3. `python3 scripts/runtime/run_on_ali_hermes.py --cwd /root/CrazyAgentsManage -- 'bash ~/.hermes/scripts/tech-radar-review.sh'`
4. 再次执行第 3 步确认 cache hit 稳定存在

宿主实测结果：

- 报告中出现 `Agent Constitution Pattern (SOUL.md/USER.md/AGENTS.md)`
- 其 evidence source 为 `x-syndication-readonly`
- 报告中出现 tweet 正文、likes、lang
- `paragents` 与 `oh-my-kimichan` 都稳定进入报告
- 两条 GitHub evidence 都显示 `Executor evidence cache: hit`

## 4. 结论

这三条风险当前都已被实质性收掉：

1. `x/twitter` 不再是未覆盖 source
2. 第二条 GitHub 不再被当前报告名额挤掉
3. GitHub 宿主侧 rate-limit 风险已有 runtime-local cache + stale fallback 缓冲

## 5. 剩余注意项

1. `techcrunch` / `podcast` 仍未进入同等级 readonly capability，但当前条目仍以 `P2` 为主，不是本轮主阻塞。
2. `x-syndication-readonly` 依赖公开 syndication 面；若宿主网络策略变化，需要重新做一次 host probe。
3. GitHub cache 现在是 runtime-local 优化，不应被误读成 repo 事实层。

## 6. 一句话结论

> Wave 2 剩余风险已经从“source 缺口 / 选择偏斜 / rate-limit 未验证”推进到“`x/twitter` 已覆盖、两条 GitHub 稳定入报告、GitHub cache 已在 `ALI-HERMES` 上持续命中”。
