# 协作工作流 (Collaboration Workflow)

## 概述
CrazyAgentsManage项目采用三态通信协议，实现HermesAgent与Codex CLI之间的高效协作。

## 三态通信协议

### 状态定义
```
Request → Confirmed → Final
```

1. **Request（请求）**: 发起方提出需求或任务
2. **Confirmed（确认）**: 接收方确认接收并开始处理
3. **Final（完成）**: 处理完成，返回结果

### 状态转换规则
- Request → Confirmed: 接收方确认接收
- Confirmed → Final: 处理完成
- Final → Request: 新一轮协作开始

## 协作角色

### HermesAgent（运营方）
- **职责**: 运营框架、任务管理、进度跟踪
- **输出**: 任务需求、验收标准、进度报告
- **输入**: 代码实现、技术方案、测试结果

### Codex CLI（开发方）
- **职责**: 代码开发、架构设计、技术实现
- **输出**: 代码提交、技术文档、测试报告
- **输入**: 需求文档、验收标准、反馈意见

## 协作流程

### 1. 需求发起 (Request)
**HermesAgent发起**:
```
@codex cli 需求: [任务描述]
- 交付物: [具体交付物]
- 截止时间: [时间]
- 验收标准: [标准]
```

**Codex CLI发起**:
```
@HermesAgent 技术方案: [方案描述]
- 实现方式: [技术方案]
- 预计时间: [时间]
- 需要支持: [资源需求]
```

### 2. 确认接收 (Confirmed)
**HermesAgent确认**:
```
@codex cli 确认: 已收到需求
- 预计完成: [时间]
- 需要澄清: [问题]
```

**Codex CLI确认**:
```
@HermesAgent 确认: 已收到方案
- 开始时间: [时间]
- 预计完成: [时间]
```

### 3. 完成交付 (Final)
**HermesAgent完成**:
```
@codex cli 完成: [任务名称]
- 交付物: [文件/链接]
- 验收状态: [通过/待修改]
- 反馈: [意见]
```

**Codex CLI完成**:
```
@HermesAgent 完成: [任务名称]
- 代码提交: [commit hash]
- 测试结果: [通过/失败]
- 文档更新: [文件列表]
```

## 协作场景

### 场景1: 新功能开发
```
HermesAgent: @codex cli 需求: 设计登录页面
- 交付物: 登录页面代码
- 截止时间: 本周五
- 验收标准: 包含用户名/密码输入框、登录按钮

Codex CLI: @HermesAgent 确认: 已收到需求
- 预计完成: 周四
- 技术方案: React + TypeScript

Codex CLI: @HermesAgent 完成: 登录页面
- 代码提交: abc123
- 测试结果: 通过
- 文档: docs/login.md

HermesAgent: @codex cli 验收: 通过
- 代码质量: 优秀
- 测试覆盖: 95%
- 建议: 增加错误提示
```

### 场景2: 问题修复
```
HermesAgent: @codex cli 问题: 登录按钮无响应
- 严重程度: 高
- 影响范围: 所有用户
- 复现步骤: [步骤]

Codex CLI: @HermesAgent 确认: 已收到问题
- 预计修复: 2小时
- 原因分析: 事件绑定错误

Codex CLI: @HermesAgent 完成: 修复登录按钮
- 代码提交: def456
- 测试结果: 通过
- 修复方案: 重新绑定事件

HermesAgent: @codex cli 验收: 通过
- 修复效果: 正常
- 回归测试: 通过
```

### 场景3: 架构优化
```
HermesAgent: @codex cli 需求: 优化数据库查询性能
- 交付物: 优化方案
- 截止时间: 下周一
- 验收标准: 查询时间减少50%

Codex CLI: @HermesAgent 确认: 已收到需求
- 预计完成: 周五
- 技术方案: 索引优化 + 缓存

Codex CLI: @HermesAgent 完成: 数据库优化
- 代码提交: ghi789
- 测试结果: 查询时间减少60%
- 文档: docs/db-optimization.md

HermesAgent: @codex cli 验收: 通过
- 性能提升: 60%
- 稳定性: 良好
- 建议: 监控查询性能
```

## 协作工具

### 消息发送
```bash
# 发送文本消息
lark-cli im +messages-send --chat-id oc_xxx --text "消息内容"

# 发送富文本消息
lark-cli im +messages-send --chat-id oc_xxx --msg-type post \
  --content '{"zh_cn":{"title":"标题","content":[[{"tag":"text","text":"内容"}]]}}'
```

### 代码协作
```bash
# 拉取最新代码
git pull origin feature/sprint4-search-responsive

# 提交代码
git add .
git commit -m "feat: 添加登录页面"
git push origin feature/sprint4-search-responsive

# 查看状态
git status
git log --oneline -5
```

### 文档协作
```bash
# 创建文档
lark-cli api POST '/open-apis/docx/v1/documents' --data '{"title":"文档标题"}'

# 更新文档
lark-cli api PATCH '/open-apis/docx/v1/documents/{document_id}' --data '{"content":"内容"}'
```

## 协作规范

### 消息规范
- 使用@明确指定接收方
- 消息内容简洁明了
- 包含必要上下文信息
- 使用统一格式

### 代码规范
- 遵循项目编码规范
- 提交前运行测试
- 编写清晰的提交信息
- 及时更新文档

### 文档规范
- 使用统一模板
- 保持文档同步更新
- 记录重要决策
- 标注版本信息

## 冲突处理

### 意见分歧
1. 双方陈述观点
2. 分析利弊
3. 寻找共识
4. 达成一致

### 资源冲突
1. 优先级排序
2. 资源分配
3. 时间协调
4. 平行处理

### 技术分歧
1. 技术评估
2. 方案对比
3. 专家意见
4. 最终决策

## 监控与改进

### 协作效率指标
- 响应时间: < 30分钟
- 任务完成率: > 90%
- 沟通轮次: < 5轮/任务

### 质量指标
- 代码审查通过率: > 95%
- 测试覆盖率: > 80%
- 文档完整度: > 90%

### 持续改进
- 定期回顾协作流程
- 收集反馈意见
- 优化协作机制
- 更新协作规范

---

**最后更新**: 2026-04-26
**维护者**: HermesAgent
**版本**: 1.0
