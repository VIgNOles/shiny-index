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
const leaves=p=>p.terms?p.terms.flatMap(leaves):[p];
const has=(rule,field,value)=>rule?.status==='structured'&&leaves(rule.expression).some(p=>p.field===field&&(value===undefined||p.value===value));
const rules=i=>[...(i.effect_details?.mechanic_conditions??[]).map(r=>r.condition),...(i.effect_details?.effects??[]).map(e=>e.mechanic_condition).filter(Boolean)];
const cases=[
 {q:'現在発動中のパッシブスキル6個以上',type:'rate_up',check:c=>c.items.some(i=>i.effect_details?.effects.some(e=>e.metric==='rate_up'&&has(e.mechanic_condition,'active_passive_count',6)))},
 {q:'Grow Lv上昇条件 VocalUP 2個付与ごと',type:'rate_up',check:c=>c.items.some(i=>i.effect_details?.effects.some(e=>e.metric==='rate_up'&&e.maximum&&e.mechanic_condition?.events_per_level===2&&has(e.mechanic_condition,'status_granted','VocalUP')))},
 {q:'Grow Lv上昇条件 DanceUP パッシブスキル強化 または',check:c=>c.items.some(i=>rules(i).some(r=>has(r,'status_granted','DanceUP')&&has(r,'status_granted','パッシブスキル強化')))},
 {q:'緋田美琴のアピール倍率UPが3個以上付与',type:'refrain',check:c=>c.items.some(i=>i.effect_details?.effects.some(e=>e.metric==='refrain'&&has(e.mechanic_condition,'idol_appeal_boost_count',3)&&e.mechanic_condition.expression.idol==='緋田美琴'))},
 {q:'履歴にコメティックのアイドル3人以上 または',type:'rate_up',check:c=>c.items.some(i=>i.effect_details?.effects.some(e=>e.metric==='rate_up'&&has(e.mechanic_condition,'history_unit_count',3)&&has(e.mechanic_condition,'history_participant','西城樹里')))},
 {q:'Grow Lv上昇条件 観客のリアクション対象になる',type:'appeal',check:c=>c.items.some(i=>i.effect_details?.effects.some(e=>e.metric==='appeal'&&has(e.mechanic_condition,'audience_reaction_targeted',true)))}
];
if(process.env.UI_FACTS_CASES==='1')cases.push(
 {q:'ダメージを受けるまで',type:'rate_up',check:c=>c.items.some(i=>i.effect_details?.effects.some(e=>e.metric==='rate_up'&&e.restrictions?.until_damage))},
 {q:'全観客',type:'interest',check:c=>c.items.some(i=>i.effect_details?.effects.some(e=>e.metric==='interest'&&e.audience==='all'))},
 {q:'Grow 最大1.6倍',type:'interest',check:c=>c.items.some(i=>i.effect_details?.effects.some(e=>e.metric==='interest'&&e.scope==='grow'&&e.maximum&&e.value===1.6))},
 {q:'思い出ゲージ増加 10%',kind:'quick_skill',type:'memory_gauge_gain',check:c=>c.items.some(i=>i.kind==='quick_skill'&&i.effect_details?.effects.some(e=>e.metric==='memory_gauge_gain'&&e.value===10))}
);
const browser=await chromium.launch({headless:true,executablePath:process.env.UI_BROWSER_PATH});
try{
 for(const width of [1280,390,320]){
  const page=await browser.newPage({viewport:{width,height:900},...(width<500?{isMobile:true,hasTouch:true}:{})}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  for(let index=0;index<cases.length;index++){
   const c=cases[index],params=new URLSearchParams({skill_q:c.q});if(c.type)params.set('effect_type',c.type);if(c.kind)params.set('skill_kind',c.kind);
   const expected=doc.cards.filter(c.check).length;assert.ok(expected>0);
   await page.goto(base+'?'+params,{waitUntil:'networkidle'});
   assert.equal(await page.evaluate(()=>window.UI_VERSION),process.env.UI_EXPECTED_VERSION??'ui-v16');assert.equal(await page.evaluate(()=>window.DETAIL_VERSION),pointer.detail_version);
   assert.equal(await page.locator('#count').textContent(),expected+' / '+total+' 件',width+' case '+index+' '+c.q);
   await page.locator('.detail-toggle').first().click();const match=page.locator('.matched-effect').first();assert.ok(await match.isVisible(),width+' case '+index+' '+c.q);await match.scrollIntoViewIfNeeded();
   const text=await match.textContent();
   for(const word of c.q.split(' '))assert.ok(text.includes(word),word+' missing in '+text);
   assert.ok(!text.includes('未構造化'));assert.ok(!text.includes('undefined'));
   if(index===1)assert.ok(text.includes('最大300%'));
   if(c.q==='ダメージを受けるまで')assert.ok(!/\\[\\d+ターン\\]/.test(text));
   if(c.q.startsWith('Grow')){assert.ok(!text.includes('発動条件：'));assert.ok(text.includes('翌ターン反映'));assert.ok(text.includes('使用後Lv0'));}
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   if(output&&index===1)await page.screenshot({path:path.join(output,width+'-grow-rule.png')});
   await page.reload({waitUntil:'networkidle'});assert.equal(await page.locator('#skill-q').inputValue(),c.q);
  }
  await page.goto(base+'?'+new URLSearchParams({effect_type:'appeal',skill_q:'VocalUP 2個付与ごと'}),{waitUntil:'networkidle'});
  assert.equal(await page.locator('#count').textContent(),'0 / '+total+' 件'); // standalone condition cannot invent a matching effect
  await page.locator('#reset').click();assert.equal(await page.locator('#count').textContent(),total+' / '+total+' 件');
  assert.deepEqual(errors,[]);await page.close();console.log(width+' live activation and Grow rules PASS');
 }
}finally{await browser.close();if(server)await new Promise(r=>server.close(r));}
