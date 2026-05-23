# 三态通信协议

> 基于《OpenClaw 实战》文章的通信协议设计，防止 Agent 间 ACK 风暴。

## 背景

当两个 Agent 互相 @ 对方时，会产生经典的 ACK Storm：A → B → A → B → ... 无限循环。

文章中 Macro 和 Trading 在"伊朗局势对 A 股影响"上互相"收到/确认/感谢"刷了十几轮，分析早就做完了但停不下来。

根因不是"Agent 太客套"，是**缺乏终态协议**。

## 协议设计

### 固定三态协议（强制）

```
[request]    @对方 + ack_id + 期望动作 + 截止时间
             模板: @agent [state=request] [ack_id=topic-YYYYMMDDHHMM]
             
[confirmed]  @发起方 + ack_id + 版本号/生效时间/关键结论
             模板: @requester [state=confirmed] [ack_id=...] 版本=vN
             
[final]      @相关方 + ack_id + 终态收敛（全线程仅 1 条）
             发出后全员进入静默，"收到/感谢/OK" → NO_REPLY
```

### 超时规则

```
5 分钟无 confirmed → 催办 1 次
10 分钟仍无 → 升级 Zoe 仲裁
```

### 线程规则

```
- 同一线程只允许一个 ack_id，新一轮必须新开
- final 后禁止续话；必须补充时优先 edit 既有消息
- sessions_send 超时 ≠ 失败 → 同一 ack_id 不得重试
- 同一内容最多重试 1 次；第二次超时 → shared-context/ 文件投递
```

## 子线程策略

多轮协作的内容任务默认开专用子线程（命名: `<主题>-<负责人>-<日期>`），主频道只同步三次状态：

```
[Dispatch] → [ACK] → [DraftReady]
```

## 三种通信机制

| 机制 | 用途 | 示例 |
|------|------|------|
| sessions_send | 实时任务分派/圆桌讨论 | Zoe → Macro "分析伊朗局势" |
| shared-context/ | 异步状态共享 | Macro 写入宏观因子包 → Trading 直接读取 |
| 知识归档 | 结构化素材接口 | ainews 报告末尾留"改写要点" → content 消费 |

## DRI 原则

一个问题只有一个 Directly Responsible Individual 出最终结论。非 DRI 只能补充，不能覆盖。Zoe 组织和归档，不替代专业 Agent 出专业意见。

## 在 CrazyAgentsManage 中的实现路径

当前状态：🟡 已有 repo-tracked 最小实现

当前仓库已具备：

1. `scripts/three_state_protocol.py`
   - `send / confirm / final`
   - request status transition
   - automation promotion state update
2. `shared-context/agent-requests/requests.jsonl`
   - request bus 主对象流
3. `shared-context/agent-requests/events.jsonl`
   - transition / promotion 审计事件流
4. WebUI `Tasks`
   - `inbox / working / outbox / archive`
   - operator 可见的 status transition
   - prototype → rehearsed → approved-for-automation → automated 晋升门槛

当前仍未完成的，是把它进一步与 role isolation、executor capability plane、Operations control room 做更深耦合，而不是继续停留在“是否有协议脚本”的层面。

实现优先级：
1. P2: 在飞书群协作中人工遵守三态协议
2. P3: 在 delegate_task 中加入 ack_id 追踪
3. P4: 文件级状态存储 + WebUI 控制面已落最小 lane
4. 后续: role isolation / executor capability plane / Operations control room 深化

## 参考

- 文章原文：《OpenClaw 实战》"核心问题三：多 Agent 协作是协议问题，不是群聊问题"
- HermesAgent 运营设计：`docs/06-agent-ops/hermes-agent-operations-design.md` Part 2.2.2
