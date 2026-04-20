import paramiko, time

SERVER = '47.99.217.1'
USER = 'root'
PASSWORD = 'J6J3jlzcrazy'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(SERVER, username=USER, password=PASSWORD, timeout=30)

def run(cmd):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    return out, err

# 1. Check what nginx actually loaded
print("=== 1. Nginx -T (show full parsed config) ===")
out, _ = run("nginx -T 2>&1 | grep -A5 'location /manage\\|server {' | head -30")
print(out[:800])

# 2. Check if the file was actually written
print("\n=== 2. Verify written files ===")
out, _ = run("ls -la /etc/nginx/sites-enabled/ && echo '---' && ls -la /etc/nginx/sites-available/")
print(out)

# 3. Read exact content of hermes config
print("\n=== 3. Exact hermes config content ===")
out, _ = run("cat -A /etc/nginx/sites-available/hermes | head -50")
print(out[:1000])

# 4. Check nginx main conf for include paths
print("\n=== 4. Nginx main.conf includes ==="
out, _ = run("grep -E 'include|sites' /etc/nginx/nginx.conf")
print(out)

# 5. Verbose test of /manage
print("\n=== 5. Verbose curl to /manage ===")
out, _ = run("curl -sv http://127.0.0.1:80/manage 2>&1 | head -25")
print(out[:1000])

# 6. Try accessing port 5002 from external (may need firewall rule)
print("\n=== 6. Firewall check ===")
out, _ = run("iptables -L INPUT -n | head -20 || ufw status 2>/dev/null || echo 'no iptables/ufw'")
print(out[:500])

client.close()
