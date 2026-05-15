const { chromium } = require('playwright');
const fs = require('fs');

(async() => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1200 } });
  const base = 'http://127.0.0.1:5002';
  const pages = [
    {
      key: 'overview',
      url: '/overview',
      checks: {
        shell: '.global-nav-shell',
        primaryRail: '.nav-primary-rail',
        summaryLabel: '.ov-briefing-label',
        roleHeading: '.ov-section-heading .ov-section-title',
        summaryHeading: '.ov-summary-section .ov-section-title'
      }
    },
    {
      key: 'runtime',
      url: '/runtime',
      checks: {
        shell: '.global-nav-shell',
        summaryLabel: '.rt-brief-label',
        roleHeading: '.rt-subpages',
        triage: '#rt-triage-list'
      }
    },
    {
      key: 'operations',
      url: '/operations',
      checks: {
        shell: '.global-nav-shell',
        summaryLabel: '.ops-briefing-label',
        roleHeading: '.ops-subpages',
        summaryGrid: '.ops-summary-grid'
      }
    },
    {
      key: 'governance',
      url: '/governance',
      checks: {
        shell: '.global-nav-shell',
        heroStatus: '.gv-status-label',
        panelEyebrow: '.gv-panel-eyebrow',
        contextPanel: '.gv-nav-panel'
      }
    },
    {
      key: 'collaboration',
      url: '/collaboration',
      checks: {
        shell: '.global-nav-shell',
        summaryLabel: '.cl-brief-label',
        roleHeading: '.cl-subpages',
        triage: '#cl-triage-list'
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
    await page.waitForTimeout(2000);

    const checks = {};
    for (const [key, selector] of Object.entries(item.checks)) {
      checks[key] = await page.locator(selector).count();
    }

    results[item.key] = {
      status: response ? response.status() : null,
      checks,
      title: await page.title(),
      railActive: await page.locator('.nav-rail-item.active').evaluateAll(nodes => nodes.map(n => n.textContent.replace(/\s+/g, ' ').trim())),
      bodyLinks: await page.locator('main a').count(),
      consoleErrors,
    };

    await page.screenshot({ path: `C:/Users/123/AppData/Local/Temp/stage-c-${item.key}.png`, fullPage: true });
    await page.close();
  }

  fs.writeFileSync('C:/Users/123/AppData/Local/Temp/stage-c-results.json', JSON.stringify(results, null, 2));
  console.log(JSON.stringify(results, null, 2));
  await context.close();
  await browser.close();
})();
