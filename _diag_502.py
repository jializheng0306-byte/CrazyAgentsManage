import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

print("=== 1. Test external :5002 access from server ===")
_, out, _ = c.exec_command('curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://47.99.217.1:5002/overview 2>&1')
print(f"  External :5002: {out.read().decode().strip()}")

_, out, _ = c.exec_command('curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://172.28.14.86:5002/overview 2>&1')
print(f"  Internal IP :5002: {out.read().decode().strip()}")

print("\n=== 2. Test nginx :80 access ===")
_, out, _ = c.exec_command('curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/manage/overview 2>&1')
print(f"  nginx /manage/overview: {out.read().decode().strip()}")

_, out, _ = c.exec_command('curl -s http://127.0.0.1/manage/overview 2>/dev/null | head -5')
print(f"  nginx HTML (first 5 lines):\n{out.read().decode().strip()}")

print("\n=== 3. Full nginx config ===")
_, out, _ = c.exec_command('nginx -T 2>/dev/null')
print(out.read().decode().strip())

print("\n=== 4. Nginx error log ===")
_, out, _ = c.exec_command('tail -20 /var/log/nginx/error.log 2>/dev/null')
print(out.read().decode().strip() or "(empty)")

c.close()
