import paramiko
import os

BASE = os.path.dirname(os.path.abspath(__file__))
print(f"BASE: {BASE}")

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

sftp = c.open_sftp()

print("\n=== Uploading files ===")

files = [
    ('src/webui/templates/overview.html',   'templates/overview.html'),
    ('src/webui/static/css/overview.css',   'static/css/overview.css'),
    ('src/webui/static/js/overview.js',     'static/js/overview.js'),
    ('src/webui/templates/home.html',       'templates/home.html'),
    ('src/webui/templates/dashboard.html',  'templates/dashboard.html'),
    ('src/webui/static/css/dashboard.css',  'static/css/dashboard.css'),
    ('src/webui/static/js/dashboard.js',    'static/js/dashboard.js'),
    ('src/webui/static/css/design-system.css', 'static/css/design-system.css'),
    ('src/webui/static/css/nav.css',        'static/css/nav.css'),
    ('src/webui/static/css/components.css', 'static/css/components.css'),
    ('src/webui/app.py',                    'app.py'),
    ('src/webui/api.py',                    'api.py'),
]

for local, remote in files:
    local_path = os.path.join(BASE, local)
    remote_path = '/opt/crazyagentsmanage/src/webui/' + remote
    print(f"  {local_path} -> {remote_path}")
    if not os.path.exists(local_path):
        print(f"    SKIP (not found locally)")
        continue
    # Ensure remote dir exists
    remote_dir = os.path.dirname(remote_path)
    try:
        sftp.stat(remote_dir)
    except:
        print(f"    MKDIR {remote_dir}")
        sftp.mkdir(remote_dir, 0o755)
    sftp.put(local_path, remote_path)
    sftp.chmod(remote_path, 0o644)
    print(f"    OK")

sftp.close()

print("\n=== Killing old process ===")
_, out, _ = c.exec_command('ss -tlnp | grep 5002 | grep -oP "pid=\\K\\d+"', timeout=10)
pid = out.read().decode().strip()
if pid:
    print(f"  Killing PID {pid}")
    c.exec_command(f'kill -9 {pid}')

import time
time.sleep(2)

print("\n=== Restarting ===")
c.exec_command('cd /opt/crazyagentsmanage/src/webui && nohup /usr/bin/python3 /opt/cam_launcher.py > /tmp/webui-new.log 2>&1 &', timeout=5)
time.sleep(3)

print("\n=== Verifying ===")
_, out, _ = c.exec_command('ls -la /opt/crazyagentsmanage/src/webui/templates/overview.html')
print(f"overview.html: {out.read().decode().strip()}")

_, out, _ = c.exec_command('ls -la /opt/crazyagentsmanage/src/webui/static/css/overview.css')
print(f"overview.css: {out.read().decode().strip()}")

_, out, _ = c.exec_command('ls -la /opt/crazyagentsmanage/src/webui/static/js/overview.js')
print(f"overview.js: {out.read().decode().strip()}")

_, out, _ = c.exec_command('grep "overview" /opt/crazyagentsmanage/src/webui/app.py')
print(f"app.py route: {out.read().decode().strip()}")

for i in range(10):
    _, out, _ = c.exec_command('curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5002/overview', timeout=10)
    code = out.read().decode().strip()
    if code == '200':
        break
    print(f"  Attempt {i+1}: HTTP {code}")
    time.sleep(1)

print(f"\nGET /overview -> HTTP {code}")

_, out, _ = c.exec_command('curl -s http://127.0.0.1:5002/overview 2>/dev/null | head -15')
print(f"HTML preview:\n{out.read().decode().strip()}")

_, out, _ = c.exec_command('curl -s http://127.0.0.1:5002/api/overview 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps({\"metrics\": list(d.get(\"metrics\",{}).keys()), \"active_sessions\": len(d.get(\"active_sessions\",[])), \"tool_usage\": len(d.get(\"tool_usage\",[])), \"errors\": len(d.get(\"recent_errors\",[])), \"sources\": len(d.get(\"sources\",[]))}, indent=2))"')
print(f"API summary:\n{out.read().decode().strip() or '(error)'}")

_, out, _ = c.exec_command('tail -10 /tmp/webui-new.log 2>/dev/null')
print(f"\nServer log:\n{out.read().decode().strip()}")

c.close()
print("\nDone!")
