# Hermes Agent 可观测性数据增强设计文档

> **来源**：基于对 `D:\opensource\hermes-agent` 的深度代码扫描和阿里云服务器生产数据库（state.db）实测分析
> **日期**：2026-04-22
> **状态**：设计稿

---

## 一、探索方法论

### 1.1 探索范围

| 探索维度 | 方法 | 工具 |
|---------|------|------|
| 数据模型定义 | 扫描所有 dataclass/TypedDict/CREATE TABLE | `grep`, `ast.parse` |
| 数据库操作 | 搜索 sqlite3/INSERT/append_message | `grep`, 代码追踪 |
| Token统计 | 搜索 token_count/usage/response.choices | `grep`, 代码审查 |
| 工具调用 | 搜索 tool_call/handle_function_call | `grep`, 代码审查 |
| 错误追踪 | 搜索 error/exception/traceback | `grep`, 代码审查 |
| 时间追踪 | 搜索 time.time()/duration/elapsed | `grep`, 代码审查 |
| 遥测观测 | 搜索 telemetry/observability/trace/span | `grep`, 代码审查 |
| 生产数据验证 | 远程 SSH 查询 state.db 真实数据 | `sqlite3`, `paramiko` |

### 1.2 生产数据规模

| 指标 | 数值 | 来源 |
|------|------|------|
| 会话数 | 32 | sessions 表 COUNT |
| 消息数 | 1884 | messages 表 COUNT |
| 总输入Token | 21,764,573 | SUM(input_tokens) |
| 总输出Token | 188,056 | SUM(output_tokens) |
| 缓存读取Token | 30,208 | SUM(cache_read_tokens) |
| 工具调用记录 | 211 | COUNT(finish_reason='tool_calls') |
| 活跃会话 | 26 | COUNT(ended_at IS NULL) |
| 已完成会话 | 6 | COUNT(ended_at IS NOT NULL) |
| 使用模型 | glm-5 (22次), mimo-v2-pro (10次) | model 字段分布 |
| 来源分布 | cli (21次), api_server (11次) | source 字段分布 |
| 平均会话时长 | 51 分钟 | AVG(ended_at - started_at) |
| 最长会话时长 | 3.1 小时 | MAX(ended_at - started_at) |

---

## 二、数据生产链路完整分析

### 2.1 核心调用路径

```
用户输入 (Gateway)
    │
    ▼
gateway/run.py: run_conversation(session_id, message)
    │
    ├── 1. 读取会话配置 (config.yaml)
    │      → model, provider, system_prompt
    │
    ├── 2. 加载会话上下文 (session_store.load_transcript)
    │      → 从 messages 表读取历史消息
    │
    ├── 3. 构建 System Prompt
    │      → prompt_builder.build_system_prompt()
    │         → 注入 identity.md, memory, skills, tools
    │
    ├── 4. 调用 LLM API
    │      → _interruptible_streaming_api_call(client, messages)
    │         │
    │         ├── [埋点] api_start_time = time.time()
    │         │
    │         ├── client.chat.completions.create(...)
    │         │   → stream=True, stream_options={"include_usage": True}
    │         │
    │         ├── stream_delta_callback(delta, usage)
    │         │   │
    │         │   ├── [埋点] if first_token: first_token_time = time.time()
    │         │   │   → ttft_ms = (first_token_time - api_start_time) * 1000
    │         │   │
    │         │   ├── 累积 content += delta.content
    │         │   ├── 累积 tool_calls += delta.tool_calls
    │         │   └── 提取 usage (completion_tokens, prompt_tokens, etc.)
    │         │
    │         └── [埋点] api_end_time = time.time()
    │              → duration_ms = (api_end_time - api_start_time) * 1000
    │              → tps = completion_tokens / (duration_ms / 1000)
    │
    ├── 5. 处理 API 响应
    │      → if tool_calls:
    │         │
    │         ├── 保存 assistant 消息 (append_to_transcript)
    │         │   → role='assistant', tool_calls=JSON, finish_reason='tool_calls'
    │         │   → [问题] token_count 未赋值 (生产环境全为 NULL)
    │         │
    │         └── for each tool_call in tool_calls:
    │              │
    │              ├── [埋点] tool_start = time.time()
    │              │
    │              ├── handle_function_call(name, arguments)
    │              │   → 执行工具逻辑 (文件操作/终端/网络/MCP等)
    │              │   → 捕获异常
    │              │
    │              ├── [埋点] tool_end = time.time()
    │              │   → tool_duration_ms = (tool_end - tool_start) * 1000
    │              │   → tool_result_status = 'success' or 'error'
    │              │
    │              └── 保存 tool 消息 (append_to_transcript)
    │                   → role='tool', tool_call_id=tc.id, content=result
    │                   → [问题] tool_name 未赋值 (生产环境全为 NULL)
    │
    │      → else (无 tool_calls, 纯文本回复):
    │         │
    │         └── 保存 assistant 消息
    │              → role='assistant', content=reply, finish_reason='stop'
    │              → [问题] token_count 未赋值
    │
    ├── 6. 会话结束
    │      → session_store.update_session(...)
    │         → input_tokens = session_prompt_tokens
    │         → output_tokens = session_completion_tokens
    │      → session_db.set_token_counts(absolute=True)
    │         → 写入 sessions 表 (会话级聚合)
    │
    └── 7. 可能触发上下文压缩
           → context_compressor.compress(conversation)
              → 生成压缩摘要
              → 创建新会话 (parent_session_id 链)
```

