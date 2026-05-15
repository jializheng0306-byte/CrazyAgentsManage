const { chromium } = require('playwright');
const fs = require('fs');

(async() => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1200 } });
  const base = process.env.BASE_URL || 'http://127.0.0.1:5002';
  const pages = [
    {
      key: 'governance',
      url: '/governance',
      selectors: {
        shell: '.fm-shell-nav',
        graphData: '#gv-node-list',
        graphPreview: '#gv-graph-preview',
        agentList: '#gv-agent-list',
        metrics: '#gv-node-count'
      }
    },
    {
      key: 'collaboration',
      url: '/collaboration',
      selectors: {
        shell: '.fm-shell-nav',
        handoffList: '#cl-handoff-list',
        traceGrid: '#cl-trace-grid',
        tasksLink: 'a[href="/collaboration/tasks"]',
        metrics: '#cl-handoff-count'
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
    for (const [name, selector] of Object.entries(item.selectors)) {
      checks[name] = await page.locator(selector).count();
    }

    const metricText = checks.metrics ? await page.locator(item.selectors.metrics).textContent() : null;

    results[item.key] = {
      status: response ? response.status() : null,
      checks,
      metricText,
      title: await page.title(),
      primaryActive: await page.locator('.fm-primary-link.active').evaluateAll(nodes => nodes.map(n => n.textContent.replace(/\s+/g, ' ').trim())),
      consoleErrors
    };
    await page.close();
  }

  fs.writeFileSync('C:/Users/123/AppData/Local/Temp/gov-collab-recheck.json', JSON.stringify(results, null, 2));
  console.log(JSON.stringify(results, null, 2));
  await context.close();
  await browser.close();
})();
