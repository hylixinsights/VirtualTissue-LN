import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const generated=spawnSync(process.env.PYTHON_EXECUTABLE||'python3',['-c',"import sys,json;sys.path.insert(0,'tests');from test_design_preview import ui_fixture;print(json.dumps(ui_fixture()))"],{cwd:fileURLToPath(new URL('../',import.meta.url)),encoding:'utf8'});
assert.equal(generated.status,0,generated.stderr);
const packet=JSON.parse(generated.stdout);assert.equal(packet.test_fixture,true);
const browser=await chromium.launch({channel:process.env.CI?undefined:'chrome',headless:true});
const page=await browser.newPage({viewport:{width:1512,height:1100}});const errors=[];
page.on('pageerror',e=>errors.push(e.message));
await page.route('**/api/**',async route=>{
 assert.equal(route.request().method(),'GET','A completed preview must make no mutation requests');
 const pathname=new URL(route.request().url()).pathname;
 assert(['/api/state','/api/recordings'].includes(pathname));
 await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(pathname==='/api/state'?packet.state:{recordings:[]})});
});
try{
 await page.goto(process.env.STUDIO_URL||'http://127.0.0.1:8010/');
 await page.waitForFunction(()=>document.querySelector('#illustrated').getAttribute('aria-pressed')==='true');
 assert.equal(await page.locator('[data-preview-cell]').count(),10);
 for(const id of ['play','step','reset','pulse','provider'])assert(await page.locator('#'+id).isDisabled());
 for(const id of packet.state.design_preview.selected_ids){
  await page.locator(`[data-preview-cell="${id}"]`).click();
  assert((await page.locator('#cellAction').innerText()).includes(id));
  assert((await page.locator('#cellAction').innerText()).includes('Jev: MOVE'));
 }
 await page.locator('#previewBefore').click();
 assert.equal(await page.locator('#time').textContent(),'0.0 h');
 assert((await page.locator('#cellAction').innerText()).includes('Awaiting'));
 await page.locator('#previewAfter').click();
 assert.equal(await page.locator('#time').textContent(),'0.5 h');
 assert((await page.locator('#cellAction').innerText()).includes('Jev: MOVE'));
 await page.setViewportSize({width:390,height:844});
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 assert.deepEqual(errors,[]);
 console.log({test:'ten-decision preview, synthetic transport',tenSelectableCells:true,noFurtherCalls:true,beforeAfter:true,mobileOverflow:false,errors});
}finally{await browser.close();}
