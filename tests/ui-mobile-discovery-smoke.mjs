import {chromium,devices} from 'playwright';
import {createServer} from 'node:http';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=path.resolve(process.argv[2]??'site'),output=process.env.UI_AUDIT_DIR;
if(output)await mkdir(output,{recursive:true});
const server=process.env.UI_BASE_URL?null:createServer(async(req,res)=>{
 try{const u=new URL(req.url,'http://localhost'),p=path.resolve(root,u.pathname==='/'?'index.html':decodeURIComponent(u.pathname).slice(1));if(!p.startsWith(root+path.sep))throw Error('path');res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.mjs':'text/javascript','.css':'text/css','.json':'application/json'})[path.extname(p)]??'application/octet-stream');res.end(await readFile(p));}catch{res.writeHead(404);res.end();}
});
if(server)await new Promise(r=>server.listen(0,'127.0.0.1',r));
const base=process.env.UI_BASE_URL??'http://127.0.0.1:'+server.address().port+'/';
const browser=await chromium.launch({headless:true,executablePath:process.env.UI_BROWSER_PATH});
const results=[];
try{
 for(const profile of ['iPhone 13','Pixel 7']){
  const context=await browser.newContext({...devices[profile]}),page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base,{waitUntil:'networkidle'});assert.equal(await page.evaluate(()=>window.UI_VERSION),process.env.UI_EXPECTED_VERSION??'ui-v26');
  for(const id of ['people-filter','series-shortcuts','skill-filters'])assert.equal(await page.locator('#'+id).evaluate(e=>!!e.closest('dialog')),false);
  await page.locator('[data-browse-shortcut=twilights]').tap();assert.ok(new URL(page.url()).searchParams.getAll('browse').includes('twilights'));assert.equal(await page.locator('#filter-dialog').isVisible(),false);
  await page.locator('#reset').tap();await page.locator('#people-filter>summary').tap();await page.locator('[data-person-unit=unit_1]').check();assert.ok(new URL(page.url()).searchParams.getAll('person').includes('unit:unit_1'));await page.locator('#reset').tap();
  await page.locator('#skill-filters>summary').tap();await page.locator('#skill-kind').selectOption('panel_passive');await page.locator('#effect-type').selectOption('passive_up');await page.locator('#effect-target').selectOption('Vocal');assert.equal(await page.locator('#count').textContent(),'626 / 1466 件');
  await page.locator('#open-filters').tap();await page.locator('#filter-dialog').waitFor({state:'visible'});assert.equal(await page.locator('#filter-dialog-heading').textContent(),'詳しい検索条件');
  await page.locator('#advanced-filters>summary').tap();await page.locator('#from-year').selectOption('2025');assert.equal(await page.locator('#count').textContent(),'626 / 1466 件');
  await page.locator('#cancel-filters').tap();await page.locator('#filter-dialog').waitFor({state:'hidden'});assert.equal(new URL(page.url()).searchParams.has('from'),false);
  if(output)await page.screenshot({path:path.join(output,profile+'-inline.png')});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);assert.deepEqual(errors,[]);
  results.push({profile,engine:'Chromium emulation, not physical device/Safari',width:await page.evaluate(()=>innerWidth),status:'pass'});console.log(profile+' touch common filters and advanced cancel PASS');await context.close();
 }
}finally{await browser.close();if(server)await new Promise(r=>server.close(r));if(output)await writeFile(path.join(output,'mobile-discovery.json'),JSON.stringify(results,null,2)+'\n');}
