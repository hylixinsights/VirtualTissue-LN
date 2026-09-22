// Browser-only interception of synthetic Jev-wire test packets. No remote calls.
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const {chromium} = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = fileURLToPath(new URL('../',import.meta.url));
const python = process.env.PYTHON_EXECUTABLE || 'python3';
const generated = spawnSync(python, ['-c', "import sys,json;sys.path.insert(0,'tests');from test_jev_studio import ui_fixture;print(json.dumps(ui_fixture()))"], {cwd:root, encoding:'utf8'});
assert.equal(generated.status,0,generated.stderr);
const packets = JSON.parse(generated.stdout);
assert.equal(packets.test_fixture,true);
const browser = await chromium.launch({channel:process.env.CI?undefined:'chrome',headless:true});
const page = await browser.newPage({viewport:{width:1512,height:1100}});
const errors=[];let stepped=false, steps=0;
page.on('pageerror',error=>errors.push(error.message));
await page.route('**/api/**',async route=>{
  const url=new URL(route.request().url());
  let value;
  if(url.pathname==='/api/state')value=stepped?packets.after:packets.before;
  else if(url.pathname==='/api/recordings')value={recordings:[]};
  else if(url.pathname==='/api/step'){
    assert.equal(route.request().method(),'POST');
    assert.equal(route.request().headers()['x-ln-token'],'test-session-token');
    stepped=true;steps++;value=packets.after;
  }else throw Error('Unexpected simulation operation: '+url.pathname);
  await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(value)});
});
try{
  await page.goto(process.env.STUDIO_URL || 'http://127.0.0.1:8010/');
  await page.waitForFunction(()=>document.querySelector('#illustrated').getAttribute('aria-pressed')==='true');
  assert.equal(await page.locator('#provider').inputValue(),'jev');
  assert.equal(await page.locator('#budget').inputValue(),'5');
  assert.equal(await page.locator('#budgetWrap').isVisible(),true);
  assert((await page.locator('#play').textContent()).includes('Run with Jev'));
  assert.equal(steps,0,'Opening the LN must not start inference');
  await page.locator('#step').click();
  await page.waitForFunction(()=>document.querySelector('#time').textContent==='0.5 h');
  assert.equal(steps,1);
  assert.equal(await page.locator('#legend .atlas-thumb').count(),3);
  const bounds=await page.locator('#scene').boundingBox();
  const scale=bounds.height/(2*470*Math.tan(39*Math.PI/360))*150/packets.after.tissue.params.radius_um;
  for(const kind of ['B','CD4','DC']){
    const cell=packets.after.tissue.cells.find(c=>c.kind===kind);
    await page.mouse.click(bounds.x+bounds.width/2+cell.x*scale,bounds.y+bounds.height/2-cell.y*scale);
    const label=await page.locator('#cellAction').innerText();
    assert(label.includes(cell.id));assert(label.includes('Jev: MOVE'));assert(label.includes('applied'));
  }
  assert.deepEqual(errors,[]);
  console.log({test:'synthetic Jev wire + browser',directJevStart:true,requestsOnOpen:0,illustratedAgentKinds:['B','CD4','DC'],appliedDecisionsVisible:true,errors});
}finally{await browser.close();}
