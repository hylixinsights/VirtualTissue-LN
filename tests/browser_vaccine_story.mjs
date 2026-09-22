import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=process.env.STORY_URL||'http://127.0.0.1:8014/web/vaccine-demo.html';
const browser=await chromium.launch({channel:process.env.CI?undefined:'chrome',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1080}});
const errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(r.url()));
await mkdir('docs/vaccine-review',{recursive:true});
async function seek(value){await page.locator('#storySeek').fill(String(value));}
try{
 await page.goto(base);await page.waitForFunction(()=>document.querySelector('#sceneLoading').hidden);
 assert.equal(await page.locator('html').getAttribute('lang'),'en');
 await page.waitForFunction(()=>+document.querySelector('#storySeek').value>0.8);
 await page.locator('#playStory').click();const paused=await page.locator('#storySeek').inputValue();
 await page.waitForTimeout(250);assert.equal(await page.locator('#storySeek').inputValue(),paused);
 assert.equal(await page.locator('#chapters button').count(),8);
 for(const stage of ['arrival','capture','process','prime','helper','help','commit','secrete']){
  await page.locator(`#chapters [data-stage="${stage}"]`).click();
  assert.equal(await page.locator('#vaccineScene').getAttribute('data-stage'),stage);
  assert.equal(await page.locator('#playStory').getAttribute('aria-pressed'),'false');
 }
 await seek(27);assert.equal(await page.locator('#decisionAction').textContent(),'PRIME');
 await page.screenshot({path:'docs/vaccine-review/dc-primes-cd4.png',fullPage:true});
 await seek(45);assert.equal(await page.locator('#decisionAction').textContent(),'HELP');
 await page.screenshot({path:'docs/vaccine-review/helper-b-contact.png',fullPage:true});
 await seek(76);assert.equal(await page.locator('#antibodyCount').textContent(),'3');
 assert((await page.locator('[data-actor="b"]').innerText()).includes('Plasmablast'));
 assert((await page.locator('[data-actor="helper"]').innerText()).includes('T follicular helper'));
 assert.equal(await page.locator('#playState').textContent(),'Response complete');
 await page.screenshot({path:'docs/vaccine-review/antibody-output.png',fullPage:true});
 await page.locator('[data-actor="dc"]').click();assert.equal(await page.locator('[data-actor="dc"]').getAttribute('aria-pressed'),'true');
 await page.locator('#overview').click();assert.equal(await page.locator('#overview').getAttribute('aria-pressed'),'true');
 await page.screenshot({path:'docs/vaccine-review/whole-tissue.png',fullPage:true});
 await page.locator('#focus').click();
 await page.setViewportSize({width:882,height:700});await seek(27);
 await page.screenshot({path:'docs/vaccine-review/compact-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.screenshot({path:'docs/vaccine-review/mobile.png',fullPage:true});
 await page.emulateMedia({reducedMotion:'reduce'});await page.reload();await page.waitForFunction(()=>document.querySelector('#sceneLoading').hidden);
 assert.equal(await page.locator('#playStory').getAttribute('aria-pressed'),'false');
 await page.locator('#speed').selectOption('4');await page.locator('#restart').click();
 await page.waitForFunction(()=>document.querySelector('#playState').textContent==='Response complete',{timeout:25000});
 assert.equal(await page.locator('#antibodyCount').textContent(),'3');
 assert.equal(await page.locator('#playStory').getAttribute('aria-pressed'),'false');
 assert(requests.every(url=>url.startsWith(new URL(base).origin)));
 assert(!requests.some(url=>url.includes('/api/')));
 assert.deepEqual(errors,[]);
 const text=await page.locator('body').innerText();assert(!/prévia|célula|decisões|após|linfonodo|nenhuma/i.test(text));
 console.log({scripted:true,apiCalls:0,autoplay:true,pause:true,restartToCompletion:true,seekableStages:8,antibodyUnits:3,english:true,mobileOverflow:false,errors});
}finally{await browser.close();}
