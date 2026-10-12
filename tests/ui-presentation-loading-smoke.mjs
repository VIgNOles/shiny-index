import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {chromium} from 'playwright';
const root=path.resolve(process.argv[2]??'site'),web=path.resolve('web');
const json=async name=>JSON.parse(await readFile(path.join(root,name),'utf8'));
const bp=await json('data/latest.json'),dp=await json('details/latest.json');
const basic=await json(`data/${bp.dataset_version}/cards.json`),detail=await json(`details/${dp.detail_version}/details.json`);
const sourceWeb=process.env.UI_SOURCE_WEB==='1';
const server=createServer(async(req,res)=>{
 try{
  const url=new URL(req.url,'http://localhost'),name=url.pathname==='/'?'index.html':decodeURIComponent(url.pathname).slice(1);
  const source=sourceWeb&&['index.html','app.mjs','details.mjs','search.mjs','style.css'].includes(name)?web:root;
  const file=path.resolve(source,name);if(!file.startsWith(source+path.sep))throw Error('path');
  let bytes=await readFile(file);
  if(sourceWeb&&name==='index.html')bytes=Buffer.from(bytes.toString().replaceAll('__VERSION__',bp.dataset_version).replaceAll('__DETAIL_VERSION__',dp.detail_version));
  res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.mjs':'text/javascript','.css':'text/css','.json':'application/json'})[path.extname(file)]??'application/octet-stream');res.end(bytes);
 }catch{res.writeHead(404);res.end();}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const base='http://127.0.0.1:'+server.address().port+'/',browser=await chromium.launch({headless:true,executablePath:process.env.UI_BROWSER_PATH});
const errors=[];
const pageFor=async(options={})=>{const page=await browser.newPage(options);page.on('pageerror',e=>errors.push(e.message));return page;};
const holdDetails=async page=>{
 let release;const gate=new Promise(resolve=>{release=resolve;});
 await page.route('**/details/*/details.json',async route=>{await gate;await route.continue();});return release;
};
const loaded=page=>page.waitForFunction(()=>document.querySelector('#detail-version').textContent.includes('詳細データ版'));
const hasRate=(item,target)=>item.kind==='panel_passive'&&(item.numeric_facts??[]).some(f=>f.metric==='rate'&&f.direction==='UP'&&(f.targets??[f.target]).includes(target));
try{
 const page=await pageFor(),release=await holdDetails(page);
 await page.goto(base,{waitUntil:'domcontentloaded'});await page.locator('.card').first().waitFor();
 assert.equal(await page.locator('#count').textContent(),basic.cards.length+' / '+basic.cards.length+' 件');
 assert.equal(await page.locator('#skill-controls').evaluate(e=>e.disabled),true);
 assert.equal(await page.locator('.card-detail>*').count(),0,'closed card details must have no built content');
 assert.ok((await page.locator('.detail-status').first().textContent()).includes('読込中'));
 await page.locator('.detail-toggle').first().click();
 await page.evaluate(()=>{window.firstCard=document.querySelector('.card');window.firstDetail=document.querySelector('.card-detail');});
 await page.locator('#more').click();
 assert.equal(await page.locator('.card').count(),200);
 assert.equal(await page.evaluate(()=>window.firstCard===document.querySelector('.card')&&window.firstDetail===document.querySelector('.card-detail')),true,'append must retain existing DOM');
 assert.equal(await page.locator('.card-detail').first().isVisible(),true);
 assert.equal(await page.evaluate(()=>document.activeElement===document.querySelectorAll('.card')[100].querySelector('.detail-toggle')),true);
 await page.locator('#q').fill('櫻木真乃');
 const expectedBasic=basic.cards.filter(c=>c.idol_name==='櫻木真乃').length;
 await page.waitForFunction(expected=>document.querySelector('#count').textContent===expected,expectedBasic+' / '+basic.cards.length+' 件');
 assert.equal(await page.locator('#q').inputValue(),'櫻木真乃');
 release();await loaded(page);
 assert.equal(await page.locator('#count').textContent(),expectedBasic+' / '+basic.cards.length+' 件');
 assert.equal(await page.locator('#q').inputValue(),'櫻木真乃');
 assert.equal(await page.locator('#skill-controls').evaluate(e=>e.disabled),false);
 console.log('basic search before detail verification, lazy card details and append DOM/focus PASS');
 await page.close();

 const query='skill_kind=panel_passive&effect_type=passive_up&effect_target=Vocal';
 const perf=await pageFor(),releasePerf=await holdDetails(perf);
 await perf.goto(base+'?'+query,{waitUntil:'domcontentloaded'});
 await perf.waitForFunction(()=>document.querySelector('#count').textContent==='詳細情報を読み込み中');
 assert.equal(await perf.locator('.card').count(),0,'performance URL must not be shown as a basic-only result');
 assert.equal(new URL(perf.url()).search.slice(1),query);
 assert.equal(await perf.locator('#effect-target').inputValue(),'Vocal');
 releasePerf();await loaded(perf);
 const expected=detail.cards.filter(c=>c.items.some(i=>hasRate(i,'Vocal')));
 assert.equal(await perf.locator('#count').textContent(),expected.length+' / '+basic.cards.length+' 件');
 assert.equal(await perf.locator('.card-detail>*').count(),0);
 assert.equal(await perf.locator('.match-list').count(),0,'match expansion content is lazy');
 const first=perf.locator('.card').first(),id=await first.getAttribute('data-card-id');
 const expectedItems=expected.find(c=>c.card_id===id).items.filter(i=>hasRate(i,'Vocal'));
 await first.locator('.match-details>summary').click();
 await first.locator('.match-item').first().waitFor();
 assert.equal(await first.locator('.match-item').count(),expectedItems.length);
 for(const item of expectedItems){
  const text=await first.locator('.match-item[data-detail-id="'+item.detail_id+'"]').textContent();
  for(const f of item.numeric_facts.filter(f=>['activation_probability','activation_limit'].includes(f.metric)))assert.ok(text.includes(f.value+(f.metric==='activation_probability'?'%':'回')));
  if(item.unlock_star!=null)assert.ok(text.includes('特訓 '+item.unlock_star));
  if(item.activation_condition||item.activation_condition_v2||item.activation_condition_v3)assert.ok(text.includes('発動条件：'));
 }
 await first.locator('.detail-toggle').click();
 assert.equal(await first.locator('.card-detail').evaluate(e=>e.firstElementChild.className),'performance');
 assert.ok(await first.locator('.matched-effect').count()>0);
 await perf.locator('#more').click();
 assert.equal(await first.locator('.match-details').evaluate(e=>e.open),true,'append preserves expanded match reasons');
 console.log('pending performance URL, all matching values/conditions/probabilities/limits/unlocks and information order PASS');
 await perf.close();

 const duplicate=detail.cards.find(c=>c.items.some(i=>(i.numeric_facts??[]).some(f=>f.metric==='appeal'&&(i.effect_details?.effects??[]).some(e=>e.scope==='base'&&e.metric==='appeal'&&e.value===f.value&&(f.targets??[f.target]).length===e.targets.length&&(f.targets??[f.target]).every(t=>e.targets.includes(t))))));
 const duplicateCard=basic.cards.find(c=>c.card_id===duplicate.card_id),dedup=await pageFor();
 await dedup.goto(base+'?'+new URLSearchParams({q:duplicateCard.card_title}),{waitUntil:'networkidle'});
 const duplicateRow=dedup.locator('.card[data-card-id="'+duplicate.card_id+'"]');await duplicateRow.locator('.detail-toggle').click();
 for(const item of duplicate.items){
  for(const fact of (item.numeric_facts??[]).filter(f=>f.metric==='appeal')){
   const same=(item.effect_details?.effects??[]).some(e=>e.scope==='base'&&e.metric==='appeal'&&e.value===fact.value&&!e.maximum&&e.minimum==null&&(fact.targets??[fact.target]).length===e.targets.length&&(fact.targets??[fact.target]).every(t=>e.targets.includes(t)));
   if(same){
    const row=duplicateRow.locator('.skill-item[data-detail-id="'+item.detail_id+'"]');
    assert.ok(await row.locator('.effect-facts').count()>0);
    assert.equal((await row.locator('p.skill-values').allTextContents()).some(t=>t==='参考数値：'+(fact.targets??[fact.target]).join(' & ')+' '+fact.value+'倍'),false);
   }
  }
 }
 await dedup.close();
 const draft=await pageFor({viewport:{width:390,height:844}}),releaseDraft=await holdDetails(draft);
 await draft.goto(base,{waitUntil:'domcontentloaded'});await draft.locator('.card').first().waitFor();
 await draft.locator('#open-filters').click();await draft.locator('#advanced-filters>summary').click();await draft.locator('#from-year').selectOption('2025');
 assert.equal(await draft.locator('#count').textContent(),basic.cards.length+' / '+basic.cards.length+' 件');
 releaseDraft();await loaded(draft);
 assert.equal(await draft.locator('#count').textContent(),basic.cards.length+' / '+basic.cards.length+' 件','detail arrival cannot apply the draft to visible results');
 assert.equal(await draft.locator('#from-year').inputValue(),'2025');
 const dateCount=basic.cards.filter(c=>c.first_implemented_on>='2025-01-01').length;
 assert.ok((await draft.locator('#draft-count').textContent()).includes(dateCount+'件'));
 await draft.locator('#cancel-filters').click();await draft.locator('#filter-dialog').waitFor({state:'hidden'});
 assert.equal(new URL(draft.url()).searchParams.has('from'),false);
 assert.equal(await draft.locator('#count').textContent(),basic.cards.length+' / '+basic.cards.length+' 件');
 await draft.close();
 console.log('equivalent numeric fact deduplication and late detail arrival during cancellable draft PASS');

 const missing=basic.cards.find(c=>!detail.cards.some(d=>d.card_id===c.card_id));
 const unrecorded=await pageFor();
 await unrecorded.goto(base+'?'+new URLSearchParams({q:missing.card_title}),{waitUntil:'networkidle'});
 assert.ok((await unrecorded.locator('.card[data-card-id="'+missing.card_id+'"] .detail-status').textContent()).includes('詳細未収録'));
 await unrecorded.close();
 const failed=await pageFor();await failed.route('**/details/*/details.json',route=>route.fulfill({status:503,body:'unavailable'}));
 await failed.goto(base,{waitUntil:'networkidle'});
 assert.equal(await failed.locator('#count').textContent(),basic.cards.length+' / '+basic.cards.length+' 件');
 assert.ok((await failed.locator('#detail-coverage').textContent()).includes('基本情報の検索は利用できます'));
 await failed.goto(base+'?'+query,{waitUntil:'networkidle'});
 assert.equal(await failed.locator('#count').textContent(),'条件を適用できません');
 assert.equal(await failed.locator('.card').count(),0);
 assert.equal(new URL(failed.url()).search.slice(1),query);
 await failed.locator('#filter-issues button').first().click();
 assert.equal(await failed.locator('#count').textContent(),basic.cards.length+' / '+basic.cards.length+' 件');
 await failed.close();
 console.log('unrecorded list indication, detail failure preserves conditions and basic search recovery PASS');
 assert.deepEqual(errors,[]);
}finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
