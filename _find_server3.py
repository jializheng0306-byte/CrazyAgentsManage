import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

print("=== Port 5002 process cmdline ===")
_, out, _ = c.exec_command('cat /proc/$(ss -tlnp | grep 5002 | grep -oP "pid=\\K\\d+")/cmdline 2>/dev/null | tr "\\0" " "')
print(out.read().decode().strip())

print("\n=== Process 5002 cwd ===")
_, out, _ = c.exec_command('ls -la /proc/$(ss -tlnp | grep 5002 | grep -oP "pid=\\K\\d+")/cwd 2>/dev/null')
print(out.read().decode().strip())

print("\n=== /opt/hermes-webui structure ===")
_, out, _ = c.exec_command('ls -la /opt/hermes-webui/')
print(out.read().decode().strip())

print("\n=== /opt/hermes-webui/templates ===")
_, out, _ = c.exec_command('ls -la /opt/hermes-webui/templates/')
print(out.read().decode().strip() or "NOT FOUND")

print("\n=== /opt/hermes-webui/static/css ===")
_, out, _ = c.exec_command('ls -la /opt/hermes-webui/static/css/')
print(out.read().decode().strip() or "NOT FOUND")

print("\n=== /opt/hermes-webui/static/js ===")
_, out, _ = c.exec_command('ls -la /opt/hermes-webui/static/js/')
print(out.read().decode().strip() or "NOT FOUND")

print("\n=== /opt/hermes-webui/server.py first 5 lines ===")
_, out, _ = c.exec_command('head -5 /opt/hermes-webui/server.py 2>/dev/null')
print(out.read().decode().strip() or "NOT FOUND")

print("\n=== app.py and api.py locations ===")
_, out, _ = c.exec_command('find /opt -name "app.py" -o -name "api.py" 2>/dev/null | head -10')
print(out.read().decode().strip())

_, out, _ = c.exec_command('find /root -name "app.py" -o -name "api.py" 2>/dev/null | head -10')
print(out.read().decode().strip())

c.close()
