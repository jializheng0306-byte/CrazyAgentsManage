import paramiko
import json
import tempfile

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

script = """
import sqlite3, json

conn = sqlite3.connect("/root/.hermes/state.db")
conn.row_factory = sqlite3.Row

def q(sql, params=()):
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        return [{"error": str(e)}]

results = {}

results["schema"] = q("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
results["sessions_count"] = q("SELECT COUNT(*) as cnt FROM sessions")
results["messages_count"] = q("SELECT COUNT(*) as cnt FROM messages")
results["session_cols"] = q("PRAGMA table_info(sessions)")
results["message_cols"] = q("PRAGMA table_info(messages)")
results["sample_sessions"] = q("SELECT * FROM sessions ORDER BY started_at DESC LIMIT 3")
results["sample_messages"] = q("SELECT id, session_id, role, tool_name, tool_call_id, token_count, finish_reason, length(content) as content_len, timestamp FROM messages ORDER BY timestamp DESC LIMIT 10")
results["token_by_role"] = q("SELECT role, COUNT(*) as cnt, COUNT(CASE WHEN token_count > 0 THEN 1 END) as with_tokens, COALESCE(SUM(token_count),0) as total, COALESCE(AVG(token_count),0) as avg FROM messages GROUP BY role ORDER BY cnt DESC")
results["session_tokens"] = q("SELECT COALESCE(SUM(input_tokens),0) as total_input, COALESCE(SUM(output_tokens),0) as total_output, COALESCE(SUM(cache_read_tokens),0) as total_cache_read, COALESCE(SUM(cache_write_tokens),0) as total_cache_write, COALESCE(SUM(reasoning_tokens),0) as total_reasoning, COUNT(CASE WHEN input_tokens > 0 OR output_tokens > 0 THEN 1 END) as sessions_with_tokens, COUNT(*) as total_sessions FROM sessions")
results["tool_stats"] = q("SELECT tool_name, COUNT(*) as cnt, COUNT(CASE WHEN token_count > 0 THEN 1 END) as with_tokens, COALESCE(SUM(token_count),0) as total_tokens FROM messages WHERE role='tool' AND tool_name IS NOT NULL GROUP BY tool_name ORDER BY cnt DESC LIMIT 20")
results["end_reasons"] = q("SELECT end_reason, COUNT(*) as cnt, COALESCE(AVG(ended_at - started_at), 0) as avg_duration FROM sessions WHERE end_reason IS NOT NULL GROUP BY end_reason ORDER BY cnt DESC")
results["sources"] = q("SELECT COALESCE(source, '(null)') as src, COUNT(*) as cnt, COALESCE(SUM(input_tokens + output_tokens), 0) as total_tokens FROM sessions GROUP BY source ORDER BY cnt DESC")
results["models"] = q("SELECT COALESCE(model, '(null)') as m, COUNT(*) as cnt FROM sessions GROUP BY model ORDER BY cnt DESC LIMIT 10")
results["billing"] = q("SELECT COALESCE(billing_provider, '(null)') as bp, COUNT(*) as cnt, COALESCE(SUM(input_tokens + output_tokens), 0) as total_tokens, COALESCE(SUM(estimated_cost_usd), 0) as total_cost FROM sessions GROUP BY billing_provider")
results["durations"] = q("SELECT COALESCE(AVG(CASE WHEN ended_at IS NOT NULL THEN ended_at - started_at END), 0) as avg_sec, COALESCE(MAX(CASE WHEN ended_at IS NOT NULL THEN ended_at - started_at END), 0) as max_sec, COALESCE(MIN(CASE WHEN ended_at IS NOT NULL THEN started_at END), 0) as earliest, COUNT(CASE WHEN ended_at IS NULL THEN 1 END) as active_sessions, COUNT(*) as total_sessions FROM sessions")
results["tool_calls_json"] = q("SELECT id, role, length(tool_calls) as tool_calls_len, tool_call_id FROM messages WHERE tool_calls IS NOT NULL AND tool_calls != '' LIMIT 5")
results["finish_reasons"] = q("SELECT COALESCE(finish_reason, '(null)') as fr, COUNT(*) as cnt FROM messages GROUP BY finish_reason")
results["time_spread"] = q("SELECT id, role, timestamp, token_count, tool_name FROM messages WHERE session_id = (SELECT id FROM sessions ORDER BY started_at DESC LIMIT 1) ORDER BY timestamp, id")
results["parent_sessions"] = q("SELECT id, title, parent_session_id, started_at, end_reason FROM sessions WHERE parent_session_id IS NOT NULL ORDER BY started_at DESC LIMIT 5")

conn.close()
print(json.dumps(results, default=str, ensure_ascii=False, indent=2))
"""

# Write to temp file and upload via SFTP
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
    f.write(script)
    temp_path = f.name

sftp = c.open_sftp()
sftp.put(temp_path, '/tmp/_deep_scan.py')
sftp.close()

import os
os.unlink(temp_path)

stdin, stdout, stderr = c.exec_command('/root/hermes-agent/venv/bin/python /tmp/_deep_scan.py', timeout=60)
output = stdout.read().decode('utf-8', errors='replace')
err = stderr.read().decode('utf-8', errors='replace')

if err:
    print("STDERR:", err[:2000])

if output:
    try:
        data = json.loads(output)
        print(json.dumps(data, default=str, ensure_ascii=False, indent=2))
    except:
        print(output[:5000])
else:
    print("No output from server")

c.close()
