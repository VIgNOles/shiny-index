import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
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
  res.setHeader('Content-Type',ext==='.html'?'text/html; charset=utf-8':ext==='.css'?'text/css':ext==='.mjs'?'text/javascript':ext==='.json'?'application/json':'application/octet-stream');
  res.end(data);
 }catch(e){res.writeHead(404);res.end(String(e));}
});
if(server)await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
let browser;
try{
 const launch=process.env.UI_BROWSER_PATH?{executablePath:process.env.UI_BROWSER_PATH}:{};
 browser=await chromium.launch({headless:true,...launch});
 const url=publicUrl??'http://127.0.0.1:'+server.address().port+'/';
 for(const [label,viewport] of [['desktop',{width:1280,height:800}],['mobile',{width:390,height:844}],['mobile-narrow',{width:320,height:720}]]){
  const page=await browser.newPage({viewport,...(label.startsWith('mobile')?{isMobile:true,hasTouch:true}:{})});
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(url,{waitUntil:'networkidle'});
  const count=()=>page.locator('#count').textContent();
  assert.equal(await count(),total+' / '+total+' 件');
  const uiV2=await page.locator('#coverage-details').count()>0;
  if(uiV2){
   assert.equal(await page.locator('#count').getAttribute('role'),'status');
   if(label.startsWith('mobile'))assert.ok((await page.locator('#q').boundingBox()).y<450);
  }
  assert.match(await page.locator('#version').textContent(),new RegExp(latest.dataset_version));
  assert.equal(await page.locator('#downloads a').count(),6);
  assert.equal(await page.getByRole('checkbox',{name:'P',exact:true}).count(),1);
  if(label==='desktop'){
   const summary=page.locator('#advanced-filters > summary');
   await summary.focus();await page.keyboard.press('Enter');
   assert.equal(await page.locator('#advanced-filters').evaluate(el=>el.open),true);
   await page.keyboard.press('Enter');
   assert.equal(await page.locator('#advanced-filters').evaluate(el=>el.open),false);
  }
  assert.ok(await page.locator('.card').first().locator('.sources a').count()>=1);
  assert.match(await page.locator('.card').first().textContent(),/確認状態：/);
  assert.match(await page.locator('#coverage').textContent(),new RegExp('P '+doc.coverage.by_kind.P+'件'));
  if(uiV2){
   await page.locator('#coverage-details > summary').click();
   assert.equal(await page.locator('#coverage-details').evaluate(el=>el.open),true);
   await page.locator('#coverage-details > summary').click();
  }
  const noUnit=cards.find(c=>!c.unit_name);
  if(noUnit){
   assert.match(await page.locator('#coverage').textContent(),/ユニット欄空欄/);
   await page.locator('#q').fill(noUnit.idol_name);
   assert.match(await page.locator('.card').first().textContent(),/ユニット欄空欄/);
   await page.locator('#q').fill('');
  }
  assert.equal(await page.locator('.card').count(),100);
  await page.locator('#more').click();
  assert.equal(await page.locator('.card').count(),200);
  if(uiV2){
   const wikiBox=await page.locator('.card-action a').first().boundingBox();
   assert.ok(wikiBox.width>=24&&wikiBox.height>=24);
  }
  await page.locator('input[name="card_kind"][value="P"]').check();
  assert.equal(await count(),doc.coverage.by_kind.P+' / '+total+' 件');
  await page.locator('input[name="card_kind"][value="S"]').check();
  assert.equal(await count(),total+' / '+total+' 件');
  await page.locator('input[name="rarity"][value="SSR"]').check();
  const ssr=cards.filter(c=>c.rarity==='SSR').length;
  assert.equal(await count(),ssr+' / '+total+' 件');
  assert.match(await page.locator('#active-filters').textContent(),/P・S/);
  await page.locator('#advanced-filters > summary').click();
  await page.locator('#advanced-groups details').first().locator('summary').click();
  await page.locator('input[name="idol_name"]').first().check();
  assert.match(page.url(),/idol_name=/);
  await page.locator('#sort').selectOption('card_title');
  await page.locator('#direction').selectOption('asc');
  assert.match(page.url(),/sort=card_title/);
  await page.reload({waitUntil:'networkidle'});
  assert.equal(await page.locator('#sort').inputValue(),'card_title');
  assert.equal(await page.locator('input[name="card_kind"][value="P"]').isChecked(),true);
  await page.locator('#reset').click();
  assert.equal(await count(),total+' / '+total+' 件');
  assert.equal(await page.locator('#active-filters').textContent(),'絞り込み条件なし');
  assert.equal(new URL(page.url()).search,'');
  await page.locator('#q').fill('検索結果が存在しない文字列987654321');
  assert.equal(await count(),'0 / '+total+' 件');
  assert.match(await page.locator('#cards').textContent(),/条件に一致するカードはありません/);
  if(uiV2){
   await page.locator('.empty-state button').click();
   assert.equal(await count(),total+' / '+total+' 件');
  }
  const withoutWiki=cards.find(c=>!c.wiki_url);
  if(withoutWiki){
   await page.locator('#q').fill(withoutWiki.card_title);
   const noPageCard=page.locator('.card').filter({hasText:'Wiki個別ページ未確認（一覧に収録）'}).first();
   assert.ok(await noPageCard.count());
   assert.equal(await noPageCard.getByRole('link',{name:/Wiki個別ページ/}).count(),0);
  }
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  assert.deepEqual(errors,[]);
  await page.close();
  console.log(label+' PASS');
 }
}finally{if(browser)await browser.close();if(server)await new Promise(resolve=>server.close(resolve));}