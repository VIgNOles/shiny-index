
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
 {q:'カトレアの花言葉',skill_kind:'memory_appeal',effect_type:'appeal',effect_target:'Visual',items:3,text:'Visual'},
 {q:'ワーキングスナップ～デート 甘奈',skill_kind:'panel_live',effect_type:'mental_recovery',items:1,text:'メンタル回復 · メンタル 5%'},
 {q:'ワーキングスナップ～デート 甜花',skill_kind:'panel_live',effect_type:'mental_recovery',items:1,text:'メンタル回復 · メンタル 5%'},
 {q:'ワーキングスナップ～デート 甘奈',skill_kind:'panel_live',effect_type:'relax',effect_turns:'3',items:1,text:'[3ターン]'},
 {q:'ROOTS',effect_type:'random_grant',effect_target:'アピール値',skill_q:'七草にちか 0.2倍',effect_turns:'4',items:1,text:'七草にちかのアピール倍率に+0.2倍'},
 {q:'ROOTS',effect_type:'random_grant',effect_target:'アピール値',skill_q:'緋田美琴 0.2倍',effect_turns:'4',items:1,text:'選択確率不明'},
 {q:'ROOTS',effect_type:'random_grant',effect_target:'アピール値',skill_q:'斑鳩ルカ 0.2倍',effect_turns:'4',items:1,text:'付与は保証されません'},
 {q:'は～と♡に火をつけて',skill_kind:'memory_appeal',effect_type:'rate_up',effect_target:'Visual',items:3,text:'Visual'},
 {q:'泣けよ洗濯機',skill_kind:'panel_live',effect_type:'rate_up',effect_target:'Dance',items:1,text:'Link：'},
 {q:'よそゆき顔のセレナーデ',effect_type:'rate_down',effect_target:'注目度',skill_kind:'memory_appeal',items:5,text:'注目度'},
];
const negatives=[
 {q:'カトレアの花言葉',skill_kind:'memory_appeal',effect_type:'appeal',effect_target:'Dance'},
 {q:'ワーキングスナップ～デート 甘奈',effect_type:'mental_recovery',effect_turns:'1'},
 {q:'ワーキングスナップ～デート 甜花',effect_type:'mental_recovery',effect_turns:'3'},
 {q:'ワーキングスナップ～デート',effect_type:'rate_up',effect_target:'メンタル'},
 {q:'ROOTS',effect_type:'random_grant',skill_q:'0.2倍',effect_turns:'5'},
 {q:'ROOTS',effect_type:'random_grant',skill_q:'20%UP'},
 {q:'ROOTS',effect_type:'idol_appeal_bonus'},
 {q:'よそゆき顔のセレナーデ',effect_type:'rate_down',effect_target:'注目度',effect_turns:'1'},
 {q:'は～と♡に火をつけて',skill_kind:'memory_appeal',effect_type:'rate_up',effect_turns:'1'},
 {q:'泣けよ洗濯機',effect_type:'rate_up',skill_q:'Link：',effect_turns:'1'},
];
const browser=await chromium.launch({headless:true,executablePath:process.env.UI_BROWSER_PATH});
try{
 for(const width of [1280,390,320]){
  const page=await browser.newPage({viewport:{width,height:900},...(width<500?{isMobile:true,hasTouch:true}:{})}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  for(let ix=0;ix<cases.length;ix++){
   const {items,text,...params}=cases[ix];
   await page.goto(base+'?'+new URLSearchParams(params),{waitUntil:'networkidle'});
   assert.equal(await page.evaluate(()=>window.UI_VERSION),'ui-v24');assert.equal(await page.evaluate(()=>window.DETAIL_VERSION),pointer.detail_version);
   assert.equal(await page.locator('#count').textContent(),'1 / 1466 件',JSON.stringify(params));
   assert.equal(await page.locator('#effect-type').inputValue(),params.effect_type);
   await page.locator('.detail-toggle').first().click();
   const matches=page.locator('.matched-effect');assert.equal(await matches.count(),items,JSON.stringify(params));
   for(const value of await matches.allTextContents()){assert.ok(value.includes(text),value);assert.ok(!value.includes('undefined'));}
   await matches.first().scrollIntoViewIfNeeded();
   if(output&&[0,1,4,7].includes(ix))await page.screenshot({path:path.join(output,width+'-confirmed-'+ix+'.png')});
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   await page.reload({waitUntil:'networkidle'});assert.equal(await page.locator('#effect-type').inputValue(),params.effect_type);
  }
  for(const params of negatives){
   await page.goto(base+'?'+new URLSearchParams(params),{waitUntil:'networkidle'});
   assert.equal(await page.locator('#count').textContent(),'0 / 1466 件',JSON.stringify(params));
  }
  await page.goto(base+'?effect_type=mental_recovery',{waitUntil:'networkidle'});
  await page.locator('.filter-chip').filter({hasText:'効果：メンタル回復'}).click();assert.equal(await page.locator('#effect-type').inputValue(),'');
  assert.deepEqual(errors,[]);await page.close();console.log(width+' UI24 user confirmations positive10/negative10, Visual/instant heal/ROOTS/unknown duration/reload/chip/no-overflow PASS');
 }
}finally{await browser.close();if(server)await new Promise(r=>server.close(r));}
