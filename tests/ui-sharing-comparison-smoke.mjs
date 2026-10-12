import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {chromium} from 'playwright';
const root=path.resolve(process.argv[2]??'site'),output=process.env.UI_AUDIT_DIR;
const json=async name=>JSON.parse(await readFile(path.join(root,name),'utf8'));
const bp=await json('data/latest.json'),dp=await json('details/latest.json');
const basic=await json(`data/${bp.dataset_version}/cards.json`),details=await json(`details/${dp.detail_version}/details.json`);
const detailById=new Map(details.cards.map(card=>[card.card_id,card]));
const assets=new Set(['index.html','app.mjs','details.mjs','search.mjs','style.css']);
const server=createServer(async(req,res)=>{
 try{
  const url=new URL(req.url,'http://localhost'),name=url.pathname==='/'?'index.html':decodeURIComponent(url.pathname).slice(1);
  const source=process.env.UI_SOURCE_WEB==='1'&&assets.has(name)?path.resolve('web'):root;
  const file=path.resolve(source,name);if(!file.startsWith(source+path.sep))throw Error('path');
  let bytes=await readFile(file);
  if(source!==root&&name==='index.html')bytes=Buffer.from(bytes.toString().replaceAll('__VERSION__',bp.dataset_version).replaceAll('__DETAIL_VERSION__',dp.detail_version));
  res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.mjs':'text/javascript','.css':'text/css','.json':'application/json'})[path.extname(file)]??'application/octet-stream');res.end(bytes);
 }catch{res.writeHead(404);res.end();}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const base='http://127.0.0.1:'+server.address().port+'/',browser=await chromium.launch({headless:true,executablePath:process.env.UI_BROWSER_PATH});
const report=[];
const currentMatchItems=(selected,{target='Vocal',star=null}={})=>selected.flatMap(id=>(detailById.get(id)?.items??[]).filter(item=>item.kind==='panel_passive'&&(star==null||Number.isInteger(item.unlock_star)&&item.unlock_star>=0&&item.unlock_star<=star)&&(item.numeric_facts??[]).some(f=>f.metric==='rate'&&f.direction==='UP'&&(!target||(f.targets??[f.target]).includes(target)))));
const comparisonIds=page=>page.locator('#comparison-table .comparison-skill').evaluateAll(nodes=>nodes.map(node=>node.dataset.detailId));
const equalIds=(actual,expected,message)=>assert.deepEqual([...actual].sort(),expected.map(item=>item.detail_id).sort(),message);
const ensureOpen=async(page,id)=>{if(!await page.locator('#'+id).evaluate(e=>e.open))await page.locator('#'+id+'>summary').click();};
try{
 for(const width of [1280,390,320]){
  const context=await browser.newContext({viewport:{width,height:900},...(width<900?{isMobile:true,hasTouch:true}:{})});
  await context.grantPermissions(['clipboard-read','clipboard-write']);
  const page=await context.newPage(),errors=[];page.on('pageerror',error=>errors.push(error.message));
  try{
   await page.goto(base,{waitUntil:'networkidle'});
   assert.equal(await page.evaluate(()=>window.UI_VERSION),process.env.UI_EXPECTED_VERSION??'ui-v27');
   const rows=page.locator('.card'),initialIds=await rows.evaluateAll(nodes=>nodes.slice(0,5).map(node=>node.dataset.cardId));
   await rows.nth(0).locator('.compare-toggle').click();
   assert.equal(await page.locator('#comparison-selection').isVisible(),true);
   assert.equal(await page.locator('#compare-cards').isEnabled(),false,'a single card cannot open comparison');
   assert.equal(await page.locator('#comparison-selected button').count(),1);
   for(let index=1;index<4;index++)await rows.nth(index).locator('.compare-toggle').click();
   assert.equal(await page.locator('#compare-cards').isEnabled(),true);
   await rows.nth(4).locator('.compare-toggle').evaluate(button=>{button.click();button.click();button.click();});
   assert.equal(await page.locator('#comparison-selected button').count(),4,'repeated add cannot exceed four cards');
   assert.equal(await rows.nth(4).locator('.compare-toggle').getAttribute('aria-pressed'),'false');
   await page.locator('#comparison-selected button[data-card-id="'+initialIds[0]+'"]').click();
   assert.equal(await rows.nth(0).locator('.compare-toggle').getAttribute('aria-pressed'),'false');
   await rows.nth(4).locator('.compare-toggle').click();
   const selected=initialIds.slice(1,5);
   assert.equal(await page.locator('#comparison-selected button').count(),4);
   await page.locator('#compare-cards').click();
   assert.equal(await page.locator('#card-comparison').isVisible(),true);
   assert.equal(await page.evaluate(()=>document.activeElement.id),'comparison-heading');
   assert.equal(await page.locator('#comparison-table thead th').count(),5);
   for(const id of selected){const card=basic.cards.find(c=>c.card_id===id);assert.ok((await page.locator('#comparison-table').textContent()).includes(card.card_title));}
   const expandable=page.locator('#comparison-table details');assert.ok(await expandable.count()>0,'without performance conditions full skills remain expandable');
   await expandable.first().locator('summary').click();await page.locator('#comparison-table .comparison-skill').first().waitFor();
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'comparison scroll stays inside the viewport');
   await page.locator('#close-comparison').click();assert.equal(await page.locator('#card-comparison').isVisible(),false);
   await ensureOpen(page,'skill-filters');
   await page.locator('#skill-kind').selectOption('panel_passive');await page.locator('#effect-type').selectOption('passive_up');await page.locator('#effect-target').selectOption('Vocal');
   assert.equal(await page.locator('#comparison-selected button').count(),4,'search updates preserve the temporary selection');
   await page.locator('#compare-cards').click();
   equalIds(await comparisonIds(page),currentMatchItems(selected),'current same-skill matches for all selected cards');
   for(const item of currentMatchItems(selected)){
    const text=await page.locator('#comparison-table .comparison-skill[data-detail-id="'+item.detail_id+'"]').textContent();
    assert.ok(text.includes(item.name));
    if(item.unlock_star!=null)assert.ok(text.includes('特訓 '+item.unlock_star));
    for(const fact of item.numeric_facts.filter(f=>['activation_probability','activation_limit'].includes(f.metric)))assert.ok(text.includes(fact.value+(fact.metric==='activation_probability'?'%':'回')));
    if(item.activation_condition||item.activation_condition_v2||item.activation_condition_v3)assert.ok(text.includes('発動条件'));
   }
   // Browser history recomputes the current comparison without losing its selection.
   await page.goBack({waitUntil:'networkidle'});assert.equal(new URL(page.url()).searchParams.has('effect_target'),false);
   equalIds(await comparisonIds(page),currentMatchItems(selected,{target:null}),'history back restores the previous comparison conditions');
   await page.goForward({waitUntil:'networkidle'});assert.equal(new URL(page.url()).searchParams.get('effect_target'),'Vocal');
   equalIds(await comparisonIds(page),currentMatchItems(selected),'history forward restores same-ID selection and matches');
   if(width<900){
    await page.locator('#open-filters').click();await page.locator('#unlock-star-max').selectOption('2');
    equalIds(await comparisonIds(page),currentMatchItems(selected),'unapplied draft cannot change the comparison');
    await page.locator('#cancel-filters').click();await page.locator('#filter-dialog').waitFor({state:'hidden'});
    equalIds(await comparisonIds(page),currentMatchItems(selected),'draft cancellation retains the comparison');
    await page.locator('#open-filters').click();await page.locator('#unlock-star-max').selectOption('2');await page.locator('#apply-filters').click();await page.locator('#filter-dialog').waitFor({state:'hidden'});
   }else{await ensureOpen(page,'performance-advanced');await page.locator('#unlock-star-max').selectOption('2');}
   equalIds(await comparisonIds(page),currentMatchItems(selected,{star:2}),'applied training condition recomputes matching skills');
   for(const row of await page.locator('.card').all()){
    const id=await row.getAttribute('data-card-id');assert.equal(await row.locator('.compare-toggle').getAttribute('aria-pressed'),String(selected.includes(id)));
   }
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'active comparison scroll stays inside the viewport');
   if(output){await mkdir(output,{recursive:true});await page.screenshot({path:path.join(output,'comparison-open-'+width+'.png')});}
   await page.locator('#clear-comparison').click();
   assert.equal(await page.locator('#card-comparison').isVisible(),false);
   assert.equal(await page.locator('#comparison-selection').isVisible(),false);
   assert.equal(await page.locator('.compare-toggle[aria-pressed="true"]').count(),0);

   // Copying flushes a debounced basic query and retains the actual selected conditions.
   await page.locator('#q').fill('真乃');await page.locator('#copy-search-link').click();
   await page.waitForFunction(()=>document.querySelector('#copy-link-status').textContent.includes('コピーしました'));
   const copied=await page.evaluate(()=>navigator.clipboard.readText());
   assert.equal(copied,page.url());assert.equal(new URL(copied).searchParams.get('q'),'真乃');
   assert.ok((await page.locator('#copy-link-status').textContent()).length>0);
   await page.locator('#reset').click();
   const first=page.locator('.card').first(),firstId=await first.getAttribute('data-card-id'),permalink=await first.locator('.card-permalink').getAttribute('href');
   const fixed=new URL(permalink,page.url());assert.equal(fixed.searchParams.get('card_id'),firstId);assert.equal(fixed.searchParams.size,1,'individual links contain a stable ID only');
   const prior=page.url();await first.locator('.card-permalink').click();await page.waitForLoadState('networkidle');
   assert.equal(await page.locator('.card').count(),1);assert.equal(await page.locator('.card').getAttribute('data-card-id'),firstId);
   assert.equal(await page.locator('.detail-toggle').getAttribute('aria-expanded'),'true');
   assert.ok(await page.locator('.card-detail>*').count()>0);
   await page.goBack({waitUntil:'networkidle'});assert.equal(page.url(),prior);
   const original=basic.cards.find(card=>card.card_id===firstId),opposite=original.card_kind==='P'?'S':'P';
   await page.goto(base+'?'+new URLSearchParams({card_id:firstId,card_kind:opposite}),{waitUntil:'networkidle'});
   assert.equal(await page.locator('#count').textContent(),'0 / '+basic.cards.length+' 件','card ID is an AND condition');
   await page.goto(base+'?card_id=00000000-0000-0000-0000-000000000000',{waitUntil:'networkidle'});
   assert.equal(await page.locator('#count').textContent(),'条件を適用できません');assert.equal(await page.locator('.card').count(),0);
   await ensureOpen(page,'selected-conditions');await page.locator('.filter-chip').click();
   assert.equal(new URL(page.url()).searchParams.has('card_id'),false);assert.equal(await page.locator('#count').textContent(),basic.cards.length+' / '+basic.cards.length+' 件');
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);assert.deepEqual(errors,[]);
   if(output){await mkdir(output,{recursive:true});await page.screenshot({path:path.join(output,'sharing-comparison-'+width+'.png')});}
   report.push({width,status:'pass',selectedCards:selected});console.log(width+' fixed-ID URL, clipboard, 2–4 comparison, current matches, draft and history PASS');
  }finally{await context.close();}
 }
 const fallbackContext=await browser.newContext();
 await fallbackContext.addInitScript(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw Error('denied');}}}));
 const fallback=await fallbackContext.newPage(),fallbackErrors=[];fallback.on('pageerror',error=>fallbackErrors.push(error.message));
 await fallback.goto(base+'?q=真乃',{waitUntil:'networkidle'});await fallback.locator('#copy-search-link').click();
 const value=fallback.locator('#copy-link-value');await value.waitFor({state:'visible'});assert.equal(await value.isVisible(),true);assert.equal(await value.inputValue(),fallback.url());assert.equal(await value.getAttribute('readonly'),'');
 assert.equal(await value.evaluate(input=>document.activeElement===input&&input.selectionStart===0&&input.selectionEnd===input.value.length),true);
 assert.ok((await fallback.locator('#copy-link-status').textContent()).length>0);assert.deepEqual(fallbackErrors,[]);
 await fallbackContext.close();
 console.log('clipboard denial exposes a selected, labelled, readonly copy fallback PASS');

 const memoryId='0902c0d7-ddc9-4b79-b4ea-ed4a521df032',memoryItemId='adac56e3-14df-491f-a4c8-d0c1a40c634e';
 const supportId='002fef8b-4e0e-4a65-875f-718ac69fd638',formulaItemId='5a43d0f3-a3c9-42ca-b9b2-91d6a86f7f58';
 const supplemental=await browser.newPage({viewport:{width:1280,height:900}});
 await supplemental.goto(base+'?'+new URLSearchParams({q:basic.cards.find(c=>c.card_id===memoryId).card_title}),{waitUntil:'networkidle'});
 await supplemental.locator('.compare-toggle[data-card-id="'+memoryId+'"]').click();
 await supplemental.locator('#q').fill(basic.cards.find(c=>c.card_id===supportId).card_title);
 await supplemental.waitForFunction(id=>!!document.querySelector('.compare-toggle[data-card-id="'+id+'"]'),supportId);
 await supplemental.locator('.compare-toggle[data-card-id="'+supportId+'"]').click();await supplemental.locator('#compare-cards').click();
 for(const summary of await supplemental.locator('#comparison-table .comparison-all-skills>summary').all())await summary.click();
 const memoryRow=supplemental.locator('.comparison-skill[data-detail-id="'+memoryItemId+'"]'),formulaRow=supplemental.locator('.comparison-skill[data-detail-id="'+formulaItemId+'"]');
 await memoryRow.waitFor();await formulaRow.waitFor();
 assert.match(await memoryRow.locator('.memory-charge').textContent(),/補足.*1\.25/);
 const formulaText=await formulaRow.textContent();
 assert.ok(formulaText.includes('スキルLv×5'),'a level formula must remain visible instead of only its maximum value');
 assert.ok(formulaText.includes('30 → 2')&&formulaText.includes('50 → 4'),'the support-level progression must stay visible');
 assert.match(formulaText,/必要特訓.*未確認/,'unknown unlock is shown explicitly');
 await ensureOpen(supplemental,'skill-filters');await supplemental.locator('#skill-kind').selectOption('memory_appeal');await supplemental.locator('#effect-type').selectOption('appeal');
 await ensureOpen(supplemental,'performance-advanced');await supplemental.locator('#effect-scope').selectOption('memory_link');
 await memoryRow.waitFor();
 const primaryTexts=await memoryRow.locator('.skill-values:not(.memory-charge):not(.memory-link)').allTextContents();
 assert.ok(primaryTexts.some(text=>text.includes('思い出Link')&&text.includes('2倍')));
 assert.ok(primaryTexts.every(text=>!text.includes('1.25')),'charge reference cannot become the matched Link amount');
 assert.match(await memoryRow.locator('.memory-charge').textContent(),/補足.*1\.25/,'an unmatched old reference remains clearly supplemental');
 await supplemental.close();
 console.log('comparison retains old charge references, distinguishes matched Link amounts, and preserves level formula/progression/unknown unlock PASS');

 const unavailable=basic.cards.find(card=>!detailById.has(card.card_id)),missing=await browser.newPage();
 await missing.goto(base,{waitUntil:'networkidle'});await missing.locator('.compare-toggle').first().click();
 await missing.locator('#q').fill(unavailable.card_title);await missing.waitForFunction(id=>!!document.querySelector('.card[data-card-id="'+id+'"]'),unavailable.card_id);
 await missing.locator('.card[data-card-id="'+unavailable.card_id+'"] .compare-toggle').click();await missing.locator('#compare-cards').click();
 assert.match(await missing.locator('#comparison-table').textContent(),/詳細.*未収録/);await missing.close();
 const failed=await browser.newPage();await failed.route('**/details/*/details.json',route=>route.fulfill({status:503,body:'unavailable'}));
 await failed.goto(base,{waitUntil:'networkidle'});for(let index=0;index<2;index++)await failed.locator('.compare-toggle').nth(index).click();await failed.locator('#compare-cards').click();
 assert.match(await failed.locator('#comparison-table').textContent(),/読み込め|読込失敗|読み込み.*失敗/);await failed.close();
 console.log('comparison distinguishes unrecorded details and detail download failure PASS');
}finally{await browser.close();await new Promise(resolve=>server.close(resolve));if(output)await writeFile(path.join(output,'sharing-comparison.json'),JSON.stringify(report,null,2)+'\n');}
