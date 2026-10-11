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
 {type:'rate_up',target:'Visual',recipient:'all_units',q:'対象：全ユニット',check:e=>e.metric==='rate_up'&&e.targets.includes('Visual')&&e.recipient==='all_units'},
 {type:'rate_down',target:'Visual',recipient:'rivals',q:'自身以外の全ユニット',check:e=>e.metric==='rate_down'&&e.targets.includes('Visual')&&e.recipient==='rivals'},
 {type:'mental_recovery',recipient:'all_units',q:'対象：全ユニット',check:e=>e.metric==='mental_recovery'&&e.recipient==='all_units'},
 {type:'relax',recipient:'all_units',q:'翌ターン 最大メンタル アピールフェイズ開始時',check:e=>e.metric==='relax'&&e.recipient==='all_units'&&e.starts_next_turn&&e.trigger==='appeal_phase_start'},
 {type:'mental_cost',recipient:'self',q:'対象：自身',check:e=>e.metric==='mental_cost'&&e.recipient==='self'},
 {type:'appeal',recipient:'all_audience',target:'Dance',q:'全観客',check:e=>e.metric==='appeal'&&e.targets.includes('Dance')&&e.audience==='all'},
];
const browser=await chromium.launch({headless:true,executablePath:process.env.UI_BROWSER_PATH});
try{
 for(const width of [1280,390,320]){
  const page=await browser.newPage({viewport:{width,height:900},...(width<500?{isMobile:true,hasTouch:true}:{})}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  for(let index=0;index<cases.length;index++){
   const c=cases[index],params=new URLSearchParams({skill_q:c.q});if(c.type)params.set('effect_type',c.type);if(c.kind)params.set('skill_kind',c.kind);if(c.target)params.set('effect_target',c.target);
   if(c.turns)params.set('effect_turns',c.turns);params.set('effect_recipient',c.recipient);
   const expected=doc.cards.filter(card=>card.items.some(i=>(!c.kind||i.kind===c.kind)&&i.effect_details?.effects.some(c.check))).length;assert.ok(expected>0);
   await page.goto(base+'?'+params,{waitUntil:'networkidle'});
   assert.equal(await page.evaluate(()=>window.UI_VERSION),process.env.UI_EXPECTED_VERSION??'ui-v20');assert.equal(await page.evaluate(()=>window.DETAIL_VERSION),pointer.detail_version);
   assert.equal(await page.locator('#effect-type').inputValue(),c.type);assert.equal(await page.locator('#effect-recipient').inputValue(),c.recipient);
   assert.equal(await page.locator('#count').textContent(),expected+' / '+total+' 件',width+' case '+index+' '+c.q);
   await page.locator('.detail-toggle').first().click();const match=page.locator('.matched-effect').first();assert.ok(await match.isVisible(),width+' case '+index+' '+c.q);await match.scrollIntoViewIfNeeded();
   const text=await match.textContent();
   for(const word of c.q.split(' '))assert.ok(text.includes(word),word+' missing in '+text);
   assert.ok(!text.includes('未構造化'));assert.ok(!text.includes('undefined'));
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   if(output&&[0,2,3].includes(index))await page.screenshot({path:path.join(output,width+'-special-'+index+'.png')});
   await page.reload({waitUntil:'networkidle'});assert.equal(await page.locator('#skill-q').inputValue(),c.q);
  }
  for(const p of [
   {effect_recipient:'rivals',effect_type:'mental_cost'},
   {effect_recipient:'all_units',effect_type:'mental_recovery',effect_turns:'1'},
   {effect_recipient:'all_units',effect_type:'appeal'},
   {effect_recipient:'all_audience',effect_type:'relax'},
   {effect_recipient:'all_units',effect_type:'mental_recovery',skill_q:'翌ターン'},
   {q:'ちょっとあげる～',effect_recipient:'all_units',effect_target:'Vocal',effect_type:'rate_up'},
   {effect_recipient:'rivals',effect_target:'メンタル',effect_type:'rate_down'}
  ]){
   await page.goto(base+'?'+new URLSearchParams(p),{waitUntil:'networkidle'});
   assert.equal(await page.locator('#count').textContent(),'0 / '+total+' 件',JSON.stringify(p));
  }
  await page.locator('#reset').click();assert.equal(await page.locator('#count').textContent(),total+' / '+total+' 件');
  if(!await page.locator('#skill-filters').evaluate(n=>n.open))await page.locator('#skill-filters > summary').click();
  await page.locator('#effect-recipient').selectOption('all_units');
  const count=doc.cards.filter(c=>c.items.some(i=>i.effect_details?.effects.some(e=>e.recipient==='all_units'))).length;
  assert.equal(await page.locator('#count').textContent(),count+' / '+total+' 件');
  assert.equal(await page.locator('label[for="effect-recipient"]').isVisible(),true);
  await page.reload({waitUntil:'networkidle'});assert.equal(await page.locator('#effect-recipient').inputValue(),'all_units');
  await page.locator('#active-filters .filter-chip').filter({hasText:'受ける側：全ユニット'}).click();
  assert.equal(await page.locator('#effect-recipient').inputValue(),'');assert.equal(await page.locator('#count').textContent(),total+' / '+total+' 件');
  assert.equal(new URL(page.url()).searchParams.has('effect_recipient'),false);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  assert.deepEqual(errors,[]);await page.close();console.log(width+' recipient scope, delayed recovery, negative filters, select/reload/chip PASS');
 }
}finally{await browser.close();if(server)await new Promise(r=>server.close(r));}
