const { chromium } = require('playwright');
const fs = require('fs');

(async() => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1200 } });
  const base = process.env.BASE_URL || 'http://127.0.0.1:5002';

  const pages = [
    {
      key: 'runtime',
      url: '/runtime',
      checks: {
        shell: '.fm-shell-nav',
        left: '.rt-column-left',
        center: '.rt-column-center',
        right: '.rt-column-right',
        objectPool: '#rt-active-sessions-grid',
        workspace: '.rt-panel-main',
        detail: '.rt-column-right .rt-panel'
      }
    },
    {
      key: 'operations',
      url: '/operations',
      checks: {
        shell: '.fm-shell-nav',
        left: '.ops-column-left',
        center: '.ops-column-center',
        right: '.ops-column-right',
        objectPool: '#ops-cron-list',
        workspace: '.ops-column-center .ops-panel-main',
        detail: '.ops-column-right .ops-panel'
      }
    },
    {
      key: 'governance',
      url: '/governance',
      checks: {
        shell: '.fm-shell-nav',
        left: '.gv-column-left',
        center: '.gv-column-center',
        right: '.gv-column-right',
        objectPool: '#gv-node-list',
        workspace: '.gv-column-center .gv-panel',
        detail: '.gv-column-right .gv-panel'
      }
    },
    {
      key: 'collaboration',
      url: '/collaboration',
      checks: {
        shell: '.fm-shell-nav',
        left: '.cl-column-left',
        center: '.cl-column-center',
        right: '.cl-column-right',
        objectPool: '#cl-handoff-list',
        workspace: '.cl-column-center .cl-panel-main',
        detail: '.cl-column-right .cl-panel'
      }
    }
  ];

  const results = {};
  for (const item of pages) {
    const page = await context.newPage();
    const consoleErrors = [];
    page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
    page.on('pageerror', err => consoleErrors.push(String(err)));

    const response = await page.goto(base + item.url, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1800);

    const checks = {};
    for (const [name, selector] of Object.entries(item.checks)) {
      checks[name] = await page.locator(selector).count();
    }

    results[item.key] = {
      status: response ? response.status() : null,
      title: await page.title(),
      checks,
      primaryActive: await page.locator('.fm-primary-link.active').evaluateAll(nodes => nodes.map(n => n.textContent.replace(/\s+/g, ' ').trim())),
      bodyLinks: await page.locator('main a').count(),
      consoleErrors,
    };

    await page.close();
  }

  fs.writeFileSync('C:/Users/123/AppData/Local/Temp/stage3-domain-results.json', JSON.stringify(results, null, 2));
  console.log(JSON.stringify(results, null, 2));

  await context.close();
  await browser.close();
})();
