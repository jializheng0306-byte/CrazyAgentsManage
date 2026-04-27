import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

print("=== Test CSS loading via public IP ===")
for path in [
    'http://47.99.217.1:5002/manage/static/css/overview.css',
    'http://47.99.217.1:5002/manage/static/js/overview.js',
    'http://47.99.217.1:5002/manage/static/css/design-system.css',
    'http://47.99.217.1:5002/api/overview',
]:
    _, out, _ = c.exec_command(f'curl -sI "{path}" 2>/dev/null | head -5')
    print(f"  {path}:")
    print(f"    {out.read().decode().strip()}")

print("\n=== Check nginx config ===")
_, out, _ = c.exec_command('cat /etc/nginx/sites-enabled/default 2>/dev/null || cat /etc/nginx/conf.d/*.conf 2>/dev/null || echo "no nginx config found"')
print(out.read().decode().strip())

print("\n=== Is nginx running? ===")
_, out, _ = c.exec_command('ss -tlnp | grep ":80 "')
print(out.read().decode().strip() or "nginx not on port 80")

_, out, _ = c.exec_command('ss -tlnp | grep ":443 "')
print(out.read().decode().strip() or "no port 443")

print("\n=== Check if user is accessing via nginx proxy ===")
_, out, _ = c.exec_command('curl -sI http://47.99.217.1:5002/overview 2>/dev/null | head -10')
print(out.read().decode().strip())

c.close()
