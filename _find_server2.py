import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

print("=== Port 5002 process ===")
_, out, _ = c.exec_command('ss -tlnp | grep 5002')
print(out.read().decode().strip())

_, out, _ = c.exec_command('cat /proc/$(ss -tlnp | grep 5002 | grep -oP "pid=\\K\\d+")/cmdline 2>/dev/null | tr "\\0" " "')
print(out.read().decode().strip())

print("\n=== /opt/hermes-webui structure ===")
_, out, _ = c.exec_command('ls -la /opt/hermes-webui/')
print(out.read().decode().strip())

print("\n=== /opt/hermes-webui/templates ===")
_, out, _ = c.exec_command('ls -la /opt/hermes-webui/templates/')
print(out.read().decode().strip() or "NOT FOUND")

print("\n=== /opt/hermes-webui/static ===")
_, out, _ = c.exec_command('ls -la /opt/hermes-webui/static/css/ /opt/hermes-webui/static/js/ 2>/dev/null')
print(out.read().decode().strip())

print("\n=== Check server.py ===")
_, out, _ = c.exec_command('head -5 /opt/hermes-webui/server.py 2>/dev/null')
print(out.read().decode().strip() or "NOT FOUND")

c.close()
