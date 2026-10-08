import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {mkdir, readFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';

const project=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const root=path.resolve(process.argv[2]??path.join(project,'site'));
const latest=JSON.parse(await readFile(path.join(root,'data/latest.json'),'utf8'));
const doc=JSON.parse(await readFile(path.join(root,'data',latest.dataset_version,'cards.json'),'utf8'));
const cards=doc.cards,total=cards.length;
const publicUrl=process.env.UI_BASE_URL;
const server=publicUrl?null:createServer(async(req,res)=>{
 try{
  const url=new URL(req.url,'http://127.0.0.1');
  const name=decodeURIComponent(url.pathname)==='/'?'index.html':decodeURIComponent(url.pathname).slice(1);
  const file=path.resolve(root,name);
  if(!file.startsWith(root+path.sep))throw Error('invalid path');
  const data=await readFile(file);
  const ext=path.extname(file);
  res.setHeader('Content-Type',ext==='.html'?'text/html; charset=utf-8':
   ext==='.css'?'text/css':ext==='.mjs'?'text/javascript':
   ext==='.json'?'application/json':'application/octet-stream');
  res.end(data);
 }catch(error){res.writeHead(404);res.end(String(error));}
});
if(server)await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
let browser;
try{
 const launch=process.env.UI_BROWSER_PATH?{executablePath:process.env.UI_BROWSER_PATH}:{};
 browser=await chromium.launch({headless:true,...launch});
 const base=publicUrl??'http://127.0.0.1:'+server.address().port+'/';
 for(const [name,viewport] of [
  ['desktop',{width:1280,height:800}],
  ['mobile',{width:390,height:844}],
  ['mobile-narrow',{width:320,height:720}]
 ]){
  const page=await browser.newPage({viewport,...(name.startsWith('mobile')?{isMobile:true,hasTouch:true}:{})});
  const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  const count=()=>page.locator('#count').textContent();
  await page.goto(base,{waitUntil:'networkidle'});
  if(process.env.UI_SCREENSHOT_DIR){
   await mkdir(process.env.UI_SCREENSHOT_DIR,{recursive:true});
   await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,name+'.png'),fullPage:false});
   await page.locator('#results-heading').scrollIntoViewIfNeeded();
   await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,name+'-results.png'),fullPage:false});
  }
  assert.equal(await count(),total+' / '+total+' 件');
  assert.match(await page.locator('#version').textContent(),/ui-v3/);
  assert.equal(await page.locator('#downloads a').count(),6);
  assert.deepEqual(await page.locator('input[name="rarity"]').evaluateAll(items=>items.map(item=>item.value)),
   ['UR','SSR','SR','R','N']);
  assert.deepEqual(await page.locator('#series-shortcuts button').allTextContents(),
   ['トワコレ','キャスコレ','マイコレ','パラコレ','プレコレ','誕生日']);
  assert.equal(await page.locator('.card').count(),100);
  assert.equal(await page.locator('.card-detail').first().isHidden(),true);
  const first=page.locator('.card').first();
  await first.locator('.detail-toggle').click();
  assert.equal(await first.locator('.detail-toggle').getAttribute('aria-expanded'),'true');
  assert.equal(await first.locator('.card-detail').isVisible(),true);
  await first.locator('.detail-toggle').focus();
  await page.keyboard.press('Enter');
  assert.equal(await first.locator('.card-detail').isHidden(),true);
  await page.keyboard.press('Space');
  assert.equal(await first.locator('.card-detail').isVisible(),true);
  assert.equal(await first.locator('.card-sources').evaluate(el=>el.open),false);
  await first.locator('.card-sources summary').click();
  assert.ok(await first.locator('.card-sources a').count()>0);
  await page.locator('#more').click();
  assert.equal(await page.locator('.card').count(),200);
  assert.equal(await page.locator('.card-detail').first().isVisible(),true);
  await page.locator('#reset').click();

  const twilights=cards.filter(card=>card.series_ids.includes('twilights')).length;
  const quick=page.locator('[data-series-shortcut="twilights"]');
  await quick.click();
  assert.equal(await count(),twilights+' / '+total+' 件');
  assert.equal(new URL(page.url()).searchParams.get('series_ids'),'twilights');
  await page.reload({waitUntil:'networkidle'});
  assert.equal(await quick.getAttribute('aria-pressed'),'true');
  await quick.click();
  assert.equal(await count(),total+' / '+total+' 件');
  await page.goBack({waitUntil:'networkidle'});
  assert.equal(await count(),twilights+' / '+total+' 件');
  assert.equal(await quick.getAttribute('aria-pressed'),'true');
  const downloadWait=page.waitForEvent('download');
  await page.locator('#export').click();
  const download=await downloadWait;
  assert.equal(download.suggestedFilename(),'cards-'+latest.dataset_version+'-search.csv');
  const csvText=await readFile(await download.path(),'utf8');
  assert.equal(csvText.split('\r\n').length,twilights+1);
  await page.goForward({waitUntil:'networkidle'});
  assert.equal(await count(),total+' / '+total+' 件');

  if(!await page.locator('#advanced-filters').evaluate(el=>el.open))await page.locator('#advanced-filters > summary').click();
  if(!await page.locator('#people-filter').evaluate(el=>el.open))await page.locator('#people-filter > summary').click();
  const unit=page.locator('input[data-person-unit="unit_1"]');
  await unit.check();
  const unitCards=cards.filter(card=>card.unit_id==='unit_1').length;
  assert.equal(await count(),unitCards+' / '+total+' 件');
  assert.equal(new URL(page.url()).searchParams.get('person'),'unit:unit_1');
  const group=page.locator('.people-unit').filter({has:unit});
  await group.locator('.people-unit-header button').click();
  const child=group.locator('input[data-person-idol="idol_1"]');
  assert.equal(await child.isChecked(),true);
  await child.uncheck();
  assert.equal(await unit.evaluate(el=>el.indeterminate),true);
  assert.match(await group.locator('.people-unit-state').textContent(),/一部選択/);
  assert.equal(new URL(page.url()).searchParams.has('person'),true);
  await page.locator('#reset').click();
  const legacy=new URLSearchParams({unit_name:'イルミネーションスターズ',idol_name:'月岡恋鐘'});
  await page.goto(base+'?'+legacy,{waitUntil:'networkidle'});
  assert.equal(await count(),'0 / '+total+' 件');
  assert.match(await page.locator('#active-filters').textContent(),/旧条件/);

  await page.goto(base,{waitUntil:'networkidle'});
  await page.locator('#advanced-filters > summary').click();
  await page.locator('#from-year').selectOption('2024');
  await page.locator('#from-month').selectOption('02');
  await page.locator('#to-year').selectOption('2024');
  await page.locator('#to-month').selectOption('02');
  assert.equal(new URL(page.url()).searchParams.has('from'),false);
  await page.locator('#date-apply').click();
  const feb=cards.filter(card=>card.first_implemented_on?.startsWith('2024-02')).length;
  assert.equal(await count(),feb+' / '+total+' 件');
  assert.equal(new URL(page.url()).searchParams.get('from'),'2024-02');
  assert.equal(new URL(page.url()).searchParams.get('to'),'2024-02');
  assert.equal(await page.locator('#from-native').inputValue(),'');
  assert.match(await page.locator('#date-hint').textContent(),/実装日未確認/);
  assert.equal(await page.locator('#from-day option[value="29"]').count(),1);
  await page.locator('#from-year').selectOption('2025');
  await page.locator('#date-apply').click();
  assert.equal(await page.locator('#date-error').isVisible(),true);
  assert.equal(new URL(page.url()).searchParams.get('from'),'2024-02');
  await page.locator('#reset').click();
  if(!await page.locator('#advanced-filters').evaluate(el=>el.open))await page.locator('#advanced-filters > summary').click();
  await page.locator('#from-native').fill('2024-02-29');
  assert.equal(await page.locator('#from-day').inputValue(),'29');
  await page.locator('#date-apply').click();
  assert.equal(new URL(page.url()).searchParams.get('from'),'2024-02-29');
  await page.locator('#from-year').selectOption('2025');
  assert.equal(await page.locator('#from-day option[value="29"]').count(),0);
  await page.locator('#reset').click();

  await page.locator('#sort').selectOption('rarity_high');
  assert.equal(await page.locator('.card .badge').first().textContent(),'S / UR');
  await page.locator('#sort').selectOption('unit_official');
  assert.equal(await page.locator('.card .card-person').first().textContent(),'櫻木真乃');
  await page.locator('#reset').click();
  await page.locator('#q').fill('一致しない文字列987654321');
  assert.equal(await count(),'0 / '+total+' 件');
  await page.locator('.empty-state button').click();
  assert.equal(await count(),total+' / '+total+' 件');

  const noWiki=cards.find(card=>!card.wiki_url);
  await page.locator('#q').fill(noWiki.card_title);
  const noPage=page.locator('.card').filter({hasText:noWiki.idol_name}).first();
  await noPage.locator('.detail-toggle').click();
  assert.equal(await noPage.locator('.card-action a').count(),0);
  assert.match(await noPage.locator('.card-action').textContent(),/個別ページ未確認/);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  assert.deepEqual(errors,[]);
  await page.close();
  console.log(name+' PASS');
 }
}finally{
 if(browser)await browser.close();
 if(server)await new Promise(resolve=>server.close(resolve));
}