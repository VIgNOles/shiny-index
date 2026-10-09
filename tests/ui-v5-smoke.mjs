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
const dl=JSON.parse(await readFile(path.join(root,'details/latest.json'),'utf8'));
const details=JSON.parse(await readFile(path.join(root,'details',dl.detail_version,'details.json'),'utf8'));
let browser;
try{
 const launch=process.env.UI_BROWSER_PATH?{executablePath:process.env.UI_BROWSER_PATH}:{};
 browser=await chromium.launch({headless:true,...launch});
 const base=publicUrl??'http://127.0.0.1:'+server.address().port+'/';
 for(const [name,viewport] of [['desktop',{width:1280,height:800}],['mobile',{width:390,height:844}],['mobile-narrow',{width:320,height:720}]]){
  const page=await browser.newPage({viewport,...(name.startsWith('mobile')?{isMobile:true,hasTouch:true}:{})});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base,{waitUntil:'networkidle'});
  if(process.env.UI_EXPECTED_VERSION)assert.equal(await page.evaluate(()=>window.UI_VERSION),process.env.UI_EXPECTED_VERSION);
  assert.equal(await page.locator('#count').textContent(),total+' / '+total+' 件');
  assert.ok((await page.locator('#detail-version').textContent()).includes(dl.detail_version));
  assert.equal(await page.locator('#skill-controls').isDisabled(),false);
  await page.locator('#skill-filters summary').click();
  await page.locator('#detail-available').check();
  assert.equal(await page.locator('#count').textContent(),details.cards.length+' / '+total+' 件');
  await page.reload({waitUntil:'networkidle'});
  assert.equal(await page.locator('#detail-available').isChecked(),true);
  await page.locator('#skill-q').fill('切り拓いて・茨');
  await page.locator('#skill-kind').selectOption('mb_live');
  await page.locator('input[name="mechanic"][value="plus"]').check();
  assert.equal(await page.locator('#count').textContent(),'1 / '+total+' 件');
  await page.locator('.detail-toggle').click();
  const performance=page.locator('.performance');
  assert.equal(await performance.locator('summary').filter({hasText:'MBライブスキル'}).count(),1);
  await performance.locator('summary').filter({hasText:'MBライブスキル'}).click();
  assert.ok((await performance.textContent()).includes('MB 2/5'));
  if(process.env.UI_SCREENSHOT_DIR){
   await mkdir(process.env.UI_SCREENSHOT_DIR,{recursive:true});
   await performance.scrollIntoViewIfNeeded();
   await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,name+'-details.png')});
  }
  await page.locator('#skill-kind').selectOption('panel_live');
  assert.equal(await page.locator('#count').textContent(),'0 / '+total+' 件');
  await page.locator('#active-filters button').filter({hasText:'Plus'}).click();
  assert.equal(await page.locator('#count').textContent(),'1 / '+total+' 件');
  await page.locator('#reset').click();
  assert.equal(await page.locator('#count').textContent(),total+' / '+total+' 件');
  const generation=details.cards.find(card=>card.items.some(item=>item.kind==='generated_live'));
  if(generation&&process.env.UI_EXPECTED_VERSION!=='ui-v5'){
   await page.locator('#skill-q').fill('Cherish You++++');
   await page.locator('#skill-kind').selectOption('generated_live');
   await page.locator('input[name="mechanic"][value="change"]').check();
   assert.equal(await page.locator('#count').textContent(),'1 / '+total+' 件');
   await page.locator('.detail-toggle').click();
   const group=page.locator('.performance summary').filter({hasText:'生成ライブスキル'});
   assert.equal(await group.count(),1);await group.click();
   assert.ok((await page.locator('.performance').textContent()).includes('生成 2連目 / 生成元 Cherish You+++'));
   if(process.env.UI_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,name+'-generated.png')});
   await page.locator('#skill-kind').selectOption('panel_live');
   assert.equal(await page.locator('#count').textContent(),'0 / '+total+' 件');
   await page.locator('#reset').click();
  }
  const missing=details.cards.find(card=>card.max_status?.missing_fields?.length);
  if(missing){
   const baseCard=cards.find(card=>card.card_id===missing.card_id);
   await page.locator('#q').fill(baseCard.card_title+' '+baseCard.idol_name);
   assert.equal(await page.locator('#count').textContent(),'1 / '+total+' 件');
   await page.locator('.detail-toggle').click();
   assert.ok((await page.locator('.performance').textContent()).includes('未記載'));
   assert.ok((await page.locator('.performance').textContent()).includes('最大Lv '+missing.max_status.level));
   await page.locator('#reset').click();
  }
  const downloaded=await page.request.get(new URL(await page.locator('#detail-downloads a').first().getAttribute('href'),base).href);
  assert.equal(downloaded.status(),200);
  const payload=await downloaded.json();assert.equal(payload.meta.detail_version,dl.detail_version);
  assert.equal(payload.meta.base_dataset_version,latest.dataset_version);
  assert.equal(payload.coverage.detail_item_count,details.coverage.detail_item_count);
  assert.ok(!JSON.stringify(payload).includes('effect_private'));
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  assert.deepEqual(errors,[]);
  await page.close();console.log(name+' details PASS');
 }
}finally{if(browser)await browser.close();if(server)await new Promise(resolve=>server.close(resolve));}
