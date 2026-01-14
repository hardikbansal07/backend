// Puppeteer UI snapshot script (CommonJS)
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

(async () => {
  const outDir = path.resolve(__dirname, '..', '..', 'artifacts');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

  const ports = [3001, 3000];
  let url = null;

  for (const p of ports) {
    try {
      const res = await fetch(`http://localhost:${p}`);
      if (res.ok) { url = `http://localhost:${p}`; break; }
    } catch (e) {
      // ignore
    }
  }

  if (!url) {
    console.error('Could not reach frontend on ports 3001 or 3000');
    process.exit(2);
  }

  const browser = await puppeteer.launch({ args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1400, height: 1000 });
    console.log('Opening', url);
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
    const ts = new Date().toISOString().replace(/[:.]/g, '-');
    const png = path.join(outDir, `frontend_snapshot_${ts}.png`);
    const html = path.join(outDir, `frontend_snapshot_${ts}.html`);
    await page.screenshot({ path: png, fullPage: true });
    const content = await page.content();
    fs.writeFileSync(html, content, 'utf8');
    console.log('WROTE', png);
    console.log('WROTE', html);
  } finally {
    await browser.close();
  }
})();
