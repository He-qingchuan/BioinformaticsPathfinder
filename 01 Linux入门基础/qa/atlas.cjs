const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {pathToFileURL} = require('node:url');
const root = path.resolve(__dirname, '..');
const out = path.join(__dirname, 'artifacts');
fs.mkdirSync(path.join(out, 'browser-tmp'), {recursive: true});
process.env.TMPDIR = path.join(out, 'browser-tmp');
process.env.TEMP = process.env.TMPDIR; process.env.TMP = process.env.TMPDIR;
const {chromium} = require('playwright');
const home = pathToFileURL(path.join(root, 'index.html')).href;
const lessons = JSON.parse(fs.readFileSync(path.join(root, 'content/course.json'))).lessons;
const key = 'pathfinder-linux-read-v1';
const report = {widths: [], checks: [], externalRequests: [], errors: []};
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
let browser;

async function geometry(page, width) {
  const problems = await page.locator('#atlas-map .map-lesson').evaluateAll(links => {
    const problems = [], boxes = links.map(a => a.getBoundingClientRect());
    for (let i = 0; i < links.length; i++) {
      const a = links[i], r = boxes[i], id = a.dataset.courseLesson;
      const map = a.closest('#atlas-map').getBoundingClientRect();
      if (r.width < 44 || r.height < 44) problems.push(`${id}: small target`);
      if (r.top < map.top || r.bottom > map.bottom - 8 || r.left < map.left || r.right > map.right) problems.push(`${id}: clipped by map boundary`);
      if (a.scrollWidth > a.clientWidth + 1) problems.push(`${id}: text overflow`);
      for (let j = i + 1; j < boxes.length; j++) {
        const b = boxes[j];
        if (Math.min(r.right, b.right) - Math.max(r.left, b.left) > 1 && Math.min(r.bottom, b.bottom) - Math.max(r.top, b.top) > 1) problems.push(`${id}: overlaps ${links[j].dataset.courseLesson}`);
      }
    }
    if (document.documentElement.scrollWidth > innerWidth + 1) problems.push('page overflow');
    return problems;
  });
  assert.deepEqual(problems, [], `${width}px`);
}

