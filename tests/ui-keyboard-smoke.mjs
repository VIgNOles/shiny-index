import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {chromium} from 'playwright';
const root=path.resolve(process.argv[2]??'site');
const pointer=JSON.parse(await readFile(path.join(root,'details/latest.json'),'utf8'));
const doc=JSON.parse(await readFile(path.join(root,'details',pointer.detail_version,'details.json'),'utf8'));
const total=doc.coverage.base_card_count;
const output=process.env.UI_SCREENSHOT_DIR;if(output)await mkdir(output,{recursive:true});
const server=process.env.UI_BASE_URL?null:createServer(async(req,res)=>{
 try{const u=new URL(req.url,'http://127.0.0.1'),p=path.resolve(root,u.pathname==='/'?'index.html':decodeURIComponent(u.pathname).slice(1));
 if(!p.startsWith(root+path.sep))throw Error('path');
 res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.mjs':'text/javascript','.css':'text/css','.json':'application/json'})[path.extname(p)]??'application/octet-stream');res.end(await readFile(p));
 }catch(e){res.writeHead(404);res.end(String(e));}
});
if(server)await new Promise(r=>server.listen(0,'127.0.0.1',r));
const base=process.env.UI_BASE_URL??'http://127.0.0.1:'+server.address().port+'/';
const browser=await chromium.launch({headless:true,executablePath:process.env.UI_BROWSER_PATH});
try{
 for(const width of [1280,390,320]){
  const page=await browser.newPage({viewport:{width,height:900},...(width<500?{isMobile:true,hasTouch:true}:{})}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base,{waitUntil:'networkidle'});
  assert.equal(await page.evaluate(()=>window.UI_VERSION),process.env.UI_EXPECTED_VERSION??'ui-v17');
  const summary=page.locator('#skill-filters > summary');
  await summary.focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('#skill-filters').getAttribute('open'),'');
  const type=page.locator('#effect-type');
  const options=await type.locator('option').evaluateAll(es=>es.map(e=>e.value));
  const index=options.indexOf('resurrection');assert.ok(index>0);
  await type.focus();await page.keyboard.press('Home');
  for(let i=0;i<index;i++)await page.keyboard.press('ArrowDown');
  assert.equal(await type.inputValue(),'resurrection');
  await page.waitForTimeout(150);
  const expected=doc.cards.filter(c=>c.items.some(i=>i.effect_details?.effects.some(e=>e.metric==='resurrection'))).length;
  assert.equal(await page.locator('#count').textContent(),expected+' / '+total+' 件');
  await page.keyboard.press('Tab');assert.equal(await page.evaluate(()=>document.activeElement.id),'effect-target');
  await page.keyboard.press('Tab');assert.equal(await page.evaluate(()=>document.activeElement.id),'effect-turns');
  await page.keyboard.press('Home');await page.keyboard.press('ArrowDown');
  assert.equal(await page.locator('#effect-turns').inputValue(),'1');
  await page.waitForTimeout(150);
  assert.equal(await page.locator('#count').textContent(),expected+' / '+total+' 件');
  const unnamed=await page.locator('input:not([type=hidden]),select,button').evaluateAll(es=>es.filter(e=>e.getClientRects().length&&!e.disabled).filter(e=>{
   const name=e.getAttribute('aria-label')||(e.getAttribute('aria-labelledby')||'').split(' ').map(id=>document.getElementById(id)?.textContent||'').join(' ')||[...(e.labels||[])].map(x=>x.textContent).join(' ')||(e.matches('button')?e.textContent:'');
   return !name.trim();
  }).map(e=>({tag:e.tagName,id:e.id})));
  assert.deepEqual(unnamed,[]);
  await page.locator('.detail-toggle').first().focus();await page.keyboard.press('Enter');
  assert.ok(await page.locator('.card-detail').first().isVisible());
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  if(output)await page.screenshot({path:path.join(output,width+'-keyboard-detail.png')});
  await page.locator('#reset').focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('#count').textContent(),total+' / '+total+' 件');
  assert.deepEqual(errors,[]);await page.close();console.log(width+' keyboard filters, focus order, visible control labels PASS');
 }
}finally{await browser.close();if(server)await new Promise(r=>server.close(r));}
