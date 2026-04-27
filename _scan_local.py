"""深度扫描本地 hermes-agent 项目源码，分析运行时数据产生和管理机制"""
import os
import re
import json

PROJECT = r"D:\opensource\hermes-agent"

def search_in_files(pattern, extensions=None):
    """在所有py文件中搜索匹配pattern的代码"""
    if extensions is None:
        extensions = ['.py', '.yaml', '.yml', '.json', '.md', '.toml']
    results = []
    for root, dirs, files in os.walk(PROJECT):
        # Skip common non-source dirs
        skip = {'__pycache__', '.git', 'node_modules', 'venv', '.pytest_cache', 'dist', 'build'}
        dirs[:] = [d for d in dirs if d not in skip]
        for f in files:
            if any(f.endswith(ext) for ext in extensions):
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
                        content = fh.read()
                        for i, line in enumerate(content.split('\n'), 1):
                            if re.search(pattern, line, re.IGNORECASE):
                                results.append((path, i, line.strip()))
                except:
                    pass
    return results

def read_file(path, max_lines=200):
    """读取文件内容"""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            return ''.join(lines[:max_lines])
    except:
        return "(read error)"

print("=" * 80)
print("HERMES AGENT 本地源码深度扫描")
print("=" * 80)

# ========== 1. 数据库相关 ==========
print("\n【1】数据库连接和写入代码")
db_files = search_in_files(r'(state\.db|sqlite|INSERT INTO|CREATE TABLE)')
for path, line, code in db_files[:20]:
    rel = os.path.relpath(path, PROJECT)
    print(f"  {rel}:{line} | {code[:120]}")

# ========== 2. 数据模型定义 ==========
print("\n【2】数据模型定义 (dataclass, TypedDict, class)")
model_files = search_in_files(r'(@dataclass|TypedDict|class\s+\w+(Message|Session|Tool|Token|Event|Span|Trace))')
for path, line, code in model_files[:20]:
    rel = os.path.relpath(path, PROJECT)
    print(f"  {rel}:{line} | {code[:120]}")

# ========== 3. Token 相关 ==========
print("\n【3】Token 统计代码")
token_files = search_in_files(r'(token_count|input_tokens|output_tokens|token_usage)')
for path, line, code in token_files[:15]:
    rel = os.path.relpath(path, PROJECT)
    print(f"  {rel}:{line} | {code[:120]}")

# ========== 4. Tool Call 相关 ==========
print("\n【4】Tool Call 相关代码")
tool_files = search_in_files(r'(tool_name|tool_call|tool_calls|tool_result)')
for path, line, code in tool_files[:15]:
    rel = os.path.relpath(path, PROJECT)
    print(f"  {rel}:{line} | {code[:120]}")

# ========== 5. 错误追踪 ==========
print("\n【5】错误和异常记录")
error_files = search_in_files(r'(end_reason|error.*reason|exception|traceback|failed)', ['.py'])
for path, line, code in error_files[:15]:
    rel = os.path.relpath(path, PROJECT)
    print(f"  {rel}:{line} | {code[:120]}")

# ========== 6. 时间戳相关 ==========
print("\n【6】时间戳和数据采集")
ts_files = search_in_files(r'(timestamp|started_at|ended_at|created_at)')
for path, line, code in ts_files[:15]:
    rel = os.path.relpath(path, PROJECT)
    print(f"  {rel}:{line} | {code[:120]}")

# ========== 7. Telemetry/Observability ==========
print("\n【7】遥测/可观测性相关")
tel_files = search_in_files(r'(telemetry|observability|metric|trace|span|opentelemetry|otel)')
for path, line, code in tel_files[:15]:
    rel = os.path.relpath(path, PROJECT)
    print(f"  {rel}:{line} | {code[:120]}")

