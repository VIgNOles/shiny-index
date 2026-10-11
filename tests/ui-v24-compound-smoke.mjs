
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
 {q:'夏空への挑戦',effect_type:'mental_overflow',items:1,text:'超過分のみ思い出ゲージに変換'},
 {q:'Feel Like Flower',effect_type:'mental_overflow',items:2,text:'固定量のゲージ増加ではありません'},
 {q:'ないしょのスイーツ',effect_type:'mental_overflow',skill_kind:'memory_appeal',items:3,text:'超過分のみ'},
 {q:'空・風・明・鳴',effect_type:'flexible',effect_turns:'2',items:1,text:'Plusの発動条件を無視'},
 {q:'眩いステージ',effect_type:'flexible',skill_kind:'mb_live',effect_turns:'2',items:2,text:'付与翌ターンを1ターン目'},
 {q:'Starlight',effect_type:'sparkle_eyes',items:2,text:'注目度UPの付与条件の代用不可'},
 {q:'In red',effect_type:'sparkle_eyes',skill_kind:'memory_appeal',effect_turns:'3',items:3,text:'1個につき注目度50%UP'},
 {q:'HoP PoP らびっつ',effect_type:'vigor_gain',items:1,text:'気力 1増加'},
 {q:'恋人たち',effect_type:'vigor_gain',skill_kind:'mb_live',items:2,text:'Link：'},
 {q:'Cherish You',effect_type:'vigor_gain',skill_kind:'generated_live',items:2,text:'気力 1増加'},
 {q:'常夏CLIMAX',effect_type:'memory_gauge_loss',items:1,text:'思い出ゲージ 30%'},
 {q:'今、できることを全て',effect_type:'status_conversion',skill_kind:'mb_live',effect_turns:'4',effect_recipient:'self',items:1,text:'Visual 60%UPへ変換'},
 {q:'事務所。静寂。大輪の華',effect_type:'appeal_perfect',effect_target:'Dance',items:1,text:'PERFECT時は3倍'},
 {q:'夕つ方まみみチック',effect_type:'instant_satisfaction',skill_q:'ごくごく稀',items:1,text:'数値確率は未確認'},
 {q:'Hug？',effect_type:'charm',effect_turns:'2',effect_recipient:'all_audience',skill_q:'Grow：',items:1,text:'[2～3ターン]'},
 {q:'片恋はあと',effect_type:'rate_up',effect_target:'Dance',skill_q:'使用者 リーダーシップ',items:2,text:'使用者がキーワード「リーダーシップ」を全て所持'},
];
const negatives=[
 {q:'夏空への挑戦',effect_type:'memory_gauge_gain'},
 {q:'夏空への挑戦',effect_type:'mental_overflow',effect_target:'思い出ゲージ'},
 {q:'夏空への挑戦',effect_type:'mental_overflow',effect_turns:'1'},
 {q:'Feel Like Flower',effect_type:'mental_overflow',skill_q:'Link：'},
 {q:'Feel Like Flower',effect_type:'mental_overflow',card_kind:'S'},
 {q:'空・風・明・鳴',effect_type:'flexible',effect_turns:'3'},
 {q:'眩いステージ',effect_type:'flexible',skill_kind:'mb_live',effect_turns:'3'},
 {q:'Starlight',effect_type:'sparkle_eyes',effect_target:'注目度'},
 {q:'Starlight',effect_type:'rate_up',effect_target:'注目度'},
 {q:'恋人たち',effect_type:'vigor_gain',effect_turns:'1'},
 {q:'恋人たち',effect_type:'vigor_gain',skill_kind:'memory_appeal'},
 {q:'常夏CLIMAX',effect_type:'memory_gauge_loss',effect_turns:'1'},
 {q:'今、できることを全て',effect_type:'status_conversion',effect_turns:'5'},
 {q:'今、できることを全て',effect_type:'rate_up',skill_q:'変換対象'},
 {q:'事務所。静寂。大輪の華',effect_type:'appeal_perfect',effect_target:'Visual'},
 {q:'夕つ方まみみチック',effect_type:'instant_satisfaction',effect_turns:'1'},
 {q:'Hug？',effect_type:'charm',effect_turns:'3',effect_recipient:'all_audience',skill_q:'Grow：'},
 {q:'片恋はあと',effect_type:'rate_up',effect_turns:'5',skill_q:'リーダーシップ'},
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
   if(output&&[0,4,6,8,11,14,15].includes(ix))await page.screenshot({path:path.join(output,width+'-compound-'+ix+'.png')});
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   await page.reload({waitUntil:'networkidle'});assert.equal(await page.locator('#effect-type').inputValue(),params.effect_type);
  }
  for(const params of negatives){
   await page.goto(base+'?'+new URLSearchParams(params),{waitUntil:'networkidle'});
   assert.equal(await page.locator('#count').textContent(),'0 / 1466 件',JSON.stringify(params));
  }
  await page.goto(base+'?effect_type=mental_overflow',{waitUntil:'networkidle'});
  await page.locator('.filter-chip').filter({hasText:'効果：超過回復'}).click();assert.equal(await page.locator('#effect-type').inputValue(),'');
  assert.deepEqual(errors,[]);await page.close();console.log(width+' UI24 compound positive16/negative18, P/S/normal/MB/generated/memory/Link/Plus, duration/recipient/conditional-amount/reload/chip/no-overflow PASS');
 }
}finally{await browser.close();if(server)await new Promise(r=>server.close(r));}
