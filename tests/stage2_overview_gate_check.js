const { chromium } = require('playwright');
const fs = require('fs');

(async() => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1200 } });
  const base = process.env.BASE_URL || 'http://127.0.0.1:5002';
  const page = await context.newPage();
  const consoleErrors = [];
  page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
  page.on('pageerror', err => consoleErrors.push(String(err)));

  const response = await page.goto(base + '/overview', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1800);

  const checks = {
    shell: await page.locator('.fm-shell-nav').count(),
    primaryRail: await page.locator('.fm-primary-rail').count(),
    contextPanel: await page.locator('.fm-context-panel').count(),
    leftWorkbench: await page.locator('.ov-column-left').count(),
    centerWorkspace: await page.locator('.ov-column-center').count(),
    rightDetail: await page.locator('.ov-column-right').count(),
    objectTree: await page.locator('#object-session-list').count(),
    supportSignals: await page.locator('#support-signals-list').count(),
    workspaceTitle: await page.locator('#workspace-object-title').count(),
    workspaceMetrics: await page.locator('#workspace-metrics').count(),
    focusCard: await page.locator('#workspace-focus-card').count(),
    toolsPanel: await page.locator('#workspace-tools').count(),
    performancePanel: await page.locator('#workspace-performance').count(),
    errorPanel: await page.locator('#workspace-errors').count(),
    detailFacts: await page.locator('#detail-facts-list').count(),
    detailSources: await page.locator('#detail-source-list').count(),
    referenceLinks: await page.locator('.ov-reference-link').count(),
  };

  const result = {
    status: response ? response.status() : null,
    title: await page.title(),
    checks,
    primaryActive: await page.locator('.fm-primary-link.active').evaluateAll(nodes => nodes.map(n => n.textContent.replace(/\s+/g, ' ').trim())),
    bodyLinks: await page.locator('main#overview-app a').count(),
    consoleErrors,
  };

  fs.writeFileSync('C:/Users/123/AppData/Local/Temp/stage2-overview-results.json', JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 2));

  await page.close();
  await context.close();
  await browser.close();
})();
