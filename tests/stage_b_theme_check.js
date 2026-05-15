const { chromium } = require('playwright');
const fs = require('fs');

(async() => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1200 } });
  const base = 'http://127.0.0.1:5002';
  const pages = [
    { key: 'overview', url: '/overview', checks: ['.global-nav-shell', '.nav-primary-rail', '.nav-secondary-panel', 'main#overview-app'] },
    { key: 'runtime', url: '/runtime', checks: ['main#runtime-app', '#rt-next-hop', '.rt-subpage-card'] },
    { key: 'operations', url: '/operations', checks: ['main#ops-app', '#ops-next-hop', '.ops-subpage-card'] },
    { key: 'governance', url: '/governance', checks: ['main#gv-app', '.gv-metric-card', '.gv-entry-card'] },
    { key: 'collaboration', url: '/collaboration', checks: ['main#cl-app', '#cl-next-hop', '.cl-subpage-card'] },
  ];

  const results = {};
  for (const item of pages) {
    const page = await context.newPage();
    const consoleErrors = [];
    page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
    page.on('pageerror', err => consoleErrors.push(String(err)));
    const response = await page.goto(base + item.url, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
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
    await page.screenshot({ path: `C:/Users/123/AppData/Local/Temp/stage-b-${item.key}.png`, fullPage: true });
    await page.close();
  }

  fs.writeFileSync('C:/Users/123/AppData/Local/Temp/stage-b-results.json', JSON.stringify(results, null, 2));
  console.log(JSON.stringify(results, null, 2));
  await context.close();
  await browser.close();
})();
