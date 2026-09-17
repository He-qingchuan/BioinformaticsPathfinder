const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const {pathToFileURL} = require('node:url');
const root = path.resolve(__dirname, '..');
const report = {pass:false, checks:[], searchCases:0, viewports:[], errors:[], externalRequests:[]};
const url = name => pathToFileURL(path.join(root, name)).href;
const map = '01_海岛探险教案.html', reading = '02_完整教案_阅读与打印.html';
let browser;
async function allImages(page) {
  await page.locator('img').evaluateAll(images => images.forEach(img => img.loading='eager'));
  await page.waitForFunction(() => [...document.images].filter(i=>i.getAttribute('src')).every(i=>i.complete&&i.naturalWidth>0));
}
async function openStation(page, id) {
  await page.evaluate(id=>document.querySelector(`.station-node[data-station="${id}"]`).click(),id);
  await page.waitForFunction(id=>location.hash==='#station/'+id && document.getElementById('lesson-dialog').open,id);
}
async function escapeGlossary(page) {
  await page.keyboard.press('Escape');
  await page.waitForFunction(()=>!document.getElementById('glossary-dialog').open);
  await page.waitForTimeout(50);
}
function attach(context) {
  context.on('page',page=>{
    page.on('pageerror',e=>report.errors.push(e.message));
    page.on('request',r=>{if(/^https?:/.test(r.url()))report.externalRequests.push(r.url());});
  });
}
(async()=>{
  browser=await chromium.launch({headless:true});
  const context=await browser.newContext({offline:true,viewport:{width:1440,height:1000},reducedMotion:'reduce'});
  attach(context);
  const page=await context.newPage();
  await page.goto(url(map),{waitUntil:'load'});
  const count=await page.evaluate(()=>window.GLOSSARY.entries.length);
  assert.equal(count,178);
  await page.locator('#open-glossary').click();
  assert.equal(await page.locator('#glossary-entries .glossary-entry').count(),count);
  const cases=await page.evaluate(()=>{
    let checked=0;const errors=[];
    const input=document.getElementById('glossary-query');
    for(const e of window.GLOSSARY.entries){
      for(const q of new Set([e.zh,e.en,e.abbr,...e.aliases].filter(Boolean))){
        input.value=q;input.dispatchEvent(new Event('input',{bubbles:true}));
        const results=[...document.querySelectorAll('#glossary-entries [data-entry]')].map(n=>n.dataset.entry);
        if(!results.includes(e.id))errors.push({query:q,wanted:e.id,actual:results});
        checked++;
      }
    }
    return {checked,errors};
  });
  assert.deepEqual(cases.errors,[]);report.searchCases=cases.checked;
  for(const [q,id] of [['BP','go_bp'],['bp','base'],['Count','enrichment_count'],['counts','counts'],['log₂FC','log2fc'],['log2FC','log2fc'],['BH.Q','padj'],['p.adjust','padj'],['membership','membership']]){
    await page.locator('#glossary-query').fill(q);
    assert.deepEqual(await page.locator('#glossary-entries [data-entry]').evaluateAll(es=>es.map(e=>e.dataset.entry)),[id]);
  }
  await page.locator('#glossary-query').fill('unfindable_没有这个词');
  assert.equal(await page.locator('#glossary-entries .glossary-entry').count(),0);
  assert.ok(await page.locator('.glossary-empty').isVisible());
  await page.locator('#glossary-all').click();
  await page.locator('#glossary-category').selectOption('时间与聚类');
  assert.ok(await page.locator('#glossary-entries .glossary-entry').count()>5);
  assert.ok((await page.locator('#glossary-entries .glossary-category').allTextContents()).every(t=>t==='时间与聚类'));
  await escapeGlossary(page);
  report.checks.push('178 项全部中文、英文、缩写和别名可查；Count/counts、BP/bp、公式别名区分；分类、无结果、清空正常');

  await openStation(page,'trend');
  await allImages(page);
  const opener=page.locator('#lesson-content .term[data-term="membership"]').first();
  await opener.scrollIntoViewIfNeeded();
  const position=await page.evaluate(()=>({top:document.getElementById('lesson-scroll').scrollTop,hash:location.hash}));
  await opener.click();
  assert.equal(await page.locator('#glossary-entries .glossary-entry').count(),1);
  assert.equal(await page.locator('#glossary-entries .glossary-part').count(),4);
  assert.equal(await page.locator('#glossary-entries details').count(),0);
  assert.ok((await page.locator('.glossary-english').textContent()).includes('degree of membership'));
  await page.screenshot({path:path.join(__dirname,'glossary_membership_1440.png')});
  await page.locator('#glossary-entries .glossary-related [data-term="fuzzy_clustering"]').click();
  assert.equal(await page.locator('#glossary-entries [data-entry="fuzzy_clustering"]').count(),1);
  for(let i=0;i<8;i++){
    await page.keyboard.press('Tab');
    assert.ok(await page.evaluate(()=>!!document.activeElement.closest('#glossary-dialog')));
  }
  await escapeGlossary(page);
  assert.ok(await opener.evaluate(el=>document.activeElement===el));
  assert.deepEqual(await page.evaluate(()=>({top:document.getElementById('lesson-scroll').scrollTop,hash:location.hash})),position);
  await page.locator('[data-figure="trend_lines"] [data-zoom]').click();
  const figTerm=page.locator('#image-caption .term[data-term="membership"]').first();
  await figTerm.scrollIntoViewIfNeeded();
  const captionTop=await page.locator('#image-caption').evaluate(el=>el.scrollTop);
  await figTerm.click();
  assert.equal(await page.locator('dialog[open]').count(),3);
  await escapeGlossary(page);
  assert.equal(await page.locator('dialog[open]').count(),2);
  assert.ok(await figTerm.evaluate(el=>document.activeElement===el));
  assert.equal(await page.locator('#image-caption').evaluate(el=>el.scrollTop),captionTop);
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('dialog[open]').count(),1);
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('dialog[open]').count(),0);
  report.checks.push('正文点击精确单项；四层解释展开；相关术语切换；三层窗口逐层 Esc；键盘焦点与滚动位置恢复');

  for(const [width,height] of [[320,740],[390,844],[768,1024],[1440,1000]]){
    await page.setViewportSize({width,height});
    await page.goto(url(map),{waitUntil:'load'});
    await openStation(page,'trend');
    await page.locator('#lesson-content .term[data-term="membership"]').first().click();
    const fit=await page.evaluate(()=>{
      const d=document.getElementById('glossary-dialog'),c=document.getElementById('glossary-entries');
      const r=d.getBoundingClientRect();
      return {fits:r.left>=-1&&r.right<=innerWidth+1&&r.top>=-1&&r.bottom<=innerHeight+1,
        noOverflow:c.scrollWidth<=c.clientWidth+1,readableHeight:c.clientHeight};
    });
    assert.ok(fit.fits&&fit.noOverflow&&fit.readableHeight>220,JSON.stringify({width,fit}));
    report.viewports.push({width,height,...fit});
    await page.screenshot({path:path.join(__dirname,`glossary_membership_${width}.png`)});
    await page.locator('#glossary-entries').evaluate(el=>el.scrollTop=el.scrollHeight);
    assert.ok(await page.locator('#glossary-entries .glossary-related').isVisible());
  }
  report.checks.push('320 / 390 / 768 / 1440 像素下术语窗口可读、无横向溢出');

  await page.setViewportSize({width:1440,height:1000});
  await page.goto(url(reading),{waitUntil:'load'});
  await allImages(page);
  const readerTerm=page.locator('#trend .term[data-term="membership"]').first();
  await readerTerm.scrollIntoViewIfNeeded();
  const readerTop=await page.evaluate(()=>scrollY);
  await readerTerm.click();
  assert.equal(await page.locator('#glossary-entries [data-entry="membership"]').count(),1);
  await escapeGlossary(page);
  assert.ok(await readerTerm.evaluate(el=>document.activeElement===el));
  assert.equal(await page.evaluate(()=>scrollY),readerTop);
  await page.locator('[data-figure="volcano_classic"] [data-zoom]').click();
  await page.locator('#image-caption .term[data-term="padj"]').first().click();
  assert.equal(await page.locator('#glossary-entries [data-entry="padj"]').count(),1);
  await escapeGlossary(page);await page.keyboard.press('Escape');
  assert.equal(await page.locator('.glossary-appendix .glossary-entry').count(),count);
  report.checks.push('完整阅读页和放大图解使用相同解释；关闭后保留原阅读位置');
  await page.emulateMedia({media:'print'});
  assert.equal(await page.locator('#glossary-dialog').isVisible(),false);
  await page.pdf({path:'/tmp/rnaseq-v3-print-proof.pdf',format:'A4',printBackground:true,
    margin:{top:'12mm',bottom:'12mm',left:'13mm',right:'13mm'}});
  report.printProof='/tmp/rnaseq-v3-print-proof.pdf';

  const noJS=await browser.newContext({offline:true,javaScriptEnabled:false,viewport:{width:1200,height:900}});
  attach(noJS);const staticPage=await noJS.newPage();
  await staticPage.goto(url(reading),{waitUntil:'load'});
  const staticTerm=staticPage.locator('#trend .term[data-term="membership"]').first();
  await staticTerm.click();
  assert.ok(staticPage.url().endsWith('#glossary-26'));
  assert.ok((await staticPage.locator('#glossary-26').textContent()).includes('degree of membership'));
  assert.equal(await staticPage.locator('#reading-glossary').isVisible(),false);
  await noJS.close();
  report.checks.push('禁用脚本时跳到完整中英术语附录；原 glossary-26 等旧锚点保留；打印包含所有条目');

  const temp=fs.mkdtempSync(path.join(os.tmpdir(),'rnaseq-v3-glossary-'));
  try{
    const moved=path.join(temp,'移动 后的新教案');
    fs.cpSync(root,moved,{recursive:true,filter:p=>!p.startsWith(path.join(root,'qa'))});
    const movedPage=await context.newPage();
    await movedPage.goto(pathToFileURL(path.join(moved,map)).href,{waitUntil:'load'});
    await openStation(movedPage,'trend');
    await movedPage.locator('#lesson-content .term[data-term="membership"]').first().click();
    assert.equal(await movedPage.locator('#glossary-entries [data-entry="membership"]').count(),1);
    await movedPage.goto(pathToFileURL(path.join(moved,reading)).href,{waitUntil:'load'});
    await movedPage.locator('#reading-glossary').click();
    await movedPage.locator('#glossary-query').fill('Count');
    assert.equal(await movedPage.locator('#glossary-entries [data-entry="enrichment_count"]').count(),1);
    await movedPage.close();
  }finally{fs.rmSync(temp,{recursive:true,force:true});}
  report.checks.push('整包复制、改名并离线打开后，两个入口的术语仍能查询');
  assert.deepEqual(report.errors,[]);assert.deepEqual(report.externalRequests,[]);
  report.pass=true;report.checked_utc=new Date().toISOString();
  fs.writeFileSync(path.join(__dirname,'glossary_browser.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report));
  await browser.close();
})().catch(async error=>{
  report.failure=error.stack;
  fs.writeFileSync(path.join(__dirname,'glossary_browser.json'),JSON.stringify(report,null,2)+'\n');
  console.error(error);
  if(browser)await browser.close();
  process.exit(1);
});
