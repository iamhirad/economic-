// Render build/print.html to an A4 PDF with Chromium (Playwright).
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [src, out] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve(src), { waitUntil: 'networkidle' });
  await page.evaluate(async () => {
    document.querySelectorAll('details').forEach(d => (d.open = true));
    await document.fonts.ready;
  });
  await page.emulateMedia({ media: 'print' });
  await page.pdf({ path: out, format: 'A4', printBackground: true, preferCSSPageSize: true, outline: true, tagged: true });
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
