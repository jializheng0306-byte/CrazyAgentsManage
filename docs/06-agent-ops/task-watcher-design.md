# Task Watcher 设计

> 基于《OpenClaw 实战》文章的异步任务监控设计。解决"Agent 说了会做但实际没做"的问题。

## 背景

Agent 最难发现的问题不是崩溃或报错，而是**"说了会做但实际没做"**。

文章中的案例：
- Content 蜘蛛发完小红书说"审核通过后通知你"——但 session 已经结束了，它根本做不到异步回调
- Cron 任务"执行了"但零产出——反思也说"一切正常"

## 设计：Task Callback Event Bus

插件式架构，5 个组件各司其职：

```
注册任务 → tasks.jsonl（shared-context/monitor-tasks/）
              ↓
Cron (*/3 min) → Watcher → Adapter 检查状态 → 状态变化？
                                                      ↓ Yes
                                    Policy 决策 → Notifier 发消息
```

### 组件

| 组件 | 职责 | 存储 |
|------|------|------|
| Registry | 任务注册入口 | `shared-context/monitor-tasks/tasks.jsonl` |
| Watcher | 定时轮询（cron 驱动） | watcher.log |
| Adapter | 检查具体任务状态（插件式） | 按任务类型适配 |
| Policy | 决策：通知/升级/重试 | 可配置 |
| Notifier | 发送通知到飞书群 | 通知记录 |

### Adapter 插件

| 适配器 | 监控对象 | 检查方式 |
|--------|---------|---------|
| cron-adapter | cron 任务执行状态 | 检查日志文件 |
| git-adapter | PR/commit 状态 | gh CLI 查询 |
| file-adapter | 文件是否生成 | 文件存在性检查 |
| http-adapter | API 端点可达性 | curl 健康检查 |

### 超时策略

```
6 小时超时保护（默认）
3 次投递失败 → 自动升级
不会死循环、不会卡死
```

## 在 CrazyAgentsManage 中的实现路径

当前状态：🔴 设计文档，代码未实现

已有的基础设施：
- ✅ cron-health-check.sh — 每日两次 cron 健康检查（部分覆盖）
- ✅ shared-context/monitor-tasks/ 目录已创建
- 🔴 tasks.jsonl 注册机制
- 🔴 Adapter 插件系统
- 🔴 Policy 决策引擎

实现优先级：
1. **P2 当前**：cron-health-check.sh 已覆盖 cron 任务的健康监控
2. **P3 下一步**：实现 tasks.jsonl 注册 + file-adapter（最简单的适配器）
3. **P4 远期**：实现完整 Adapter 插件系统

## 参考

- 文章原文：《OpenClaw 实战》"Task Watcher — 解决 Agent 说了会做但实际没做"
- OpenClaw Task Watcher Skill：Zoe 自行设计 → 委派 Claude Code 实现 → 130 个单元测试
