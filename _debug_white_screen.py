import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

print("=== Port 5002 ===")
_, out, _ = c.exec_command('ss -tlnp | grep 5002')
print(out.read().decode().strip() or "(no process)")

_, out, _ = c.exec_command('ss -tlnp | grep 5002 | grep -oP "pid=\\K\\d+"')
pid = out.read().decode().strip()
print(f"PID: {pid}")

if pid:
    print(f"\n=== Process cmdline ===")
    _, out, _ = c.exec_command(f'cat /proc/{pid}/cmdline 2>/dev/null | tr "\\0" " "')
    print(out.read().decode().strip())

    print(f"\n=== Process cwd ===")
    _, out, _ = c.exec_command(f'ls -la /proc/{pid}/cwd 2>/dev/null')
    print(out.read().decode().strip())

print("\n=== Server log (last 30 lines) ===")
_, out, _ = c.exec_command('tail -30 /opt/hermes-webui/server.log 2>/dev/null')
print(out.read().decode().strip() or "(empty)")

print("\n=== Check overview.html ===")
_, out, _ = c.exec_command('ls -la /opt/crazyagentsmanage/src/webui/templates/overview.html 2>/dev/null')
print(out.read().decode().strip() or "NOT FOUND")

print("\n=== Check overview.css ===")
_, out, _ = c.exec_command('ls -la /opt/crazyagentsmanage/src/webui/static/css/overview.css 2>/dev/null')
print(out.read().decode().strip() or "NOT FOUND")

print("\n=== Check overview.js ===")
_, out, _ = c.exec_command('ls -la /opt/crazyagentsmanage/src/webui/static/js/overview.js 2>/dev/null')
print(out.read().decode().strip() or "NOT FOUND")

print("\n=== Check app.py route ===")
_, out, _ = c.exec_command("grep -n 'overview' /opt/crazyagentsmanage/src/webui/app.py 2>/dev/null")
print(out.read().decode().strip() or "NOT FOUND")

print("\n=== CURL test ===")
_, out, _ = c.exec_command('curl -sI http://127.0.0.1:5002/overview')
print(out.read().decode().strip() or "(empty)")

_, out, _ = c.exec_command('curl -s http://127.0.0.1:5002/overview 2>/dev/null | head -30')
print(out.read().decode().strip() or "(empty)")

c.close()
