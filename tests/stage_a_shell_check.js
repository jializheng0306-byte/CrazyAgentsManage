const { chromium } = require('playwright');
const fs = require('fs');

(async() => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1200 } });
  const base = 'http://127.0.0.1:5002';
  const pages = [
    { key: 'overview', url: '/overview', checks: ['.global-nav-shell', '.nav-primary-rail', '.nav-secondary-panel', 'main#overview-app'] },
    { key: 'runtime', url: '/runtime', checks: ['.global-nav-shell', '.nav-sub-item[href="/runtime/sessions"]', 'main#runtime-app'] },
    { key: 'operations', url: '/operations', checks: ['.global-nav-shell', '.nav-sub-item[href="/operations/skills"]', 'main#ops-app'] },
    { key: 'governance', url: '/governance', checks: ['.global-nav-shell', '.nav-sub-item[href="/governance/graph"]', 'main#gv-app'] },
    { key: 'collaboration', url: '/collaboration', checks: ['.global-nav-shell', '.nav-sub-item[href="/collaboration/tasks"]', 'main#cl-app'] },
    { key: 'sessions-legacy', url: '/sessions', checks: ['.global-nav-shell', '.nav-sub-item[href="/runtime/sessions"]'] },
    { key: 'dashboard-legacy', url: '/dashboard', checks: ['.global-nav-shell', '.nav-sub-item[href="/runtime/dashboard"]'] },
    { key: 'skills-legacy', url: '/skills', checks: ['.global-nav-shell', '.nav-sub-item[href="/operations/skills"]'] },
    { key: 'graph-legacy', url: '/graph', checks: ['.global-nav-shell', '.nav-sub-item[href="/governance/graph"]'] },
    { key: 'tasks-legacy', url: '/tasks', checks: ['.global-nav-shell', '.nav-sub-item[href="/collaboration/tasks"]'] },
  ];

  const results = {};
  for (const item of pages) {
    const page = await context.newPage();
    const consoleErrors = [];
    page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
    page.on('pageerror', err => consoleErrors.push(String(err)));
    const response = await page.goto(base + item.url, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1500);
    const checks = {};
    for (const selector of item.checks) {
      checks[selector] = await page.locator(selector).count();
    }
    results[item.key] = {
      status: response ? response.status() : null,
      checks,
      title: await page.title(),
      railActive: await page.locator('.nav-rail-item.active').evaluateAll(nodes => nodes.map(n => n.textContent.replace(/\s+/g, ' ').trim())),
      consoleErrors,
    };
    await page.close();
  }
  fs.writeFileSync('C:/Users/123/AppData/Local/Temp/stage-a-shell-results.json', JSON.stringify(results, null, 2));
  console.log(JSON.stringify(results, null, 2));
  await context.close();
  await browser.close();
})();
