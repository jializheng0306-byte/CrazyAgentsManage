import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

print("=== Test CSS paths ===")
paths = [
    '/manage/static/css/design-system.css',
    '/manage/static/css/nav.css',
    '/manage/static/css/overview.css',
    '/manage/static/css/components.css',
    '/manage/static/js/overview.js',
    '/api/overview',
]
for p in paths:
    _, out, _ = c.exec_command(f'curl -s -o /dev/null -w "%{{http_code}} %{{size_download}}" http://127.0.0.1:5002{p}', timeout=10)
    result = out.read().decode().strip()
    print(f"  {p}: {result}")

print("\n=== API /api/overview response (first 100 chars) ===")
_, out, _ = c.exec_command('curl -s http://127.0.0.1:5002/api/overview 2>/dev/null | head -c 500')
print(out.read().decode().strip())

print("\n=== Server log (last 10 lines) ===")
_, out, _ = c.exec_command('tail -10 /tmp/webui-new.log')
print(out.read().decode().strip())

c.close()
