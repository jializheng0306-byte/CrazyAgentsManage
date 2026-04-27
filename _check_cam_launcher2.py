import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

print("=== /opt/crazyagentsmanage is symlink? ===")
_, out, _ = c.exec_command('ls -ld /opt/crazyagentsmanage 2>/dev/null')
print(out.read().decode().strip() or "NOT FOUND")

print("\n=== cam_launcher.py ===")
_, out, _ = c.exec_command('cat /opt/cam_launcher.py')
print(out.read().decode().strip())

print("\n=== /opt/hermes-webui server.py ===")
_, out, _ = c.exec_command('head -30 /opt/hermes-webui/server.py')
print(out.read().decode().strip())

print("\n=== /opt/hermes-webui/api/ ===")
_, out, _ = c.exec_command('ls -la /opt/hermes-webui/api/')
print(out.read().decode().strip())

print("\n=== /opt/hermes-webui/static/ ===")
_, out, _ = c.exec_command('ls -la /opt/hermes-webui/static/')
print(out.read().decode().strip())

print("\n=== /opt/hermes-webui/api/routes.py first 30 lines ===")
_, out, _ = c.exec_command('head -30 /opt/hermes-webui/api/routes.py')
print(out.read().decode().strip())

print("\n=== Does /opt/hermes-webui have templates dir? ===")
_, out, _ = c.exec_command('find /opt/hermes-webui -name "templates" -type d 2>/dev/null')
print(out.read().decode().strip() or "NO templates dir")

print("\n=== Where are dashboard.html files? ===")
_, out, _ = c.exec_command('find /opt -name "dashboard.html" 2>/dev/null')
print(out.read().decode().strip())

c.close()
