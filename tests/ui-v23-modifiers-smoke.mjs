
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
 {q:'アルマ',effect_type:'appeal_enhanced',skill_kind:'mb_live',effect_target:'Vocal',skill_q:'魅了効果',expect:'魅了効果を1.5倍で計算'},
 {q:'いつかのアルファルドへ',effect_type:'appeal_enhanced',skill_kind:'mb_live',effect_target:'Dance',skill_q:'Danceステータス効果',expect:'パッシブ対象外・このアピールのみ'},
 {q:'ヘブンリーブルーをつかまえて',effect_type:'appeal_enhanced',skill_kind:'memory_appeal',effect_target:'Visual',skill_q:'Visualステータス効果',expect:'Visualステータス効果を2倍で計算'},
 {q:'ひな♡まつり',effect_type:'appeal_enhanced',skill_kind:'panel_live',effect_target:'Vocal',expect:'Vocalステータス効果を2倍で計算'},
 {q:'きっと、もう少し',effect_type:'idol_appeal_bonus',effect_turns:'4',skill_q:'緋田美琴 最大0.5倍を加算 Grow：',expect:'Grow Lv上昇条件'},
 {q:'きっと、もう少し',effect_type:'idol_appeal_bonus',effect_turns:'4',skill_q:'七草にちか・緋田美琴',expect:'対象アイドル：七草にちか・緋田美琴'},
 {q:'花ノ名前',effect_type:'idol_appeal_bonus',skill_kind:'mb_live',effect_turns:'4',skill_q:'緋田美琴 1.3倍を加算 Plus：',expect:'1ターン以前'},
 {q:'Noisy Rush',effect_type:'idol_appeal_bonus',skill_kind:'generated_live',effect_turns:'3',skill_q:'斑鳩ルカ 0.5倍を加算',expect:'対象アイドル：斑鳩ルカ'},
 {q:'This way',effect_type:'idol_appeal_bonus',skill_kind:'mb_live',effect_turns:'2',skill_q:'七草にちか・斑鳩ルカ',expect:'対象アイドル：七草にちか・斑鳩ルカ'},
 {q:'This way',effect_type:'idol_appeal_bonus',skill_kind:'memory_appeal',effect_turns:'3',skill_q:'緋田美琴',expect:'思い出Link：'},
 {q:'Candyならいらない',effect_type:'idol_appeal_bonus',effect_turns:'4',skill_q:'小宮果穂・西城樹里',expect:'履歴に放課後クライマックスガールズ'},
];
const negative=[
 {q:'アルマ',effect_type:'appeal_enhanced',skill_kind:'mb_live',effect_target:'Dance'},
 {q:'アルマ',effect_type:'appeal_enhanced',effect_turns:'1'},
 {q:'アルマ',effect_type:'rate_up',skill_q:'魅了効果を1.5倍'},
 {q:'きっと、もう少し',effect_type:'idol_appeal_bonus',skill_q:'西城樹里'},
 {q:'きっと、もう少し',effect_type:'appeal',skill_q:'0.5倍を加算'},
 {q:'花ノ名前',effect_type:'idol_appeal_bonus',skill_kind:'panel_live',skill_q:'1.3倍を加算'},
 {q:'This way',effect_type:'idol_appeal_bonus',skill_kind:'memory_appeal',skill_q:'七草にちか・斑鳩ルカ'},
 {q:'Noisy Rush',effect_type:'idol_appeal_bonus',skill_kind:'generated_live',effect_turns:'4'},
 {q:'ひな♡まつり',effect_type:'appeal_enhanced',skill_q:'Link：'},
 {q:'ROOTS',effect_type:'idol_appeal_bonus'},
 {effect_type:'idol_appeal_bonus',effect_target:'Vocal'},
 {effect_type:'appeal_boost',skill_q:'思い出本体・[追加]効果・チャージには適用なし'},
];
const browser=await chromium.launch({headless:true,executablePath:process.env.UI_BROWSER_PATH});
try{
 for(const width of [1280,390,320]){
  const page=await browser.newPage({viewport:{width,height:900},...(width<500?{isMobile:true,hasTouch:true}:{})}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  for(let ix=0;ix<cases.length;ix++){
   const {expect,...params}=cases[ix];
   await page.goto(base+'?'+new URLSearchParams(params),{waitUntil:'networkidle'});
   assert.equal(await page.evaluate(()=>window.UI_VERSION),'ui-v23');assert.equal(await page.evaluate(()=>window.DETAIL_VERSION),pointer.detail_version);
   assert.equal(await page.locator('#count').textContent(),'1 / 1466 件',JSON.stringify(params));
   await page.locator('.detail-toggle').first().click();
   const matches=page.locator('.matched-effect');assert.ok(await matches.count()>0,JSON.stringify(params));
   for(const text of await matches.allTextContents()){
    assert.ok(text.includes(expect),text);assert.ok(!text.includes('undefined'));
    if(params.effect_type==='idol_appeal_bonus'){
     assert.ok(text.includes('倍を加算（アピール値%UPとは別）'));assert.ok(text.includes('思い出本体・[追加]効果・チャージには適用なし'));
    }else assert.ok(text.includes('このアピールのみ'));
   }
   await matches.first().scrollIntoViewIfNeeded();
   if(output&&[0,2,4,8].includes(ix))await page.screenshot({path:path.join(output,width+'-modifier-'+ix+'.png')});
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   await page.reload({waitUntil:'networkidle'});assert.equal(await page.locator('#effect-type').inputValue(),params.effect_type);
  }
  for(const params of negative){
   await page.goto(base+'?'+new URLSearchParams(params),{waitUntil:'networkidle'});
   assert.equal(await page.locator('#count').textContent(),'0 / 1466 件',JSON.stringify(params));
  }
  await page.goto(base+'?effect_type=appeal_enhanced',{waitUntil:'networkidle'});
  await page.locator('.filter-chip').filter({hasText:'効果：強化アピール'}).click();assert.equal(await page.locator('#effect-type').inputValue(),'');
  assert.deepEqual(errors,[]);await page.close();
  console.log(width+' modifiers positive11/negative12, normal/MB/generated/memory/Grow/shared-persons, additive/enhancement/reload/chip/no-overflow PASS');
 }
}finally{await browser.close();if(server)await new Promise(r=>server.close(r));}
