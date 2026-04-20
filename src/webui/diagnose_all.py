import paramiko, time

SERVER = '47.99.217.1'
USER = 'root'
PASSWORD = 'J6J3jlzcrazy'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USER, password=PASSWORD, timeout=30)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(out[:500])
    if err: print("[E] " + err[:300])
    return out

# 1. Check all services
print("=== 1. All services status ===")
run("systemctl list-units --type=service --state=running | grep -iE 'nginx|crazy|hermes|flask|webui'")

# 2. Check nginx
print("\n=== 2. Nginx ===")
out = run("systemctl status nginx --no-pager | head -10")
print("Nginx process:", run("ps aux | grep nginx | grep -v grep | head -3"))

# 3. Check CrazyAgentsManage service
print("\n=== 3. CrazyAgentsManage ===")
out = run("systemctl status crazyagentsmanage --no-pager")
print(out[:600])

# 4. Check port 5002
print("\n=== 4. Port 5002 ===")
out = run("ss -tlnp | grep 5002")
print("Port 5002:", out)

# 5. Check Flask app directly
print("\n=== 5. Direct Flask test ===")
out = run("curl -s -o /dev/null -w '%{http_code} size=%{size_download}' http://127.0.0.1:5002/ 2>&1; echo")
print(":5002/ response:", out)

# 6. Check hermes-webui (port 3001)
print("\n=== 6. Hermes WebUI (3001) ===")
out = run("ss -tlnp | grep 3001")
print("Port 3001:", out)
out2 = run("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3001/")
print(":3001/ HTTP:", out2)

# 7. Nginx config check
print("\n=== 7. Current nginx config ===")
out = run("cat /etc/nginx/sites-enabled/hermes")
print(out)

# 8. Nginx error log
print("\n=== 8. Recent nginx errors ===")
out = run("tail -20 /var/log/nginx/error.log 2>/dev/null || echo 'no log'")
print(out[:800])

client.close()
