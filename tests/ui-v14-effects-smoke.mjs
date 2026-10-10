import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {chromium} from 'playwright';
const root=path.resolve(process.argv[2]??'site');
const pointer=JSON.parse(await readFile(path.join(root,'details/latest.json'),'utf8'));
const doc=JSON.parse(await readFile(path.join(root,'details',pointer.detail_version,'details.json'),'utf8'));
const output=process.env.UI_SCREENSHOT_DIR;
if(output)await mkdir(output,{recursive:true});
const server=process.env.UI_BASE_URL?null:createServer(async(req,res)=>{
 try{const url=new URL(req.url,'http://127.0.0.1');const file=path.resolve(root,url.pathname==='/'?'index.html':decodeURIComponent(url.pathname).slice(1));
 if(!file.startsWith(root+path.sep))throw Error('path');
 res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.mjs':'text/javascript','.css':'text/css','.json':'application/json'})[path.extname(file)]??'application/octet-stream');res.end(await readFile(file));
 }catch(e){res.writeHead(404);res.end(String(e));}
});
if(server)await new Promise(r=>server.listen(0,'127.0.0.1',r));
const base=process.env.UI_BASE_URL??'http://127.0.0.1:'+server.address().port+'/';
const browser=await chromium.launch({headless:true,executablePath:process.env.UI_BROWSER_PATH});
try{
 for(const width of [1280,390,320]){
  const page=await browser.newPage({viewport:{width,height:900},...(width<500?{isMobile:true,hasTouch:true}:{})});const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base,{waitUntil:'networkidle'});assert.equal(await page.evaluate(()=>window.UI_VERSION),process.env.UI_EXPECTED_VERSION??'ui-v14');
  await page.locator('#skill-filters > summary').click();
  assert.ok(await page.locator('#effect-type').isVisible());
  assert.equal(await page.locator('#effect-type').getAttribute('id'),'effect-type');
  const cases=[['support_recovery','体力',''],['support_cost_down','体力',''],['rate_up','Dance','5'],['appeal_boost','アピール値',''],['appeal','Vocal','']];
  if(['ui-v15','ui-v16'].includes(process.env.UI_EXPECTED_VERSION))cases.push(['mental_recovery','メンタル',''],['memory_gauge_gain','思い出ゲージ',''],['rate_up','パッシブスキル発動率','3'],['passive_boost','パッシブスキル','3'],['refrain','過去のアピール',''],['exchange_count_up','交換数','']);
  for(const [metric,target,turns] of cases){
   await page.locator('#reset').click();
   if(!await page.locator('#skill-filters').evaluate(n=>n.open))await page.locator('#skill-filters > summary').click();
   await page.locator('#effect-type').selectOption(metric);await page.locator('#effect-target').selectOption(target);await page.locator('#effect-turns').selectOption(turns);
   const expected=doc.cards.filter(c=>c.items.some(i=>i.effect_details?.effects.some(e=>e.metric===metric&&e.targets.includes(target)&&(!turns||e.turns>=Number(turns))))).length;
   assert.ok(expected>0);assert.equal(await page.locator('#count').textContent(),expected+' / 1466 件');
   const url=page.url();assert.equal(new URL(url).searchParams.get('effect_target'),target);
   await page.reload({waitUntil:'networkidle'});assert.equal(await page.locator('#effect-type').inputValue(),metric);assert.equal(await page.locator('#effect-turns').inputValue(),turns);
   await page.locator('.detail-toggle').first().click();
   const match=page.locator('.matched-effect').first();assert.ok(await match.isVisible());await match.scrollIntoViewIfNeeded();
   assert.ok((await match.textContent()).includes(target));
   if(turns)assert.ok(/\[\d+ターン\]/.test(await match.textContent()));
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   assert.ok(!(await match.textContent()).includes('undefined'));
   if(output&&['mental_recovery','refrain'].includes(metric))await page.screenshot({path:path.join(output,width+'-'+metric+'.png')});
  }
  await page.locator('#reset').click();assert.equal(await page.locator('#effect-type').inputValue(),'');assert.equal(await page.locator('#effect-target').inputValue(),'');
  await page.locator('#effect-type').selectOption('support_bond');await page.locator('#effect-target').selectOption('絆');await page.locator('#skill-q').fill('プロデュース開始時 スキルLv×5');
  assert.ok(Number((await page.locator('#count').textContent()).split(' / ')[0])>0);
  await page.locator('.detail-toggle').first().click();assert.ok((await page.locator('.performance').first().textContent()).includes('取得表の最大スキルLv'));
  if(['ui-v15','ui-v16'].includes(process.env.UI_EXPECTED_VERSION)){
   await page.locator('#reset').click();await page.locator('#effect-type').selectOption('rate_up');await page.locator('#effect-target').selectOption('Dance');await page.locator('#skill-q').fill('2ターン以前');
   assert.ok(Number((await page.locator('#count').textContent()).split(' / ')[0])>0);
   await page.locator('.detail-toggle').first().click();const m=page.locator('.matched-effect').first();await m.scrollIntoViewIfNeeded();
   assert.ok((await m.textContent()).includes('発動条件：'));assert.ok((await m.textContent()).includes('2ターン以前'));
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   if(output)await page.screenshot({path:path.join(output,width+'-live-condition.png')});
  }
  await page.locator('#reset').click();await page.locator('#effect-type').selectOption('interest');
  await page.goBack({waitUntil:'networkidle'});assert.equal(await page.locator('#effect-type').inputValue(),'');await page.goForward({waitUntil:'networkidle'});assert.equal(await page.locator('#effect-type').inputValue(),'interest');
  assert.deepEqual(errors,[]);await page.close();console.log(width+' effects PASS');
 }
}finally{await browser.close();if(server)await new Promise(r=>server.close(r));}
