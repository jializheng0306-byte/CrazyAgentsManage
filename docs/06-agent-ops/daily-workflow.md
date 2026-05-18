# 每日工作流 (Daily Workflow)

## 概述
CrazyAgentsManage项目的每日工作流，覆盖07:00-23:45全天运营节奏。

## 工作流时间表

### 07:00 - 08:00 晨间准备
- **07:00** 系统自检
  - 检查所有Agent状态
  - 验证API连接
  - 确认定时任务运行正常
- **07:30** 环境准备
  - 更新依赖
  - 拉取最新代码
  - 清理临时文件

### 08:00 - 09:00 晨间情报 (Morning Intel)
- **08:00** 情报采集
  - 技术博客监控 (blogwatcher)
  - 学术论文搜索 (arxiv)
  - 行业新闻聚合
- **08:30** 情报分析
  - 筛选相关度高的内容
  - 生成情报摘要
  - 标记需要关注的事项
- **08:45** 情报分发
  - 发送到飞书群
  - 更新知识库

### 09:00 - 10:00 承诺审查 (Promise Review)
- **09:00** 承诺状态检查
  - 获取所有待处理承诺
  - 检查截止日期
  - 评估进度状态
- **09:30** 审查报告生成
  - 统计各状态承诺数量
  - 识别即将到期承诺
  - 标记阻塞问题
- **09:45** 跟进动作触发
  - 通知相关人员
  - 更新承诺状态
  - 安排后续任务

### 10:00 - 12:00 核心工作时间
- 专注处理高优先级任务
- 与Codex CLI协作开发
- 代码审查和测试

### 12:00 - 13:00 午间论文解读 (Noon Paper Review)
- **12:00** 论文搜索
  - arxiv最新论文
  - 相关领域研究
- **12:30** 论文解读
  - 摘要提取
  - 关键点分析
  - 应用场景评估
- **12:45** 知识沉淀
  - 更新知识库
  - 生成学习笔记

### 13:00 - 17:00 下午工作时间
- 继续核心任务
- 会议和协作
- 代码提交和部署

### 17:00 - 18:00 日终总结
- **17:00** 进度汇总
  - 完成任务统计
  - 未完成任务分析
  - 明日计划制定
- **17:30** 问题记录
  - 记录遇到的问题
  - 分析原因
  - 制定解决方案
- **17:45** 知识归档
  - 整理当日学习内容
  - 更新记忆体系

### 20:00 - 21:00 晚间趋势分析 (Evening Trend Analysis)
- **20:00** 趋势监控
  - 技术趋势分析
  - 行业动态跟踪
  - 竞品动态观察
- **20:30** 分析报告
  - 生成趋势报告
  - 识别机会和风险
  - 提出建议
- **20:45** 决策支持
  - 更新项目路线图
  - 调整优先级
  - 规划下一步行动

### 23:00 - 23:45 每日反思 (Daily Reflection)
- **23:00** 当日回顾
  - 完成情况评估
  - 效率分析
  - 经验总结
- **23:30** 改进计划
  - 识别改进点
  - 制定改进措施
  - 更新工作流程
- **23:45** 系统维护
  - 日志清理
  - 数据备份
  - 系统优化

## 定时任务配置

### Cron Jobs
```bash
# 晨间情报 (08:30)
30 8 * * * /root/.hermes/scripts/morning-intel.sh

# 承诺审查统一刷新链（operator hours, only-if-changed）
*/30 8-21 * * * cd /root/CrazyAgentsManage && PROMISE_BITABLE_CONFIG_PATH=/root/CrazyAgentsManage/shared-context/promise-bitable-config.json PROMISE_LARK_AS=bot PROMISE_REVIEW_ONLY_IF_CHANGED=1 /usr/bin/python3 /root/.hermes/scripts/daily-promise-review.py >> /root/.hermes/logs/daily-promise-review.log 2>&1

# 午间论文解读 (12:00)
0 12 * * * /root/.hermes/scripts/noon-paper-review.sh

# 晚间趋势分析 (20:00)
0 20 * * * /root/.hermes/scripts/evening-trend-analysis.sh

# 每日反思 (23:00)
0 23 * * * /root/.hermes/scripts/daily-reflection.sh
```

### Hermes AI Cron Guard

除上述 `system crontab` 外，Hermes 还可能在：

- `~/.hermes/cron/jobs.json`

中维护 runtime-local AI cron job。

从 2026-05-16 起，涉及本地脚本路径的 AI cron 创建必须满足：

1. 脚本真实存在
2. 脚本是 git-tracked 文件
3. 若 prompt 用相对路径，必须同时提供 `workdir`
4. 候选方案 / 设计稿中的脚本名，不能直接进入 live runtime

对于承诺审查统一链，2026-05-16 起还增加：

5. 虽然 `system crontab` 每 30 分钟触发一次，但 `daily-promise-review.py` 会先计算承诺 + truth/trace/feedback 状态摘要
6. 只有摘要变化时，才执行 Bitable 写回、报告落盘和飞书群发送
7. 摘要不变时，脚本静默退出，不产生运营噪音

治理细则见：

- [hermes-runtime-ai-cron-guard-governance-2026-05-16.md](/home/flowmind/CrazyAgentsManage/docs/06-agent-ops/hermes-runtime-ai-cron-guard-governance-2026-05-16.md)

### 当前 AI Cron 保留原则

2026-05-16 起，`ALI-HERMES` 上的 AI cron 只保留：

1. 不与 `system crontab` 重复的任务
2. 有明确 repo source-of-truth 或已被治理批准的任务
3. provider 已验证可运行的任务

当前保留的启用中 AI cron 为：

- `Cron健康检查-每日两次`
- `Tech Radar周审查-每周日`

## 工作流工具

### 情报采集工具
- **blogwatcher**: RSS/博客监控
- **arxiv**: 学术论文搜索
- **web_extract**: 网页内容提取

### 承诺管理工具
- **promise-governance**: 承诺治理技能
- **flowmind-candidate-ingress**: 候选提交
- **flowmind-pilot**: 测试执行

### 协作工具
- **lark-cli**: 飞书消息发送
- **feishu-lark-cli-docs**: 飞书文档操作
- **git**: 代码版本控制

## 工作流优化

### 效率提升
- 自动化重复任务
- 批量处理同类工作
- 使用模板减少重复输入

### 质量保证
- 代码审查机制
- 测试覆盖要求
- 文档同步更新

### 持续改进
- 定期回顾工作流程
- 收集反馈意见
- 优化工作节奏

## 应急处理

### 紧急任务
- 优先处理紧急任务
- 调整当日计划
- 记录处理过程

### 系统故障
- 快速定位问题
- 启动备用方案
- 及时通知相关人员

### 任务延期
- 分析延期原因
- 调整时间计划
- 与相关方沟通

## 监控指标

### 效率指标
- 任务完成率
- 平均处理时间
- 代码提交频率

### 质量指标
- 测试通过率
- 缺陷密度
- 文档覆盖率

### 协作指标
- 响应时间
- 沟通效率
- 知识共享度

---

**最后更新**: 2026-04-26
**维护者**: HermesAgent
**版本**: 1.0
