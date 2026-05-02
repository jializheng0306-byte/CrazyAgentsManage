# 自动情报捕获与痕迹留存 — 配置指南

> 日期: 2026-05-02  
> 状态: 已部署  

## 部署结构

- 规则文件: `~/.hermes/rules/intent-analysis-rules.json`
- 分析脚本: `scripts/auto-trace-to-bitable.py`
- 留痕脚本: `scripts/send-capture-trace-to-feishu.py`
- 回调钩子: `AGENTS.md` → `## Auto-Capture Trace Post-Hook`
- 版本控制副本: `config/rules/intent-analysis-rules.json`

## 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `BITABLE_APP_TOKEN` | Bitable Base 的 app_token | (空) |
| `BITABLE_TABLE_ID` | Bitable 表 ID | (空) |
| `CAPTURE_GROUP_CHAT_ID` | FlowMind 群 chat_id | `oc_bbde...` |
| `CAPTURE_USER_OPEN_ID` | 用户飞书 open_id | (空) |

## 手动测试

模拟外部任务完成后自动捕获:
```bash
echo '{"source_task":"evening-trend","raw_content":"测试: 今天发现了关于 multi-agent 的新 benchmark 报告、竞品动态..."}' | python3 scripts/auto-trace-to-bitable.py
```

## 验收标准

1. **规则匹配**: confidence>=40 触发留痕, <40 跳过
2. **Bitable 写入**: 新增一条 status=待确认 的记录
3. **群聊通知**: FlowMind 群收到摘要通知
4. **私聊通知**: 用户收到详细捕获内容
5. **日志记录**: `~/.hermes/logs/auto-capture-trace.log` 有对应记录
6. **故障隔离**: 规则文件损坏时不阻塞主流程
