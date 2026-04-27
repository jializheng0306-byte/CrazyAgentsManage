import paramiko
import time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

print("=== 1. Check port 5002 process ===")
_, out, _ = c.exec_command('ss -tlnp | grep 5002')
status = out.read().decode().strip()
print(status or "NO PROCESS")

print("\n=== 2. Test from server localhost ===")
_, out, _ = c.exec_command('curl -s -o /dev/null -w "HTTP %{http_code}" http://127.0.0.1:5002/overview')
print(out.read().decode().strip())

print("\n=== 3. Test from server public IP ===")
_, out, _ = c.exec_command('curl -s -o /dev/null -w "HTTP %{http_code}" http://47.99.217.1:5002/overview')
print(out.read().decode().strip())

print("\n=== 4. Check security group / iptables ===")
_, out, _ = c.exec_command('iptables -L -n 2>/dev/null | head -20')
print(out.read().decode().strip() or "no iptables rules")

_, out, _ = c.exec_command('ufw status 2>/dev/null')
print(out.read().decode().strip() or "ufw not installed")

print("\n=== 5. Test nginx (port 80) ===")
_, out, _ = c.exec_command('curl -s -o /dev/null -w "HTTP %{http_code}" http://127.0.0.1/manage/overview')
print(f"nginx /manage/overview: {out.read().decode().strip()}")

_, out, _ = c.exec_command('curl -s -o /dev/null -w "HTTP %{http_code}" http://127.0.0.1/manage/static/css/overview.css')
print(f"nginx CSS: {out.read().decode().strip()}")

_, out, _ = c.exec_command('curl -s http://127.0.0.1/manage/overview 2>/dev/null | grep -o "href.*overview" | head -3')
print(f"nginx HTML links: {out.read().decode().strip()}")

print("\n=== 6. Server log (last 10 lines) ===")
_, out, _ = c.exec_command('tail -10 /tmp/webui-new.log 2>/dev/null')
print(out.read().decode().strip())

print("\n=== 7. Check if Flask process is healthy ===")
_, out, _ = c.exec_command('ps aux | grep cam_launcher | grep -v grep')
print(out.read().decode().strip() or "(no process)")

c.close()
