import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {chromium} from 'playwright';

const root=path.resolve(process.argv[2]??'site'),output=process.env.UI_AUDIT_DIR;
const read=async name=>JSON.parse(await readFile(path.join(root,name),'utf8'));
const basePointer=await read('data/latest.json'),detailPointer=await read('details/latest.json');
const cards=(await read(`data/${basePointer.dataset_version}/cards.json`)).cards;
const detail=(await read(`details/${detailPointer.detail_version}/details.json`)).cards;
const ids=predicate=>detail.filter(predicate).map(card=>card.card_id);
const setEqual=(actual,expected,message)=>assert.deepEqual([...actual].sort(),[...expected].sort(),message);
// These expectations read raw published fields, independently of every app search function.
const cases=[
 {query:'effect_type=appeal&effect_target=Vocal&effect_scope=link&effect_unit=multiplier&effect_min=3&effect_max=5&unlock_star_max=4',expected:ids(card=>card.items.some(item=>Number.isInteger(item.unlock_star)&&item.unlock_star<=4&&(item.effect_details?.effects??[]).some(e=>e.metric==='appeal'&&e.targets.includes('Vocal')&&e.scope==='link'&&e.unit==='multiplier'&&typeof e.value==='number'&&e.value>=3&&e.value<=5&&!e.maximum&&e.minimum==null&&!e.formula&&!e.unknown&&!e.amount_unknown&&e.perfect_value==null&&!e.per_member&&!e.status_consumption&&!e.restrictions?.scaling)))},
 {query:'effect_type=passive_up&effect_target=Dance&effect_unit=percent&effect_min=100&unlock_star_max=2',expected:ids(card=>card.items.some(item=>item.kind==='panel_passive'&&Number.isInteger(item.unlock_star)&&item.unlock_star<=2&&(item.numeric_facts??[]).some(fact=>fact.metric==='rate'&&fact.direction==='UP'&&(fact.targets??[fact.target]).includes('Dance')&&fact.value>=100)))},
 {query:'effect_type=cap_increase&effect_target=Vocal&effect_unit=points&effect_min=100&unlock_star_max=3',expected:ids(card=>card.items.some(item=>item.kind==='cap_increase'&&Number.isInteger(item.unlock_star)&&item.unlock_star<=3&&item.cap_targets.includes('Vocal')&&item.cap_delta>=100))},
 {query:'trait_idea=vocal&trait_inspiration=vocal&trait_music=singing',expected:ids(card=>card.card_kind==='S'&&card.traits?.idea==='ボーカル'&&['Vo.','Vo'].includes(card.traits?.inspiration)&&card.traits?.music_proficiencies.includes('歌唱力'))}
];
for(const amount of [40,10])cases.push({
 query:`effect_type=random_grant&effect_scope=base&effect_target=Vocal&effect_turns=4&effect_unit=percent&effect_min=${amount}&effect_max=${amount}`,
 expected:ids(card=>card.items.some(item=>(item.effect_details?.effects??[]).some(e=>e.metric==='random_grant'&&e.scope==='base'&&(e.random_pool?.options??[]).some(option=>option.targets.includes('Vocal')&&option.turns>=4&&option.unit==='percent'&&option.value===amount))))
});
const assets=new Set(['index.html','app.mjs','details.mjs','search.mjs','style.css']);
const server=process.env.UI_BASE_URL?null:createServer(async(req,res)=>{
 try{
  const url=new URL(req.url,'http://127.0.0.1'),name=url.pathname==='/'?'index.html':decodeURIComponent(url.pathname).slice(1);
  const source=process.env.UI_SOURCE_WEB&&assets.has(name)?path.resolve('web'):root;
  const file=path.resolve(source,name);if(!file.startsWith(source+path.sep))throw Error('path');
  res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.mjs':'text/javascript','.css':'text/css','.json':'application/json'})[path.extname(file)]??'application/octet-stream');
  const body=await readFile(file);
  res.end(process.env.UI_SOURCE_WEB&&name==='index.html'?body.toString('utf8').replaceAll('__VERSION__',basePointer.dataset_version).replaceAll('__DETAIL_VERSION__',detailPointer.detail_version):body);
 }catch{res.writeHead(404);res.end();}
});
let browser;const report=[];
try{
 if(output)await mkdir(output,{recursive:true});
 if(server)await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const base=process.env.UI_BASE_URL??'http://127.0.0.1:'+server.address().port+'/';
 browser=await chromium.launch({headless:true,executablePath:process.env.UI_BROWSER_PATH});
 for(const width of [1280,390,320]){
  const page=await browser.newPage({viewport:{width,height:900},...(width<500?{isMobile:true,hasTouch:true}:{})}),errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  const go=async query=>{await page.goto(base+'?'+query,{waitUntil:'networkidle'});};
  const count=async n=>{await page.waitForFunction(expected=>document.getElementById('count')?.textContent===expected,`${n} / ${cards.length} 件`);};
  const allIds=async()=>{
   while(await page.locator('#more').isVisible())await page.locator('#more').click();
   return page.locator('.card').evaluateAll(nodes=>nodes.map(node=>node.dataset.cardId));
  };
  try{
   for(const item of cases){
    await go(item.query);await count(item.expected.length);
    assert.equal(await page.evaluate(()=>window.DETAIL_VERSION),detailPointer.detail_version);
    if(process.env.UI_EXPECTED_VERSION)assert.equal(await page.evaluate(()=>window.UI_VERSION),process.env.UI_EXPECTED_VERSION);
    setEqual(await allIds(),item.expected,item.query);
    for(const [key,value] of new URLSearchParams(item.query)){
     const control=page.locator('#'+key.replaceAll('_','-'));
     assert.equal(await control.inputValue(),value,'URL restoration: '+key);
    }
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    if(item.query.startsWith('trait_')){
     assert.equal(await page.locator('#trait-controls').evaluate(e=>!!e.closest('dialog')),false);
    }else if(item.expected.length){
     await page.locator('.detail-toggle').first().click();
     assert.ok(await page.locator('.card').first().locator('.matched-effect').count()>0,'same-effect highlighting');
    }
   }
   // Mobile uses the existing draft transaction for all numeric/scope/training controls.
   await go(cases[0].query);await count(cases[0].expected.length);
   const initial=page.url();
   if(width<900){
   await page.locator('#open-filters').click();await page.locator('#filter-dialog').waitFor({state:'visible'});
   await page.locator('#effect-min').fill('4');await page.locator('#effect-min').dispatchEvent('change');
   assert.equal(await page.locator('#count').textContent(),`${cases[0].expected.length} / ${cards.length} 件`,'draft leaves applied results intact');
   assert.equal(new URL(page.url()).searchParams.get('effect_min'),'3');
   await page.locator('#cancel-filters').click();await page.locator('#filter-dialog').waitFor({state:'hidden'});
   await page.waitForFunction(()=>new URL(location.href).searchParams.get('effect_min')==='3');
   assert.equal(new URL(page.url()).search, new URL(initial).search);
   assert.equal(await page.locator('#effect-min').inputValue(),'3');
   await page.locator('#open-filters').click();await page.locator('#filter-dialog').waitFor({state:'visible'});
   await page.locator('#effect-min').fill('6');await page.locator('#effect-min').dispatchEvent('change');
   await page.waitForFunction(()=>document.getElementById('apply-filters').disabled);
   assert.match(await page.locator('#draft-filter-issues').textContent(),/下限.*上限/);
   await page.locator('#effect-min').fill('4');await page.locator('#effect-min').dispatchEvent('change');
   await page.waitForFunction(()=>!document.getElementById('apply-filters').disabled);
   await page.locator('#apply-filters').click();await page.locator('#filter-dialog').waitFor({state:'hidden'});
   await page.waitForFunction(()=>new URL(location.href).searchParams.get('effect_min')==='4');
   assert.equal(await page.locator('#effect-min').inputValue(),'4');
   await page.goBack({waitUntil:'networkidle'});
   await page.waitForFunction(()=>new URL(location.href).searchParams.get('effect_min')==='3');
   assert.equal(await page.locator('#effect-min').inputValue(),'3');
   }else{
    await page.locator('#effect-min').fill('4');await page.locator('#effect-min').dispatchEvent('change');
    await page.waitForFunction(()=>new URL(location.href).searchParams.get('effect_min')==='4');
    assert.equal(await page.locator('#filter-issues').isVisible(),false);
   }
   if(width===1280){
    await go(cases[0].query);await count(cases[0].expected.length);
    assert.equal(await page.locator('#search-guide').evaluate(e=>e.open),false);
    await page.locator('#search-guide>summary').click();
    assert.equal(await page.locator('#search-guide .search-examples a').count(),7);
    await page.locator('#search-guide .search-examples a').first().click();await page.waitForLoadState('networkidle');
    assert.equal(new URL(page.url()).searchParams.toString(),new URLSearchParams({q:'まどか Hug?'}).toString(),'example replaces all existing conditions');
    await count(1);assert.deepEqual(await allIds(),['94b670b4-7328-4e96-8b9b-ace60917e7df'],'reading example fixed approved card');
    for(const [query,message] of [
     ['effect_min=4',/単位/],
     ['effect_unit=multiplier&effect_min=NaN',/0以上/],
     ['effect_unit=multiplier&effect_min=6&effect_max=3',/下限.*上限/],
     ['effect_scope=unknown',/不明な効果範囲/],
     ['unlock_star_max=5',/0〜4/],
     ['trait_idea=unknown',/不明な育成特性/],
     ['card_kind=P&trait_idea=vocal',/Sカード専用/]
    ]){
     await go(query);assert.equal(await page.locator('#count').textContent(),'条件を適用できません',query);
     assert.match(await page.locator('#filter-issues').textContent(),message,query);
     assert.equal(new URL(page.url()).searchParams.toString(),new URLSearchParams(query).toString());
    }
    // All current unknown/absent training values must stay out of an explicit zero limit.
    await go('unlock_star_max=0');
    const zero=ids(card=>card.items.some(item=>item.unlock_star===0));await count(zero.length);setEqual(await allIds(),zero,'explicit training zero only');
    // Existing Link ownership still permits matching the normal effect on that skill.
    await go('mechanic=link&effect_scope=base&effect_type=appeal&effect_unit=multiplier&effect_min=3');
    assert.notEqual(await page.locator('#count').textContent(),'条件を適用できません');
    assert.ok(await page.locator('.card').count()>0);
   }
   if(output)await page.screenshot({path:path.join(output,`priority67-${width}.png`)});
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);assert.deepEqual(errors,[]);
   report.push({width,status:'pass',independentQueries:cases.map(c=>({query:c.query,count:c.expected.length}))});
   console.log(`${width} numeric/scope/training/traits URL, independent result sets, draft cancel/apply and validation PASS`);
  }finally{await page.close();}
 }
}finally{
 if(browser)await browser.close();
 if(server?.listening)await new Promise(resolve=>server.close(resolve));
 if(output)await writeFile(path.join(output,'priority67.json'),JSON.stringify(report,null,2)+'\n');
}
