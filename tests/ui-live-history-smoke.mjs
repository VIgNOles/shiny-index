import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {chromium} from 'playwright';
import {detailSearch} from '../web/details.mjs';
const root=path.resolve(process.argv[2]??'site');
const pointer=JSON.parse(await readFile(path.join(root,'details/latest.json'),'utf8'));
const doc=JSON.parse(await readFile(path.join(root,'details',pointer.detail_version,'details.json'),'utf8'));
const b=JSON.parse(await readFile(path.join(root,'data/latest.json'),'utf8'));
const cards=JSON.parse(await readFile(path.join(root,'data',b.dataset_version,'cards.json'),'utf8')).cards;
const server=process.env.UI_BASE_URL?null:createServer(async(req,res)=>{
 try{const url=new URL(req.url,'http://127.0.0.1'),file=path.resolve(root,url.pathname==='/'?'index.html':decodeURIComponent(url.pathname).slice(1));
 if(!file.startsWith(root+path.sep))throw Error('path');
 res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.mjs':'text/javascript','.css':'text/css','.json':'application/json'})[path.extname(file)]??'application/octet-stream');res.end(await readFile(file));
 }catch(e){res.writeHead(404);res.end(String(e));}
});
if(server)await new Promise(r=>server.listen(0,'127.0.0.1',r));
const base=process.env.UI_BASE_URL??'http://127.0.0.1:'+server.address().port+'/';
const params=new URLSearchParams({effect_type:'appeal',skill_q:'アピール履歴 浅倉透'});
const expected=detailSearch(cards,params,new Map(doc.cards.map(c=>[c.card_id,c]))).length;assert.ok(expected>0);
const browser=await chromium.launch({headless:true,executablePath:process.env.UI_BROWSER_PATH});
try{
 for(const width of [1280,390,320]){
  const page=await browser.newPage({viewport:{width,height:900},...(width<500?{isMobile:true,hasTouch:true}:{})});const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+'?'+params,{waitUntil:'networkidle'});
  assert.equal(await page.evaluate(()=>window.UI_VERSION),process.env.UI_EXPECTED_VERSION??'ui-v15');assert.equal(await page.evaluate(()=>window.DETAIL_VERSION),pointer.detail_version);
  assert.equal(await page.locator('#count').textContent(),expected+' / '+cards.length+' 件');
  await page.locator('.detail-toggle').first().click();const match=page.locator('.matched-effect').first();assert.ok(await match.isVisible());
  const text=await match.textContent();assert.ok(text.includes('アピール履歴 浅倉透'));assert.ok(!text.includes('参加アイドル 浅倉透'));
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  await page.reload({waitUntil:'networkidle'});assert.equal(await page.locator('#skill-q').inputValue(),'アピール履歴 浅倉透');
  assert.deepEqual(errors,[]);await page.close();console.log(width+' Link history PASS');
 }
}finally{await browser.close();if(server)await new Promise(r=>server.close(r));}
