const { chromium } = require('playwright');
const fs = require('fs');

(async() => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1200 } });
  const base = 'http://127.0.0.1:5002';
  const pages = [
    { key: 'overview', url: '/overview', checks: ['main#overview-app', 'a.nav-item[href="/runtime"]'] },
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
    const checkResults = {};
    for (const selector of item.checks) {
      checkResults[selector] = await page.locator(selector).count();
    }
    results[item.key] = {
      status: response ? response.status() : null,
      checks: checkResults,
      title: await page.title(),
      navActive: await page.locator('.nav-item.active').evaluateAll(nodes => nodes.map(n => n.textContent.trim())),
      consoleErrors,
    };
    await page.screenshot({ path: `C:/Users/123/AppData/Local/Temp/${item.key}-page-check.png`, fullPage: true });
    await page.close();
  }

  fs.writeFileSync('C:/Users/123/AppData/Local/Temp/full-ia-gate-results.json', JSON.stringify(results, null, 2));
  console.log(JSON.stringify(results, null, 2));
  await context.close();
  await browser.close();
})();
