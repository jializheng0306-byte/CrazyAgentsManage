# tech-radar.review × executor GitHub activity enrichment closeout（2026-05-19）

> 宿主: `ALI-HERMES`  
> 任务类型: `tech-radar.review`  
> 范围: `Wave 2` 第二步推进  
> 入口脚本: `/root/.hermes/scripts/tech-radar-review.sh`

## 1. 本轮结论

基于当前 `shared-context/tech-radar.json` 的实际分布，本轮不新增 `x/twitter` source。

理由不是“以后永远不做”，而是：

- 当前 `P0/P1` 条目分布里：
  - `arxiv`: 15
  - `github`: 2
  - `x/twitter`: 1
- `x/twitter` 仍没有稳定、repo-tracked、readonly executor source
- `github` 已经有稳定 source，但上一轮只拿到仓库静态元数据，缺少对“仓库是否还在活跃演进”的证据

因此本轮最值当的推进不是扩新 source，而是：

> 在现有 `github-repo-readonly` 上补齐 recent activity signal，让 `tech-radar.review` 对 GitHub 类 radar 条目的 evidence enrichment 更接近运营判断所需信息。

## 2. 实际落地内容

### 2.1 扩展 GitHub readonly capability

更新：

- `shared-context/executor-sources/github-repo-readonly-openapi.v1.json`

新增只读接口：

- `repos.listRepoCommits`

这样 executor 不再只能返回 repo metadata，也能返回最近提交活动。

### 2.2 GitHub evidence enrichment 改为“元数据 + 最近提交”

更新：

- `scripts/fetch-tech-radar-evidence-via-executor.py`

当前对 GitHub 条目的补证据结果包含：

- stars / forks / open issues
- language
- updated_at / pushed_at
- default_branch / archived
- recent commits（短 SHA / 日期 / 首行 commit message / commit URL）

同时保持只读边界不变：

- 不修改 `shared-context/tech-radar.json`
- 不把 executor 变成 repo truth authority

### 2.3 宿主 source 自动升级

更新：

- `scripts/runtime/ensure_github_repo_readonly_source.py`
- `scripts/tech-radar-review.sh`

由于 Crazy façade 的 HTTP mode 不支持直接 patch OpenAPI spec，本轮采用的宿主升级策略是：

1. 检查 `github-repo-readonly` 是否已存在
2. 若存在，再检查是否已有 `listRepoCommits`
3. 若缺少该 tool，则删除旧 source 并按最新 spec 重建

这样 `ALI-HERMES` 上已存在的 source 也能实际看到新 capability，而不是只同步了仓库文件但宿主 source 仍停留在旧版本。

## 3. 验证

### 3.1 本地验证

已通过：

- `.venv/bin/python -m pytest tests/test_fetch_tech_radar_evidence_via_executor.py tests/test_ensure_github_repo_readonly_source.py -q`
- `bash scripts/check_harness_governance_all.sh`

其中新增覆盖包括：

- GitHub 条目 recent commit 渲染
- GitHub commit 子调用失败隔离
- `ensure_github_repo_readonly_source.py` 在 required tool 缺失时的删建升级路径

### 3.2 宿主验证

按固定顺序执行：

1. `python3 scripts/governance/sync_live_deploy_copy.py --workspace-root . --profile crazy-runtime-live --skip-verify --json`
2. `python3 scripts/runtime/run_on_ali_hermes.py --cwd /root/CrazyAgentsManage -- 'python3 scripts/runtime/sync_hermes_script_mirror.py'`
3. `python3 scripts/runtime/run_on_ali_hermes.py --cwd /root/CrazyAgentsManage -- 'bash ~/.hermes/scripts/tech-radar-review.sh'`

实测结果：

- 宿主成功生成 `tech-radar-review-2026-05-19.md`
- `oh-my-kimichan` 条目下出现：
  - `Executor evidence source: github-repo-readonly`
  - 最近三条 commit 的短 SHA、日期、首行 message 与 URL

这说明：

- GitHub readonly source 已具备新 tool
- `tech-radar.review` 已开始消费 GitHub recent activity signal

## 4. 影响与边界

本轮没有改变的内容：

- `tech-radar.review` 主体仍是本地 summary 主链
- executor 仍只是 readonly capability plane
- `shared-context/tech-radar.json` 仍是 repo truth

本轮新增的价值：

- 对 GitHub radar 条目，周审查不再只看到“仓库存在 + 星数”
- 现在能直接看到“最近是否持续活跃提交、在改什么”

## 5. 剩余风险

1. 当前 `P0/P1` 未覆盖 source 仍有 1 条 `x/twitter`，但仓库里还没有同等稳定的 readonly capability 面。
2. `max_entries=5` 的选择逻辑仍可能让部分 `P1 github` 条目被高优先级 `arxiv` 条目挤出。
3. GitHub public API 的 rate limit 仍可能影响宿主侧补证据稳定性，但当前最近提交子调用已做 best-effort 失败隔离。

## 6. 一句话结论

> Wave 2 当前最值当的下一步不是扩新 source，而是把现有 `github` evidence enrichment 从静态 repo metadata 推进到 recent activity signal；这一步已在 `ALI-HERMES` 上真实落地并进入 `tech-radar-review` 报告。
