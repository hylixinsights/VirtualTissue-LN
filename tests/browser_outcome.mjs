// Read-only inspection of an already running/finished managed local run.
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=process.env.OUTCOME_URL||'http://127.0.0.1:8018';
const browser=await chromium.launch({channel:'chrome',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1080}}),errors=[],writes=[];
page.on('pageerror',e=>errors.push(String(e)));page.on('request',r=>{if(r.method()!=='GET')writes.push(r.url());});
await page.goto(base);await page.locator('#loading').waitFor({state:'hidden'});
assert.match(await page.locator('#provider').textContent(),/Jev.*50,000 API calls/);
for(const id of ['play','step','reset','introduce','applyPrompt'])assert.equal(await page.locator('#'+id).isEnabled(),false);
const state=await (await page.request.get(base+'/api/state')).json();
assert(state.run_control.managed);assert.equal(state.provider.provider,'jev');
const chosen=state.run_control.outcome?.cell||state.tissue.cells.find(c=>c.last_decision)?.id;
if(chosen){await page.locator('#cellSelect').selectOption(chosen);assert.match(await page.locator('#choice').textContent(),/Jev/);}
await page.screenshot({path:process.env.OUTCOME_SCREENSHOT||fileURLToPath(new URL('../recordings/private/reactive-jev-igm-guided/browser-proof.png',import.meta.url)),fullPage:true});
await page.setViewportSize({width:390,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
assert.deepEqual(errors,[]);assert.deepEqual(writes,[]);
console.log({status:state.run_control.status,requests:state.provider.requests,mutations:writes,errors});
await browser.close();
