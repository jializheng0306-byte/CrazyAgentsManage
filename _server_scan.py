import paramiko
import json

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

DB = '/root/.hermes/state.db'

print("=" * 80)
print("HERMES 服务器真实数据深度探索")
print("=" * 80)

# 1. Database schema
print("\n【1】数据库表结构")
_, out, _ = c.exec_command(f'sqlite3 {DB} ".schema"')
print(out.read().decode().strip())

# 2. Table list + row counts
print("\n【2】表和行数")
_, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT name FROM sqlite_master WHERE type=\\"table\\" ORDER BY name;"')
tables = out.read().decode().strip().split('\n')
for t in tables:
    t = t.strip()
    if t:
        _, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT COUNT(*) FROM \\"{t}\\";"')
        print(f"  {t}: {out.read().decode().strip()} 行")

# 3. Sessions full column names
print("\n【3】Sessions 所有字段")
_, out, _ = c.exec_command(f'sqlite3 {DB} "PRAGMA table_info(sessions);"')
print(out.read().decode().strip())

# 4. Messages full column names
print("\n【4】Messages 所有字段")
_, out, _ = c.exec_command(f'sqlite3 {DB} "PRAGMA table_info(messages);"')
print(out.read().decode().strip())

# 5. Sessions sample with all columns
print("\n【5】Sessions 样本（前2条，所有列）")
_, out, _ = c.exec_command(f'sqlite3 -header -separator " | " {DB} "SELECT * FROM sessions LIMIT 2;"')
print(out.read().decode().strip())

# 6. Messages sample
print("\n【6】Messages 样本（各role一条，含token_count）")
for role in ['user', 'assistant', 'tool', 'system']:
    _, out, _ = c.exec_command(f'sqlite3 -header -separator " | " {DB} "SELECT id, session_id, role, tool_name, token_count, length(content) as content_len, timestamp FROM messages WHERE role=\\"{role}\\" LIMIT 1;"')
    result = out.read().decode().strip()
    if result:
        print(f"  --- {role} ---")
        print(f"  {result}")

# 7. Token distribution
print("\n【7】Token 统计")
_, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT \\"total_input: \\" || COALESCE(SUM(input_tokens),0), \\"total_output: \\" || COALESCE(SUM(output_tokens),0), \\"sessions_with_tokens: \\" || COUNT(CASE WHEN input_tokens > 0 OR output_tokens > 0 THEN 1 END) FROM sessions;"')
print(out.read().decode().strip())

# 8. Token per message analysis
print("\n【8】Message Token 分布")
_, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT role, COUNT(*) as cnt, COUNT(CASE WHEN token_count > 0 THEN 1 END) as with_tokens, COALESCE(SUM(token_count),0) as total, COALESCE(AVG(token_count),0) as avg FROM messages GROUP BY role ORDER BY cnt DESC;"')
print(out.read().decode().strip())

# 9. Tool calls detail
print("\n【9】Tool Call 详细统计")
_, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT tool_name, COUNT(*), COALESCE(SUM(token_count),0) as total_tokens FROM messages WHERE role=\\"tool\\" AND tool_name IS NOT NULL GROUP BY tool_name ORDER BY COUNT(*) DESC LIMIT 15;"')
print(out.read().decode().strip())

# 10. Tool calls without token
print("\n【10】Tool Call 中 token_count 为 NULL 的比例")
_, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT \\"total_tools: \\" || COUNT(*), \\"with_token: \\" || COUNT(CASE WHEN token_count > 0 THEN 1 END), \\"null_token: \\" || COUNT(CASE WHEN token_count IS NULL THEN 1 END) FROM messages WHERE role=\\"tool\\";"')
print(out.read().decode().strip())

# 11. Error analysis
print("\n【11】错误会话分析")
_, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT end_reason, COUNT(*), COALESCE(AVG(ended_at - started_at), 0) as avg_duration FROM sessions WHERE end_reason IS NOT NULL GROUP BY end_reason ORDER BY COUNT(*) DESC;"')
print(out.read().decode().strip())

# 12. Session source
print("\n【12】Session 来源分布")
_, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT COALESCE(source, \\"(null)\\") as src, COUNT(*), COALESCE(SUM(input_tokens+output_tokens),0) as total_tokens FROM sessions GROUP BY source ORDER BY COUNT(*) DESC;"')
print(out.read().decode().strip())

