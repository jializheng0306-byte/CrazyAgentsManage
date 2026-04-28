import paramiko
import time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

print("=== 1. Is Flask process running? ===")
_, out, _ = c.exec_command('ss -tlnp | grep 5002')
print(out.read().decode().strip() or "NO PROCESS")

_, out, _ = c.exec_command('ps aux | grep cam_launcher | grep -v grep')
print(f"\n{out.read().decode().strip() or '(none)'}")

print("\n=== 2. Local test ===")
_, out, _ = c.exec_command('curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5002/overview')
print(f"HTTP {out.read().decode().strip()}")

print("\n=== 3. Server log (last 20 lines) ===")
_, out, _ = c.exec_command('tail -20 /tmp/webui-new.log')
print(out.read().decode().strip())

print("\n=== 4. Python syntax check ===")
_, out, _ = c.exec_command("python3 -c \"import ast; ast.parse(open('/opt/crazyagentsmanage/src/webui/app.py').read()); print('SYNTAX OK')\"")
print(out.read().decode().strip())

print("\n=== 5. Check if there's a crash loop ===")
_, out, _ = c.exec_command('journalctl -u cam_launcher --no-pager -n 20 2>/dev/null || echo "no systemd service"')
print(out.read().decode().strip())

c.close()
