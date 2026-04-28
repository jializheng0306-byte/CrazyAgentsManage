import paramiko
import os
import time

BASE = os.path.dirname(os.path.abspath(__file__))
print(f"BASE: {BASE}")

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

sftp = c.open_sftp()

# Upload updated app.py
local_app = os.path.join(BASE, 'src/webui/app.py')
remote_app = '/opt/crazyagentsmanage/src/webui/app.py'
print(f"Uploading app.py: {local_app} -> {remote_app}")
sftp.put(local_app, remote_app)
sftp.chmod(remote_app, 0o644)
sftp.close()

# Kill and restart
print("Killing old process...")
_, out, _ = c.exec_command('ss -tlnp | grep 5002 | grep -oP "pid=\\K\\d+"', timeout=10)
pid = out.read().decode().strip()
if pid:
    c.exec_command(f'kill -9 {pid}')
    time.sleep(2)

print("Starting new process...")
c.exec_command('cd /opt/crazyagentsmanage/src/webui && nohup /usr/bin/python3 /opt/cam_launcher.py > /tmp/webui-new.log 2>&1 &', timeout=5)
time.sleep(3)

print("\n=== Verify ===")
_, out, _ = c.exec_command('ss -tlnp | grep 5002')
print(f"Port 5002: {out.read().decode().strip() or 'NOT LISTENING'}")

# Test direct :5002 access (what user is doing)
for attempt in range(8):
    _, out, _ = c.exec_command('curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5002/overview', timeout=10)
    code = out.read().decode().strip()
    if code == '200':
        break
    print(f"  Attempt {attempt+1}: HTTP {code}")
    time.sleep(1)

print(f"\nGET /overview -> HTTP {code}")

# Check CSS loading on direct :5002
_, out, _ = c.exec_command('curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5002/manage/static/css/overview.css', timeout=10)
css_code = out.read().decode().strip()
print(f"GET /manage/static/css/overview.css -> HTTP {css_code}")

_, out, _ = c.exec_command('curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5002/manage/static/js/overview.js', timeout=10)
js_code = out.read().decode().strip()
print(f"GET /manage/static/js/overview.js -> HTTP {js_code}")

# Check via nginx
_, out, _ = c.exec_command('curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/manage/overview', timeout=10)
nginx_code = out.read().decode().strip()
print(f"\nnginx GET /manage/overview -> HTTP {nginx_code}")

_, out, _ = c.exec_command('curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/manage/static/css/overview.css', timeout=10)
nginx_css = out.read().decode().strip()
print(f"nginx GET /manage/static/css/overview.css -> HTTP {nginx_css}")

_, out, _ = c.exec_command('curl -s http://127.0.0.1:5002/overview 2>/dev/null | grep -o "BASE.*=.*[^<]*" | head -1')
print(f"\nBASE in HTML: {out.read().decode().strip()}")

_, out, _ = c.exec_command('tail -10 /tmp/webui-new.log')
print(f"\nServer log:\n{out.read().decode().strip()}")

c.close()
print("\nDone!")
