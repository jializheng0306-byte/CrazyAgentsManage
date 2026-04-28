# Hermes Config 变更记录

> P1 实施：session Harness 参数调优

## 变更日期：2026-04-29

## 变更内容

### 1. sessions 配置

```yaml
# 变更前
sessions:
  auto_prune: false
  retention_days: 90

# 变更后
sessions:
  auto_prune: true
  retention_days: 7
```

**原因**：文章描述 session 膨胀是 P0 事故根因。90 天保留期过长，改为 7 天自动清理。
对应文章中的 `session.maintenance.pruneAfter: "7d"`。

### 2. checkpoints 配置

```yaml
# 变更前
checkpoints:
  auto_prune: false

# 变更后
checkpoints:
  auto_prune: true
```

**原因**：启用自动清理过期 checkpoint，防止磁盘被撑满。

### 3. compression 配置

```yaml
# 变更前
compression:
  threshold: 0.5

# 变更后
compression:
  threshold: 0.4
```

**原因**：将压缩触发阈值从 50% 降到 40%，更早触发压缩，防止 session 膨胀到危险水平。
对应文章中的 `compaction.memoryFlush.softThresholdTokens: 40000`。

## 未变更项（需要 Hermes 框架支持）

| 参数 | 文章描述 | Hermes 现状 | 说明 |
|------|---------|------------|------|
| session reset | 每天 5:00 自动重置 | 无对应机制 | 需要框架级支持 |
| contextPruning cache-ttl | 6h TTL 裁剪 | 无对应机制 | compression 部分覆盖 |
| memoryFlush | 超阈值提取精华到 memory/ | 无对应机制 | 用 cron 脚本模拟 |
| bootstrap hook | 启动时注入历史经验 | prefill_messages_file 可部分覆盖 | 见 bootstrap-context.sh |

## 参考

- 文章配置：`docs/06-agent-ops/hermes-agent-operations-design.md` 附录 A.1
- 路线图：`docs/roadmap/prd-execution-roadmap.md` Phase 4 P1
