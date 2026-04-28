import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

sftp = c.open_sftp()
files = [
    ('src/webui/templates/dashboard.html', '/opt/crazyagentsmanage/src/webui/templates/dashboard.html'),
    ('src/webui/static/css/dashboard.css', '/opt/crazyagentsmanage/src/webui/static/css/dashboard.css'),
    ('src/webui/static/js/dashboard.js', '/opt/crazyagentsmanage/src/webui/static/js/dashboard.js'),
]
for local, remote in files:
    print(f"Uploading {local}")
    sftp.put(local, remote)
sftp.close()

print("\n=== Restart ===")
_, out, _ = c.exec_command('kill -9 $(ss -tlnp | grep 5002 | grep -oP "pid=\K\d+") 2>/dev/null; sleep 2; systemctl start crazyagentsmanage; sleep 5; echo done')
print(out.read().decode().strip())

print("\n=== Verify ===")
_, out, _ = c.exec_command('curl -s -o /dev/null -w "HTTP:%{http_code}\n" http://127.0.0.1:5002/dashboard')
print(f"Direct: {out.read().decode().strip()}")
_, out, _ = c.exec_command('grep -c "vw-trace-tree" /opt/crazyagentsmanage/src/webui/static/css/dashboard.css')
print(f"Tree CSS: {out.read().decode().strip()}")
_, out, _ = c.exec_command('grep -c "buildTraceTree" /opt/crazyagentsmanage/src/webui/static/js/dashboard.js')
print(f"Tree JS: {out.read().decode().strip()}")
_, out, _ = c.exec_command('grep -c "renderDualPanel\|vw-gantt-bar" /opt/crazyagentsmanage/src/webui/static/js/dashboard.js')
print(f"Old Gantt (should be 0): {out.read().decode().strip()}")

c.close()
print("\nDone!")
