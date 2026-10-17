import {chromium} from 'playwright';
import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {extname,resolve} from 'node:path';
import assert from 'node:assert/strict';
const root=resolve('dist');
const mime={'.html':'text/html','.mjs':'text/javascript','.css':'text/css','.json':'application/json'};
const server=createServer(async(req,res)=>{try{const pathname=new URL(req.url,'http://localhost').pathname;const path=resolve(root,'.'+(pathname==='/'?'/index.html':pathname));if(!path.startsWith(root+'/')){res.writeHead(403).end();return;}const data=await readFile(path);res.writeHead(200,{'Content-Type':mime[extname(path)]||'application/octet-stream'});res.end(data);}catch{res.writeHead(404).end();}});
await new Promise((ok,no)=>{server.on('error',no);server.listen(8765,'127.0.0.1',ok);});
let browser;const failures=[];
try{
 const ctx=await chromium.launchPersistentContext('/tmp/stories-drink-lens-test-profile',{channel:'chromium',headless:true,args:['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream'],viewport:{width:1440,height:1100},permissions:['camera']});browser=ctx;const page=await ctx.newPage();page.on('pageerror',e=>failures.push(e.message));
 page.on('console',msg=>{if(msg.type()==='error')console.log('BROWSER:',msg.text().slice(0,400));});
 const referenceRequests=[];page.on('request',r=>{if(r.url().includes('/assets/references/'))referenceRequests.push(r.url());});
 await page.goto('http://127.0.0.1:8765/');await page.waitForFunction(()=>!document.getElementById('manual-open').disabled);
 assert.equal(referenceRequests.length,0);assert(await page.locator('input[value=descriptions]').isChecked());console.log('PASS default mode makes no reference-collection requests');
 await page.locator('#manual-open').click();await page.locator('#drink-select').selectOption('Iced Matcha');await page.locator('#branch').selectOption('Garden');await page.locator('#confirm').click();assert.equal(await page.locator('.pairing-card').count(),3);await page.locator('.pairing-card button').first().click();assert.match(await page.locator('#basket-preview').innerText(),/no order has been placed/);console.log('PASS manual menu, branch change, data-backed pairings, preview');
 await page.locator('#about-open').click();assert(await page.locator('#about').isVisible());await page.keyboard.press('Escape');assert(!(await page.locator('#about').isVisible()));
 await page.locator('#upload').setInputFiles({name:'bad.txt',mimeType:'text/plain',buffer:Buffer.from('bad')});assert.match(await page.locator('#error').innerText(),/JPG/);console.log('PASS accessible dialog and invalid upload feedback');
 await page.locator('#camera-open').click();await page.waitForFunction(()=>document.getElementById('camera').videoWidth>0);await page.evaluate(()=>window.testTrack=document.getElementById('camera').srcObject.getVideoTracks()[0]);await page.locator('#capture').click();assert(await page.locator('#photo').isVisible());assert.equal(await page.evaluate(()=>window.testTrack.readyState),'ended');console.log('PASS camera capture, photo preview, camera track released');
 await page.setViewportSize({width:390,height:844});await page.evaluate(()=>window.scrollTo(0,0));assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));await page.screenshot({path:'/tmp/stories-drink-lens-mobile.png',fullPage:true});console.log('PASS mobile layout without horizontal overflow');
 await page.setViewportSize({width:1440,height:1100});await page.screenshot({path:'/tmp/stories-drink-lens-desktop.png',fullPage:true});
 if(process.env.RUN_VISION==='1'){
  await page.locator('#upload').setInputFiles('/tmp/stories-vision-coffee.jpg');await page.locator('#scan').click();console.log('LIVE VISION: waiting for model download and inference…');
  await page.waitForFunction(()=>!document.getElementById('vision-result').hidden||!document.getElementById('error').hidden,{},{timeout:300_000});
  const err=await page.locator('#error').isVisible()?await page.locator('#error').innerText():'';assert.equal(err,'');console.log('PASS real CLIP inference:',await page.locator('#match-title').innerText());
  await page.locator('.visual-option').first().click();await page.locator('#confirm').click();assert.equal(await page.locator('.pairing-card').count(),3);await page.screenshot({path:'/tmp/stories-drink-lens-live-result.png',fullPage:true});
 }

 assert.equal(referenceRequests.length,0);
 await page.locator('input[value=references]').check();await page.locator('#reference-gallery').evaluate(e=>e.open=true);await page.waitForFunction(()=>document.querySelectorAll('.reference-tile').length>=3);assert(referenceRequests.length>0);assert(await page.locator('#reference-gallery').isVisible());
 await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));await page.screenshot({path:'/tmp/stories-drink-lens-reference-mobile.png',fullPage:true});
 console.log('PASS optional gallery loads only when selected, with credits and mobile layout');
 if(process.env.RUN_VISION==='1'){
  await page.locator('#scan').click();await page.waitForFunction(()=>!document.getElementById('vision-result').hidden||!document.getElementById('error').hidden,{},{timeout:300_000});
  assert.equal(await page.locator('#error').isVisible(),false);assert.match(await page.locator('#match-label').innerText(),/REFERENCE/);assert.equal(await page.locator('.reference-thumb').count(),3);console.log('PASS real image-to-image inference:',await page.locator('#match-title').innerText());await page.locator('.visual-option').first().click();await page.locator('#confirm').click();assert.equal(await page.locator('.pairing-card').count(),3);
  await page.setViewportSize({width:1440,height:1100});await page.screenshot({path:'/tmp/stories-drink-lens-reference-result.png',fullPage:true});
  await page.locator('input[value=descriptions]').check();await page.locator('#scan').click();await page.waitForFunction(()=>!document.getElementById('vision-result').hidden||!document.getElementById('error').hidden,{},{timeout:300_000});assert.equal(await page.locator('#error').isVisible(),false);console.log('PASS switching back to description inference');
 }
 const isolated=await ctx.newPage();const isolatedRequests=[];isolated.on('request',r=>{if(r.url().includes('/assets/references/'))isolatedRequests.push(r.url());});await isolated.goto('http://127.0.0.1:8765/?references=off');assert(!(await isolated.locator('#reference-mode-choice').isVisible()));await isolated.locator('#manual-open').click();assert.equal(isolatedRequests.length,0);await isolated.close();console.log('PASS references=off disables optional gallery without breaking default menu');
 assert.deepEqual(failures,[]);console.log('PASS no uncaught browser errors');
}finally{await browser?.close();await new Promise(ok=>server.close(ok));}
