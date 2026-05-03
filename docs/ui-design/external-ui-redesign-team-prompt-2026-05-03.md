# External UI Redesign — Team Assessment Prompt

> 日期: 2026-05-03  
> 收件方: 外部 UI 设计团队  
> 发起方: CrazyAgentsManage 运营侧（HermesAgent）

---

## 评估目标

对 CrazyAgentsManage WebUI 的当前实现状态做独立评估，并给出重设计方案建议。

---

## 需要评估的事项

### 1. 一级 IA 是否合理

当前 IA 为 6 个一级页面 + 1 个动态页面：
- `/overview` — 总览
- `/runtime` — 运行态
- `/operations` — 运营面
- `/governance` — 治理面
- `/collaboration` — 协作面
- `/timeline` — 承诺时序图（动态，数据来自 FlowMind trace）

请评价：
- 分类是否清晰、互不重叠
- 命名的外部可理解性
- 是否有明显的缺失或冗余

### 2. 页面分工是否清楚

每个页面有对应的 PRD 规格文档（见 handoff 包的补充参考）。请评价：
- 每页的职责边界是否明确
- 是否存在"一页做多件事"或"多页做一件事"

### 3. 当前 UI 实现质量

当前实现以 Flask Jinja2 模板 + 原生 HTML/CSS/JS 为主。请评价：
- 是否有"旧页面平铺"痕迹（模板堆砌而非组件化）
- 数据消费面（timeline 的 traceEvents[]、handoff 的 moduleDetails.handoff）是否已可作为 UI 数据合同
- 交互一致性

### 4. 重设计方案建议

请给出：
- 建议的前端技术栈（是否引入框架/组件库）
- 建议的组件拆分方案
- 建议的 IA 调整（如有）
- 迁移路径（一次性重写 vs 渐进式替换）
- 工作量估算

---

## 不做什么

- **不**要求产出高保真设计稿（此轮只需评估和建议）
- **不**要求修改后端 API 或数据契约
- **不**要求处理部署/运维

---

## 交付要求

1. 一份评估报告（Markdown 或 PDF）
2. 至少覆盖上述 4 个评估事项
3. 如有重设计建议，附带简要的组件树/页面结构草图
4. 对 IA 的每个页面的独立评价

---

## 判断标准

| 维度 | 可接受 | 优秀 |
|---|---|---|
| IA 评价 | 指出至少 1 个改进点 | 给出具体重构方案 |
| 页面分工 | 确认边界清晰 | 提出合并/拆分建议 |
| 当前实现 | 指出模板平铺问题 | 给出组件化方案 |
| 重设计建议 | 给出一套合理技术栈 | 附带迁移路径和估时 |

---

## 参考资料（仓库内已有）

| 文档 | 路径 |
|---|---|
| 交接包 | `docs/ui-design/external-ui-redesign-handoff-2026-05-03.md` |
| 上位产品文档 | `docs/prd/hermesagent-hosted-flowmind-product-foundation.md` |
| 页面 PRD（6 页） | `docs/prd/pages/*.md` |
| 运营实现 PRD | `docs/prd/operations-implementation-prd.md` |
| 技术实现 PRD | `docs/prd/technical-implementation-prd.md` |
| WebUI README | `src/webui/README.md` |
| 联合产品基线 | `docs/roadmap/HermesAgent-FlowMind-联合产品功能基线-2026-04-30.md` |