### 2.2 数据存储路径

| 数据类型 | 存储位置 | 写入方式 | 频率 |
|---------|---------|---------|------|
| 会话元数据 | state.db sessions 表 | INSERT + UPDATE | 每会话 2 次 |
| 消息记录 | state.db messages 表 | INSERT 批量写入 | 每消息 1 次 |
| 工具调用 | messages.tool_calls (JSON) | 与消息一起写入 | 每调用 1 次 |
| Token 统计 | sessions 表字段 | UPDATE 会话结束时 | 每会话 1 次 |
| 网关状态 | ~/.hermes/gateway_state.json | 覆盖写入 | 实时 |
| 认证信息 | ~/.hermes/auth.json | 覆盖写入 | API 调用时 |
| 后台进程 | ~/.hermes/processes.json | 覆盖写入 | 实时 |
| 会话快照 | state.db messages 表 | FTS5 全文索引 | 每消息 1 次 |

### 2.3 数据读取路径

| 读取方 | 读取位置 | 读取方式 | 用途 |
|-------|---------|---------|------|
| WebUI API | state.db | SELECT + JOIN | 展示会话列表/详情/统计 |
| AIAgent | state.db | SELECT WHERE session_id | 恢复会话上下文 |
| Gateway | state.db | SELECT + FTS5 | 搜索历史消息 |
| WebUI API | shared-context/ | glob + json.load | 读取任务状态 |
| WebUI API | ~/.hermes/teams/ | glob + open | 读取团队记忆 |
| WebUI API | ~/.hermes/cron/jobs.json | json.load | 读取定时任务 |
| WebUI API | gateway_state.json | json.load | 读取网关状态 |

---

## 三、当前数据完整性评估

### 3.1 数据完整性矩阵

| 数据维度 | 字段 | 预期覆盖率 | 实际覆盖率 | 评级 |
|---------|------|-----------|-----------|------|
| **会话创建** | sessions.id, source, model | 100% | 100% | ✅ 完整 |
| **会话时间** | sessions.started_at, ended_at | 100% | 100% (started) / 19% (ended) | ⚠️ 大部分活跃 |
| **会话Token** | sessions.input_tokens, output_tokens | 100% | 100% | ✅ 完整 |
| **缓存Token** | sessions.cache_read_tokens | 100% | 部分 (仅 Anthropic) | ⚠️ 部分 |
| **消息创建** | messages.id, role, content | 100% | 100% | ✅ 完整 |
| **消息时间** | messages.timestamp | 100% | 100% (但精度无意义) | ⚠️ 批量写入 |
| **消息Token** | messages.token_count | 100% | **0%** | ❌ 缺失 |
| **工具调用** | messages.tool_calls | 100% | 有 JSON 数据 | ✅ 完整 |
| **工具名称** | messages.tool_name | 100% | **0%** | ❌ 缺失 |
| **工具耗时** | — | 100% | **无字段** | ❌ 缺失 |
| **API延迟** | — | 100% | **无字段** | ❌ 缺失 |
| **TTFT** | — | 100% | **无字段** | ❌ 缺失 |
| **TPS** | — | 100% | **无字段** | ❌ 缺失 |
| **错误详情** | messages.error_message | 100% | **无字段** | ❌ 缺失 |
| **工具状态** | messages.tool_result_status | 100% | **无字段** | ❌ 缺失 |
| **压缩记录** | sessions.compression_count | 100% | **无字段** | ❌ 缺失 |
| **模型切换** | sessions.model_switch_count | 100% | **无字段** | ❌ 缺失 |

### 3.2 数据缺口根因分析

