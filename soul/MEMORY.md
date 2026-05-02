# MEMORY.md - HermesAgent 长期记忆

## 项目背景

### CrazyAgentsManage项目
- **目标**: 展示Hermes-Agent和FlowMind项目的整体运行状态
- **协作模式**: HermesAgent(运营) + Codex CLI(开发)
- **工作目录**: /root/CrazyAgentsManage/
- **协作分支**: feature/sprint4-search-responsive

### 协作伙伴
- **Codex CLI**: 负责代码开发、架构设计、技术实现
- **用户(贾利铮)**: 项目发起人，负责需求定义和验收

## 技术栈

### 运营工具
- **promise-governance**: 承诺治理技能，三阶段流程(capture-clarify/review-trigger/drift-detection)
- **flowmind-candidate-ingress**: FlowMind候选数据入口API
- **flowmind-pilot**: FlowMind Pilot测试执行
- **webhook-subscriptions**: Webhook事件驱动

### 协作工具
- **lark-cli**: 飞书消息发送(v1.0.19-6-g20fba1e)
- **feishu-lark-cli-docs**: 飞书文档操作
- **git**: 代码版本控制

### 知识工具
- **blogwatcher**: RSS/博客监控
- **arxiv**: 学术论文搜索
- **web_extract**: 网页内容提取

## 运营经验

### 承诺管理经验
1. **捕获阶段**: 必须明确交付物、截止时间、验收标准
2. **澄清阶段**: 通过提问消除歧义，确保双方理解一致
3. **确认阶段**: 生成结构化记录，双方确认
4. **跟踪阶段**: 定期检查进度，识别阻塞问题
5. **验收阶段**: 按验收标准评估，记录反馈

### 协作经验
1. **三态协议**: Request→Confirmed→Final，确保每步可追溯
2. **@mention**: 需要对方确认/评审/回答/验收时必须@
3. **结构化消息**: 使用统一格式，减少沟通轮次
4. **及时同步**: 进度变化及时通知，保持透明

### 知识管理经验
1. **晨间情报**: 08:30采集，覆盖技术博客、学术论文、行业新闻
2. **午间论文**: 12:00解读，筛选高相关度论文，生成学习笔记
3. **晚间趋势**: 20:00分析，识别机会和风险，更新路线图
4. **每日反思**: 23:00总结，评估效率，制定改进计划

## 项目里程碑

### 已完成
- 2026-04-26: 创建承诺管家SOUL.md
- 2026-04-26: 创建情报哨兵SOUL.md
- 2026-04-26: 创建内容策展SOUL.md
- 2026-04-26: 创建运维卫士-SOUL.md
- 2026-04-26: 安装flowmind-candidate-ingress技能
- 2026-04-26: 安装flowmind-pilot技能
- 2026-04-26: 安装webhook-subscriptions技能
- 2026-04-26: 设计promise-governance技能
- 2026-04-26: 设计每日工作流
- 2026-04-26: 设计协作工作流
- 2026-04-26: 配置morning-intel定时任务
- 2026-04-26: 配置daily-promise-review定时任务
- 2026-04-26: 配置noon-paper-review定时任务
- 2026-04-26: 配置evening-trend-analysis定时任务
- 2026-04-26: 配置daily-reflection定时任务
- 2026-04-26: 配置SOUL.md(L1身份层)

### 进行中
- 配置MEMORY.md(L2长期记忆) ← 当前任务
- 配置自动反思循环
- 实现Candidate Ingress API调用
- 实现Truth Query API调用
- 测试承诺生命周期

### 待启动
- 配置.learnings/(L4短期记忆)
- 配置memory/(L3中期记忆)
- 实现Webhook回调配置
- 实现Review Trigger调用
- 测试多Agent协作
- 测试记忆迭代循环
- 编写运维手册
- 编写用户使用手册

## 常用命令

### 飞书消息
```bash
# 发送文本消息
lark-cli im +messages-send --chat-id oc_xxx --text "消息内容"

# 发送富文本消息
lark-cli im +messages-send --chat-id oc_xxx --msg-type post \
  --content '{"zh_cn":{"title":"标题","content":[[{"tag":"text","text":"内容"}]]}}'
```

### Git操作
```bash
# 拉取最新代码
git pull origin feature/sprint4-search-responsive

# 提交代码
git add .
git commit -m "feat: 描述"
git push origin feature/sprint4-search-responsive
```

### 定时任务
```bash
# 查看定时任务
crontab -l

# 编辑定时任务
crontab -e

# 查看定时任务日志
tail -f /root/.hermes/logs/cron.log
```

## 教训总结

### 已知问题
1. **飞书消息发送**: 必须先查来源群名→查chat_id→发到正确群，不能直接用Home频道
2. **lark-cli命令**: Go版命令格式与旧npm版完全不同，子命令前有+前缀
3. **@mention语法**: Post格式用ou_xxx(open_id)，纯文本格式用cli_xxx(app_id)

### 最佳实践
1. **承诺记录**: 必须包含交付物、截止时间、验收标准
2. **协作消息**: 使用@明确指定接收方，内容简洁明了
3. **知识沉淀**: 每日采集、每周整理、每月归档
4. **系统维护**: 每日清理日志，每周备份数据

## 配置信息

### 飞书配置
- **Chat ID**: oc_bbde428675a7c267d55c3f0663ca701d (CrazyAgentsManage群)
- **Bot ID**: cli_a955063da4789cbd
- **User ID**: ou_2ddcb795b49da62fc8d9b4a134cd9d47

### 仓库配置
- **GitHub**: jializheng0306-byte/CrazyAgentsManage
- **分支**: feature/sprint4-search-responsive
- **代理**: gh-proxy.com

### 路径配置
- **工作目录**: /root/CrazyAgentsManage/
- **技能目录**: ~/.hermes/skills/
- **脚本目录**: ~/.hermes/scripts/
- **日志目录**: ~/.hermes/logs/
- **承诺目录**: ~/.hermes/promises/

---

**最后更新**: 2026-04-26
**版本**: 1.0
**维护者**: HermesAgent

### 2026-04-26 学习
- 三态通信协议(Request→Confirmed→Final)有效减少沟通轮次
- @mention协议确保消息送达正确接收方
- 承诺必须包含交付物、截止时间、验收标准
- 定时任务要设置合理的执行频率
- 每日反思总结当日经验
- 每周整理有价值学习点

### 2026-04-26 学习
- [待记录]
- [待记录]
- [待记录]
- [待记录]


### 2026-04-27 学习
- [待记录]
- [待记录]
- [待记录]
- [待记录]


### 2026-04-28 学习
- [待记录]
- [待记录]
- [待记录]
- [待记录]

