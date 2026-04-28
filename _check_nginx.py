import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

print("=== 当前 nginx 配置 ===")
_, out, _ = c.exec_command('cat /etc/nginx/sites-enabled/default')
print(out.read().decode().strip())

print("\n=== 其他可能的 nginx 配置 ===")
_, out, _ = c.exec_command('find /etc/nginx -name "*.conf" -exec echo "=== {} ===" \; -exec cat {} \; 2>/dev/null | head -100')
print(out.read().decode().strip())

c.close()