| 缺口 | 根因 | 代码位置 |
|------|------|---------|
| messages.token_count 全为 NULL | `session_store.append_message()` 中 token_count 参数未传入 | `gateway/session.py:append_message()` |
| messages.tool_name 全为 NULL | INSERT 时 tool_name 字段未赋值 | `hermes_state.py:append_message()` |
| 无工具耗时 | 工具执行前后无 time.time() 记录 | `run_agent.py:handle_function_call()` |
| 无 API 延迟 | API 调用前后无计时 | `gateway/run.py` |
| 无 TTFT | stream_delta_callback 中无首次时间记录 | `gateway/run.py` |
| 无错误详情 | 异常仅记录日志，不写入数据库 | 各 except 块 |

---

## 四、数据增强方案

### 4.1 Schema Migration 脚本

```python
# hermes_state.py: SCHEMA_VERSION 6 → 7

SCHEMA_V7_UPGRADES = [
    # messages 表新增字段
    "ALTER TABLE messages ADD COLUMN duration_ms REAL DEFAULT NULL",
    "ALTER TABLE messages ADD COLUMN ttft_ms REAL DEFAULT NULL",
    "ALTER TABLE messages ADD COLUMN tps REAL DEFAULT NULL",
    "ALTER TABLE messages ADD COLUMN tool_duration_ms REAL DEFAULT NULL",
    "ALTER TABLE messages ADD COLUMN tool_result_status TEXT DEFAULT NULL",
    "ALTER TABLE messages ADD COLUMN error_message TEXT DEFAULT NULL",
    "ALTER TABLE messages ADD COLUMN error_traceback TEXT DEFAULT NULL",
    "ALTER TABLE messages ADD COLUMN reasoning_tokens INTEGER DEFAULT 0",
    "ALTER TABLE messages ADD COLUMN compression_ratio REAL DEFAULT NULL",
    "ALTER TABLE messages ADD COLUMN model_used TEXT DEFAULT NULL",

    # sessions 表新增字段
    "ALTER TABLE sessions ADD COLUMN total_tool_duration_ms REAL DEFAULT NULL",
    "ALTER TABLE sessions ADD COLUMN total_api_duration_ms REAL DEFAULT NULL",
    "ALTER TABLE sessions ADD COLUMN avg_tps REAL DEFAULT NULL",
    "ALTER TABLE sessions ADD COLUMN min_ttft_ms REAL DEFAULT NULL",
    "ALTER TABLE sessions ADD COLUMN max_ttft_ms REAL DEFAULT NULL",
    "ALTER TABLE sessions ADD COLUMN model_switch_count INTEGER DEFAULT 0",
    "ALTER TABLE sessions ADD COLUMN compression_count INTEGER DEFAULT 0",
    "ALTER TABLE sessions ADD COLUMN error_details TEXT DEFAULT NULL",
]
```

### 4.2 数据采集埋点实现

#### 4.2.1 API 延迟 + TTFT + TPS (gateway/run.py)

```python
def _interruptible_streaming_api_call(client, messages):
    api_start_time = time.time()
    first_token_time = None
    chunks_received = 0

    def stream_delta_callback(delta, usage):
        nonlocal first_token_time, chunks_received
        if first_token_time is None:
            first_token_time = time.time()
        chunks_received += 1
        # ... existing delta handling ...

    # ... existing API call ...

    api_end_time = time.time()
    duration_ms = (api_end_time - api_start_time) * 1000
    ttft_ms = (first_token_time - api_start_time) * 1000 if first_token_time else None
    completion_tokens = usage.get('completion_tokens', 0) if usage else 0
    tps = completion_tokens / (duration_ms / 1000) if duration_ms > 0 else None

    return response, {
        'duration_ms': duration_ms,
        'ttft_ms': ttft_ms,
        'tps': tps,
        'chunks_received': chunks_received,
        'model_used': model_name,  # 从配置中提取
    }
```

#### 4.2.2 工具耗时 + 状态 (run_agent.py)

```python
def handle_function_call(self, function_name, function_args):
    tool_start = time.time()
    result_status = 'success'
    error_msg = None
    error_tb = None

    try:
        result = self._execute_tool(function_name, function_args)
        tool_duration_ms = (time.time() - tool_start) * 1000
        return {
            'result': result,
            'tool_duration_ms': tool_duration_ms,
            'tool_result_status': 'success',
            'tool_name': function_name,  # 新增：工具名称
        }
    except Exception as e:
        tool_duration_ms = (time.time() - tool_start) * 1000
        error_msg = str(e)
        error_tb = traceback.format_exc()
        logger.error(f"Tool {function_name} failed: {e}")
        return {
            'result': f"Error: {e}",
            'tool_duration_ms': tool_duration_ms,
            'tool_result_status': 'error',
            'error_message': error_msg,
            'error_traceback': error_tb,
            'tool_name': function_name,
        }
```

