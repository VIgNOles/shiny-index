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
const publicUrl=process.env.UI_BASE_URL||undefined;
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
  const spacing=await performance.evaluate(node=>({noteBottom:node.querySelector('.detail-note').getBoundingClientRect().bottom,summaryTop:node.querySelector('summary').getBoundingClientRect().top}));
  assert.ok(spacing.summaryTop>=spacing.noteBottom+4,'Skill summary overlaps detail note: '+JSON.stringify(spacing));
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
  if(Number((process.env.UI_EXPECTED_VERSION??'').match(/^ui-v(\d+)/)?.[1])>=8){
   const memory=details.cards.find(card=>card.items.some(item=>item.memory_link_present&&item.memory_charge_present&&item.memory_charge_facts?.length));
   assert.ok(memory,'Expected an acquired memory appeal with separate Link and charge effects');
   const baseCard=cards.find(card=>card.card_id===memory.card_id);
   await page.locator('#q').fill(baseCard.card_title+' '+baseCard.idol_name);
   assert.equal(await page.locator('#count').textContent(),'1 / '+total+' 件');
   await page.locator('.detail-toggle').click();
   const group=page.locator('.performance summary').filter({hasText:'思い出アピール'});
   await group.click();
   assert.ok(await page.locator('.memory-link').count()>0);assert.ok(await page.locator('.memory-charge').count()>0);
   assert.ok((await page.locator('.memory-charge').first().textContent()).includes('倍'));
   if(process.env.UI_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,name+'-memory.png')});
   await page.locator('#reset').click();
  }
  if(Number((process.env.UI_EXPECTED_VERSION??'').match(/^ui-v(\d+)/)?.[1])>=8){
   const rangeCard=details.cards.find(card=>card.items.some(item=>item.memory_link_facts?.some(f=>f.metric==='appeal_range')));
   assert.ok(rangeCard,'Expected a saved variable memory Link appeal');
   const baseCard=cards.find(card=>card.card_id===rangeCard.card_id);
   await page.locator('#q').fill(baseCard.card_title+' '+baseCard.idol_name);
   await page.locator('#skill-kind').selectOption('memory_appeal');
   await page.locator('#skill-q').fill('Link Vocal 0.4~2倍');
   assert.equal(await page.locator('#count').textContent(),'1 / '+total+' 件');
   await page.locator('.detail-toggle').click();await page.locator('.performance summary').filter({hasText:'思い出アピール'}).click();
   assert.ok((await page.locator('.memory-link').first().textContent()).includes('0.4～2倍（条件未構造化）'));
   if(process.env.UI_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,name+'-memory-range.png')});
   await page.locator('input[name="mechanic"][value="link"]').check();assert.equal(await page.locator('#count').textContent(),'0 / '+total+' 件');
   await page.locator('#reset').click();
  }
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
  if(details.cards.some(card=>card.items.some(item=>item.generation_origin_kind==='mb_live'))){
   await page.locator('#skill-q').fill('[MB]Could Be++');
   await page.locator('#skill-kind').selectOption('generated_live');
   await page.locator('input[name="mechanic"][value="change"]').check();
   assert.equal(await page.locator('#count').textContent(),'1 / '+total+' 件');
   await page.locator('.detail-toggle').click();
   await page.locator('.performance summary').filter({hasText:'生成ライブスキル'}).click();
   assert.ok((await page.locator('.performance').textContent()).includes('[MB]Could Be(2/5)'));
   await page.locator('#reset').click();
  }
  if(details.cards.some(card=>card.items.some(item=>item.random_effect_options?.length))&&process.env.UI_EXPECTED_VERSION==='ui-v7'){
   await page.locator('#skill-q').fill('Find M Trick ランダム 200%');
   await page.locator('#skill-kind').selectOption('panel_live');
   await page.locator('input[name="mechanic"][value="plus"]').check();
   assert.equal(await page.locator('#count').textContent(),'1 / '+total+' 件');
   await page.locator('.detail-toggle').click();
   await page.locator('.performance summary').filter({hasText:'パネルのライブスキル'}).click();
   assert.ok((await page.locator('.performance').textContent()).includes('ランダム効果の候補（確率未収録）'));
   if(process.env.UI_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,name+'-random.png')});
   await page.locator('#reset').click();
  }
  const cheer=details.cards.find(card=>card.card_id==='ef2aca8d-9d14-48a0-8669-3d44b15c62d6');
  if(cheer){
   const baseCard=cards.find(card=>card.card_id===cheer.card_id);
   await page.locator('#q').fill(baseCard.card_title+' '+baseCard.idol_name);
   await page.locator('#skill-kind').selectOption('cap_increase');
   assert.equal(await page.locator('#count').textContent(),'1 / '+total+' 件');
   await page.locator('.detail-toggle').click();
   await page.locator('.performance summary').filter({hasText:'上限UP'}).click();
   assert.ok((await page.locator('.performance').textContent()).includes('Vocal / Dance / Visual 上限 +25'));
   if(process.env.UI_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,name+'-cheer-cap.png')});
   await page.locator('#reset').click();
  }
  const mixedAbilities=details.cards.find(card=>card.card_id==='b986cf13-2752-47e1-ae42-aa43b76b3e1e');
  if(mixedAbilities){
   const baseCard=cards.find(card=>card.card_id===mixedAbilities.card_id);
   await page.locator('#q').fill(baseCard.card_title+' '+baseCard.idol_name);
   await page.locator('#skill-kind').selectOption('unique_ability');
   assert.equal(await page.locator('#count').textContent(),'1 / '+total+' 件');
   assert.equal(mixedAbilities.items.filter(item=>item.kind==='unique_ability').length,2);
   await page.locator('.detail-toggle').click();
   await page.locator('.performance summary').filter({hasText:'固有アビリティ'}).click();
   const rendered=await page.locator('.performance').textContent();
   assert.ok(rendered.includes('基礎能力値UP(+3%)')&&rendered.includes('芹沢 あさひとの約束'));
   if(process.env.UI_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,name+'-mixed-abilities.png')});
   await page.locator('#reset').click();
  }
  const adjustedSupport=details.cards.find(card=>card.card_id==='8703c650-e57a-4eb6-88db-37099c2c1d93');
  if(adjustedSupport){
   const baseCard=cards.find(card=>card.card_id===adjustedSupport.card_id);
   await page.locator('#q').fill(baseCard.card_title+' '+baseCard.idol_name);
   await page.locator('#skill-kind').selectOption('support_skill');
   await page.locator('#skill-q').fill('ビジュアルマスタリーVi');
   assert.equal(await page.locator('#count').textContent(),'1 / '+total+' 件');
   await page.locator('.detail-toggle').click();
   await page.locator('.performance summary').filter({hasText:'サポートスキル'}).click();
   const rendered=await page.locator('.performance').textContent();
   assert.ok(rendered.includes('ビジュアルマスタリーVi')&&!rendered.includes('ダンスマスタリーDa'));
   if(process.env.UI_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,name+'-current-support.png')});
   await page.locator('#skill-q').fill('ダンスマスタリーDa');
   assert.equal(await page.locator('#count').textContent(),'0 / '+total+' 件');
   await page.locator('#reset').click();
  }
  const historyAppeal=details.cards.find(card=>card.card_id==='1cb8b247-2c8c-4da9-8dab-afc7e2f8e472');
  if(historyAppeal){
   const baseCard=cards.find(card=>card.card_id===historyAppeal.card_id);
   await page.locator('#q').fill(baseCard.card_title+' '+baseCard.idol_name);
   await page.locator('#skill-kind').selectOption('panel_live');
   await page.locator('#skill-q').fill('最大6.5倍');
   assert.equal(await page.locator('#count').textContent(),'1 / '+total+' 件');
   await page.locator('.detail-toggle').click();
   await page.locator('.performance summary').filter({hasText:'パネルのライブスキル'}).click();
   assert.ok((await page.locator('.performance').textContent()).includes('Vocal 最大6.5倍（条件未構造化）'));
   if(process.env.UI_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,name+'-history-appeal.png')});
   assert.ok(!JSON.stringify(historyAppeal).includes('history_appeal_table_private'));
   await page.locator('#reset').click();
  }
  const scene=details.cards.find(card=>card.card_id==='be7cb223-2d49-4d67-8f0d-bdbb86893055');
  if(scene){
   const baseCard=cards.find(card=>card.card_id===scene.card_id);
   await page.locator('#q').fill(baseCard.card_title+' '+baseCard.idol_name);
   await page.locator('#skill-kind').selectOption('generated_live');
   await page.locator('#skill-q').fill('[MB]Scene With You+++');
   assert.equal(await page.locator('#count').textContent(),'1 / '+total+' 件');
   await page.locator('.detail-toggle').click();
   await page.locator('.performance summary').filter({hasText:'生成ライブスキル'}).click();
   assert.ok((await page.locator('.performance').textContent()).includes('生成元 [MB]Scene With You++(4/5)'));
   assert.ok(!(await page.locator('.performance').textContent()).includes('*1'));
   await page.locator('#reset').click();
  }
  const shared=details.cards.find(card=>card.card_id==='34f1b963-2bbc-4ef3-a863-43b3817dabab');
  if(shared&&Number((process.env.UI_EXPECTED_VERSION??'').match(/^ui-v(\d+)/)?.[1])>=9){
   const baseCard=cards.find(card=>card.card_id===shared.card_id);
   await page.locator('#q').fill(baseCard.card_title+' '+baseCard.idol_name);
   await page.locator('#skill-kind').selectOption('generated_live');
   await page.locator('#skill-q').fill('new or …+(☆4)');
   await page.locator('input[name="mechanic"][value="change"]').check();
   assert.equal(await page.locator('#count').textContent(),'1 / '+total+' 件');
   await page.locator('.detail-toggle').click();
   await page.locator('.performance summary').filter({hasText:'生成ライブスキル'}).click();
   assert.ok((await page.locator('.performance').textContent()).includes('生成元 new or … / new or …+(☆4)'));
   if(process.env.UI_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,name+'-shared-generation.png')});
   await page.locator('#reset').click();
  }
  const kite=details.cards.find(card=>card.card_id==='cd191d49-a396-4b8d-864c-37cc36d9c29d');
  if(kite){
   const baseCard=cards.find(card=>card.card_id===kite.card_id);
   await page.locator('#q').fill(baseCard.card_title+' '+baseCard.idol_name);
   await page.locator('#skill-kind').selectOption('mb_live');
   await page.locator('#skill-q').fill('ランダム 100%');
   await page.locator('input[name="mechanic"][value="plus"]').check();
   assert.equal(await page.locator('#count').textContent(),'1 / '+total+' 件');
   await page.locator('.detail-toggle').click();
   const mbSection=page.locator('.performance details').filter({has:page.locator('summary',{hasText:'MBライブスキル'})});
   await mbSection.locator('summary').click();
   const mbText=await mbSection.textContent();
   assert.ok(mbText.includes('Vocal 100% UP [5ターン]'));
   assert.ok(mbText.includes('Vocal 140% UP [5ターン]'));
   assert.ok(!mbText.includes('Vocal 10% UP [5ターン]'));
   if(process.env.UI_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,name+'-mb-random.png')});
   await page.locator('#skill-kind').selectOption('panel_live');
   assert.equal(await page.locator('#count').textContent(),'0 / '+total+' 件');
   await page.locator('#skill-q').fill('ランダム 10%');
   assert.equal(await page.locator('#count').textContent(),'1 / '+total+' 件');
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
