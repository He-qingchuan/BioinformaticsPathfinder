const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const path=require('node:path');
const fs=require('node:fs');
const {pathToFileURL}=require('node:url');
const root=path.resolve(__dirname,'..');
const home=pathToFileURL(path.join(root,'01_海岛探险教案.html')).href;
const reading=pathToFileURL(path.join(root,'02_完整教案_阅读与打印.html')).href;
const result={guides:[],illustrations:[],responsive:[],errors:[],externalRequests:[]};
let browser;
(async()=>{
 browser=await chromium.launch({headless:true});
 const context=await browser.newContext({offline:true,viewport:{width:1440,height:1000}});
 context.on('page',page=>{
   page.on('pageerror',e=>result.errors.push(e.message));
   page.on('request',r=>{if(/^https?:/.test(r.url()))result.externalRequests.push(r.url());});
 });
 const page=await context.newPage();
 await page.goto(reading,{waitUntil:'load'});
 await page.locator('main img').evaluateAll(xs=>xs.forEach(x=>x.loading='eager'));
 await page.waitForFunction(()=>[...document.querySelectorAll('main img')].every(x=>x.complete&&x.naturalWidth>0));
 assert.equal(await page.locator('.figure-reading').count(),37);
 assert.equal(await page.locator('.guide-section').count(),149);
 assert.equal(await page.locator('main .figure-reading details').count(),0);
 const figures=page.locator('main figure:has([data-zoom])');
 assert.equal(await figures.count(),37);
 for(let i=0;i<37;i++){
   const fig=figures.nth(i);
   const title=await fig.locator('.figure-summary>strong').textContent();
   const guideText=await fig.locator('.figure-reading').innerText();
   assert.equal(await fig.locator('.figure-summary').isVisible(),true);
   if(await fig.locator('.figure-guide').count())assert.equal(await fig.locator('.figure-guide').isVisible(),true);
   await fig.locator('[data-zoom]').click();
   await page.waitForFunction(()=>document.getElementById('large-image').complete&&document.getElementById('large-image').naturalWidth>0);
   assert.equal(await page.locator('#image-title').textContent(),title);
   assert.equal(await page.locator('#image-caption').innerText(),guideText);
   assert.equal(await page.locator('#image-dialog').evaluate(e=>e.open),true);
   if(i===0)await page.screenshot({path:path.join(__dirname,'concept_zoom_desktop.png')});
   await page.keyboard.press('Escape');
   assert.equal(await fig.locator('[data-zoom]').evaluate(e=>document.activeElement===e),true);
   result.guides.push({title,paragraphs:await fig.locator('.guide-section').count(),zoom:true});
 }
 const classic=page.locator('[data-figure="volcano_classic"]');
 await classic.locator('[data-annotations]').click();
 assert.equal(await classic.locator('.figure-summary').isVisible(),true);
 assert.equal(await classic.locator('.figure-guide').isVisible(),true);
 assert.equal(await classic.locator('.figure-marker').first().isVisible(),false);
 await classic.screenshot({path:path.join(__dirname,'volcano_full_guide.png')});
 await classic.locator('[data-annotations]').click();
 await page.locator('.term').first().click();
 assert.equal(await page.locator('#glossary-dialog').evaluate(el=>el.open),true);
 assert.equal(await page.locator('#glossary-entries .glossary-entry').count(),1);
 await page.keyboard.press('Escape');
 for(const [width,height] of [[320,800],[390,844],[768,1024],[1440,1000],[1920,1080]]){
   await page.setViewportSize({width,height});
   for(const id of ['qc_quality_before','retention','volcano_enhanced','ora_go','trend_heat']){
     const fig=page.locator(`[data-figure="${id}"]`);
     await fig.locator('.figure-summary').scrollIntoViewIfNeeded();
     assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true,'reader overflow '+width);
     assert.equal(await fig.locator('.figure-guide').evaluate(e=>e.scrollWidth<=e.clientWidth+1),true,'guide overflow '+id+' '+width);
   }
   const fig=page.locator('[data-figure="volcano_classic"]');
   await fig.locator('[data-zoom]').click();
   assert.ok(await page.locator('#image-dialog').evaluate(e=>e.getBoundingClientRect().right<=innerWidth+1));
   assert.ok(await page.locator('#image-caption').evaluate(e=>e.scrollWidth<=e.clientWidth+1));
   if(width===390||width===768){
     await page.screenshot({path:path.join(__dirname,`figure_zoom_${width}.png`)});
     if(width===390){
       await page.locator('#image-caption .guide-section').first().scrollIntoViewIfNeeded();
       await page.screenshot({path:path.join(__dirname,'figure_guide_390.png')});
     }
   }
   await page.keyboard.press('Escape');
   result.responsive.push({width,height,pass:true});
 }
 // Inspect all new vector text bounds, and produce contact sheets for human visual review.
 const art=await context.newPage();
 await art.setViewportSize({width:1460,height:1050});
 const files=fs.readdirSync(path.join(root,'assets/illustrations')).filter(f=>f.endsWith('.svg')).sort();
 const entries=[];
 for(const file of files){
   const svg=fs.readFileSync(path.join(root,'assets/illustrations',file),'utf8');
   await art.setContent(svg);
   await art.evaluate(()=>document.fonts.ready);
   const details=await art.locator('svg').evaluate(svg=>{
     const v=svg.viewBox.baseVal;
     return [...svg.querySelectorAll('text')].map(t=>({text:t.textContent,b:t.getBBox()})).filter(x=>x.b.x<0||x.b.y<0||x.b.x+x.b.width>v.width+.5||x.b.y+x.b.height>v.height+.5).map(x=>x.text);
   });
   result.illustrations.push({file,outOfBounds:details});
   entries.push(`<article><h2>${file}</h2>${svg}</article>`);
 }
 for(let i=0;i<entries.length;i+=4){
   await art.setContent(`<html><head><style>body{margin:12px;background:#e8eee3;font-family:sans-serif}main{display:grid;grid-template-columns:1fr 1fr;gap:14px}article{background:#fff;padding:8px;min-width:0}h2{font-size:14px;margin:6px;color:#496b65}svg{width:100%;height:auto;display:block}</style></head><body><main>${entries.slice(i,i+4).join('')}</main></body></html>`);
   await art.screenshot({path:path.join(__dirname,`illustrations_${Math.floor(i/4)+1}.png`),fullPage:true});
 }
 await page.setViewportSize({width:1280,height:900});
 await page.goto(home,{waitUntil:'load'});
 await page.evaluate(()=>document.querySelector('[data-station="sample"]').click());
 await page.locator('.teaching-visual [data-zoom]').click();
 assert.equal(await page.locator('#image-eyebrow').textContent(),'原理插图 · 教学示意');
 await page.keyboard.press('Escape');
 assert.equal(await page.locator('#lesson-dialog').evaluate(e=>e.open),true);
 await page.locator('#close-lesson').click();
 await page.goto(reading,{waitUntil:'load'});
 await page.locator('main img').evaluateAll(xs=>xs.forEach(x=>x.loading='eager'));
 await page.waitForFunction(()=>[...document.querySelectorAll('main img')].every(x=>x.complete&&x.naturalWidth>0));
 await page.emulateMedia({media:'print'});
 assert.equal(await page.locator('.figure-summary').first().isVisible(),true);
 assert.equal(await page.locator('.figure-guide').first().isVisible(),true);
 assert.equal(await page.locator('.quiz details[open]').count(),16);
 // A temporary print proof for pagination inspection, not a third user-facing entrance.
 result.printProof='/tmp/rnaseq-v3-print-proof.pdf'; // Produced and checked by glossary_browser.cjs / print_validate.py.
 assert.deepEqual(result.errors,[]);
 assert.deepEqual(result.externalRequests,[]);
 assert.ok(result.illustrations.every(x=>x.outOfBounds.length===0),'SVG text extends beyond canvas');
 result.pass=true;
 fs.writeFileSync(path.join(__dirname,'figures_review.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify({pass:true,guides:result.guides.length,illustrations:result.illustrations.length,responsive:result.responsive,printProof:result.printProof}));
 await browser.close();
})().catch(async e=>{
 result.pass=false;result.failure=e.stack;
 fs.writeFileSync(path.join(__dirname,'figures_review.json'),JSON.stringify(result,null,2));
 console.error(e);
 if(browser)await browser.close();
 process.exit(1);
});
