import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {chromium} from 'playwright';
import {search,browseOptions} from '../web/search.mjs';
import {detailSearch} from '../web/details.mjs';
const root=path.resolve(process.argv[2]??'site');
const bp=JSON.parse(await readFile(path.join(root,'data/latest.json'),'utf8'));
const dp=JSON.parse(await readFile(path.join(root,'details/latest.json'),'utf8'));
const basic=JSON.parse(await readFile(path.join(root,'data',bp.dataset_version,'cards.json'),'utf8'));
const detail=JSON.parse(await readFile(path.join(root,'details',dp.detail_version,'details.json'),'utf8'));
const map=new Map(detail.cards.map(c=>[c.card_id,c]));
const server=process.env.UI_BASE_URL?null:createServer(async(req,res)=>{
 try{const u=new URL(req.url,'http://localhost'),p=path.resolve(root,u.pathname==='/'?'index.html':decodeURIComponent(u.pathname).slice(1));if(!p.startsWith(root+path.sep))throw Error('path');res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.mjs':'text/javascript','.css':'text/css','.json':'application/json'})[path.extname(p)]??'application/octet-stream');res.end(await readFile(p));}catch{res.writeHead(404);res.end();}
});
if(server)await new Promise(r=>server.listen(0,'127.0.0.1',r));
const base=process.env.UI_BASE_URL??'http://127.0.0.1:'+server.address().port+'/';
const output=process.env.UI_AUDIT_DIR;if(output)await mkdir(output,{recursive:true});
const report={base_version:bp.dataset_version,detail_version:dp.detail_version,ui:process.env.UI_EXPECTED_VERSION??'ui-v26',checks:[],independent_checks:0,option_checks:0};
const browser=await chromium.launch({headless:true,executablePath:process.env.UI_BROWSER_PATH});
try{
 const page=await browser.newPage({viewport:{width:1280,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 const load=async query=>{await page.goto(base+(query?'?'+query:''),{waitUntil:'networkidle'});assert.equal(await page.evaluate(()=>window.UI_VERSION),report.ui);};
 const visibleIds=()=>page.locator('.card').evaluateAll(es=>es.map(e=>e.dataset.cardId));
 const check=async(label,independent=null)=>{
  const params=new URLSearchParams(new URL(page.url()).search),expected=detailSearch(search(basic.cards,params),params,map);
  assert.equal(await page.locator('#count').textContent(),expected.length+' / '+basic.cards.length+' 件',label);
  assert.deepEqual(await visibleIds(),expected.slice(0,100).map(c=>c.card_id),label+' displayed order');
  if(independent){assert.deepEqual([...expected.map(c=>c.card_id)].sort(),independent.map(c=>c.card_id).sort(),label+' independent card set');report.independent_checks++;}
  assert.equal(await page.locator('#filter-issues').isVisible(),false,label);
  report.checks.push({label,query:params.toString(),count:expected.length});
  return expected;
 };
 await load('');
 // Every visible basic choice has an independent set based on exported rows.
 for(const field of ['card_kind','rarity']){
  const values=await page.locator('[name='+field+']').evaluateAll(es=>es.map(e=>e.value));
  for(const value of values){await page.locator('[name='+field+'][value="'+value+'"]').check();await check(field+':'+value,basic.cards.filter(c=>c[field]===value));await page.locator('#reset').click();}
 }
 await page.locator('[name=card_kind][value=P]').check();await page.locator('[name=card_kind][value=S]').check();await page.locator('[name=rarity][value=SSR]').check();await page.locator('[name=rarity][value=UR]').check();await check('P-or-S AND SSR-or-UR',basic.cards.filter(c=>['SSR','UR'].includes(c.rarity)));await page.locator('#reset').click();
 await page.locator('#people-filter>summary').click();
 const units=await page.locator('[data-person-unit]').evaluateAll(es=>es.map(e=>e.dataset.personUnit));
 for(const unit of units){await page.locator('[data-person-unit="'+unit+'"]').check();await check('unit:'+unit,basic.cards.filter(c=>unit==='none'?c.unit_id==null:c.unit_id===unit));await page.locator('#reset').click();}
 for(const [value] of browseOptions){
  const set=basic.cards.filter(c=>['prelude','casting','parallel','twilights','mysongs'].includes(value)?c.series_ids.includes(value):value==='other'?!c.series_ids.some(v=>['prelude','casting','parallel','twilights','mysongs'].includes(v))&&!['limited_gacha','permanent_gacha'].includes(c.acquisition_category):c.acquisition_category===value);
  await page.locator('[data-browse-shortcut='+value+']').click();await check('browse:'+value,set);await page.locator('#reset').click();
 }
 await page.locator('[data-browse-shortcut=twilights]').click();await page.locator('[data-browse-shortcut=permanent_gacha]').click();await page.locator('[name=card_kind][value=P]').check();await check('browse OR combined with card AND',basic.cards.filter(c=>c.card_kind==='P'&&(c.series_ids.includes('twilights')||c.acquisition_category==='permanent_gacha')));await page.locator('#reset').click();
 // All kind/effect choices are exercised through actual controls, then exact engine result and order checked.
 await page.locator('#skill-filters>summary').click();
 const kinds=await page.locator('#skill-kind option').evaluateAll(es=>es.map(e=>e.value));
 for(const kind of kinds){
  await page.locator('#effect-type').selectOption('');await page.locator('#effect-target').selectOption('');await page.locator('#skill-kind').selectOption(kind);await check('kind:'+kind);
  const types=await page.locator('#effect-type option').evaluateAll(es=>es.map(e=>e.value).filter(Boolean));
  for(const type of types){
   await page.locator('#effect-target').selectOption('');await page.locator('#effect-type').selectOption(type);const matches=await check('effect:'+kind+'/'+type);assert.ok(matches.length>0);report.option_checks++;
   const targets=await page.locator('#effect-target option').evaluateAll(es=>es.map(e=>e.value).filter(Boolean));
   for(const target of targets.slice(0,2)){await page.locator('#effect-target').selectOption(target);await check('target:'+kind+'/'+type+'/'+target);report.option_checks++;}
  }
  console.log('kind '+(kind||'all')+': '+report.checks.length+' result sets checked');
 }
 await page.locator('#reset').click();
 const sorts=await page.locator('#sort option').evaluateAll(es=>es.map(e=>e.value));
 for(const sort of sorts){await page.locator('#sort').selectOption(sort);await check('sort:'+sort);}
 await page.locator('#sort').selectOption('date_new');
 while(await page.locator('#more').isVisible())await page.locator('#more').click();
 const all=await visibleIds();assert.equal(all.length,basic.cards.length);assert.equal(new Set(all).size,basic.cards.length);assert.deepEqual(all,search(basic.cards,new URLSearchParams('sort=date_new')).map(c=>c.card_id));
 const links=await page.locator('.card-action a').evaluateAll(es=>es.map(e=>e.href));assert.ok(links.every(u=>u.startsWith('https://wikiwiki.jp/shinycolors/')));assert.equal(links.length,basic.cards.filter(c=>c.wiki_url).length);
 report.full_results=all.length;report.wiki_links=links.length;report.no_page_cards=basic.cards.length-links.length;
 assert.deepEqual(errors,[]);await page.close();
 report.status='pass';console.log(JSON.stringify({status:report.status,checks:report.checks.length,independent:report.independent_checks,kind_effect_target:report.option_checks,full_results:report.full_results,wiki_links:report.wiki_links,no_page_cards:report.no_page_cards}));
}finally{
 await browser.close();if(server)await new Promise(r=>server.close(r));if(output)await writeFile(path.join(output,'search-audit.json'),JSON.stringify(report,null,2)+'\n');
}
