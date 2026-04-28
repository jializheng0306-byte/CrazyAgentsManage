import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

DB = '/root/.hermes/state.db'

print("=" * 80)
print("HERMES STATE.DB 深度探索")
print("=" * 80)

# 1. Table list
print("\n【1】数据库表")
_, out, _ = c.exec_command(f'sqlite3 {DB} ".tables"')
print(out.read().decode().strip())

# 2. Full schema
print("\n【2】完整 Schema")
_, out, _ = c.exec_command(f'sqlite3 {DB} ".schema"')
print(out.read().decode().strip())

# 3. Row counts
print("\n【3】数据量统计")
_, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT \\"sessions: \\" || count(*) FROM sessions; SELECT \\"messages: \\" || count(*) FROM messages;"')
print(out.read().decode().strip())

# 4. Sessions table - first 3 rows with ALL columns
print("\n【4】Sessions 数据样本（前3条）")
_, out, _ = c.exec_command(f'sqlite3 -header -column {DB} "SELECT * FROM sessions LIMIT 3;"')
print(out.read().decode().strip())

# 5. Messages table - sample rows with all roles
print("\n【5】Messages 数据样本（各角色各1条）")
_, out, _ = c.exec_command(f'sqlite3 -header -column {DB} "SELECT id, session_id, role, substr(content,1,100), tool_name, token_count, timestamp FROM messages WHERE role=\\"user\\" LIMIT 1 UNION ALL SELECT id, session_id, role, substr(content,1,100), tool_name, token_count, timestamp FROM messages WHERE role=\\"assistant\\" LIMIT 1 UNION ALL SELECT id, session_id, role, substr(content,1,100), tool_name, token_count, timestamp FROM messages WHERE role=\\"tool\\" LIMIT 1;"')
print(out.read().decode().strip())

# 6. Check what fields messages actually has
print("\n【6】Messages 所有字段样本")
_, out, _ = c.exec_command(f'sqlite3 {DB} "PRAGMA table_info(messages);"')
print(out.read().decode().strip())

# 7. Check sessions fields
print("\n【7】Sessions 所有字段")
_, out, _ = c.exec_command(f'sqlite3 {DB} "PRAGMA table_info(sessions);"')
print(out.read().decode().strip())

# 8. Token data analysis
print("\n【8】Token 统计")
_, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT \\"total_input: \\" || COALESCE(SUM(input_tokens),0), \\"total_output: \\" || COALESCE(SUM(output_tokens),0) FROM sessions;"')
print(out.read().decode().strip())

# 9. Token per message
print("\n【9】Message Token 分布")
_, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT role, COUNT(*), COALESCE(SUM(token_count),0) as total_tokens, COALESCE(AVG(token_count),0) as avg_tokens FROM messages WHERE token_count > 0 GROUP BY role;"')
print(out.read().decode().strip())

# 10. Tool call analysis
print("\n【10】Tool Call 统计")
_, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT tool_name, COUNT(*), COALESCE(SUM(token_count),0) FROM messages WHERE role=\\"tool\\" GROUP BY tool_name ORDER BY COUNT(*) DESC LIMIT 10;"')
print(out.read().decode().strip())

# 11. Error sessions
print("\n【11】错误会话")
_, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT end_reason, COUNT(*) FROM sessions WHERE end_reason IS NOT NULL AND end_reason != \\"stop\\" GROUP BY end_reason;"')
print(out.read().decode().strip())

# 12. Source distribution
print("\n【12】来源分布")
_, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT source, COUNT(*), COALESCE(SUM(input_tokens + output_tokens),0) as total_tokens FROM sessions GROUP BY source ORDER BY COUNT(*) DESC;"')
print(out.read().decode().strip())

# 13. Model distribution
print("\n【13】模型分布")
_, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT model, COUNT(*) FROM sessions WHERE model IS NOT NULL AND model != \\"\\" GROUP BY model ORDER BY COUNT(*) DESC LIMIT 10;"')
print(out.read().decode().strip())

# 14. Billing provider
print("\n【14】计费供应商")
_, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT billing_provider, COUNT(*) FROM sessions WHERE billing_provider IS NOT NULL AND billing_provider != \\"\\" GROUP BY billing_provider;"')
print(out.read().decode().strip())

# 15. Time range
print("\n【15】时间范围")
_, out, _ = c.exec_command(f'sqlite3 {DB} "SELECT datetime(MIN(started_at), \\"unixepoch\\"), datetime(MAX(started_at), \\"unixepoch\\"), datetime(MIN(ended_at), \\"unixepoch\\"), datetime(MAX(ended_at), \\"unixepoch\\") FROM sessions;"')
print(out.read().decode().strip())

# 16. Check if there's a separate hermes process that writes to state.db
print("\n【16】Hermes Gateway 进程")
_, out, _ = c.exec_command('ps aux | grep hermes | grep -v grep')
print(out.read().decode().strip())

# 17. Check hermes gateway data directory
print("\n【17】Hermes 数据目录")
_, out, _ = c.exec_command('ls -la /root/.hermes/ && ls -la /root/hermes-agent/ 2>/dev/null | head -20')
print(out.read().decode().strip())

# 18. Check if there's telemetry/observability config
print("\n【18】Hermes 配置（遥测相关）")
_, out, _ = c.exec_command('cat /root/.hermes/config.yaml | grep -i -A5 "observability\\|telemetry\\|trace\\|metric\\|log" 2>/dev/null || echo "No observability config found"')
print(out.read().decode().strip())

# 19. Check the full config
print("\n【19】完整 Hermes 配置")
_, out, _ = c.exec_command('cat /root/.hermes/config.yaml')
print(out.read().decode().strip())

c.close()
print("\n" + "=" * 80)
print("探索完成")
