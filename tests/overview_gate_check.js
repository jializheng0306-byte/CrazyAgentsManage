const { chromium } = require('playwright');
const fs = require('fs');

(async() => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1200 } });
  const baseUrl = 'http://127.0.0.1:5002';
  const results = {
    overviewStatus: null,
    navLinks: {},
    hero: {},
    jumps: {},
    architectureLinks: {},
    summaryLinks: {},
    runtimeCards: 0,
    errorsCount: 0,
    sourceCards: 0,
    consoleErrors: []
  };

  page.on('console', msg => {
    if (msg.type() === 'error') results.consoleErrors.push(msg.text());
  });
  page.on('pageerror', err => {
    results.consoleErrors.push(String(err));
  });

  const response = await page.goto(baseUrl + '/overview', { waitUntil: 'domcontentloaded' });
  results.overviewStatus = response ? response.status() : null;
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: 'C:/Users/123/AppData/Local/Temp/overview-gate.png', fullPage: true });

  async function hrefFor(selector) {
    const el = page.locator(selector).first();
    if (await el.count() === 0) return null;
    return await el.getAttribute('href');
  }

  results.navLinks.overview = await hrefFor('a.nav-item[href$="/overview"]');
  results.navLinks.runtime = await hrefFor('a.nav-item[href$="/runtime"]');
  results.navLinks.operations = await hrefFor('a.nav-item[href$="/operations"]');
  results.navLinks.governance = await hrefFor('a.nav-item[href$="/governance"]');
  results.navLinks.collaboration = await hrefFor('a.nav-item[href$="/collaboration"]');

  results.hero.kicker = await page.locator('.ov-kicker').textContent();
  results.hero.title = await page.locator('#hero-briefing-title').textContent();
  results.hero.copy = await page.locator('#hero-briefing-copy').textContent();
  results.hero.nextHopHref = await hrefFor('#hero-next-hop');
  results.hero.nextHopSurface = await page.locator('#hero-next-hop-surface').textContent();
  results.hero.nextHopReason = await page.locator('#hero-next-hop-reason').textContent();

  results.jumps.quickLinks = await page.locator('.ov-quick-links a').evaluateAll(nodes => nodes.map(n => ({ text: n.textContent.trim(), href: n.getAttribute('href') })));
  results.architectureLinks.cards = await page.locator('.ov-architecture-link').evaluateAll(nodes => nodes.map(n => ({ text: n.textContent.trim(), href: n.getAttribute('href') })));
  results.summaryLinks.cards = await page.locator('.ov-summary-action').evaluateAll(nodes => nodes.map(n => ({ text: n.textContent.trim(), href: n.getAttribute('href') })));

  results.runtimeCards = await page.locator('.ov-session-card').count();
  results.errorsCount = await page.locator('.ov-error-item').count();
  results.sourceCards = await page.locator('.ov-source-card').count();

  fs.writeFileSync('C:/Users/123/AppData/Local/Temp/overview-gate-results.json', JSON.stringify(results, null, 2));
  console.log(JSON.stringify(results, null, 2));

  await browser.close();
})();
