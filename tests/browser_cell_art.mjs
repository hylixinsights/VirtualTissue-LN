import assert from 'node:assert/strict';
import {mkdir, writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
const {chromium} = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = fileURLToPath(new URL('../', import.meta.url));
const base = process.env.STUDIO_URL || 'http://127.0.0.1:8010';
const output = root + 'docs/cell-art-review/';
await mkdir(output, {recursive: true});
const browser = await chromium.launch({channel: process.env.CI ? undefined : 'chrome', headless: true});
const page = await browser.newPage({viewport: {width: 1512, height: 1100}});
const errors = [], measurements = [];
page.on('pageerror', error => errors.push(error.message));
page.on('console', message => {if (message.type() === 'error') errors.push(message.text());});
page.on('dialog', dialog => dialog.accept());

try {
  await page.goto(base);
  await page.locator('#loading').waitFor({state: 'hidden'});
  await page.waitForFunction(() => document.querySelector('#illustrated').getAttribute('aria-pressed') === 'true');
  for (const population of [100, 300]) {
    await page.locator('#population').selectOption(String(population));
    await page.locator('#reset').click();
    await page.waitForFunction(n => document.querySelector('#metricLive').textContent === String(n), population);
    assert.equal(await page.locator('#legend .atlas-thumb').count(), 3, 'B, CD4 and cDC2 must all use the supplied artwork');
    const before = (await (await page.request.get(base + '/api/state')).json()).tissue;
    const intervals = await page.evaluate(() => new Promise(resolve => {
      const times = []; let last;
      function frame(now) {if (last !== undefined) times.push(now-last); last=now; if (times.length<90) requestAnimationFrame(frame); else resolve(times);}
      requestAnimationFrame(frame);
    }));
    intervals.sort((a,b) => a-b);
    measurements.push({population, medianFrameMs: +intervals[45].toFixed(2), p95FrameMs: +intervals[85].toFixed(2)});
    const after = (await (await page.request.get(base + '/api/state')).json()).tissue;
    assert.deepEqual(after, before, 'Illustrative animation must not change any kernel state');
    const bounds = await page.locator('#scene').boundingBox();
    const pixelsPerUnit = bounds.height / (2 * 470 * Math.tan(39 * Math.PI / 360)) * 150 / before.params.radius_um;
    for (const kind of ['B', 'CD4', 'DC']) {
      const cell = before.cells.find(cell => cell.kind === kind);
      await page.mouse.click(bounds.x + bounds.width / 2 + cell.x * pixelsPerUnit, bounds.y + bounds.height / 2 - cell.y * pixelsPerUnit);
      assert((await page.locator('.cell-name').innerText()).includes(cell.id), `${kind} artwork must select the correct stable ID`);
    }
    await page.screenshot({path: output + `tissue-${population}.png`});
  }
  await page.locator('#artMotion').click();
  assert.equal(await page.locator('#artMotion').getAttribute('aria-pressed'), 'false');
  // Let camera damping settle. GPU readback can round a channel by one level.
  await page.waitForTimeout(250);
  const frozen = await page.locator('#scene').screenshot();
  await page.waitForTimeout(220);
  const later = await page.locator('#scene').screenshot();
  const pausedPixelDelta = await page.evaluate(async screenshots => {
    const pixels = await Promise.all(screenshots.map(async base64 => {
      const image = new Image(); image.src = 'data:image/png;base64,' + base64; await image.decode();
      const canvas = document.createElement('canvas'); canvas.width = image.width; canvas.height = image.height;
      const ctx = canvas.getContext('2d'); ctx.drawImage(image,0,0);
      return ctx.getImageData(0,0,canvas.width,canvas.height).data;
    }));
    let max = 0;
    for (let i=0;i<pixels[0].length;i++) max=Math.max(max,Math.abs(pixels[0][i]-pixels[1][i]));
    return max;
  }, [frozen.toString('base64'), later.toString('base64')]);
  assert(pausedPixelDelta <= 1, 'Pause must freeze visual motion (one-channel-level GPU rounding tolerance)');
  await page.locator('#original3d').click();
  assert.equal(await page.locator('#legend .atlas-thumb').count(), 0);
  await page.locator('#illustrated').click();
  assert.equal(await page.locator('#legend .atlas-thumb').count(), 3);
  await page.locator('#population').selectOption('100'); await page.locator('#reset').click();
  await page.waitForFunction(() => document.querySelector('#metricLive').textContent === '100');
  await page.setViewportSize({width: 390, height: 844});
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
  await page.screenshot({path: output + 'tissue-mobile.png', fullPage: true});

  await page.setViewportSize({width: 1440, height: 1100});
  await page.goto(base + '/web/cell-gallery.html');
  await page.waitForFunction(() => document.querySelector('#loadStatus').textContent === '');
  assert.equal(await page.locator('.card').count(), 4);
  assert((await page.locator('[data-cell="NEUTROPHIL"]').innerText()).includes('does not simulate neutrophils'));
  const poses = new Set();
  for (let i = 0; i < 8; i++) {
    await page.locator(`[data-cell="B"] [data-pose="${i}"]`).click();
    assert.equal(await page.locator('#poseLabel').textContent(), `${i+1} / 8`);
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    poses.add((await page.locator('[data-cell="B"] .art-stage canvas').screenshot()).toString('base64'));
  }
  assert.equal(poses.size, 8, 'Each supplied pose must be independently visible');
  await page.locator('[data-cell="B"] [data-pose="0"]').click();
  await page.screenshot({path: output + 'gallery-desktop.png', fullPage: true});
  await page.setViewportSize({width:390,height:844});
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
  await page.screenshot({path: output + 'gallery-mobile.png', fullPage: true});
  await page.emulateMedia({reducedMotion:'reduce'}); await page.reload();
  await page.waitForFunction(() => document.querySelector('#loadStatus').textContent === '');
  assert.equal(await page.locator('#motion').getAttribute('aria-pressed'), 'false');
  await page.goto(base);
  await page.waitForFunction(() => document.querySelector('#illustrated').getAttribute('aria-pressed') === 'true');
  assert.equal(await page.locator('#artMotion').getAttribute('aria-pressed'), 'false');

  const fallback = await browser.newPage();
  await fallback.route('**/assets/cells/Dendritic_cells.png', route => route.abort());
  await fallback.goto(base);
  await fallback.waitForFunction(() => document.querySelector('#artStatus').textContent.includes('could not load'));
  assert.equal(await fallback.locator('#original3d').getAttribute('aria-pressed'), 'true');
  assert.equal(await fallback.locator('#illustrated').isEnabled(), false);
  await fallback.close();

  assert.deepEqual(errors, []);
  const result = {browser:'Headless Chrome on this Windows computer', measurements, kernelUnchanged:true, stableSelection:['B','CD4','DC'], poses:poses.size, pausedPixelDelta, mobileOverflow:false, reducedMotion:true, missingArtworkFallback:true, errors};
  await writeFile(output + 'checks.json', JSON.stringify(result,null,2)+'\n');
  console.log(result);
} finally {await browser.close();}
