import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

print("=== What is cam_launcher.py? ===")
_, out, _ = c.exec_command('cat /opt/cam_launcher.py')
print(out.read().decode().strip())

print("\n=== /opt/crazyagentsmanage structure ===")
_, out, _ = c.exec_command('ls -la /opt/crazyagentsmanage/')
print(out.read().decode().strip() or "NOT FOUND")

print("\n=== /opt/crazyagentsmanage/src/webui structure ===")
_, out, _ = c.exec_command('ls -laR /opt/crazyagentsmanage/src/webui/ 2>/dev/null | head -40')
print(out.read().decode().strip() or "NOT FOUND")

print("\n=== Does crazyagentsmanage have venv? ===")
_, out, _ = c.exec_command('ls -la /opt/crazyagentsmanage/venv/bin/python 2>/dev/null')
print(out.read().decode().strip() or "NO VENV")

print("\n=== Does crazyagentsmanage have src/webui/server.py? ===")
_, out, _ = c.exec_command('ls -la /opt/crazyagentsmanage/src/webui/server.py 2>/dev/null')
print(out.read().decode().strip() or "NO server.py")

print("\n=== Does crazyagentsmanage have __main__.py? ===")
_, out, _ = c.exec_command('cat /opt/crazyagentsmanage/src/webui/__main__.py 2>/dev/null')
print(out.read().decode().strip() or "NO __main__.py")

print("\n=== What is in /opt/crazyagentsmanage/app.py? ===")
_, out, _ = c.exec_command('head -20 /opt/crazyagentsmanage/app.py 2>/dev/null')
print(out.read().decode().strip() or "NOT FOUND")

c.close()
