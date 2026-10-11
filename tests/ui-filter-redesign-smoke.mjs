import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {chromium} from 'playwright';
import {search} from '../web/search.mjs';
const root=path.resolve(process.argv[2]??'site');
const bp=JSON.parse(await readFile(path.join(root,'data/latest.json'),'utf8'));
const dp=JSON.parse(await readFile(path.join(root,'details/latest.json'),'utf8'));
const basic=JSON.parse(await readFile(path.join(root,'data',bp.dataset_version,'cards.json'),'utf8'));
const detail=JSON.parse(await readFile(path.join(root,'details',dp.detail_version,'details.json'),'utf8'));
const server=process.env.UI_BASE_URL?null:createServer(async(req,res)=>{
 try{const u=new URL(req.url,'http://localhost'),p=path.resolve(root,u.pathname==='/'?'index.html':decodeURIComponent(u.pathname).slice(1));
 if(!p.startsWith(root+path.sep))throw Error('path');
 res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.mjs':'text/javascript','.css':'text/css','.json':'application/json'})[path.extname(p)]??'application/octet-stream');res.end(await readFile(p));
 }catch{res.writeHead(404);res.end();}
});
if(server)await new Promise(r=>server.listen(0,'127.0.0.1',r));
const base=process.env.UI_BASE_URL??'http://127.0.0.1:'+server.address().port+'/';
const output=process.env.UI_SCREENSHOT_DIR;if(output)await mkdir(output,{recursive:true});
const browser=await chromium.launch({headless:true,executablePath:process.env.UI_BROWSER_PATH});
try{
 for(const width of [1280,900,899,768,390,320]){
  const page=await browser.newPage({viewport:{width,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  for(const [kind,type,target] of [['panel_passive','passive_up','Vocal'],['cap_increase','cap_increase','Visual']]){
   const expected=detail.cards.filter(c=>c.items.some(i=>i.kind===kind&&(kind==='panel_passive'?i.numeric_facts.some(f=>f.metric==='rate'&&f.direction==='UP'&&(f.targets??[f.target]).includes(target)):i.cap_targets.includes(target)))).map(c=>c.card_id);
   await page.goto(base+'?'+new URLSearchParams({skill_kind:kind,effect_type:type,effect_target:target}),{waitUntil:'networkidle'});
   assert.equal(await page.evaluate(()=>window.UI_VERSION),process.env.UI_EXPECTED_VERSION??'ui-v25');
   assert.equal(await page.locator('#count').textContent(),expected.length+' / '+basic.cards.length+' 件');
   const shown=await page.locator('.card').evaluateAll(nodes=>nodes.map(n=>n.dataset.cardId));assert.ok(shown.every(id=>expected.includes(id)));
   assert.equal(await page.locator('.match-reason').count(),shown.length);
   await page.locator('.detail-toggle').first().click();assert.ok(await page.locator('.card').first().locator('.matched-effect').count()>0);
   assert.ok((await page.locator('.card').first().locator('.matched-effect').allTextContents()).every(t=>t.includes(target)));
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   if(output)await page.screenshot({path:path.join(output,width+'-'+type+'.png')});
  }
  if(width===1280){
   const go=async query=>{await page.goto(base+'?'+query,{waitUntil:'networkidle'});};
   const count=async n=>assert.equal(await page.locator('#count').textContent(),n+' / '+basic.cards.length+' 件');
   await go('browse=limited_gacha&series_ids=birthday');await count(basic.cards.filter(c=>c.acquisition_category==='limited_gacha'&&c.series_ids.includes('birthday')).length);
   assert.equal(await page.locator('#people-filter').evaluate(e=>e.parentElement.id),'filter-panel');
   assert.equal(await page.locator('#legacy-filters').isVisible(),false);
   assert.equal(await page.locator('[name=series_ids][value=twilights]').isVisible(),false);
   const legacy='series_ids=twilights&series_ids=birthday&acquisition_category=limited_gacha';await go(legacy);await count(search(basic.cards,new URLSearchParams(legacy)).length);
   assert.equal(await page.locator('#legacy-filters').isVisible(),true);assert.equal(await page.locator('[name=series_ids][value=twilights]').isChecked(),true);
   await page.locator('[name=series_ids][value=twilights]').uncheck();await count(search(basic.cards,new URLSearchParams('series_ids=birthday&acquisition_category=limited_gacha')).length);
   const old=new URLSearchParams({unit_name:'イルミネーションスターズ',idol_name:'櫻木真乃',sort:'card_title',direction:'desc',review_status:'wiki_only'});await go(old);await count(search(basic.cards,old).length);
   assert.equal(await page.locator('#legacy-filters').isVisible(),true);assert.equal(await page.locator('[data-person-unit]').first().isDisabled(),true);
   await page.locator('#reset').click();await count(basic.cards.length);assert.equal(new URL(page.url()).searchParams.get('sort'),'card_title');assert.equal(new URL(page.url()).searchParams.get('direction'),'desc');
   await go('q=no_such_card_123');await count(0);assert.equal(await page.locator('#filter-issues').isVisible(),false);
   for(const query of ['skill_kind=memory_appeal&mechanic=link','skill_kind=panel_passive&effect_turns=1','card_kind=P&skill_kind=support_skill','from=2026-02-30','effect_type=unknown_future']){
    await go(query);assert.equal(await page.locator('#count').textContent(),'条件を適用できません',query);assert.equal(await page.locator('.card').count(),0);assert.ok((await page.locator('#active-filters').textContent()).length);assert.ok(new URL(page.url()).search.length>1);
   }
   await go('skill_kind=support_skill&effect_type=support_cost_down');assert.ok(Number((await page.locator('#count').textContent()).split(' ')[0])>0);assert.equal(await page.locator('#skill-kind').inputValue(),'support_skill');
   await go('skill_kind=panel_live&skill_kind=possessed_live');assert.equal(await page.locator('#skill-kind').inputValue(),'live');assert.equal(await page.locator('[name=live_origin]:checked').count(),2);
   await page.locator('#skill-kind').selectOption('panel_passive');assert.equal(new URL(page.url()).searchParams.get('skill_kind'),'panel_passive');
   console.log('F01/F03-F05/F09/F10/F12/F18: grouping, legacy AND/OR, editable conditions, reset sort, invalid vs zero PASS');
  }
  if(width<900){
   await page.goto(base,{waitUntil:'networkidle'});
   if(output)await page.screenshot({path:path.join(output,width+'-initial.png')});
   const initial=page.url(),historyLength=await page.evaluate(()=>history.length);
   await page.locator('#open-filters').click();assert.equal(await page.locator('#filter-dialog').isVisible(),true);assert.equal(await page.evaluate(()=>document.activeElement.id),'filter-dialog-heading');
   await page.keyboard.press('Shift+Tab');assert.equal(await page.evaluate(()=>document.querySelector('#filter-dialog').contains(document.activeElement)),true);
   await page.locator('#skill-filters').evaluate(e=>e.open=true);
   await page.locator('#skill-kind').selectOption('panel_passive');await page.locator('#effect-type').selectOption('passive_up');await page.locator('#effect-target').selectOption('Vocal');
   const n=detail.cards.filter(c=>c.items.some(i=>i.kind==='panel_passive'&&i.numeric_facts.some(f=>f.metric==='rate'&&f.direction==='UP'&&(f.targets??[f.target]).includes('Vocal')))).length;
   assert.equal(await page.locator('#apply-filters').textContent(),n+'件を表示');assert.equal(page.url(),initial);assert.equal(await page.locator('#count').textContent(),basic.cards.length+' / '+basic.cards.length+' 件');
   await page.locator('#cancel-filters').click();await page.locator('#filter-dialog').waitFor({state:'hidden'});assert.equal(page.url(),initial);assert.equal(await page.evaluate(()=>document.activeElement.id),'open-filters');
   await page.locator('#open-filters').click();await page.locator('#skill-kind').selectOption('panel_passive');await page.locator('#effect-type').selectOption('passive_up');await page.locator('#effect-target').selectOption('Vocal');
   await page.locator('#apply-filters').click();assert.equal(await page.locator('#filter-dialog').isVisible(),false);assert.equal(await page.locator('#count').textContent(),n+' / '+basic.cards.length+' 件');assert.equal(await page.evaluate(()=>history.length),historyLength+1);assert.equal(await page.evaluate(()=>document.activeElement.id),'results-heading');
   await page.goBack();assert.equal(await page.locator('#count').textContent(),basic.cards.length+' / '+basic.cards.length+' 件');await page.goForward();assert.equal(await page.locator('#count').textContent(),n+' / '+basic.cards.length+' 件');
   await page.locator('#open-filters').click();await page.locator('#skill-kind').selectOption('live');await page.locator('#effect-type').selectOption('rate_up');await page.locator('#performance-advanced').evaluate(e=>e.open=true);await page.locator('#effect-turns').selectOption('1');await page.locator('#skill-kind').selectOption('panel_passive');assert.equal(await page.locator('#apply-filters').isDisabled(),true);assert.equal(await page.locator('#count').textContent(),n+' / '+basic.cards.length+' 件');
   await page.keyboard.press('Escape');await page.locator('#filter-dialog').waitFor({state:'hidden'});assert.equal(new URL(page.url()).searchParams.has('effect_turns'),false);
   await page.locator('#open-filters').click();await page.locator('#effect-target').selectOption('Dance');await page.goBack();assert.equal(await page.locator('#filter-dialog').isVisible(),false);assert.equal(new URL(page.url()).searchParams.get('effect_target'),'Vocal');
   await page.locator('#open-filters').click();await page.locator('#effect-target').selectOption('Dance');await page.setViewportSize({width:1280,height:900});await page.locator('#filter-dialog').waitFor({state:'hidden'});assert.equal(new URL(page.url()).searchParams.get('effect_target'),'Vocal');assert.equal(await page.locator('#filter-panel').evaluate(e=>e.parentElement.className),'controls');
   await page.setViewportSize({width,height:900});assert.equal(await page.locator('#open-filters').isVisible(),true);
   await page.locator('#open-filters').click();if(output)await page.screenshot({path:path.join(output,width+'-filter-panel.png')});await page.keyboard.press('Escape');await page.locator('#filter-dialog').waitFor({state:'hidden'});
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   await page.locator('#open-filters').click();await page.locator('#skill-q').fill('no_such_skill_012345');await page.waitForFunction(()=>document.querySelector('#apply-filters').textContent==='0件を表示');assert.equal(await page.locator('#apply-filters').isDisabled(),false);await page.locator('#apply-filters').click();assert.equal(await page.locator('#count').textContent(),'0 / '+basic.cards.length+' 件');
   await page.locator('#reset').click();assert.equal(await page.locator('#count').textContent(),basic.cards.length+' / '+basic.cards.length+' 件');
   console.log(width+' F19/F20 draft/cancel/apply/back/forward/Escape/resize/focus PASS');
  }
  if(width===1280){
   await page.goto(base,{waitUntil:'networkidle'});await page.locator('#advanced-filters').evaluate(e=>e.open=true);
   await page.locator('#from-year').selectOption('2025');assert.equal(new URL(page.url()).searchParams.get('from'),'2025');
   await page.locator('#from-month').selectOption('02');assert.equal(new URL(page.url()).searchParams.get('from'),'2025-02');
   await page.locator('#from-day').selectOption('28');assert.equal(new URL(page.url()).searchParams.get('from'),'2025-02-28');
   await page.locator('[name=date-mode][value=calendar]').check();assert.equal(await page.locator('#from-native').inputValue(),'2025-02-28');
   await page.locator('#to-native').fill('2024-01-01');await page.locator('#to-native').dispatchEvent('change');assert.equal(await page.locator('#count').textContent(),'条件を適用できません');
   await page.locator('#to-native').fill('2026-01-01');await page.locator('#to-native').dispatchEvent('change');assert.equal(await page.locator('#count').textContent(),search(basic.cards,new URLSearchParams('from=2025-02-28&to=2026-01-01')).length+' / '+basic.cards.length+' 件');
   await page.locator('#q').focus();await page.locator('#q').dispatchEvent('compositionstart');await page.locator('#q').fill('真乃');assert.equal(new URL(page.url()).searchParams.has('q'),false);
   await page.locator('#q').dispatchEvent('compositionend');await page.waitForFunction(()=>new URL(location.href).searchParams.get('q')==='真乃');
   await page.goto(base,{waitUntil:'networkidle'});if(output)await page.screenshot({path:path.join(output,width+'-initial.png')});
   await page.locator('#people-filter > summary').click();const unit=page.locator('[data-person-unit=unit_1]');await unit.check();assert.equal(await page.locator('#count').textContent(),basic.cards.filter(c=>c.unit_id==='unit_1').length+' / '+basic.cards.length+' 件');
   const child=page.locator('[data-person-idol=idol_1]');assert.equal(await child.isVisible(),true);await child.uncheck();assert.equal(await unit.evaluate(e=>e.indeterminate),true);assert.equal(await page.locator('#count').textContent(),basic.cards.filter(c=>c.unit_id==='unit_1'&&c.idol_id!=='idol_1').length+' / '+basic.cards.length+' 件');
   await page.locator('#reset').click();assert.equal(await page.locator('.card').count(),100);await page.locator('.detail-toggle').first().focus();await page.keyboard.press('Enter');assert.equal(await page.locator('.card-detail').first().isVisible(),true);await page.locator('#more').click();assert.equal(await page.locator('.card').count(),200);assert.equal(await page.locator('.card-detail').first().isVisible(),true);
   assert.equal(await page.locator('#downloads a').count(),5);assert.equal(await page.locator('#downloads a[href$="cards.csv"]').count(),0);assert.equal(await page.locator('#detail-downloads a').count(),2);assert.equal(await page.locator('.card').first().locator('.card-action a').getAttribute('rel'),'noopener noreferrer');
   const unnamed=await page.locator('input,select,button').evaluateAll(es=>es.filter(e=>e.getClientRects().length&&!e.disabled).filter(e=>!(e.getAttribute('aria-label')||[...(e.labels||[])].map(x=>x.textContent).join(' ')||(e.matches('button')?e.textContent:'')).trim()).map(e=>e.id));assert.deepEqual(unnamed,[]);
   const smallTargets=await page.locator('button,select,.filter-option,summary').evaluateAll(es=>es.filter(e=>e.getClientRects().length).filter(e=>e.getBoundingClientRect().height<43.5).map(e=>e.id||e.tagName));assert.deepEqual(smallTargets,[]);
   await page.route('**/details.json',route=>route.fulfill({status:503,body:'unavailable'}));await page.goto(base+'?skill_kind=panel_passive',{waitUntil:'networkidle'});assert.equal(await page.locator('#count').textContent(),'条件を適用できません');assert.equal(await page.locator('#skill-kind').isDisabled(),true);await page.locator('#reset').click();assert.equal(await page.locator('#count').textContent(),basic.cards.length+' / '+basic.cards.length+' 件');await page.unroute('**/details.json');
   console.log('F02/F17/F18/F22 people, dates, IME, keyboard, targets, downloads, more, detail failure PASS');

  }
  assert.deepEqual(errors,[]);await page.close();console.log(width+' passive/cap real source sets, reasons, highlights, no overflow PASS');
 }
}finally{await browser.close();if(server)await new Promise(r=>server.close(r));}
