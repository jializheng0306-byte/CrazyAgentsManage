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
    .map(candidate => ({ candidate, mtimeMs: fs.statSync(candidate).mtimeMs }))
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
  const base = (process.env.BASE_URL || 'http://127.0.0.1:5002').replace(/\/$/, '');
  const outputDir = process.env.OUTPUT_DIR || '/tmp';
  const browser = await chromium.launch({ headless: true, args: ['--no-proxy-server'] });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1400 } });
  const pages = [
    {
      key: 'collaboration',
      url: '/collaboration',
      screenshot: path.join(outputDir, 'phase-c-collaboration.png'),
      checks: [
        '.cl-brief-label',
        '#cl-next-hop',
        '#cl-triage-list .cl-triage-card',
        '#cl-evidence-jumps .cl-support-link',
      ],
    },
    {
      key: 'architecture-tech',
      url: '/architecture/tech',
      screenshot: path.join(outputDir, 'phase-c-architecture-tech.png'),
      checks: [
        '#tech-collaboration-chain .ov-gov-card',
        '#tech-collaboration-jumps .ov-reference-link',
      ],
    },
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
    await page.waitForTimeout(2500);
    const checks = {};
    for (const selector of item.checks) {
      checks[selector] = await page.locator(selector).count();
      if (checks[selector] < 1) hasFailure = true;
    }
    if (consoleErrors.length) hasFailure = true;
    await page.screenshot({ path: item.screenshot, fullPage: true });
    results[item.key] = {
      status: response ? response.status() : null,
      checks,
      title: await page.title(),
      consoleErrors,
      screenshot: item.screenshot,
    };
    await page.close();
  }

  const outputPath = path.join(outputDir, 'phase-c-collaboration-gate.json');
  fs.writeFileSync(outputPath, JSON.stringify(results, null, 2));
  console.log(JSON.stringify({ outputPath, results }, null, 2));
  await context.close();
  await browser.close();

  if (hasFailure) process.exit(1);
})();
