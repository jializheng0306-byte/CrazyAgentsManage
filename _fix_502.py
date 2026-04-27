import paramiko
import time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

print("=== Server process status ===")
_, out, _ = c.exec_command('ss -tlnp | grep 5002')
print(out.read().decode().strip() or "NO PROCESS ON 5002")

_, out, _ = c.exec_command('ps aux | grep -E "cam_launcher|src.webui" | grep -v grep')
print(f"\nProcesses:\n{out.read().decode().strip() or '(none)'}")

print("\n=== Server log ===")
_, out, _ = c.exec_command('tail -30 /tmp/webui-new.log 2>/dev/null')
print(out.read().decode().strip() or "(empty)")

_, out, _ = c.exec_command('tail -20 /opt/hermes-webui/server.log 2>/dev/null')
print(f"\nOther log:\n{out.read().decode().strip() or '(empty)'}")

print("\n=== Check app.py syntax ===")
_, out, _ = c.exec_command('python3 -c "import ast; ast.parse(open(\"/opt/crazyagentsmanage/src/webui/app.py\").read()); print(\"OK\")" 2>&1')
print(out.read().decode().strip())

print("\n=== Try starting server manually ===")
c.exec_command('cd /opt/crazyagentsmanage/src/webui && /usr/bin/python3 /opt/cam_launcher.py > /tmp/webui-manual.log 2>&1 &')
time.sleep(3)

_, out, _ = c.exec_command('ss -tlnp | grep 5002')
print(f"After start: {out.read().decode().strip() or 'FAILED'}")

_, out, _ = c.exec_command('tail -10 /tmp/webui-manual.log 2>/dev/null')
print(f"Manual log:\n{out.read().decode().strip()}")

for i in range(5):
    _, out, _ = c.exec_command('curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5002/overview', timeout=10)
    code = out.read().decode().strip()
    if code == '200':
        break
    print(f"  Attempt {i+1}: {code}")
    time.sleep(1)

print(f"\nFinal check: HTTP {code}")

_, out, _ = c.exec_command('curl -s http://127.0.0.1:5002/manage/static/css/overview.css 2>/dev/null | head -c 100')
print(f"CSS: {out.read().decode().strip()}")

c.close()
