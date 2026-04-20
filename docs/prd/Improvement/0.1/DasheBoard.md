问题1：Trace列表中蓝色标签内容显示不全
这是设计行为，不是bug。 具体原因：
在 dashboard.js:121 中，每条消息的标签文字被 truncate() 函数截断到 50-60个字符： 
JavaScript
复制
插入到光标处
添加到新文件
现在无法访问编辑器。 若要启用屏幕阅读器优化模式，请使用 Shift+Alt+F1
￼
￼
￼
CSS层面（dashboard.css:393-398）也设置了 text-overflow: ellipsis，超出部分显示省略号。
这是仿照 Vercel Workflow 时间轴的设计风格——在有限宽度的甘特图条内只能显示摘要，完整内容需要点击展开查看。但目前 onSpanClick() （dashboard.js:280）只做了 console.log，没有实现展开详情的功能。
￼
问题2：Dashboard页面完整功能清单
📋 页面结构总览（从上到下）
#
功能元素
UI位置
含义说明
数据源API
数据来源表
联动关系
A
全局导航栏
顶部
Hermes v0.5 品牌导航 + 11个页面入口
无（静态）
—
点击跳转到对应页面
A-1
Logo + 版本号
导航左侧
⚡ Hermes v0.5
静态HTML
—
—
A-2
概览
导航菜单
📊 首页入口
—
—
→ /manage/
A-3
Agent
导航菜单（当前激活态示例）
🟣 智能体管理
—
—
→ /manage/agent
A-4
任务
导航菜单
📋 任务编排
—
—
→ /manage/tasks
A-5
监控仪表板
导航菜单（当前页高亮）
📊 Dashboard
—
—
当前页
A-6
技能
导航菜单
⚡ 技能中心
—
—
→ /manage/skills
A-7
团队记忆
导航菜单
📝 记忆管理
—
—
→ /manage/team-memory
A-8
定时任务
导航菜单
⏰ Cron调度
—
—
→ /manage/cron
A-9
图谱
导航菜单
🔗 知识图谱
—
—
→ /manage/graph
A-10
流水线
导航菜单
🔴 会话列表
—
—
→ /manage/sessions
A-11
告警
导航菜单
🔔 系统告警
—
—
→ /manage/alerts
A-12
Token
导航菜单
💰 用量统计
—
—
→ /manage/tokens
A-13
搜索框
导航右侧
全局搜索占位
未实现
—
静态占位
A-14
收藏夹按钮
导航右侧
⭐ 收藏功能
未实现
—
静态占位
B
面包屑导航
标题上方
显示当前会话路径
loadSessionDetail()
sessions 表
B-6联动sessions页
B-1
返回箭头
◀
返回上一级
静态
—
视觉引导
B-2
"Hermes Agent"
文字
项目/代理名称
静态
—
品牌标识
B-3
"Workflows"
文字
工作流分类
静态
—
仿Vercel命名
B-4
会话ID
sessionRunId
当前会话ID（截取前12位）
GET /api/dashboard/session/<id>→ session.id
sessions.id
切换会话时更新
B-5
外链图标
↗
跳转到全部会话列表
静态链接
—
→ /manage/sessions
C
任务标题行
面包屑下方
会话名称 + 状态 + 操作按钮
updateHeader()
sessions 表
C-3联动刷新
C-1
任务名称
taskName (h1)
会话标题，默认"Hermes 会话追踪"
session.title
sessions.title
为空时显示默认值
C-2
状态徽章
statusPill
运行状态指示器（带脉冲动画圆点）
session.ended_at 判断
sessions.ended_at
有ended_at→绿色Completed；无→蓝色Running
C-3
"查看全部会话" 按钮
右侧操作区
跳转到sessions页面
静态链接
—
→ /manage/sessions
C-4
⋮ 更多菜单按钮
右侧操作区
弹出上下文菜单（4个选项）
toggleMenu()
JS函数
见下方菜单项
C-4-a
🔄 刷新数据
菜单项
重新加载最新会话数据
loadLatestSession()
sessions + messages 表
刷新整个时间轴
C-4-b
🔍 适应视图
菜单项
重置缩放级别为1x
fitToView()
JS状态
重绘时间轴
C-4-c
📊 查看全部会话
菜单项
跳转sessions页
静态链接
—
→ /manage/sessions
C-4-d
⏱️ 自动刷新开关
菜单项
5秒自动刷新的启停控制
startAutoRefresh() / clearInterval
JS定时器
开：每5s调loadLatestSession()；关：停止定时器
D
元数据条(Metadata Strip)
标题行下方
6个关键指标卡片
updateHeader()
sessions 表
随会话切换更新
D-1
创建时间
metaCreated
会话开始时间（相对时间格式如"9h ago"）
session.started_at
sessions.started_at
formatTimeAgo() 格式化
D-2
完成时间
metaCompleted
会话结束时间（相对时间）或"--"
session.ended_at
sessions.ended_at
未完成时显示--
D-3
持续时间
metaDuration
会话总时长（格式化如"9h 46m"）
计算 ended_at - started_at
sessions 两字段
进行中用 now - started_at
D-4
Token消耗
metaTokens
输入+输出Token总数（K/M单位）
session.input_tokens + output_tokens
sessions.input_tokens/output_tokens
formatTokenCount() 格式化
D-5
消息数
metaMessages
该会话的消息条数
`(session.messages
￼
[]).length`
D-6
来源
metaSource
会话来源平台（cli/telegram/api_server等）
session.source
sessions.source
对应sessions页的来源筛选
E
标签页栏(Tab Bar)
元数据下方
三个视图切换标签
switchTab()
JS切换
切换时间轴主体内容
E-1
Trace 标签
默认激活
📊 Gantt甘特图时间轴视图
buildTimeline()
messages 表
显示消息的时间线条
E-2
Events 标签
可切换
📋 事件列表视图（纯文本日志）
renderEventsTab()
messages 表
同一数据的另一种展示形式
E-3
Streams 标签
可切换
📡 SSE实时流监控视图
renderStreamsTab() + EventSource
sessions 表轮询
实时推送新会话/心跳事件
F
搜索栏
标签下方
过滤Trace中的span条目
filterTimeline()
DOM过滤
仅影响可见性，不重新请求
F-1
搜索图标
🔍 左侧装饰
搜索视觉提示
静态SVG
—
—
F-2
搜索输入框
timelineSearch
关键词搜索span标签文字
input 事件
—
实时过滤 .vw-row 的display属性
G
时间轴容器(Timeline)
页面核心区域
Gantt甘特图可视化区域
buildTimeline() → renderRuler() + renderGrid()
messages 表
整个dashboard的核心
G-1
时间标尺(Ruler)
时间轴顶部
时间刻度线 + 时间标签
renderRuler(baseTime, totalDuration)
计算值
根据 totalDuration 动态计算刻度间隔（6-20格）
G-1-a
刻度标签
vw-ruler-tick
时间数值（如"0s", "1:30", "2:15"）
formatTimelineTick()
计算值
<60s显示秒数，<3600显示m:ss，否则h:mm
G-1-b
垂直网格线
vw-ruler-grid-line
时间列分隔线
与刻度对齐
CSS
半透明参考线
G-2
时间轴网格(Grid)
时间轴主体
每一行是一个消息span（Gantt条）
renderGrid(spans, baseTime, totalDuration)
messages 表
每条message生成一个.vw-row
G-2-a
用户消息条
蓝灰渐变背景
👤 用户输入的内容预览
msg.role === 'user'
messages 表
class: vw-span-info，level=0（无缩进）
G-2-b
助手回复条
绿色(完成)/蓝色(运行中)
🤖 AI回复内容预览
msg.role === 'assistant'
messages 表
finish_reason='stop'→success(绿)；否则→running(蓝)
G-2-c
工具调用条
蓝色/橙色/红色/棕色
🔧 工具执行记录
msg.role === 'tool'
messages 表
level=1（缩进一层），根据tool_name着色
G-2-d
系统提示条
蓝灰色
⚙️ 系统指令
msg.role === 'system'
messages 表
class: vw-span-info
G-2-e
Span标签文字
条内部左侧
消息内容截断（50-60字符+省略号）
truncate(msg.content)
messages.content
这就是你看到的"显示不全"的文字
G-2-f
Span持续时间
条内部右侧
该消息的处理时长
计算 endTime - startTime
计算值
formatDuration() 格式化
G-2-g
树形连接线
缩进层级左侧
tool调用的父子关系连线
vw-tree-line-v
JS逻辑
当span.level > 0且上一行level较小时绘制
G-2-h
点击事件
整个span条可点击
目前仅console.log
onSpanClick(span)
span对象
未实现详情弹窗（可扩展）
H
缩放控制栏
时间轴右下方
三个缩放按钮
zoomLevel变量
JS状态
影响span的left%和width%计算
H-1
🔍+ 放大
按钮
放大1.5倍（最大5x）
zoomIn()
JS
重建时间轴
H-2
🔍− 缩小
按钮
缩小1.5倍（最小0.2x）
zoomOut()
JS
重建时间轴
H-3
⊡ 适应视图
按钮
重置为1x原始比例
fitToView()
JS
重建时间轴
I
底部Footer
最底部
版权/说明文字
静态
—
"基于SessionDB实时数据构建"
￼
🔄 数据流与联动关系图 
PlainText
复制
插入到光标处
添加到新文件
现在无法访问编辑器。 若要启用屏幕阅读器优化模式，请使用 Shift+Alt+F1
￼
￼
￼
￼
￼
⚠️ 当前已知的设计缺陷/待完善项
#
问题
位置
建议
1
Span标签文字被截断无展开方式
G-2-e
实现onSpanClick()弹窗显示完整内容
2
搜索框(F)只搜索Trace tab
F-2
切换Events/Streams时应清空或隐藏搜索框
3
Streams tab的EventSource路径硬编码
dashboard.js:371
已修复为window.APP_BASE但该行用了字符串拼接而非模板
4
"查看全部会话"按钮路径硬编码
dashboard.html:71
应改为{{ BASE }}/sessions
5
导航栏"概览"链接用绝对路径/
dashboard.html:24
应改为{{ BASE }}/
6
自动刷新不可配置间隔
C-4-d
固定5秒，可考虑添加设置选项