(async () => {
  browser = await chromium.launch({headless: true});
  const context = await browser.newContext({offline: true, viewport: {width: 1440, height: 1100}, reducedMotion: 'no-preference'});
  const page = await context.newPage();
  page.on('pageerror', e => report.errors.push(e.message));
  page.on('request', r => {if (/^https?:/.test(r.url())) report.externalRequests.push(r.url());});
  await page.goto(home);
  await page.screenshot({path: path.join(out, 'atlas-initial-1440.png'), fullPage: true});
  await page.setViewportSize({width: 390, height: 900});
  await page.screenshot({path: path.join(out, 'atlas-initial-390.png'), fullPage: true});
  await page.setViewportSize({width: 1440, height: 1100});
  for (const container of ['#atlas-map', '#map-directory']) {
    const actual = await page.locator(`${container} [data-course-lesson]`).evaluateAll(as => as.map(a => [a.dataset.courseLesson, a.getAttribute('href')]));
    assert.deepEqual(actual, lessons.map(l => [l.id, `lessons/${l.id}.html`]));
  }
  assert.equal(await page.locator('#atlas-map .is-next').getAttribute('data-course-lesson'), '01');
  await page.locator('#atlas-map').scrollIntoViewIfNeeded();
  await page.waitForFunction(() => document.getElementById('atlas-map').dataset.motion === 'playing');
  const bird = page.locator('.atlas-landscape .bird-flight');
  const transform = () => bird.evaluate(el => getComputedStyle(el).transform);
  const first = await transform(); await delay(300); assert.notEqual(await transform(), first);
  await page.locator('#atlas-motion').click();
  await page.waitForFunction(() => getComputedStyle(document.querySelector('.atlas-landscape .bird-flight')).animationPlayState === 'paused');
  // CSS pause reaches the compositor at a frame boundary; sample after it settles.
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  const stopped = await transform(); await delay(300); assert.equal(await transform(), stopped);
  await page.reload(); assert.equal(await page.locator('#atlas-motion').textContent(), '开启动态');
  await page.locator('#atlas-motion').click();
  await page.emulateMedia({reducedMotion: 'reduce'});
  await page.waitForFunction(() => document.getElementById('atlas-motion').disabled);
  assert.equal(await page.locator('#atlas-motion').isDisabled(), true);
  assert.equal(await bird.evaluate(el => getComputedStyle(el).animationName), 'none');
  await page.emulateMedia({reducedMotion: 'no-preference'});
  await page.locator('#atlas-map').scrollIntoViewIfNeeded();
  await page.waitForFunction(() => document.getElementById('atlas-map').dataset.motion === 'playing');
  await page.evaluate(() => {Object.defineProperty(document, 'hidden', {configurable: true, value: true}); document.dispatchEvent(new Event('visibilitychange'));});
  assert.equal(await page.locator('#atlas-map').getAttribute('data-motion'), 'paused');
  await page.evaluate(() => {delete document.hidden; document.dispatchEvent(new Event('visibilitychange'));});
  await page.setViewportSize({width: 1440, height: 200}); await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForFunction(() => document.getElementById('atlas-map').dataset.motion === 'paused');
  await page.setViewportSize({width: 1440, height: 1100}); await page.locator('#atlas-map').scrollIntoViewIfNeeded();
  await page.waitForFunction(() => document.getElementById('atlas-map').dataset.motion === 'playing');
  report.checks.push('real motion and pause', 'persisted pause', 'system reduced motion', 'page visibility signal', 'offscreen pause');

  await page.locator('#atlas-map [data-course-lesson="01"]').click();
  await page.locator('#mark-read').click();
  await page.getByRole('link', {name: '学习地图', exact: true}).click();
  assert.equal(await page.locator('#atlas-map .is-next').getAttribute('data-course-lesson'), '02');
  assert.equal(await page.locator('.zone-camp .zone-progress').textContent(), '1 / 3 已读');
  await page.evaluate(k => localStorage.setItem(k, '["01","03"]'), key); await page.reload();
  assert.equal(await page.locator('#atlas-map .is-next').getAttribute('data-course-lesson'), '02');
  await page.locator('#atlas-map [data-course-lesson="02"]').click(); await page.locator('#mark-read').click(); await page.goBack();
  assert.equal(await page.locator('#atlas-map .is-next').getAttribute('data-course-lesson'), '04');
  assert.equal(await page.locator('.zone-camp').evaluate(el => el.classList.contains('is-complete')), true);
  await page.locator('#atlas-map [data-course-lesson="03"]').focus(); await page.keyboard.press('Tab');
  assert.equal(await page.evaluate(() => document.activeElement.dataset.courseLesson), '04');
  assert.equal(await page.locator('[data-route-zone="files"].is-active').count(), 2);
  await page.keyboard.press('Enter'); await page.waitForURL(/lessons\/04.html$/); await page.goBack();
  await page.locator('[data-atlas-view="directory"]').click();
  assert.equal(await page.locator('#atlas-map').isVisible(), false);
  assert.equal(await page.locator('#map-directory').isVisible(), true);
  assert.equal(await page.locator('#map-directory .is-read').count(), 3);
  await page.locator('[data-atlas-view="map"]').click();
  await page.evaluate(({k, ids}) => localStorage.setItem(k, JSON.stringify(ids)), {k: key, ids: lessons.map(l => l.id)}); await page.reload();
  assert.equal(await page.locator('#atlas-map .is-next').count(), 0);
  assert.equal(await page.locator('#atlas-map .is-read').count(), 18);
  assert.equal(await page.locator('#continue-link').getAttribute('href'), 'lessons/18.html');
  await page.evaluate(k => localStorage.setItem(k, '[]'), key); await page.reload();
  assert.equal(await page.locator('#continue-link').getAttribute('href'), 'lessons/01.html');
  report.checks.push('18 matching map and directory links', 'existing progress migration', 'chapter return and browser back', 'out-of-order and complete progress', 'keyboard sequence and route focus', 'view switch');

  await page.locator('#atlas-motion').click();
  await page.evaluate(() => document.activeElement?.blur());
  for (const width of [320, 390, 768, 1024, 1101, 1440, 1920]) {
    await page.setViewportSize({width, height: 1000});
    await page.screenshot({path: path.join(out, `atlas-home-${width}.png`), fullPage: true});
    await geometry(page, width); report.widths.push(width);
  }
  await page.setViewportSize({width: 1440, height: 1100});
  await page.locator('#atlas-map').screenshot({path: path.join(out, 'atlas-map-1440.png')});
  await page.emulateMedia({media: 'print'});
  assert.equal(await page.locator('#atlas-map').isVisible(), false);
  assert.equal(await page.locator('#map-directory').isVisible(), true);
  await page.emulateMedia({media: 'screen'});

  const touch = await browser.newContext({offline: true, viewport: {width: 390, height: 844}, isMobile: true, hasTouch: true});
  const tp = await touch.newPage(); await tp.goto(home); await tp.locator('#atlas-map [data-course-lesson="18"]').tap(); await tp.waitForURL(/lessons\/18.html$/); await tp.getByRole('link', {name: '学习地图', exact: true}).tap(); await tp.waitForURL(/index.html#course$/); await touch.close();
  const staticContext = await browser.newContext({offline: true, javaScriptEnabled: false});
  const sp = await staticContext.newPage(); await sp.goto(home);
  assert.equal(await sp.locator('#map-directory').isVisible(), true);
  assert.equal(await sp.locator('.atlas-landscape .bird-flight').evaluate(el => getComputedStyle(el).animationPlayState), 'paused');
  await sp.locator('#atlas-map [data-course-lesson="06"]').click(); assert.match(sp.url(), /lessons\/06.html$/); await staticContext.close();
  const denied = await browser.newContext({offline: true});
  await denied.addInitScript(() => Object.defineProperty(window, 'localStorage', {get() {throw new Error('test storage blocked');}}));
  const dp = await denied.newPage(); await dp.goto(home); await dp.locator('#atlas-motion').click(); assert.equal(await dp.locator('#atlas-map').getAttribute('data-motion'), 'paused'); await dp.locator('#atlas-map [data-course-lesson="01"]').click(); assert.match(dp.url(), /lessons\/01.html$/); await denied.close();
  report.checks.push('44px targets and non-overlapping labels', 'touch navigation', 'static no-JavaScript map', 'blocked storage', 'print directory');

  const videoContext = await browser.newContext({offline: true, viewport: {width: 1280, height: 960}, reducedMotion: 'no-preference', recordVideo: {dir: path.join(out, 'video'), size: {width: 1280, height: 960}}});
  const vp = await videoContext.newPage(); await vp.goto(home); await vp.locator('#atlas-map').scrollIntoViewIfNeeded();
  await delay(10000); const video = vp.video(); await videoContext.close(); await video.saveAs(path.join(out, 'atlas-preview.webm'));
  assert.deepEqual(report.errors, []); assert.deepEqual(report.externalRequests, []);
  fs.writeFileSync(path.join(out, 'atlas.json'), JSON.stringify(report, null, 2) + '\n'); console.log(JSON.stringify(report));
})().catch(e => {console.error(e); process.exitCode = 1;}).finally(async () => {if (browser) await browser.close();});
