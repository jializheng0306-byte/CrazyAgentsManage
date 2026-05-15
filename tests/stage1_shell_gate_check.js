const { chromium } = require('playwright');
const fs = require('fs');

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
        primaryRail: '.fm-primary-rail',
        contextPanel: '.fm-context-panel',
        search: '.fm-context-search input',
        chips: '.fm-context-chip',
        treeItems: '.fm-tree-item',
        main: 'main#overview-app'
      }
    },
    {
      key: 'runtime',
      url: '/runtime',
      checks: {
        shell: '.fm-shell-nav',
        runtimeTree: '.fm-tree-item[href="/runtime/sessions"]',
        search: '.fm-context-search input',
        chips: '.fm-context-chip',
        main: 'main#runtime-app'
      }
    },
    {
      key: 'operations',
      url: '/operations',
      checks: {
        shell: '.fm-shell-nav',
        opsTree: '.fm-tree-item[href="/operations/skills"]',
        search: '.fm-context-search input',
        chips: '.fm-context-chip',
        main: 'main#ops-app'
      }
    },
    {
      key: 'governance',
      url: '/governance',
      checks: {
        shell: '.fm-shell-nav',
        govTree: '.fm-tree-item[href="/governance/graph"]',
        search: '.fm-context-search input',
        chips: '.fm-context-chip',
        main: 'main#gv-app'
      }
    },
    {
      key: 'collaboration',
      url: '/collaboration',
      checks: {
        shell: '.fm-shell-nav',
        collabTree: '.fm-tree-item[href="/collaboration/tasks"]',
        search: '.fm-context-search input',
        chips: '.fm-context-chip',
        main: 'main#cl-app'
      }
    },
    {
      key: 'legacy-sessions',
      url: '/sessions',
      checks: {
        shell: '.fm-shell-nav',
        runtimeTree: '.fm-tree-item[href="/runtime/sessions"]'
      }
    },
    {
      key: 'legacy-dashboard',
      url: '/dashboard',
      checks: {
        shell: '.fm-shell-nav',
        runtimeTree: '.fm-tree-item[href="/runtime/dashboard"]'
      }
    },
    {
      key: 'legacy-skills',
      url: '/skills',
      checks: {
        shell: '.fm-shell-nav',
        opsTree: '.fm-tree-item[href="/operations/skills"]'
      }
    },
    {
      key: 'legacy-graph',
      url: '/graph',
      checks: {
        shell: '.fm-shell-nav',
        govTree: '.fm-tree-item[href="/governance/graph"]'
      }
    },
    {
      key: 'legacy-tasks',
      url: '/tasks',
      checks: {
        shell: '.fm-shell-nav',
        collabTree: '.fm-tree-item[href="/collaboration/tasks"]'
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
    await page.waitForTimeout(1500);

    const checks = {};
    for (const [name, selector] of Object.entries(item.checks)) {
      checks[name] = await page.locator(selector).count();
    }

    results[item.key] = {
      status: response ? response.status() : null,
      checks,
      title: await page.title(),
      primaryActive: await page.locator('.fm-primary-link.active').evaluateAll(nodes => nodes.map(n => n.textContent.replace(/\s+/g, ' ').trim())),
      consoleErrors,
    };

    await page.close();
  }

  fs.writeFileSync('C:/Users/123/AppData/Local/Temp/stage1-shell-results.json', JSON.stringify(results, null, 2));
  console.log(JSON.stringify(results, null, 2));
  await context.close();
  await browser.close();
})();
