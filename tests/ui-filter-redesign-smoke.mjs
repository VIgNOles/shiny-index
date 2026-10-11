import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {chromium} from 'playwright';
const root=path.resolve(process.argv[2]??'site');
const bp=JSON.parse(await readFile(path.join(root,'data/latest.json'),'utf8'));
const dp=JSON.parse(await readFile(path.join(root,'details/latest.json'),'utf8'));
const basic=JSON.parse(await readFile(path.join(root,'data',bp.dataset_version,'cards.json'),'utf8'));
const detail=JSON.parse(await readFile(path.join(root,'details',dp.detail_version,'details.json'),'utf8'));
const server=process.env.UI_BASE_URL?null:createServer(async(req,res)=>{
 try{const u=new URL(req.url,'http://localhost'),p=path.resolve(root,u.pathname==='/'?'index.html':decodeURIComponent(u.pathname).slice(1));
 if(!p.startsWith(root+path.sep))throw Error('path');
 res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.mjs':'text/javascript','.css':'text/css','.json':'application/json'})[path.extname(p)]??'application/octet-stream');res.end(await readFile(p));
 }catch{res.writeHead(404);res.end();}
});
if(server)await new Promise(r=>server.listen(0,'127.0.0.1',r));
const base=process.env.UI_BASE_URL??'http://127.0.0.1:'+server.address().port+'/';
const output=process.env.UI_SCREENSHOT_DIR;if(output)await mkdir(output,{recursive:true});
const browser=await chromium.launch({headless:true,executablePath:process.env.UI_BROWSER_PATH});
try{
 for(const width of [1280,390,320]){
  const page=await browser.newPage({viewport:{width,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  for(const [kind,type,target] of [['panel_passive','passive_up','Vocal'],['cap_increase','cap_increase','Visual']]){
   const expected=detail.cards.filter(c=>c.items.some(i=>i.kind===kind&&(kind==='panel_passive'?i.numeric_facts.some(f=>f.metric==='rate'&&f.direction==='UP'&&(f.targets??[f.target]).includes(target)):i.cap_targets.includes(target)))).map(c=>c.card_id);
   await page.goto(base+'?'+new URLSearchParams({skill_kind:kind,effect_type:type,effect_target:target}),{waitUntil:'networkidle'});
   assert.equal(await page.evaluate(()=>window.UI_VERSION),process.env.UI_EXPECTED_VERSION??'ui-v25');
   assert.equal(await page.locator('#count').textContent(),expected.length+' / '+basic.cards.length+' 件');
   const shown=await page.locator('.card').evaluateAll(nodes=>nodes.map(n=>n.dataset.cardId));assert.ok(shown.every(id=>expected.includes(id)));
   assert.equal(await page.locator('.match-reason').count(),shown.length);
   await page.locator('.detail-toggle').first().click();assert.ok(await page.locator('.card').first().locator('.matched-effect').count()>0);
   assert.ok((await page.locator('.card').first().locator('.matched-effect').allTextContents()).every(t=>t.includes(target)));
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   if(output)await page.screenshot({path:path.join(output,width+'-'+type+'.png')});
  }
  assert.deepEqual(errors,[]);await page.close();console.log(width+' passive/cap real source sets, reasons, highlights, no overflow PASS');
 }
}finally{await browser.close();if(server)await new Promise(r=>server.close(r));}
