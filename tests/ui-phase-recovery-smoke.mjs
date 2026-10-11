
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {chromium} from 'playwright';
const root=path.resolve(process.argv[2]??'site');
const pointer=JSON.parse(await readFile(path.join(root,'details/latest.json'),'utf8'));
const doc=JSON.parse(await readFile(path.join(root,'details',pointer.detail_version,'details.json'),'utf8'));
const output=process.env.UI_SCREENSHOT_DIR;if(output)await mkdir(output,{recursive:true});
const server=process.env.UI_BASE_URL?null:createServer(async(req,res)=>{
 try{const u=new URL(req.url,'http://127.0.0.1'),p=path.resolve(root,u.pathname==='/'?'index.html':decodeURIComponent(u.pathname).slice(1));
 if(!p.startsWith(root+path.sep))throw Error('path');
 res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.mjs':'text/javascript','.css':'text/css','.json':'application/json'})[path.extname(p)]??'application/octet-stream');res.end(await readFile(p));
 }catch(e){res.writeHead(404);res.end(String(e));}
});
if(server)await new Promise(r=>server.listen(0,'127.0.0.1',r));
const base=process.env.UI_BASE_URL??'http://127.0.0.1:'+server.address().port+'/';

const cases=[
 {q:'彩りファッションドール',effect_type:'mental_recovery',effect_turns:'3',skill_q:'アピールフェイズ開始時',items:1,text:'メンタル 5%'},
 {q:'放課後★肝試しパニック',effect_type:'mental_recovery',effect_turns:'5',skill_q:'アピールフェイズ開始時',items:1,text:'メンタル 4%'},
 {q:'マイフェイバリット',effect_type:'mental_recovery',effect_turns:'4',skill_q:'アピールフェイズ開始時',items:2,text:'アピールフェイズ開始時'},
 {q:'四夜一夜物語',effect_type:'mental_recovery',skill_kind:'memory_appeal',effect_turns:'7',skill_q:'アピールフェイズ開始時',items:1,text:'メンタル 5%',actualTurns:'8'},
 {q:'はるかぜまち、1番地',effect_type:'mental_recovery',effect_turns:'4',skill_q:'Link： アピールフェイズ開始時',items:2,text:'メンタル 15%'},
 {q:'RELAXIN',effect_type:'relax',effect_turns:'3',items:1,text:'付与の翌ターンから最大メンタルを基準に回復'},
];
const negatives=[
 {q:'彩りファッションドール',effect_type:'mental_recovery',effect_turns:'4',skill_q:'アピールフェイズ開始時'},
 {q:'放課後★肝試しパニック',effect_type:'mental_recovery',effect_turns:'7',skill_q:'アピールフェイズ開始時'},
 {q:'マイフェイバリット',effect_type:'mental_recovery',effect_turns:'4',skill_q:'Link： アピールフェイズ開始時'},
 {q:'RELAXIN',effect_type:'mental_recovery'},
 {q:'彩りファッションドール',effect_type:'relax'},
 {q:'四夜一夜物語',effect_type:'mental_recovery',effect_target:'Visual'},
 {q:'はるかぜまち、1番地',effect_type:'mental_recovery',effect_turns:'5'},
];
const browser=await chromium.launch({headless:true,executablePath:process.env.UI_BROWSER_PATH});
try{
 for(const width of [1280,390,320]){
  const page=await browser.newPage({viewport:{width,height:900},...(width<500?{isMobile:true,hasTouch:true}:{})}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  for(let ix=0;ix<cases.length;ix++){
   const {items,text,actualTurns,...params}=cases[ix];
   await page.goto(base+'?'+new URLSearchParams(params),{waitUntil:'networkidle'});
   assert.equal(await page.evaluate(()=>window.UI_VERSION),process.env.UI_EXPECTED_VERSION??'ui-v23');assert.equal(await page.evaluate(()=>window.DETAIL_VERSION),pointer.detail_version);
   assert.equal(await page.locator('#count').textContent(),'1 / 1466 件',JSON.stringify(params));
   await page.locator('.detail-toggle').first().click();
   const matches=page.locator('.matched-effect');assert.equal(await matches.count(),items,JSON.stringify(params));
   for(const value of await matches.allTextContents()){
    assert.ok(value.includes(text),value);assert.ok(value.includes('['+(actualTurns??params.effect_turns)+'ターン]'));assert.ok(value.includes('アピールフェイズ開始時'));assert.ok(!value.includes('undefined'));
   }
   await matches.first().scrollIntoViewIfNeeded();
   if(output&&[1,4,5].includes(ix))await page.screenshot({path:path.join(output,width+'-phase-'+ix+'.png')});
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   await page.reload({waitUntil:'networkidle'});assert.equal(await page.locator('#effect-turns').inputValue(),params.effect_turns);
  }
  for(const params of negatives){
   await page.goto(base+'?'+new URLSearchParams(params),{waitUntil:'networkidle'});
   assert.equal(await page.locator('#count').textContent(),'0 / 1466 件',JSON.stringify(params));
  }
  await page.goto(base+'?effect_type=mental_recovery&effect_turns=5&skill_q='+encodeURIComponent('アピールフェイズ開始時'),{waitUntil:'networkidle'});
  await page.locator('.filter-chip').filter({hasText:'効果：メンタル回復'}).click();assert.equal(await page.locator('#effect-type').inputValue(),'');
  assert.deepEqual(errors,[]);await page.close();console.log(width+' phase recovery positive6/negative7, P/S/panel/memory/Link/short-relax, timing/duration/same-fact/reload/chip/no-overflow PASS');
 }
}finally{await browser.close();if(server)await new Promise(r=>server.close(r));}
