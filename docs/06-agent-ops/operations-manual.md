# CrazyAgentsManage 运维手册

## 概述
本手册提供CrazyAgentsManage项目的运维指南，包括系统监控、故障处理、性能优化等内容。

## 系统架构

### 核心组件
- **HermesAgent**: 运营Agent，负责任务管理、知识采集、协作协调
- **Codex CLI**: 开发Agent，负责代码开发、架构设计、技术实现
- **FlowMind**: 承诺管理系统，负责承诺生命周期管理
- **飞书**: 协作平台，负责消息通信、文档共享

### 目录结构
```
/root/CrazyAgentsManage/
├── src/                    # 源代码
│   ├── integrations/       # 集成模块
│   └── ...
├── docs/                   # 文档
│   └── 06-agent-ops/       # 运营文档
├── soul/                   # 身份定义
│   ├── SOUL.md             # L1身份层
│   └── MEMORY.md           # L2长期记忆
└── tests/                  # 测试

~/.hermes/
├── scripts/                # 运维脚本
├── logs/                   # 日志文件
├── promises/               # 承诺记录
├── learnings/              # L4短期记忆
├── memory/                 # L3中期记忆
└── skills/                 # 技能库
```

## 日常运维

### 每日检查清单
1. **系统状态检查**
   - CPU使用率 < 80%
   - 内存使用率 < 85%
   - 磁盘使用率 < 90%

2. **服务状态检查**
   - Hermes Gateway: `systemctl status hermes-gateway`
   - Cron服务: `systemctl status cron`
   - 飞书连接: 检查消息发送是否正常

3. **定时任务检查**
   - 晨间情报(08:30): 检查执行日志
   - 承诺审查(09:00): 检查审查报告
   - 午间论文(12:00): 检查论文采集
   - 晚间趋势(20:00): 检查趋势分析
   - 每日反思(23:00): 检查反思报告
   - AI Cron: 检查 `~/.hermes/cron/jobs.json` 是否出现未受仓库追踪的新 job

4. **承诺状态检查**
   - 待处理承诺数
   - 即将到期承诺数
   - 逾期承诺数

### 每周检查清单
1. **记忆维护**
   - 运行weekly-memory-maintenance.sh
   - 检查.learnings目录
   - 检查memory目录
   - 更新MEMORY.md

2. **技能更新**
   - 检查技能库更新
   - 测试新技能功能
   - 清理废弃技能

3. **性能优化**
   - 分析系统日志
   - 识别性能瓶颈
   - 执行优化措施

## 故障处理

### 常见故障及处理

#### 1. 定时任务未执行
**症状**: 定时任务未在预定时间执行

**排查步骤**:
```bash
# 检查cron服务状态
systemctl status cron

# 检查定时任务配置
crontab -l

# 检查 Hermes AI cron job
cat ~/.hermes/cron/jobs.json

# 检查执行日志
tail -f /root/.hermes/logs/cron.log

# 手动执行测试
python3 /root/.hermes/scripts/morning-intel-v2.py
```

**处理方法**:
1. 确认cron服务运行中
2. 区分是 `system crontab` 还是 `~/.hermes/cron/jobs.json` 的 job 在失败
3. 检查脚本执行权限
4. 检查脚本语法错误
5. 查看错误日志定位问题

#### 1.1 AI Cron 创建治理

当需要创建 Hermes 自己的 AI cron job 时，必须先遵守：

- `~/.hermes/cron/jobs.json` 是 runtime-local state，不是 repo truth
- prompt 中引用本地脚本前，先校验文件存在且为 git-tracked
- backlog / 设计稿 / issue 评论中的候选脚本名，不能直接创建成 live job

详细规则见：

- [hermes-runtime-ai-cron-guard-governance-2026-05-16.md](/home/flowmind/CrazyAgentsManage/docs/06-agent-ops/hermes-runtime-ai-cron-guard-governance-2026-05-16.md)

#### 2. 飞书消息发送失败
**症状**: 消息无法发送到飞书群

**排查步骤**:
```bash
# 检查lark-cli认证
lark-cli auth status

# 测试消息发送
lark-cli im +messages-send --chat-id oc_bbde428675a7c267d55c3f0663ca701d --text "测试消息"

# 检查网络连接
ping open.feishu.cn
```

**处理方法**:
1. 确认lark-cli已认证
2. 检查chat_id是否正确
3. 检查网络连接
4. 重新认证lark-cli

#### 3. FlowMind连接失败
**症状**: 无法连接FlowMind API

**排查步骤**:
```bash
# 测试FlowMind连接
curl -s "https://exclusive-harrison-mixed-dat.trycloudflare.com/api/health"

# 检查认证token
echo $FLOWMIND_TOKEN

# 测试API调用
python3 -c "
import requests
r = requests.get('https://exclusive-harrison-mixed-dat.trycloudflare.com/api/health')
print(r.status_code)
"
```

