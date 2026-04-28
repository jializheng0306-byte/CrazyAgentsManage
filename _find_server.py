import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

print("=== Port 5002 process ===")
_, out, _ = c.exec_command('ss -tlnp | grep 5002')
print(out.read().decode().strip())

_, out, _ = c.exec_command('ls -la /proc/$(ss -tlnp | grep 5002 | grep -oP "pid=\\K\\d+")/cmdline 2>/dev/null && cat /proc/$(ss -tlnp | grep 5002 | grep -oP "pid=\\K\\d+")/cmdline | tr "\\0" " "')
print(out.read().decode().strip())

print("\n=== Check /opt/hermes-webui ===")
_, out, _ = c.exec_command('ls -la /opt/hermes-webui/templates/ 2>/dev/null')
print(out.read().decode().strip() or "NOT FOUND")

print("\n=== Check /root/.hermes ===")
_, out, _ = c.exec_command('ls -la /root/.hermes/*.db 2>/dev/null')
print(out.read().decode().strip())

print("\n=== Check for CrazyAgentsManage ===")
_, out, _ = c.exec_command('find /root -maxdepth 3 -name "CrazyAgentsManage" -type d 2>/dev/null')
print(out.read().decode().strip() or "NOT FOUND")

_, out, _ = c.exec_command('find / -maxdepth 4 -name "dashboard.html" 2>/dev/null | head -5')
print(out.read().decode().strip())

c.close()
