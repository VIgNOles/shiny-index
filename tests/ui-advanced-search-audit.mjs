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
const report={base_version:bp.dataset_version,detail_version:dp.detail_version,ui:process.env.UI_EXPECTED_VERSION??'ui-v27',checks:[],independent_checks:0,option_checks:0};
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
 // Every idol, normal tag/acquisition choice and advanced field is operated through its control.
 await page.locator('#people-filter>summary').click();
 const idols=await page.locator('[data-person-idol]').evaluateAll(es=>[...new Set(es.map(e=>e.dataset.personIdol))]);
 for(const idol of idols){await page.locator('[data-person-idol="'+idol+'"]').check();await check('idol:'+idol,basic.cards.filter(c=>c.idol_id===idol));await page.locator('#reset').click();}
 for(const field of ['series_ids','acquisition_category']){
  const group=page.locator('#advanced-groups details').filter({has:page.locator('[name='+field+']')});if(!await group.evaluate(e=>e.open))await group.locator('summary').click();
  const values=await group.locator('[name='+field+']').evaluateAll(es=>es.filter(e=>!e.parentElement.hidden).map(e=>e.value));
  for(const value of values){await group.locator('[name='+field+'][value="'+value+'"]').check();await check(field+':'+value,basic.cards.filter(c=>Array.isArray(c[field])?c[field].includes(value):c[field]===value));await page.locator('#reset').click();}
 }
 await page.locator('#skill-filters>summary').click();
 await page.locator('#skill-kind').selectOption('live');await page.locator('#performance-advanced>summary').click();
 const origins=await page.locator('[name=live_origin]').evaluateAll(es=>es.map(e=>e.value));
 for(const kind of origins){await page.locator('[name=live_origin][value='+kind+']').check();const ids=new Set(detail.cards.filter(c=>c.items.some(i=>i.kind===kind)).map(c=>c.card_id));await check('live origin:'+kind,basic.cards.filter(c=>ids.has(c.card_id)));await page.locator('#reset').click();await page.locator('#skill-kind').selectOption('live');}
 const mechanics=await page.locator('[name=mechanic]').evaluateAll(es=>es.map(e=>e.value));
 for(const mechanic of mechanics){await page.locator('[name=mechanic][value="'+mechanic+'"]').check();const ids=new Set(detail.cards.filter(c=>c.items.some(i=>origins.includes(i.kind)&&i.mechanics?.includes(mechanic))).map(c=>c.card_id));await check('mechanic:'+mechanic,basic.cards.filter(c=>ids.has(c.card_id)));await page.locator('#reset').click();await page.locator('#skill-kind').selectOption('live');}
 await page.locator('[name=mechanic][value=link]').check();await page.locator('[name=mechanic][value=plus]').check();const union=new Set(detail.cards.filter(c=>c.items.some(i=>origins.includes(i.kind)&&i.mechanics?.some(m=>['link','plus'].includes(m)))).map(c=>c.card_id));await check('Link OR Plus',basic.cards.filter(c=>union.has(c.card_id)));await page.locator('#reset').click();
 await page.locator('#skill-kind').selectOption('panel_passive');
 const conditions=await page.locator('#skill-condition option').evaluateAll(es=>es.map(e=>e.value).filter(Boolean));for(const condition of conditions){await page.locator('#skill-condition').selectOption(condition);await check('activation:'+condition);}
 await page.locator('#reset').click();await page.locator('#skill-kind').selectOption('live');
 const recipients=await page.locator('#effect-recipient option').evaluateAll(es=>es.map(e=>e.value).filter(Boolean));for(const recipient of recipients){await page.locator('#effect-recipient').selectOption(recipient);await check('recipient:'+recipient);}
 await page.locator('#reset').click();await page.locator('#skill-kind').selectOption('live');await page.locator('#effect-type').selectOption('rate_up');
 const turns=await page.locator('#effect-turns option').evaluateAll(es=>es.map(e=>e.value).filter(Boolean));for(const turn of turns){await page.locator('#effect-turns').selectOption(turn);await check('turns:'+turn);}
 await page.locator('#reset').click();await page.locator('#advanced-filters>summary').click();await page.locator('#detail-available').check();const detailIds=new Set(detail.cards.map(c=>c.card_id));await check('details available',basic.cards.filter(c=>detailIds.has(c.card_id)));await page.locator('#reset').click();
 await page.locator('#advanced-filters>summary').click();const years=await page.locator('#from-year option').evaluateAll(es=>es.map(e=>e.value).filter(Boolean));for(const year of years){await page.locator('#from-year').selectOption(year);await check('from year:'+year,basic.cards.filter(c=>c.first_implemented_on>=year+'-01-01'));}
 await page.locator('#from-year').selectOption('2025');for(const month of ['01','02','06','12']){await page.locator('#from-month').selectOption(month);await check('from month:2025-'+month,basic.cards.filter(c=>c.first_implemented_on>='2025-'+month+'-01'));}
 for(const query of ['browse=not_a_series','card_kind=X','rarity=XXX','person=idol:does_not_exist','from=2026-02-30','card_kind=S&skill_kind=mb_live','skill_kind=memory_appeal&mechanic=link']){await load(query);assert.equal(await page.locator('#count').textContent(),'条件を適用できません');assert.equal(await page.locator('.card').count(),0);assert.equal(await page.locator('#filter-issues').isVisible(),true);await page.locator('#reset').click();assert.equal(await page.locator('#count').textContent(),'1466 / 1466 件');}
 report.invalid_recovery=7;
 assert.deepEqual(errors,[]);await page.close();report.status='pass';console.log(JSON.stringify({status:report.status,advanced_checks:report.checks.length,independent:report.independent_checks,invalid_recovery:report.invalid_recovery}));
}finally{await browser.close();if(server)await new Promise(r=>server.close(r));if(output)await writeFile(path.join(output,'advanced-audit.json'),JSON.stringify(report,null,2)+'\n');}
