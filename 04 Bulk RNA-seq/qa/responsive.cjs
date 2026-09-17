const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const path=require('node:path');
const fs=require('node:fs');
const {pathToFileURL}=require('node:url');
(async()=>{
 const browser=await chromium.launch({headless:true});
 const root=path.resolve(__dirname,'..');
 const context=await browser.newContext({offline:true});
 const page=await context.newPage();
 const result=[];
 for(const [width,height] of [[320,800],[390,844],[768,1024],[1440,1000]]){
  await page.setViewportSize({width,height});
  await page.goto(pathToFileURL(path.join(root,'01_海岛探险教案.html')).href,{waitUntil:'load'});
  const bounds=await page.evaluate(()=>({viewport:innerWidth,page:document.documentElement.scrollWidth,heroHeight:document.querySelector('.hero h1').getBoundingClientRect().height,headlineLineHeight:parseFloat(getComputedStyle(document.querySelector('.hero h1')).lineHeight)}));
  assert.ok(bounds.page<=bounds.viewport);
  if(width<760)assert.ok(bounds.heroHeight<=bounds.headlineLineHeight*2+2);
  if(width===768)assert.ok(bounds.heroHeight<=bounds.headlineLineHeight*2+2);
  await page.screenshot({path:path.join(__dirname,`home_${width}.png`)});
  await page.evaluate(()=>document.querySelector('[data-station="start"]').click());
  await page.locator('.science-visual').first().scrollIntoViewIfNeeded();
  await page.screenshot({path:path.join(__dirname,`science_${width}.png`)});
  assert.equal(await page.locator('#lesson-content').evaluate(el=>el.scrollWidth<=el.clientWidth+1),true);
  await page.locator('#close-lesson').click();
  await page.locator('.station-node[data-station="plots"] .station-caption').click();
  assert.ok((await page.locator('#lesson-title').textContent()).includes('火山'));
  await page.locator('#close-lesson').click();
  await page.locator('.station-node[data-station="sets"] .station-caption').click();
  assert.ok((await page.locator('#lesson-title').textContent()).includes('交集'));
  await page.locator('#close-lesson').click();
  if(width===1440)await page.locator('.atlas-section').screenshot({path:path.join(__dirname,'map.png')});
  result.push({...bounds,height,pass:true});
 }
 fs.writeFileSync(path.join(__dirname,'responsive_review.json'),JSON.stringify({pass:true,screens:result},null,2));
 console.log(JSON.stringify({pass:true,screens:result}));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
