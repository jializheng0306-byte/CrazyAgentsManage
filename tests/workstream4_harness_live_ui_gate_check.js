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
  const base = (process.env.BASE_URL || 'http://47.99.217.1/manage').replace(/\/$/, '');
  const outputDir = process.env.OUTPUT_DIR || '/tmp';
  const screenshotPath = path.join(outputDir, 'workstream4-harness-live-ui.png');
  const outputPath = path.join(outputDir, 'workstream4-harness-live-ui.json');
  const browser = await chromium.launch({ headless: true, args: ['--no-proxy-server'] });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1400 } });
  const page = await context.newPage();
  const consoleErrors = [];

  page.on('console', msg => {
    if (msg.type() !== 'error') return;
    if (shouldIgnoreConsoleError(msg.text())) return;
    consoleErrors.push(msg.text());
  });
  page.on('pageerror', err => consoleErrors.push(String(err)));

  let response = null;
  let lastError = null;
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      response = await page.goto(base + '/operations#harness', { waitUntil: 'domcontentloaded' });
      lastError = null;
      break;
    } catch (error) {
      lastError = error;
      if (attempt < 3) {
        await page.waitForTimeout(1200);
      }
    }
  }
  if (lastError) {
    throw lastError;
  }
  await page.waitForTimeout(2000);
  await page.waitForFunction(() => {
    const active = document.querySelector('.ops-tree-item.active[data-family="harness"]');
    const workspace = document.querySelector('#ops-workspace-content');
    const detail = document.querySelector('#ops-rail');
    const text = [workspace?.textContent || '', detail?.textContent || ''].join(' ');
    return Boolean(active) &&
      text.includes('Default entry') &&
      text.includes('Direct trace policy') &&
      text.includes('harness-closeout-writeback') &&
      text.includes('--allow-trivial-direct');
  }, null, { timeout: 15000 });
  await page.screenshot({ path: screenshotPath, fullPage: true });

  const payload = await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('.ops-detail-row')).map(node => ({
      label: (node.querySelector('.ops-detail-row-label') || {}).textContent?.trim() || '',
      value: (node.querySelector('.ops-detail-row-value') || {}).textContent?.trim() || '',
    }));
    const workspaceText = (document.querySelector('#ops-workspace-content') || {}).textContent || '';
    return {
      activeFamily: (document.querySelector('.ops-tree-item.active span:nth-of-type(2)') || {}).textContent?.trim() || '',
      workspaceText,
      rows,
      workspaceChecks: {
        hasDefaultEntry: workspaceText.includes('Default entry'),
        hasDirectTracePolicy: workspaceText.includes('Direct trace policy'),
        hasCloseoutCommand: workspaceText.includes('harness-closeout-writeback'),
        hasExplicitProbeFlag: workspaceText.includes('--allow-trivial-direct'),
      },
    };
  });

  const results = {
    status: response ? response.status() : null,
    title: await page.title(),
    consoleErrors,
    screenshotPath,
    rows: payload.rows,
    activeFamily: payload.activeFamily,
    workspaceChecks: payload.workspaceChecks,
  };

  fs.writeFileSync(outputPath, JSON.stringify(results, null, 2));
  console.log(JSON.stringify({ outputPath, screenshotPath, results }, null, 2));

  await context.close();
  await browser.close();

  if (
    results.status !== 200 ||
    results.activeFamily !== 'Harness' ||
    !results.workspaceChecks.hasDefaultEntry ||
    !results.workspaceChecks.hasDirectTracePolicy ||
    !results.workspaceChecks.hasCloseoutCommand ||
    !results.workspaceChecks.hasExplicitProbeFlag ||
    results.consoleErrors.length
  ) {
    process.exit(1);
  }
})();
