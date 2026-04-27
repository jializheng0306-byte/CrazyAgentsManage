import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

print("=== Checking deployed files ===")
files = [
    '/root/CrazyAgentsManage/src/webui/templates/overview.html',
    '/root/CrazyAgentsManage/src/webui/static/css/overview.css',
    '/root/CrazyAgentsManage/src/webui/static/js/overview.js',
    '/root/CrazyAgentsManage/src/webui/app.py',
    '/root/CrazyAgentsManage/src/webui/api.py',
]
for f in files:
    _, out, _ = c.exec_command(f'ls -la {f} 2>/dev/null && wc -l {f}')
    info = out.read().decode().strip()
    print(f"  {f}: {info or 'NOT FOUND'}")

print("\n=== Checking app.py route ===")
_, out, _ = c.exec_command("grep -n 'overview' /root/CrazyAgentsManage/src/webui/app.py")
print(out.read().decode().strip())

print("\n=== Checking api.py route ===")
_, out, _ = c.exec_command("grep -n 'overview' /root/CrazyAgentsManage/src/webui/api.py")
print(out.read().decode().strip())

print("\n=== Server log ===")
_, out, _ = c.exec_command("tail -30 /tmp/webui.log")
print(out.read().decode().strip() or "(empty)")

print("\n=== Port 5002 ===")
_, out, _ = c.exec_command("ss -tlnp | grep 5002")
print(out.read().decode().strip() or "(no process on 5002)")

print("\n=== Running python processes ===")
_, out, _ = c.exec_command("ps aux | grep webui | grep -v grep")
print(out.read().decode().strip() or "(none)")

c.close()
