import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

print("=== Test direct :5002 access ===")
_, out, _ = c.exec_command('curl -s http://127.0.0.1:5002/manage/static/css/overview.css 2>/dev/null | head -c 100')
print(f":5002/manage/static/css/overview.css: {out.read().decode().strip()}")

_, out, _ = c.exec_command('curl -s http://127.0.0.1:5002/static/css/overview.css 2>/dev/null | head -c 100')
print(f":5002/static/css/overview.css: {out.read().decode().strip()}")

print("\n=== Test via nginx (port 80) ===")
_, out, _ = c.exec_command('curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/manage/overview')
print(f"nginx /manage/overview: {out.read().decode().strip()}")

_, out, _ = c.exec_command('curl -s http://127.0.0.1/manage/overview 2>/dev/null | head -c 200')
print(f"nginx response: {out.read().decode().strip()}")

_, out, _ = c.exec_command('curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/manage/static/css/overview.css')
print(f"nginx /manage/static/css/overview.css: {out.read().decode().strip()}")

c.close()
