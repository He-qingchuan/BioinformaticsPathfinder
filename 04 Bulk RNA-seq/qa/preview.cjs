const { chromium } = require('playwright');
const path = require('node:path');
const fs = require('node:fs');
const { pathToFileURL } = require('node:url');
(async()=>{
 const root=path.resolve(__dirname,'..');
 const browser=await chromium.launch({headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(pathToFileURL(path.join(root,'01_海岛探险教案.html')).href,{waitUntil:'load'});
 await page.screenshot({path:path.join(__dirname,'home.png')});
 await page.locator('.atlas-section').screenshot({path:path.join(__dirname,'map.png')});
 await page.locator('.station-node[data-station="de"]').click();
 await page.screenshot({path:path.join(__dirname,'lesson.png')});
 console.log(JSON.stringify({title:await page.title(),errors,headings:await page.locator('#lesson-content h2').count(),figures:await page.locator('#lesson-content .real-figure').count(),up:await page.locator('#up-count').textContent(),dialog:await page.locator('#lesson-dialog').evaluate(el=>({width:el.clientWidth,height:el.clientHeight}))}));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
