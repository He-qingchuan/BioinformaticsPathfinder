const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const http=require('node:http');
const {pathToFileURL}=require('node:url');
const root=path.resolve(__dirname,'..');
const out=path.join(__dirname,'artifacts');
fs.mkdirSync(path.join(out,'browser-tmp'),{recursive:true});
// Respect the course's writable artifact directory even under a wrapped Node executable.
process.env.TMPDIR=path.join(out,'browser-tmp');
process.env.TMP=process.env.TMPDIR;process.env.TEMP=process.env.TMPDIR;
const {chromium}=require('playwright');
const report={lessons:[],widths:[],checks:[],externalRequests:[],errors:[]};
let browser,server;
const url=p=>pathToFileURL(path.join(root,p)).href;
async function images(page){await page.locator('img[src]').evaluateAll(xs=>xs.forEach(x=>x.loading='eager'));await page.waitForFunction(()=>[...document.querySelectorAll('img[src]')].every(x=>x.complete&&x.naturalWidth>0));}
(async()=>{
 browser=await chromium.launch({headless:true});
 const context=await browser.newContext({offline:true,viewport:{width:1440,height:1000}});
 const page=await context.newPage();
 page.on('pageerror',e=>report.errors.push(e.message));
 page.on('request',r=>{if(/^https?:/.test(r.url()))report.externalRequests.push(r.url());});
 await page.goto(url('index.html'));await images(page);assert.equal(await page.locator('#atlas-map [data-course-lesson]').count(),18);assert.equal(await page.locator('#map-directory [data-course-lesson]').count(),18);
 await page.screenshot({path:path.join(out,'home-1440.png'),fullPage:true});
 for(let i=1;i<=18;i++){
  const id=String(i).padStart(2,'0');await page.goto(url(`lessons/${id}.html`));await images(page);
  assert.equal(await page.locator('article>h1').count(),1);assert.equal(await page.locator('.exercise').count(),1);
  await page.locator('.quiz input').first().check();await page.locator('.check-quiz').click();assert.ok((await page.locator('.quiz-status').textContent()).length>0);
  report.lessons.push(id);
 }
 await page.goto(url('lessons/04.html'));await page.selectOption('#path-start','notes');assert.match(await page.locator('#path-result').textContent(),/linux-lab\/tables/);
 await page.selectOption('#path-start','.');assert.match(await page.locator('#path-result').textContent(),/走出了/);
 await page.fill('#path-input','notes');assert.match(await page.locator('#path-result').textContent(),/linux-lab\/notes/);
 const term=page.locator('[data-term="cwd"]').first();await term.click();await page.waitForSelector('#glossary-dialog[open]');assert.equal(await page.locator('#term-results .term-entry').count(),1);
 await page.fill('#term-query','PATH');assert.ok(await page.locator('#term-results .term-entry').count()>=1);
 await page.fill('#term-query','abcdef不存在');assert.match(await page.locator('#term-results').textContent(),/还没找到/);
 await page.click('#all-terms');assert.equal(await page.locator('#term-results .term-entry').count(),60);
 await page.keyboard.press('Escape');assert.equal(await page.locator('#glossary-dialog').evaluate(x=>x.open),false);
 assert.equal(await term.evaluate(x=>x===document.activeElement),true);
 await page.locator('.concept .zoom-image').first().click();assert.equal(await page.locator('#image-dialog').evaluate(x=>x.open),true);await page.keyboard.press('Escape');
 await page.click('#mark-read');await page.reload();assert.match(await page.locator('#mark-read').textContent(),/已读/);
 await page.goto(url('index.html'));assert.match(await page.locator('#progress-summary').textContent(),/已读 1 \/ 18/);
 await page.goto(url('lessons/08.html'));await page.selectOption('#glob-pattern','*.txt');assert.equal(await page.locator('#glob-files .matched').count(),2);await page.selectOption('#glob-pattern','.*');assert.equal(await page.locator('#glob-files .matched').count(),1);
 await page.goto(url('lessons/10.html'));assert.equal((await page.locator('#pipe-output').textContent()).trim(),'2 magpie\n4 sparrow');await page.uncheck('#pipe-sort');assert.equal((await page.locator('#pipe-output').textContent()).split('\n').length,5);
 await page.goto(url('lessons/13.html'));assert.match(await page.locator('#permission-result').textContent(),/640/);await page.locator('[data-perm="2"][value="4"]').check();assert.match(await page.locator('#permission-result').textContent(),/644/);
 report.checks.push('4 demonstrations','glossary search and zero results','Escape and focus restoration','zoom','persisted progress','18 quizzes');
 for(const width of [320,390,768,1440,1920]){
  await page.setViewportSize({width,height:950});
  for(const file of ['index.html','lessons/04.html','lessons/10.html','lessons/13.html','library.html']){
   await page.goto(url(file));await images(page);
   const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);assert.equal(overflow,false,`${file} at ${width}`);
  }
  report.widths.push(width);
 }
 await page.setViewportSize({width:390,height:900});await page.goto(url('lessons/04.html'));await page.screenshot({path:path.join(out,'lesson-390.png'),fullPage:true});
 await page.locator('[data-term]').first().click();await page.screenshot({path:path.join(out,'terms-390.png')});await page.keyboard.press('Escape');
 await page.setViewportSize({width:1440,height:1000});await page.goto(url('lessons/10.html'));await page.screenshot({path:path.join(out,'pipeline-1440.png'),fullPage:true});
 await page.goto(url('reading.html'));await images(page);await page.emulateMedia({media:'print'});await page.evaluate(()=>window.dispatchEvent(new Event('beforeprint')));
 assert.equal(await page.locator('main details:not([open])').count(),0);assert.equal(await page.locator('#glossary .term-entry').count(),60);
 await page.screenshot({path:path.join(out,'print-proof.png'),fullPage:false});
 const plain=await browser.newContext({javaScriptEnabled:false,offline:true});const staticPage=await plain.newPage();await staticPage.goto(url('lessons/04.html'));await staticPage.locator('[data-term="cwd"]').first().click();assert.match(staticPage.url(),/reading.html#term-cwd$/);assert.equal(await staticPage.locator('#term-cwd').count(),1);await plain.close();
 const blocked=await browser.newContext({offline:true});await blocked.addInitScript(()=>{Object.defineProperty(window,'localStorage',{get(){throw new Error('blocked for test')}});});const bp=await blocked.newPage();await bp.goto(url('lessons/03.html'));await bp.click('#mark-read');assert.match(await bp.locator('#toast').textContent(),/浏览器限制/);await blocked.close();
 server=http.createServer((req,res)=>{let name=decodeURIComponent(req.url.split('?')[0]);if(name.endsWith('/'))name+='index.html';const file=path.resolve(root,'.'+name);if(!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}fs.readFile(file,(err,data)=>{if(err){res.writeHead(404).end();return;}const type={'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.svg':'image/svg+xml'}[path.extname(file)]||'application/octet-stream';res.setHeader('Content-Type',type);res.end(data);});});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const online=await browser.newContext();const op=await online.newPage();await op.goto(`http://127.0.0.1:${server.address().port}/`);await op.locator('#atlas-map [data-course-lesson="03"]').click();assert.match(op.url(),/lessons\/03.html$/);await online.close();
 report.checks.push('offline file protocol','HTTP navigation','no-JavaScript glossary fallback','blocked localStorage','print answers and glossary');
 assert.deepEqual(report.errors,[]);assert.deepEqual(report.externalRequests,[]);
 fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(server)await new Promise(r=>server.close(r));if(browser)await browser.close();});
