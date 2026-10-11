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
 {type:'appeal_consume',target:'Dance',q:'VisualUP',check:e=>e.status_consumption?.statuses.some(s=>s.target==='Visual'&&s.direction==='UP')&&e.targets.includes('Dance')},
 {type:'appeal_consume',target:'Dance',q:'DanceDOWN',check:e=>e.status_consumption?.statuses.some(s=>s.target==='Dance'&&s.direction==='DOWN')&&e.targets.includes('Dance')},
 {type:'appeal_consume',target:'Vocal',q:'消去対象：DanceUP・VisualUP',check:e=>JSON.stringify(e.status_consumption?.statuses)===JSON.stringify([{target:'Dance',direction:'UP'},{target:'Visual',direction:'UP'}])&&e.targets.includes('Vocal')},
 {type:'appeal_consume',kind:'memory_appeal',q:'思い出Link：ライブ・思い出のアピール VocalUP',check:e=>e.scope==='memory_link'&&e.status_consumption?.statuses.some(s=>s.target==='Vocal'&&s.direction==='UP')},
 {type:'appeal_consume',kind:'panel_live',q:'Link：ライブ・思い出のアピール VocalUP',check:e=>e.scope==='link'&&e.status_consumption?.statuses.some(s=>s.target==='Vocal'&&s.direction==='UP')},
 {type:'appeal_consume',q:'消去対象：VocalDOWN',check:e=>e.status_consumption?.statuses.some(s=>s.target==='Vocal'&&s.direction==='DOWN')},
];
const browser=await chromium.launch({headless:true,executablePath:process.env.UI_BROWSER_PATH});
try{
 for(const width of [1280,390,320]){
  const page=await browser.newPage({viewport:{width,height:900},...(width<500?{isMobile:true,hasTouch:true}:{})}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  for(let index=0;index<cases.length;index++){
   const c=cases[index],params=new URLSearchParams({skill_q:c.q});if(c.type)params.set('effect_type',c.type);if(c.kind)params.set('skill_kind',c.kind);if(c.target)params.set('effect_target',c.target);
   if(c.turns)params.set('effect_turns',c.turns);
   const expected=doc.cards.filter(card=>card.items.some(i=>(!c.kind||i.kind===c.kind)&&i.effect_details?.effects.some(c.check))).length;assert.ok(expected>0);
   await page.goto(base+'?'+params,{waitUntil:'networkidle'});
   assert.equal(await page.evaluate(()=>window.UI_VERSION),process.env.UI_EXPECTED_VERSION??'ui-v19');assert.equal(await page.evaluate(()=>window.DETAIL_VERSION),pointer.detail_version);
   assert.equal(await page.locator('#effect-type').inputValue(),c.type);
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
   {effect_type:'appeal_consume',effect_turns:'1'},
   {effect_type:'rate_up',skill_q:'消去対象：VisualUP'},
   {q:'水×天カイヤナイト',effect_type:'appeal_consume',effect_target:'Visual',skill_q:'消去対象：DanceDOWN'},
   {effect_type:'appeal_consume',skill_kind:'support_skill'}
  ]){
   await page.goto(base+'?'+new URLSearchParams(p),{waitUntil:'networkidle'});
   assert.equal(await page.locator('#count').textContent(),'0 / '+total+' 件',JSON.stringify(p));
  }
  await page.locator('#reset').click();assert.equal(await page.locator('#count').textContent(),total+' / '+total+' 件');
  if(!await page.locator('#skill-filters').evaluate(n=>n.open))await page.locator('#skill-filters > summary').click();
  await page.locator('#effect-type').selectOption('appeal_consume');
  const count=doc.cards.filter(c=>c.items.some(i=>i.effect_details?.effects.some(e=>e.status_consumption))).length;
  assert.equal(await page.locator('#count').textContent(),count+' / '+total+' 件');
  await page.locator('#effect-turns').selectOption('1');assert.equal(await page.locator('#count').textContent(),'0 / '+total+' 件');
  await page.locator('#reset').click();assert.equal(await page.locator('#count').textContent(),total+' / '+total+' 件');
  assert.deepEqual(errors,[]);await page.close();console.log(width+' consumed statuses, appeal targets, memory/Link, negative filters PASS');
 }
}finally{await browser.close();if(server)await new Promise(r=>server.close(r));}
