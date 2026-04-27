import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('47.99.217.1', 22, 'root', 'J6J3jlzcrazy', timeout=15)

# Check file sizes
_, out, _ = c.exec_command('wc -l /opt/crazyagentsmanage/src/webui/static/css/dashboard.css /opt/crazyagentsmanage/src/webui/static/js/dashboard.js /opt/crazyagentsmanage/src/webui/templates/dashboard.html')
print("=== File Line Counts ===")
print(out.read().decode().strip())

# Check HTTP response
_, out, _ = c.exec_command('curl -s -o /dev/null -w "HTTP_CODE:%{http_code}\\nSIZE:%{size_download}" http://127.0.0.1:5002/manage/dashboard')
print("\n=== HTTP Response ===")
print(out.read().decode().strip())

# Check for NEW dual-panel CSS classes
_, out, _ = c.exec_command(r'grep -c "vw-gantt-bar\|vw-label-panel\|vw-side-panel\|vw-timeline-wrapper\|vw-gantt-area\|vw-gantt-grid" /opt/crazyagentsmanage/src/webui/static/css/dashboard.css')
print("\n=== New Dual-Panel CSS Classes Found ===")
print(out.read().decode().strip())

# Check for NEW dual-panel JS functions
_, out, _ = c.exec_command(r'grep -c "renderDualPanel\|openSidePanel\|closeSidePanel\|highlightRow\|getGanttBarClass" /opt/crazyagentsmanage/src/webui/static/js/dashboard.js')
print("\n=== New Dual-Panel JS Functions Found ===")
print(out.read().decode().strip())

# Check HTML has new dual-panel structure
_, out, _ = c.exec_command(r'grep "timelineWrapper\|labelPanel\|ganttArea\|sidePanel" /opt/crazyagentsmanage/src/webui/templates/dashboard.html')
print("\n=== HTML Dual-Panel Structure ===")
print(out.read().decode().strip())

# Check if service is running
_, out, _ = c.exec_command('systemctl is-active crazyagentsmanage')
print("\n=== Service Status ===")
print(out.read().decode().strip())

c.close()
print("\nDone!")
