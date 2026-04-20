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
    return out, err

# === FIX 1: Check what Flask actually returns ===
print("=== FIX 1: Check Flask response content ===")
out, _ = run("curl -s http://127.0.0.1:5002/")
print(out[:800])

# Check static files
print("\n=== Static file test ===")
out2, _ = run("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5002/static/css/design-system.css")
print("CSS:", out2)
out3, _ = run("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5002/static/js/home.js")
print("JS:", out3)

# === FIX 2: Check ALL nginx configs including conf.d ===
print("\n=== FIX 2: All nginx configs ===")
out, _ = run("ls -la /etc/nginx/sites-enabled/ /etc/nginx/conf.d/ 2>/dev/null")
print(out)

# Check if there's an SSL config that catches port 443/80 first
print("\n=== Checking for other server blocks on port 80/443 ===")
out, _ = run("grep -rn 'listen 80\\|listen 443' /etc/nginx/ --include='*.conf' 2>/dev/null | grep -v '#'")
print(out)

# === FIX 3: Rewrite nginx completely - single clean config ===
print("\n=== FIX 3: Rewriting nginx config ===")

# First, remove ALL site configs except our target ones
run("rm -f /etc/nginx/sites-enabled/* 2>/dev/null; echo cleaned sites-enabled")
run("rm -f /etc/nginx/conf.d/*.conf 2>/dev/null; echo cleaned conf.d")

# Write a single unified config that handles everything
unified_conf = """# Main server - handles both Hermes WebUI and CrazyAgentsManage
server {
    listen 80;
    listen [::]:80;
    server_name _;

    # Hermes WebUI SPA (root)
    location / {
        root /var/www/hermes;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Hermes API
    location /v1/ {
        proxy_pass http://127.0.0.1:3001/v1/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

    location /health {
        proxy_pass http://127.0.0.1:3001/health;
    }

    # CrazyAgentsManage - Management Dashboard
    location /manage {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
"""

run("cat > /etc/nginx/sites-enabled/default << 'NGINXCONF'\n" + unified_conf + "\nNGINXCONF")

# Test nginx
print("\n=== Testing nginx ===")
out, _ = run("nginx -t 2>&1")
print(out)

if 'ok' in out.lower() or 'successful' in out:
    run("systemctl restart nginx")
    time.sleep(2)
    
    print("\n=== Testing all endpoints ===")
    
    # Test /manage
    r1, _ = run("curl -s -o /dev/null -w '%{http_code} size=%{size_download}' http://127.0.0.1:80/manage")
    print("/manage (local):", r1)
    
    r2, _ = run("curl -s -o /dev/null -w '%{http_code} size=%{size_download}' http://47.99.217.1:80/manage")
    print("/manage (external):", r2)
    
    # Test direct :5002
    r3, _ = run("curl -s -o /dev/null -w '%{http_code} size=%{size_download}' http://47.99.217.1:5002/")
    print(":5002/ (direct):", r3)
    
    # Test Hermes root
    r4, _ = run("curl -s -o /dev/null -w '%{http_code} size=%{size_download}' http://47.99.217.1:80/")
    print("/:80 (hermes):", r4)

# === FIX 4: Restart hermes-webui if needed ===
print("\n=== FIX 4: Check Hermes services ===")
out, _ = run("systemctl status hermes-webui --no-pager | head -10")
print(out[:400])

# Restart hermes-webui if it's having issues
run("systemctl restart hermes-webui 2>&1 || true")
time.sleep(3)
r5, _ = run("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3001/")
print(":3001 after restart:", r5)

client.close()