# 13. Model distribution
print("\n【13】模型分布")
_, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT COALESCE(model, \\"(null)\\") as m, COUNT(*) FROM sessions GROUP BY model ORDER BY COUNT(*) DESC LIMIT 10;"')
print(out.read().decode().strip())

# 14. Billing provider
print("\n【14】计费供应商")
_, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT COALESCE(billing_provider, \\"(null)\\") as bp, COUNT(*), COALESCE(SUM(input_tokens+output_tokens),0) FROM sessions GROUP BY billing_provider;"')
print(out.read().decode().strip())

# 15. Session duration stats
print("\n【15】会话时长统计")
_, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT \\"avg_duration: \\" || COALESCE(AVG(CASE WHEN ended_at IS NOT NULL THEN ended_at - started_at END), 0), \\"max_duration: \\" || COALESCE(MAX(CASE WHEN ended_at IS NOT NULL THEN ended_at - started_at END), 0), \\"active_sessions: \\" || COUNT(CASE WHEN ended_at IS NULL THEN 1 END) FROM sessions;"')
print(out.read().decode().strip())

# 16. Message timestamps - check if there are microsecond precision timestamps
print("\n【16】时间戳精度分析")
_, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT timestamp, length(timestamp) as ts_len FROM messages LIMIT 5;"')
print(out.read().decode().strip())

# 17. Messages with tool_calls field
print("\n【17】Messages 中 tool_calls 字段")
_, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT COUNT(CASE WHEN tool_calls IS NOT NULL AND tool_calls != \\"\\" THEN 1 END) as has_tool_calls FROM messages;"')
print(out.read().decode().strip())

# 18. Messages with tool_call_id
print("\n【18】Messages 中 tool_call_id 字段")
_, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT COUNT(CASE WHEN tool_call_id IS NOT NULL AND tool_call_id != \\"\\" THEN 1 END) as has_tool_call_id FROM messages;"')
print(out.read().decode().strip())

# 19. Check for finish_reason
print("\n【19】Messages 中 finish_reason 字段")
_, out, _ = c.exec_command(f'sqlite3 {DB} "PRAGMA table_info(messages);" | grep finish')
print(out.read().decode().strip() or "无 finish_reason 字段")

# 20. Actual messages with finish_reason if exists
print("\n【20】finish_reason 分布")
_, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT finish_reason, COUNT(*) FROM messages WHERE finish_reason IS NOT NULL AND finish_reason != \\"\\" GROUP BY finish_reason;" 2>/dev/null')
print(out.read().decode().strip() or "无数据")

# 21. Gateway process info
print("\n【21】Hermes Gateway 进程")
_, out, _ = c.exec_command('ps aux | grep hermes | grep -v grep')
print(out.read().decode().strip())

# 22. Hermes gateway state file
print("\n【22】Gateway 状态文件")
_, out, _ = c.exec_command('find /root/.hermes -name "*.json" -type f 2>/dev/null | head -10')
json_files = out.read().decode().strip()
print(json_files)
if json_files:
    for f in json_files.split('\n')[:3]:
        f = f.strip()
        _, out, _ = c.exec_command(f'cat {f} 2>/dev/null | head -50')
        result = out.read().decode().strip()
        if result:
            print(f"\n  --- {f} ---")
            print(result[:500])

# 23. Check hermes-agent source code on server
print("\n【23】Hermes Agent 源码（数据写入相关）")
_, out, _ = c.exec_command('find /root/hermes-agent -name "*.py" -type f 2>/dev/null | head -20')
print(out.read().decode().strip())

# 24. Check gateway state
print("\n【24】Gateway State 目录")
_, out, _ = c.exec_command('ls -la /root/.hermes/*.json 2>/dev/null')
print(out.read().decode().strip())

# 25. response_store.db
print("\n【25】Response Store DB")
_, out, _ = c.exec_command(f'sqlite3 /root/.hermes/response_store.db ".tables" 2>/dev/null && sqlite3 /root/.hermes/response_store.db ".schema" 2>/dev/null')
print(out.read().decode().strip() or "无 response_store.db 或为空")

c.close()
print("\n" + "=" * 80)
print("服务器探索完成")
