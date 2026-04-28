import paramiko
import time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

print("=== 1. Current process state ===")
_, out, _ = c.exec_command('ss -tlnp | grep 5002')
print(out.read().decode().strip() or "NO PROCESS")

_, out, _ = c.exec_command('ps aux | grep cam_launcher | grep -v grep')
print(f"\n{out.read().decode().strip()}")

print("\n=== 2. Test current state ===")
_, out, _ = c.exec_command('curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5002/overview 2>&1')
print(f"Local :5002/overview: {out.read().decode().strip()}")

_, out, _ = c.exec_command('curl -s -o /dev/null -w "%{http_code} %{time_total}s" --connect-timeout 5 http://47.99.217.1:5002/overview 2>&1')
print(f"Public :5002/overview: {out.read().decode().strip()}")

_, out, _ = c.exec_command('curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/manage/overview 2>&1')
print(f"Nginx /manage/overview: {out.read().decode().strip()}")

print("\n=== 3. Server log ===")
_, out, _ = c.exec_command('tail -10 /tmp/webui-new.log 2>/dev/null')
print(out.read().decode().strip() or "(empty)")

print("\n=== 4. Nginx config ===")
_, out, _ = c.exec_command('nginx -T 2>/dev/null | grep -A 15 "manage"')
print(out.read().decode().strip() or "NO /manage config")

print("\n=== 5. Security group check ===")
_, out, _ = c.exec_command('iptables -L INPUT -n --line-numbers 2>/dev/null | head -20')
print(out.read().decode().strip() or "no rules")

_, out, _ = c.exec_command('security group rules 2>/dev/null; aliyun ecs DescribeSecurityGroupAttribute 2>/dev/null || echo "check aliyun console"')
print(out.read().decode().strip())

c.close()
