import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

print("=== Full nginx config ===")
_, out, _ = c.exec_command('cat /etc/nginx/nginx.conf 2>/dev/null')
print(out.read().decode().strip())

print("\n=== nginx sites-enabled ===")
_, out, _ = c.exec_command('cat /etc/nginx/sites-enabled/* 2>/dev/null')
print(out.read().decode().strip())

print("\n=== nginx conf.d ===")
_, out, _ = c.exec_command('for f in /etc/nginx/conf.d/*.conf; do echo "=== $f ==="; cat "$f"; done 2>/dev/null')
print(out.read().decode().strip())

print("\n=== Test via public IP from server ===")
# Simulate external access to port 5002
_, out, _ = c.exec_command('curl -s -o /dev/null -w "%{http_code} %{time_total}s" --connect-timeout 5 http://172.28.14.86:5002/overview')
print(f"Internal IP :5002: {out.read().decode().strip()}")

# Test via public IP
_, out, _ = c.exec_command('curl -s -o /dev/null -w "%{http_code} %{time_total}s" --connect-timeout 5 http://47.99.217.1:5002/overview')
print(f"Public IP :5002: {out.read().decode().strip()}")

# Test via nginx port 80
_, out, _ = c.exec_command('curl -s -o /dev/null -w "%{http_code} %{time_total}s" --connect-timeout 5 http://127.0.0.1/manage/overview')
print(f"Nginx /manage/overview: {out.read().decode().strip()}")

_, out, _ = c.exec_command('curl -s -o /dev/null -w "%{http_code} %{time_total}s" --connect-timeout 5 http://127.0.0.1/manage/static/css/overview.css')
print(f"Nginx CSS: {out.read().decode().strip()}")

print("\n=== Check nginx proxy config for /manage ===")
_, out, _ = c.exec_command("grep -A10 'location.*manage' /etc/nginx/sites-enabled/* /etc/nginx/conf.d/*.conf /etc/nginx/nginx.conf 2>/dev/null")
print(out.read().decode().strip() or "NO /manage location found")

_, out, _ = c.exec_command("grep -A10 '5002' /etc/nginx/sites-enabled/* /etc/nginx/conf.d/*.conf /etc/nginx/nginx.conf 2>/dev/null")
print(f"\nProxy to 5002 config:\n{out.read().decode().strip() or 'NOT FOUND'}")

c.close()