#### 4.2.3 消息存储增强 (hermes_state.py)

```python
def append_message(self, session_id, role, content,
                   token_count=None, finish_reason=None,
                   tool_calls=None, tool_call_id=None,
                   tool_name=None, tool_duration_ms=None,  # 新增
                   tool_result_status=None, error_message=None,  # 新增
                   error_traceback=None, duration_ms=None,  # 新增
                   ttft_ms=None, tps=None, reasoning_tokens=None,  # 新增
                   compression_ratio=None, model_used=None):  # 新增
    # ... existing code ...
    cursor.execute("""
        INSERT INTO messages (session_id, role, content, token_count,
            finish_reason, tool_calls, tool_call_id, tool_name,
            tool_duration_ms, tool_result_status, error_message,
            error_traceback, duration_ms, ttft_ms, tps,
            reasoning_tokens, compression_ratio, model_used, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (session_id, role, content, token_count, finish_reason,
          tool_calls, tool_call_id, tool_name,
          tool_duration_ms, tool_result_status, error_message,
          error_traceback, duration_ms, ttft_ms, tps,
          reasoning_tokens, compression_ratio, model_used, time.time()))
```

#### 4.2.4 会话聚合增强 (gateway/session.py)

```python
def update_session(self, session_id, input_tokens=None, output_tokens=None,
                   total_tool_duration_ms=None,  # 新增
                   total_api_duration_ms=None, avg_tps=None,  # 新增
                   min_ttft_ms=None, max_ttft_ms=None,  # 新增
                   model_switch_count=None, compression_count=None,  # 新增
                   error_details=None):  # 新增
    # ... existing code ...
```

### 4.3 修复现有 Bug

#### 4.3.1 token_count 赋值修复

当前问题：`append_message()` 调用时 token_count 参数为 None。

修复位置：`gateway/run.py` 中处理 API 响应后，提取 usage 并传入：

```python
# 在 run_conversation 中，收到 API 响应后:
token_count = usage.get('completion_tokens', 0) if usage else None
session_store.append_message(
    session_id=session_id,
    role='assistant',
    content=assistant_content,
    token_count=token_count,  # 修复：从 None 改为实际值
    finish_reason=finish_reason,
    tool_calls=tool_calls_json,
    # ... 其他新增字段 ...
)
```

#### 4.3.2 tool_name 赋值修复

当前问题：INSERT 时 tool_name 为 NULL。

修复位置：保存 tool 消息时，从 tool_call 中提取 name：

```python
# 在工具执行循环中:
tool_name = tc.function.name  # 从 tool_call 中提取
session_store.append_message(
    session_id=session_id,
    role='tool',
    content=tool_result,
    tool_call_id=tc.id,
    tool_name=tool_name,  # 修复：从 None 改为实际值
    # ... 其他新增字段 ...
)
```

---

## 五、WebUI 展示增强

### 5.1 Trace 树新增展示能力

| 展示项 | 数据源 | 渲染方式 |
|-------|--------|---------|
| 工具耗时条 | messages.tool_duration_ms | 深蓝色条，右侧显示耗时 (如 `read_file: 245ms`) |
| 工具执行状态 | messages.tool_result_status | 成功=绿色，失败=红色 |
| API 延迟 | messages.duration_ms | 灰色条，hover 显示 TTFT |
| 首Token时间 | messages.ttft_ms | 绿色标记点 |
| 错误信息 | messages.error_message | 红色高亮节点，点击展开详情 |
| Token 用量 | messages.token_count | 每个节点右侧显示 Token 数 |
| 压缩标记 | messages.compression_ratio | 时间轴上的特殊标记 |

### 5.2 新增 API 端点

