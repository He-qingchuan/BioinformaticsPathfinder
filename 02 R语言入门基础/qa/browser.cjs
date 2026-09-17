'use strict';
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict');
const {pathToFileURL}=require('url');
process.env.TMPDIR=process.env.RUNNER_TEMP||'/tmp/r-town-browser';fs.mkdirSync(process.env.TMPDIR,{recursive:true});
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),out=path.join(__dirname,'artifacts');fs.mkdirSync(out,{recursive:true});
const course=JSON.parse(fs.readFileSync(path.join(root,'content/course.json'),'utf8'));
const file=rel=>pathToFileURL(path.join(root,rel)).href;
const checks=[],errors=[],requests=[];
const mime={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'application/javascript','.svg':'image/svg+xml','.png':'image/png','.json':'application/json','.md':'text/plain; charset=utf-8','.R':'text/plain; charset=utf-8','.txt':'text/plain; charset=utf-8','.zip':'application/zip'};
const server=http.createServer((req,res)=>{let rel;try{rel=decodeURIComponent(new URL(req.url,'http://local').pathname).replace(/^\/r\//,'');}catch{res.writeHead(400).end();return;}
 const f=path.resolve(root,rel||'index.html');if(!f.startsWith(root+path.sep)&&f!==root){res.writeHead(403).end();return;}
 fs.readFile(f,(e,b)=>{if(e){res.writeHead(404).end();return;}res.writeHead(200,{'Content-Type':mime[path.extname(f)]||'application/octet-stream'}).end(b);});});
let browser;
async function frames(p){await p.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));}
async function noOverflow(p){const d=await p.evaluate(()=>({actual:document.documentElement.scrollWidth,viewport:innerWidth}));assert(d.actual<=d.viewport+1,JSON.stringify(d));}
(async()=>{
 browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const ctx=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'no-preference'});
 await ctx.route('https://**/*',r=>{requests.push(r.request().url());r.abort();});
 const p=await ctx.newPage();p.on('pageerror',e=>errors.push(e.message));
 await p.goto(file('index.html'));await p.locator('#atlas-map.enhanced').waitFor();
 assert.equal(await p.locator('.district-panel:visible').count(),1);
 for(const zone of course.zones){await p.locator(`[data-select-zone="${zone.id}"]`).click();const panel=p.locator(`[data-panel-zone="${zone.id}"]`);assert(await panel.isVisible());assert.equal(await panel.locator('a[data-course-lesson]').count(),course.lessons.filter(l=>l.zone===zone.id).length);}
 checks.push('all eight districts expose the correct lesson links');
 await p.locator('[data-select-zone="welcome"]').click();await p.screenshot({path:path.join(out,'town-desktop.png'),fullPage:true});
 for(const width of [320,390,768,820,1024,1440,1920]){
  await p.setViewportSize({width,height:900});await frames(p);await noOverflow(p);
  const expected=width<820?8:1;assert.equal(await p.locator('.district-panel:visible').count(),expected);
  for(const link of await p.locator('.district-panel:visible .map-lesson').all())assert((await link.boundingBox()).height>=44);
  if(width>=820){const rects=await p.locator('.town-stop').evaluateAll(xs=>xs.map(x=>{const b=x.getBoundingClientRect();return {x:b.x,y:b.y,r:b.right,b:b.bottom,w:b.width,h:b.height};}));for(let i=0;i<rects.length;i++){assert(rects[i].h>=44);for(let j=i+1;j<rects.length;j++)assert(!(rects[i].x<rects[j].r&&rects[i].r>rects[j].x&&rects[i].y<rects[j].b&&rects[i].b>rects[j].y),'district targets overlap');}}
  if(width===390)await p.screenshot({path:path.join(out,'town-mobile.png'),fullPage:true});
 }
 checks.push('seven widths, no page overflow, readable targets, desktop district and mobile street layouts');
 await p.setViewportSize({width:1440,height:900});
 await p.locator('[data-atlas-view="directory"]').click();assert(await p.locator('#map-directory').isVisible());assert.equal(await p.locator('#map-directory a[data-course-lesson]').count(),36);
 await p.locator('[data-atlas-view="map"]').click();assert(!(await p.locator('#map-directory').isVisible()));
 await p.locator('#atlas-map').scrollIntoViewIfNeeded();await p.waitForFunction(()=>document.querySelector('#atlas-map').dataset.motion==='playing');
 const moving=()=>p.locator('.town-scene .cloud-drift').first().evaluate(el=>getComputedStyle(el).transform);
 const before=await moving();await p.waitForTimeout(350);assert.notEqual(await moving(),before);
 await p.locator('#atlas-motion').click();await p.waitForFunction(()=>getComputedStyle(document.querySelector('.cloud-drift')).animationPlayState==='paused');await frames(p);
 const paused=await moving();await p.waitForTimeout(250);assert.equal(await moving(),paused);
 await p.reload();await p.locator('#atlas-map.enhanced').waitFor();assert.equal(await p.locator('#atlas-map').getAttribute('data-motion'),'paused');
 await p.locator('#atlas-motion').click();await p.emulateMedia({reducedMotion:'reduce'});await p.waitForFunction(()=>document.querySelector('#atlas-map').dataset.motion==='paused');assert.equal(await p.locator('#atlas-map').getAttribute('data-motion'),'paused');assert(await p.locator('#atlas-motion').isDisabled());await p.emulateMedia({reducedMotion:'no-preference'});
 await p.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));});assert.equal(await p.locator('#atlas-map').getAttribute('data-motion'),'paused');
 await p.evaluate(()=>{delete document.hidden;document.dispatchEvent(new Event('visibilitychange'));});
 await p.setViewportSize({width:1440,height:220});await p.evaluate(()=>scrollTo(0,document.body.scrollHeight));await p.waitForFunction(()=>document.querySelector('#atlas-map').dataset.motion==='paused');
 checks.push('actual motion, pause persistence, reduced motion, offscreen pause; hidden-page event simulation');
 await p.setViewportSize({width:1200,height:900});
 for(const l of course.lessons){await p.goto(file(`lessons/${l.id}.html`));assert((await p.locator('h1').textContent()).includes(l.title));assert.equal(await p.locator('.exercise').count(),1);assert.equal(await p.locator('.quiz').count(),1);assert.equal(await p.locator('.quiz input').count(),3);await noOverflow(p);}
 checks.push('36 chapters, exercises and quizzes open with no JavaScript errors');
 await p.goto(file('lessons/27.html'));await p.locator('[data-term="ci"]').first().click();assert(await p.locator('#glossary-dialog').isVisible());
 const backlink=p.locator('#glossary-dialog .term-backlinks a').first();assert((await backlink.getAttribute('href')).startsWith('../lessons/'));
 await p.locator('#all-terms').click();await p.locator('#term-query').fill('NA');assert((await p.locator('#term-results').innerText()).includes('缺失值'));
 await p.locator('#term-query').fill('not-a-term');assert((await p.locator('#term-status').innerText()).includes('0'));
 await p.keyboard.press('Escape');assert(!(await p.locator('#glossary-dialog').isVisible()));
 await p.locator('.zoom-image').first().click();assert(await p.locator('#image-dialog').isVisible());await p.keyboard.press('Escape');
 await p.locator('.copy-code').first().click();assert((await p.locator('#toast').innerText()).match(/复制/));
 await p.locator('.quiz input').nth(course.lessons[26].quiz.answer).check();await p.locator('.check-quiz').click();assert((await p.locator('.quiz-status').innerText()).includes('理解正确'));
 await p.setViewportSize({width:390,height:844});await noOverflow(p);await p.screenshot({path:path.join(out,'confidence-interval-mobile.png'),fullPage:true});
 checks.push('glossary search, empty result, contextual backlink, Escape, figure zoom, copy and quiz feedback');
 await p.goto(file('reading.html'));await p.emulateMedia({media:'print'});await p.evaluate(()=>window.dispatchEvent(new Event('beforeprint')));assert.equal(await p.locator('main details:not([open])').count(),0);await p.emulateMedia({media:'screen'});
 await p.goto(file('index.html'));await p.keyboard.press('Tab');assert(await p.locator('.skip-link').evaluate(x=>x===document.activeElement));
 checks.push('full reading print expands answers; keyboard skip link');
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const base=`http://127.0.0.1:${server.address().port}/r/`;
 await p.setViewportSize({width:1440,height:900});await p.goto(base+'index.html');await p.evaluate(()=>localStorage.setItem('pathfinder-linux-read-v1','["01","02","03"]'));await p.reload();assert((await p.locator('#progress-summary').innerText()).includes('0 / 36'));
 await p.locator('#continue-link').click();await p.locator('#mark-read').click();await p.goBack();await p.waitForFunction(()=>document.querySelector('#progress-summary').textContent.includes('1 / 36'));assert.equal(await p.locator('#continue-link').getAttribute('href'),'lessons/02.html');
 await p.evaluate(()=>localStorage.setItem('pathfinder-r-read-v1',JSON.stringify(['01','01','99',null,7])));await p.reload();assert((await p.locator('#progress-summary').innerText()).includes('1 / 36'));
 await p.evaluate(ids=>localStorage.setItem('pathfinder-r-read-v1',JSON.stringify(ids)),course.lessons.map(l=>l.id));await p.reload();assert((await p.locator('#progress-summary').innerText()).includes('36 / 36'));assert.equal(await p.locator('#continue-link').getAttribute('href'),'lessons/36.html');
 const download=await ctx.request.get(base+'practice/r-lab.zip');assert(download.ok());assert.equal((await download.body()).readUInt32LE(0),0x04034b50);
 checks.push('HTTP subpath, R/Linux progress isolation, back navigation, invalid storage values, completed course and practice download');
 const plain=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});const np=await plain.newPage();await np.goto(file('index.html'));assert.equal(await np.locator('.district-panel:visible').count(),8);await np.goto(file('lessons/27.html'));await np.locator('[data-term="ci"]').first().click();assert(np.url().endsWith('reading.html#term-ci'));await noOverflow(np);await plain.close();
 const blocked=await browser.newContext();await blocked.addInitScript(()=>{Object.defineProperty(window,'localStorage',{get(){throw Error('storage blocked')}});});const bp=await blocked.newPage();bp.on('pageerror',e=>errors.push(e.message));await bp.goto(file('lessons/01.html'));await bp.locator('#mark-read').click();assert((await bp.locator('#toast').innerText()).includes('限制'));await bp.goto(file('index.html'));assert(await bp.locator('#continue-link').isVisible());await blocked.close();
 checks.push('no-JavaScript reading/glossary and blocked-storage fallback');
 assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
 const report={status:'passed',checks,errors,externalRequests:requests};fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
 await ctx.close();await browser.close();await new Promise(resolve=>server.close(resolve));
})().catch(async e=>{console.error(e);fs.writeFileSync(path.join(out,'browser-failure.json'),JSON.stringify({error:String(e),checks,errors},null,2));if(browser)await browser.close();server.close();process.exitCode=1;});
