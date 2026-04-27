import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

print("=== Full HTML response ===")
_, out, _ = c.exec_command('curl -s http://127.0.0.1:5002/overview 2>/dev/null')
html = out.read().decode().strip()
print(html)
print(f"\n\n=== Length: {len(html)} ===")

print("\n=== Check JS console errors (simulated) ===")
print("Check browser DevTools Console for errors")

print("\n=== Verify CSS is correct ===")
_, out, _ = c.exec_command('curl -s http://127.0.0.1:5002/manage/static/css/overview.css 2>/dev/null | head -c 200')
print(out.read().decode().strip())

print("\n=== Verify JS is correct ===")
_, out, _ = c.exec_command('curl -s http://127.0.0.1:5002/manage/static/js/overview.js 2>/dev/null | head -c 200')
print(out.read().decode().strip())

print("\n=== Server log (last 15 lines) ===")
_, out, _ = c.exec_command('tail -15 /tmp/webui-new.log')
print(out.read().decode().strip())

print("\n=== Process status ===")
_, out, _ = c.exec_command('ss -tlnp | grep 5002')
print(out.read().decode().strip())

c.close()
