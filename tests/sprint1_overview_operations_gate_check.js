const fs = require('fs');
const os = require('os');
const path = require('path');

function resolvePlaywrightFromNpxCache() {
  const cacheRoot = path.join(os.homedir(), '.npm', '_npx');
  if (!fs.existsSync(cacheRoot)) {
    throw new Error('Playwright npx cache not found. Run `npx playwright --version` first.');
  }

  const candidates = fs.readdirSync(cacheRoot)
    .map(name => path.join(cacheRoot, name, 'node_modules', 'playwright'))
    .filter(candidate => fs.existsSync(path.join(candidate, 'package.json')))
    .map(candidate => ({
      candidate,
      mtimeMs: fs.statSync(candidate).mtimeMs,
    }))
    .sort((a, b) => b.mtimeMs - a.mtimeMs);

  if (!candidates.length) {
    throw new Error('Cached playwright package not found under ~/.npm/_npx. Run `npx playwright --version` first.');
  }

  return require(candidates[0].candidate);
}

const { chromium } = resolvePlaywrightFromNpxCache();

function shouldIgnoreConsoleError(message) {
  return String(message || '').startsWith('Failed to load resource:');
}

(async() => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1200 } });
  const base = process.env.BASE_URL || 'http://127.0.0.1:5002';
  const pages = [
    {
      key: 'overview',
      url: '/overview',
      checks: {
        shell: '.fm-shell-nav',
        briefing: '.ov-briefing-label',
        nextHop: '#ov-next-hop',
        summaryGrid: '#ov-summary-grid',
        summaryCards: '.ov-summary-card',
        supportSignals: '#support-signals-list',
      }
    },
    {
      key: 'operations',
      url: '/operations',
      checks: {
        shell: '.fm-shell-nav',
        briefing: '.ops-briefing-label',
        nextHop: '#ops-next-hop',
        summaryGrid: '.ops-summary-grid',
        summaryCards: '.ops-summary-card',
        subpages: '.ops-subpage-card',
      }
    }
  ];

  const results = {};
  let hasFailure = false;

  for (const item of pages) {
    const page = await context.newPage();
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() !== 'error') return;
      if (shouldIgnoreConsoleError(msg.text())) return;
      consoleErrors.push(msg.text());
    });
    page.on('pageerror', err => consoleErrors.push(String(err)));

    const response = await page.goto(base + item.url, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);

    const checks = {};
    for (const [name, selector] of Object.entries(item.checks)) {
      checks[name] = await page.locator(selector).count();
      if (checks[name] < 1) hasFailure = true;
    }
    if (consoleErrors.length) hasFailure = true;

    results[item.key] = {
      status: response ? response.status() : null,
      checks,
      title: await page.title(),
      consoleErrors,
    };

    await page.close();
  }

  const outputPath = '/tmp/sprint1-overview-operations-gate-results.json';
  fs.writeFileSync(outputPath, JSON.stringify(results, null, 2));
  console.log(JSON.stringify({ outputPath, results }, null, 2));

  await context.close();
  await browser.close();

  if (hasFailure) process.exit(1);
})();
