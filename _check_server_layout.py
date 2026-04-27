import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

print("=== /opt/crazyagentsmanage structure ===")
_, out, _ = c.exec_command('ls -la /opt/crazyagentsmanage/')
print(out.read().decode().strip())

print("\n=== /opt/crazyagentsmanage/src/webui structure ===")
_, out, _ = c.exec_command('ls -la /opt/crazyagentsmanage/src/webui/')
print(out.read().decode().strip())

print("\n=== /opt/crazyagentsmanage/src/webui/templates ===")
_, out, _ = c.exec_command('ls -la /opt/crazyagentsmanage/src/webui/templates/')
print(out.read().decode().strip())

print("\n=== /opt/crazyagentsmanage/src/webui/static/css ===")
_, out, _ = c.exec_command('ls -la /opt/crazyagentsmanage/src/webui/static/css/')
print(out.read().decode().strip())

print("\n=== /opt/crazyagentsmanage/src/webui/static/js ===")
_, out, _ = c.exec_command('ls -la /opt/crazyagentsmanage/src/webui/static/js/')
print(out.read().decode().strip())

print("\n=== /opt/cam_launcher.py ===")
_, out, _ = c.exec_command('cat /opt/cam_launcher.py')
print(out.read().decode().strip())

print("\n=== /opt/crazyagentsmanage/app.py first 10 lines ===")
_, out, _ = c.exec_command('head -10 /opt/crazyagentsmanage/app.py')
print(out.read().decode().strip())

print("\n=== Server log (last 20 lines) ===")
_, out, _ = c.exec_command('tail -20 /opt/hermes-webui/server.log')
print(out.read().decode().strip())

c.close()
