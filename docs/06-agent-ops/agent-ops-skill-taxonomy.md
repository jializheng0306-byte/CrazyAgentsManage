# Agent运营技能分类体系

## 概述
CrazyAgentsManage项目的Agent运营技能分类体系，用于组织和管理运营相关的技能。

## 技能分类

### 1. 承诺治理类 (Promise Governance)
**职责**: 管理承诺全生命周期

**技能列表**:
- `promise-governance`: 承诺治理核心技能
  - capture-clarify: 捕获澄清
  - review-trigger: 审查触发
  - drift-detection: 漂移检测

**使用场景**:
- 用户提出需求时
- 承诺状态变更时
- 定期审查时

### 2. 情报采集类 (Intelligence Collection)
**职责**: 采集和分析情报信息

**技能列表**:
- `blogwatcher`: RSS/博客监控
- `arxiv`: 学术论文搜索
- `web_extract`: 网页内容提取

**使用场景**:
- 晨间情报采集(08:30)
- 午间论文解读(12:00)
- 晚间趋势分析(20:00)

### 3. 内容创作类 (Content Creation)
**职责**: 创建和管理内容

**技能列表**:
- `feishu-lark-cli-docs`: 飞书文档操作
- `content-curator`: 内容策展
- `report-generator`: 报告生成

**使用场景**:
- 生成审查报告
- 创建知识文档
- 整理学习笔记

### 4. 运维维护类 (Operations Maintenance)
**职责**: 系统运维和维护

**技能列表**:
- `ops-guardian`: 运维卫士
- `health-check`: 健康检查
- `alert-response`: 告警响应
- `performance-opt`: 性能优化

**使用场景**:
- 系统状态监控
- 故障处理
- 性能优化

### 5. 协作协调类 (Collaboration)
**职责**: 多Agent协作协调

**技能列表**:
- `feishu-relay`: 飞书消息中继
- `webhook-subscriptions`: 事件订阅
- `flowmind-candidate-ingress`: FlowMind候选提交
- `flowmind-pilot`: FlowMind测试执行

**使用场景**:
- 与Codex CLI协作
- 与FlowMind集成
- 事件驱动工作流

### 6. 知识管理类 (Knowledge Management)
**职责**: 知识积累和管理

**技能列表**:
- `promise-keeper`: 承诺管家
- `intel-sentinel`: 情报哨兵
- `memory-manager`: 记忆管理

**使用场景**:
- 知识库维护
- 经验总结
- 最佳实践记录

## 技能使用规范

### 触发条件
1. **明确触发**: 用户明确要求使用某技能
2. **自动触发**: 符合技能触发条件时自动加载
3. **上下文触发**: 根据对话上下文判断是否需要

### 使用流程
1. **识别需求**: 分析用户需求，确定所需技能
2. **加载技能**: 使用skill_view加载技能内容
3. **执行操作**: 按技能指导执行操作
4. **记录结果**: 记录操作结果和经验

### 技能组合
1. **承诺管理组合**: promise-governance + flowmind-candidate-ingress + flowmind-truth-query
2. **情报采集组合**: blogwatcher + arxiv + web_extract
3. **运维监控组合**: ops-guardian + health-check + alert-response

## 技能维护

### 新增技能
1. 识别新的运营需求
2. 设计技能内容
3. 创建技能文件
4. 测试技能功能
5. 更新分类体系

### 更新技能
1. 收集使用反馈
2. 识别改进点
3. 更新技能内容
4. 测试更新效果
5. 发布新版本

### 废弃技能
1. 识别不再需要的技能
2. 评估废弃影响
3. 迁移相关功能
4. 标记为废弃
5. 清理相关资源

## 技能评估指标

### 使用频率
- 高频: 每日使用
- 中频: 每周使用
- 低频: 每月使用

### 效率提升
- 显著提升: 节省50%以上时间
- 中等提升: 节省20-50%时间
- 轻微提升: 节省20%以下时间

### 质量保证
- 高质量: 错误率<1%
- 中等质量: 错误率1-5%
- 低质量: 错误率>5%

## 技能发展路线

### 短期目标(1个月)
- 完善现有技能
- 优化技能组合
- 提升使用效率

### 中期目标(3个月)
- 新增3-5个技能
- 建立技能评估体系
- 优化技能分类

### 长期目标(6个月)
- 建立技能市场
- 实现技能共享
- 形成技能生态

---

**最后更新**: 2026-04-26
**版本**: 1.0
**维护者**: HermesAgent