**处理方法**:
1. 确认FlowMind服务运行中
2. 检查Cloudflare隧道状态
3. 验证认证token
4. 联系FlowMind管理员

#### 4. 磁盘空间不足
**症状**: 系统提示磁盘空间不足

**排查步骤**:
```bash
# 检查磁盘使用率
df -h

# 查找大文件
du -sh /root/.hermes/* | sort -rh | head -10

# 检查日志文件大小
du -sh /root/.hermes/logs/*
```

**处理方法**:
1. 清理旧日志文件
2. 清理临时文件
3. 归档历史数据
4. 扩展磁盘空间

#### 5. 内存使用过高
**症状**: 系统响应缓慢

**排查步骤**:
```bash
# 检查内存使用
free -h

# 查看进程内存占用
ps aux --sort=-%mem | head -10

# 检查Hermes进程
ps aux | grep hermes
```

**处理方法**:
1. 识别内存占用高的进程
2. 重启异常进程
3. 优化内存使用
4. 增加系统内存

## 性能优化

### 系统优化
1. **清理临时文件**
   ```bash
   # 清理超过7天的日志
   find /root/.hermes/logs -name "*.log" -mtime +7 -delete
   
   # 清理临时文件
   find /tmp -name "hermes-*" -mtime +1 -delete
   ```

2. **优化定时任务**
   - 调整任务执行频率
   - 合并同类任务
   - 错开执行时间

3. **数据库优化**
   - 定期清理过期数据
   - 优化查询语句
   - 添加必要索引

### 应用优化
1. **减少API调用**
   - 缓存API响应
   - 批量处理请求
   - 使用本地数据

2. **优化消息发送**
   - 合并多条消息
   - 使用富文本格式
   - 减少不必要的@mention

3. **提高采集效率**
   - 并行采集多个源
   - 增量更新数据
   - 智能过滤内容

## 备份恢复

### 备份策略
1. **每日备份**
   - 承诺记录: ~/.hermes/promises/
   - 学习记录: ~/.hermes/learnings/
   - 配置文件: ~/.hermes/config/

2. **每周备份**
   - 记忆数据: ~/.hermes/memory/
   - 技能库: ~/.hermes/skills/
   - 项目代码: /root/CrazyAgentsManage/

### 备份命令
```bash
# 创建备份目录
BACKUP_DIR="/root/backups/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# 备份Hermes数据
cp -r ~/.hermes/promises "$BACKUP_DIR/"
cp -r ~/.hermes/learnings "$BACKUP_DIR/"
cp -r ~/.hermes/memory "$BACKUP_DIR/"

# 备份项目代码
tar -czf "$BACKUP_DIR/CrazyAgentsManage.tar.gz" -C /root CrazyAgentsManage

echo "备份完成: $BACKUP_DIR"
```

### 恢复命令
```bash
# 恢复Hermes数据
BACKUP_DIR="/root/backups/20260426"
cp -r "$BACKUP_DIR/promises" ~/.hermes/
cp -r "$BACKUP_DIR/learnings" ~/.hermes/
cp -r "$BACKUP_DIR/memory" ~/.hermes/

# 恢复项目代码
tar -xzf "$BACKUP_DIR/CrazyAgentsManage.tar.gz" -C /root

echo "恢复完成"
```

## 监控告警

### 监控指标
1. **系统指标**
   - CPU使用率
   - 内存使用率
   - 磁盘使用率
   - 网络延迟

2. **服务指标**
   - Hermes状态
   - Cron任务状态
   - API响应时间
   - 错误率

3. **业务指标**
   - 承诺完成率
   - 情报采集率
   - 报告生成率

### 告警规则
1. **P0-紧急**
   - 系统宕机
   - 数据丢失
   - 服务完全不可用

2. **P1-严重**
   - CPU > 90%
   - 内存 > 95%
   - 磁盘 > 95%
   - 服务异常

3. **P2-一般**
   - CPU > 80%
   - 内存 > 85%
   - 磁盘 > 90%
   - 性能下降

4. **P3-轻微**
   - 告警信息
   - 建议优化
   - 非关键错误

## 安全管理

### 访问控制
1. **文件权限**
   - 敏感文件: 600
   - 配置文件: 644
   - 脚本文件: 755

2. **服务权限**
   - Hermes服务: root
   - Cron服务: root
   - Web服务: www-data

### 安全检查
1. **定期检查**
   - 检查系统更新
   - 检查安全补丁
   - 检查访问日志

2. **事件响应**
   - 安全事件报告
   - 应急响应流程
   - 事后分析总结

## 联系方式

### 技术支持
- **HermesAgent**: 飞书群@HermesAgent
- **Codex CLI**: 飞书群@codex cli
- **用户(贾利铮)**: 飞书私信

### 紧急联系
- **系统故障**: 立即通知所有相关人员
- **数据丢失**: 立即启动备份恢复流程
- **安全事件**: 立即隔离受影响系统

---

**最后更新**: 2026-04-26
**版本**: 1.0
**维护者**: HermesAgent
