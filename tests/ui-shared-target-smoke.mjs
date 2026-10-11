import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {chromium} from 'playwright';
const root=path.resolve(process.argv[2]??'site');
const pointer=JSON.parse(await readFile(path.join(root,'details/latest.json'),'utf8'));
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
  for(const title of ['新装備・バブルバスター！','メイドインナツハ']){
   for(const target of ['注目度','メンタルダメージ']){
    const p=new URLSearchParams({q:title,skill_kind:'panel_live',effect_type:'rate_up',effect_target:target,effect_turns:'1'});
    await page.goto(base+'?'+p,{waitUntil:'networkidle'});
    assert.equal(await page.evaluate(()=>window.UI_VERSION),process.env.UI_EXPECTED_VERSION??'ui-v21');
    assert.equal(await page.evaluate(()=>window.DETAIL_VERSION),pointer.detail_version);
    assert.equal(await page.locator('#count').textContent(),'1 / 1466 件');
    await page.locator('.detail-toggle').first().click();
    assert.equal(await page.locator('.matched-effect').count(),2);
    const matches=page.locator('.matched-effect');
    for(const text of await matches.allTextContents()){
     assert.ok(text.includes('注目度 / メンタルダメージ 50%'));assert.ok(text.includes('1ターン'));
     assert.ok(!text.includes('Link'));assert.ok(!text.includes('必ず最初'));
    }
    await matches.first().scrollIntoViewIfNeeded();
    if(output&&target==='注目度')await page.screenshot({path:path.join(output,width+'-'+(title.startsWith('新装備')?'kaho':'natsuha')+'.png')});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    await page.reload({waitUntil:'networkidle'});assert.equal(await page.locator('#effect-target').inputValue(),target);
   }
   for(const extra of [{effect_turns:'2'},{skill_q:'Link：'},{effect_target:'Vocal',skill_q:'注目度'},{effect_type:'rate_down'}]){
    await page.goto(base+'?'+new URLSearchParams({q:title,skill_kind:'panel_live',effect_type:'rate_up',effect_target:'注目度',effect_turns:'1',...extra}),{waitUntil:'networkidle'});
    assert.equal(await page.locator('#count').textContent(),'0 / 1466 件',JSON.stringify(extra));
   }
  }
  assert.deepEqual(errors,[]);await page.close();
  console.log(width+' shared target positive4/negative8, same-effect value/duration/highlight/reload/no-overflow PASS');
 }
}finally{await browser.close();if(server)await new Promise(r=>server.close(r));}
