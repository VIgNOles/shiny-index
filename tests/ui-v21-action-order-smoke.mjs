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
const cases=[
 {type:'appeal_first',target:'Visual',q:'必ず最初にアピール',check:e=>e.metric==='appeal'&&e.appeal_order==='first'&&e.targets.includes('Visual')},
 {type:'appeal_last',target:'Vocal',q:'必ず最後にアピール',check:e=>e.metric==='appeal'&&e.appeal_order==='last'&&e.targets.includes('Vocal')},
 {type:'action_order',q:'コラボフェス',check:e=>e.appeal_order&&e.order_excludes?.includes('collaboration_fes')},
 {type:'appeal_last',recipient:'all_audience',q:'全観客',check:e=>e.appeal_order==='last'&&e.audience==='all'},
 {type:'appeal_first',q:'アピールの行動順指定',check:e=>e.metric==='action_order'&&e.appeal_order==='first'},
 {type:'rate_up',target:'メンタルダメージ',q:'ビ～♡バップ海岸',itemQuery:true,cardCheck:c=>c.card_id==='e682e7f0-94dd-4f86-acce-c27797abe434',check:e=>e.metric==='rate_up'&&e.targets.includes('メンタルダメージ')&&[50,70].includes(e.value)},
];
const browser=await chromium.launch({headless:true,executablePath:process.env.UI_BROWSER_PATH});
try{
 for(const width of [1280,390,320]){
  const page=await browser.newPage({viewport:{width,height:900},...(width<500?{isMobile:true,hasTouch:true}:{})}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  for(let index=0;index<cases.length;index++){
   const c=cases[index],params=new URLSearchParams({skill_q:c.q});if(c.type)params.set('effect_type',c.type);if(c.kind)params.set('skill_kind',c.kind);if(c.target)params.set('effect_target',c.target);
   if(c.turns)params.set('effect_turns',c.turns);if(c.recipient)params.set('effect_recipient',c.recipient);
   const expected=doc.cards.filter(card=>(!c.cardCheck||c.cardCheck(card))&&card.items.some(i=>(!c.kind||i.kind===c.kind)&&i.effect_details?.effects.some(c.check))).length;assert.ok(expected>0);
   await page.goto(base+'?'+params,{waitUntil:'networkidle'});
   assert.equal(await page.evaluate(()=>window.UI_VERSION),process.env.UI_EXPECTED_VERSION??'ui-v21');assert.equal(await page.evaluate(()=>window.DETAIL_VERSION),pointer.detail_version);
   assert.equal(await page.locator('#effect-type').inputValue(),c.type);assert.equal(await page.locator('#effect-recipient').inputValue(),c.recipient??'');
   assert.equal(await page.locator('#count').textContent(),expected+' / '+total+' 件',width+' case '+index+' '+c.q);
   await page.locator('.detail-toggle').first().click();const match=page.locator('.matched-effect').first();assert.ok(await match.isVisible(),width+' case '+index+' '+c.q);await match.scrollIntoViewIfNeeded();
   const text=await match.textContent();
   for(const word of c.q.split(' '))assert.ok((c.itemQuery?await page.locator('.card').first().textContent():text).includes(word),word+' missing in '+text);
   if(index===4){assert.ok(!text.includes('倍'));assert.ok(!text.includes('ターン'));}
   assert.ok(!text.includes('未構造化'));assert.ok(!text.includes('undefined'));
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   if(output&&[0,3,4,5].includes(index))await page.screenshot({path:path.join(output,width+'-special-'+index+'.png')});
   await page.reload({waitUntil:'networkidle'});assert.equal(await page.locator('#skill-q').inputValue(),c.q);
  }
  for(const p of [
   {effect_type:'appeal_first',effect_turns:'1'},
   {effect_type:'appeal_first',effect_target:'メンタルダメージ'},
   {effect_type:'appeal_first',skill_q:'必ず最後にアピール'},
   {q:'ビ～♡バップ海岸',effect_type:'appeal_first',effect_target:'Dance'},
   {q:'ビ～♡バップ海岸',effect_type:'appeal',skill_kind:'panel_live'},
   {q:'曲がり角のランウェイ',effect_type:'appeal_last',effect_recipient:'all_units'},
   {effect_type:'action_order',skill_kind:'panel_passive'}
  ]){
   await page.goto(base+'?'+new URLSearchParams(p),{waitUntil:'networkidle'});
   assert.equal(await page.locator('#count').textContent(),'0 / '+total+' 件',JSON.stringify(p));
  }
  await page.locator('#reset').click();assert.equal(await page.locator('#count').textContent(),total+' / '+total+' 件');
  if(!await page.locator('#skill-filters').evaluate(n=>n.open))await page.locator('#skill-filters > summary').click();
  for(const value of ['action_order','appeal_first','appeal_last'])assert.equal(await page.locator('#effect-type option[value="'+value+'"]').count(),1);
  await page.locator('#effect-type').selectOption('action_order');
  const count=doc.cards.filter(c=>c.items.some(i=>i.effect_details?.effects.some(e=>e.appeal_order))).length;
  assert.equal(await page.locator('#count').textContent(),count+' / '+total+' 件');
  await page.locator('#effect-type').selectOption('appeal_first');
  const first=doc.cards.filter(c=>c.items.some(i=>i.effect_details?.effects.some(e=>e.appeal_order==='first'))).length;
  assert.equal(await page.locator('#count').textContent(),first+' / '+total+' 件');
  await page.reload({waitUntil:'networkidle'});assert.equal(await page.locator('#effect-type').inputValue(),'appeal_first');
  await page.locator('#active-filters .filter-chip').filter({hasText:'効果：必ず最初にアピール'}).click();
  assert.equal(await page.locator('#effect-type').inputValue(),'');assert.equal(await page.locator('#count').textContent(),total+' / '+total+' 件');
  assert.equal(new URL(page.url()).searchParams.has('effect_type'),false);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  assert.deepEqual(errors,[]);await page.close();console.log(width+' first/last order, no fabricated multiplier, immediate buff, negative filters, select/reload/chip PASS');
 }
}finally{await browser.close();if(server)await new Promise(r=>server.close(r));}