```python
# webui/api.py

@app.route('/api/sessions/<session_id>/metrics')
def get_session_metrics(session_id):
    """获取会话性能指标"""
    metrics = session_db.execute(f"""
        SELECT
            AVG(duration_ms) as avg_api_duration,
            AVG(ttft_ms) as avg_ttft,
            AVG(tps) as avg_tps,
            AVG(tool_duration_ms) as avg_tool_duration,
            COUNT(CASE WHEN tool_result_status='error' THEN 1 END) as tool_errors
        FROM messages
        WHERE session_id = ?
    """, (session_id,)).fetchone()
    return jsonify(dict(metrics))

@app.route('/api/sessions/<session_id>/tools')
def get_session_tools(session_id):
    """获取工具调用详情"""
    tools = session_db.execute(f"""
        SELECT
            tool_name,
            COUNT(*) as call_count,
            AVG(tool_duration_ms) as avg_duration,
            MAX(tool_duration_ms) as max_duration,
            COUNT(CASE WHEN tool_result_status='error' THEN 1 END) as errors,
            SUM(token_count) as total_tokens
        FROM messages
        WHERE session_id = ? AND role = 'tool'
        GROUP BY tool_name
        ORDER BY call_count DESC
    """, (session_id,)).fetchall()
    return jsonify([dict(t) for t in tools])

@app.route('/api/sessions/<session_id>/errors')
def get_session_errors(session_id):
    """获取错误详情"""
    errors = session_db.execute(f"""
        SELECT id, role, error_message, error_traceback, timestamp
        FROM messages
        WHERE session_id = ? AND error_message IS NOT NULL
        ORDER BY timestamp
    """, (session_id,)).fetchall()
    return jsonify([dict(e) for e in errors])

@app.route('/api/metrics/overview')
def get_metrics_overview():
    """全局性能概览"""
    stats = session_db.execute("""
        SELECT
            COUNT(*) as total_sessions,
            COUNT(CASE WHEN ended_at IS NULL THEN 1 END) as active_sessions,
            AVG(CASE WHEN ended_at IS NOT NULL THEN ended_at - started_at END) as avg_duration,
            SUM(input_tokens + output_tokens) as total_tokens,
            AVG(avg_tps) as global_avg_tps,
            AVG(min_ttft_ms) as global_avg_ttft
        FROM sessions
    """).fetchone()
    return jsonify(dict(stats))
```

---

## 六、实施步骤

### 6.1 Phase 1: Schema Migration (1-2 天)

1. 在 `hermes_state.py` 中新增 SCHEMA_VERSION 7 升级逻辑
2. 执行 ALTER TABLE 添加 18 个新字段
3. 验证现有数据不受影响

### 6.2 Phase 2: 数据采集埋点 (2-3 天)

1. 在 `gateway/run.py` 中添加 API 延迟/TTFT/TPS 埋点
2. 在 `run_agent.py` 中添加工具耗时/状态埋点
3. 修复 token_count 和 tool_name 赋值 Bug
4. 在 `hermes_state.py` 中更新 append_message 签名

### 6.3 Phase 3: 会话聚合 (1 天)

1. 在 `gateway/session.py` 中聚合所有性能指标
2. 在会话结束时写入 sessions 增强字段

### 6.4 Phase 4: API 端点 (1-2 天)

1. 实现 `/api/sessions/<id>/metrics` 端点
2. 实现 `/api/sessions/<id>/tools` 端点
3. 实现 `/api/sessions/<id>/errors` 端点
4. 实现 `/api/metrics/overview` 端点

### 6.5 Phase 5: WebUI 增强 (2-3 天)

1. dashboard.js 新增工具耗时条渲染
2. dashboard.js 新增错误高亮
3. dashboard.js 新增性能指标展示
4. CSS 新增耗时条和错误状态样式

### 6.6 Phase 6: 验证与测试 (1 天)

1. 在测试会话中验证数据完整性
2. 确认 messages.token_count 不再为 NULL
3. 确认工具耗时正确记录
4. 确认错误详情完整保存
5. 在阿里云服务器上部署并验证

---

## 七、预期效果

### 7.1 数据完整性提升

| 指标 | 当前 | 增强后 |
|------|------|--------|
| messages.token_count 覆盖率 | 0% | 100% |
| messages.tool_name 覆盖率 | 0% | 100% |
| 工具耗时记录 | 无 | 100% |
| API 延迟记录 | 无 | 100% |
| TTFT 记录 | 无 | 100% |
| TPS 记录 | 无 | 100% |
| 错误详情记录 | 无 | 100% |

### 7.2 可观测能力提升

| 能力 | 场景 |
|------|------|
| 性能瓶颈定位 | 哪个工具调用最慢？哪个 API 延迟最高？ |
| 成本精细归因 | 每个工具消耗多少 Token？总成本分布？ |
| 稳定性治理 | 错误模式分析、fallback 链路追踪 |
| 服务质量评估 | TTFT 趋势、TPS 分布、错误率统计 |
| 上下文优化 | 压缩比例分析、压缩频率评估 |

---

*文档维护者：CrazyAgentsManage 团队*
*最后更新：2026-04-22*
