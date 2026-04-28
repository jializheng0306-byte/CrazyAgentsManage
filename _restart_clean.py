import paramiko
import time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

print("=== Kill ALL webui processes ===")
_, out, _ = c.exec_command('ss -tlnp | grep 5002 | grep -oP "pid=\\K\\d+"', timeout=10)
pids = out.read().decode().strip()
print(f"PIDs on 5002: {pids}")

_, out, _ = c.exec_command('ps aux | grep cam_launcher | grep -v grep | awk \'{print $2}\'')
all_pids = out.read().decode().strip().split()
print(f"All launcher PIDs: {all_pids}")

for pid in all_pids:
    if pid:
        print(f"  Killing PID {pid}...")
        c.exec_command(f'kill -9 {pid}')
time.sleep(2)

print("\n=== Verify all killed ===")
_, out, _ = c.exec_command('ss -tlnp | grep 5002')
print(f"Port 5002: {out.read().decode().strip() or 'FREE'}")

print("\n=== Start fresh ===")
c.exec_command('cd /opt/crazyagentsmanage/src/webui && nohup /usr/bin/python3 /opt/cam_launcher.py > /tmp/webui-new.log 2>&1 &')
time.sleep(4)

print("\n=== Test all access methods ===")

# Direct port 5002
for i in range(5):
    _, out, _ = c.exec_command('curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5002/overview')
    code = out.read().decode().strip()
    if code == '200':
        break
    print(f"  Direct :5002 attempt {i+1}: {code}")
    time.sleep(1)
print(f"Direct :5002 -> HTTP {code}")

# Via nginx
_, out, _ = c.exec_command('curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/manage/overview')
nginx_code = out.read().decode().strip()
print(f"Nginx /manage/overview -> HTTP {nginx_code}")

print("\n=== Check what port user should use ===")
_, out, _ = c.exec_command('ss -tlnp | grep -E ":(80|443|5002) "')
print(out.read().decode().strip())

_, out, _ = c.exec_command('nginx -T 2>/dev/null | grep -A5 "listen" | head -20')
print(f"\nNginx listen config:\n{out.read().decode().strip()}")

print("\n=== Server log ===")
_, out, _ = c.exec_command('tail -5 /tmp/webui-new.log')
print(out.read().decode().strip())

c.close()