# ========== 8. Gateway 数据写入 ==========
print("\n【8】Gateway 数据写入逻辑")
gw_files = search_in_files(r'(gateway|Gateway|write.*state|save.*state|flush)', ['.py'])
for path, line, code in gw_files[:15]:
    rel = os.path.relpath(path, PROJECT)
    print(f"  {rel}:{line} | {code[:120]}")

# ========== 9. 核心 Agent 模块 ==========
print("\n【9】Agent 核心模块结构")
agent_dir = os.path.join(PROJECT, 'src', 'agent')
if os.path.isdir(agent_dir):
    for f in sorted(os.listdir(agent_dir)):
        if f.endswith('.py'):
            path = os.path.join(agent_dir, f)
            content = read_file(path, 50)
            print(f"\n  --- {f} ---")
            # Extract class and function definitions
            for line in content.split('\n'):
                stripped = line.strip()
                if stripped.startswith('class ') or stripped.startswith('def ') or stripped.startswith('async def '):
                    print(f"    {stripped}")

# ========== 10. Core 模块 ==========
print("\n【10】Core 核心模块")
core_dir = os.path.join(PROJECT, 'src', 'core')
if os.path.isdir(core_dir):
    for f in sorted(os.listdir(core_dir)):
        if f.endswith('.py'):
            path = os.path.join(core_dir, f)
            content = read_file(path, 50)
            print(f"\n  --- {f} ---")
            for line in content.split('\n'):
                stripped = line.strip()
                if stripped.startswith('class ') or stripped.startswith('def ') or stripped.startswith('async def '):
                    print(f"    {stripped}")

# ========== 11. Tools 模块 ==========
print("\n【11】Tools 模块结构")
tools_dir = os.path.join(PROJECT, 'src', 'tools')
if os.path.isdir(tools_dir):
    for f in sorted(os.listdir(tools_dir)):
        if f.endswith('.py') and not f.startswith('__'):
            path = os.path.join(tools_dir, f)
            content = read_file(path, 30)
            print(f"\n  --- {f} ---")
            for line in content.split('\n'):
                stripped = line.strip()
                if stripped.startswith('class ') or stripped.startswith('def ') or stripped.startswith('async def '):
                    print(f"    {stripped}")

# ========== 12. API 层数据查询 ==========
print("\n【12】API 层数据查询（完整的 SELECT 语句）")
api_path = os.path.join(PROJECT, 'src', 'webui', 'api.py')
if os.path.exists(api_path):
    with open(api_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Extract all SQL queries
    sql_pattern = r'["\']SELECT\s+[^"\']+["\']'
    matches = re.findall(sql_pattern, content, re.IGNORECASE | re.DOTALL)
    for m in matches[:20]:
        # Clean up
        clean = m.replace('\n', ' ').replace('"', '').replace("'", '')[:200]
        print(f"  {clean}...")

# ========== 13. 消息写入逻辑 ==========
print("\n【13】消息写入逻辑（INSERT）")
insert_files = search_in_files(r'(INSERT INTO messages|INSERT INTO sessions|execute.*INSERT)')
for path, line, code in insert_files[:20]:
    rel = os.path.relpath(path, PROJECT)
    print(f"  {rel}:{line} | {code[:150]}")

# ========== 14. 项目整体结构 ==========
print("\n【14】项目目录结构")
for root, dirs, files in os.walk(PROJECT):
    # Skip deep nesting
    depth = root.replace(PROJECT, '').count(os.sep)
    if depth > 3:
        dirs.clear()
        continue
    skip = {'__pycache__', '.git', 'node_modules', 'venv', '.pytest_cache', 'dist', 'build', '.trae', 'docs', 'test', 'tests'}
    dirs[:] = [d for d in dirs if d not in skip]
    indent = "  " * depth
    print(f"{indent}{os.path.basename(root)}/")
    for f in sorted(files)[:5]:
        if not f.startswith('.') and f.endswith(('.py', '.yaml', '.yml', '.toml', '.json', '.md')):
            print(f"{indent}  {f}")

print("\n" + "=" * 80)
print("本地扫描完成")
