
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {chromium} from 'playwright';
const root=path.resolve(process.argv[2]??'site');
const pointer=JSON.parse(await readFile(path.join(root,'details/latest.json'),'utf8'));
const doc=JSON.parse(await readFile(path.join(root,'details',pointer.detail_version,'details.json'),'utf8'));
const output=process.env.UI_SCREENSHOT_DIR;if(output)await mkdir(output,{recursive:true});
const server=process.env.UI_BASE_URL?null:createServer(async(req,res)=>{
 try{const u=new URL(req.url,'http://127.0.0.1'),p=path.resolve(root,u.pathname==='/'?'index.html':decodeURIComponent(u.pathname).slice(1));
 if(!p.startsWith(root+path.sep))throw Error('path');
 res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.mjs':'text/javascript','.css':'text/css','.json':'application/json'})[path.extname(p)]??'application/octet-stream');res.end(await readFile(p));
 }catch(e){res.writeHead(404);res.end(String(e));}
});
if(server)await new Promise(r=>server.listen(0,'127.0.0.1',r));
const base=process.env.UI_BASE_URL??'http://127.0.0.1:'+server.address().port+'/';
const cases=[
 {q:'song for you',skill_kind:'panel_live',skill_q:'60%UP',effect_target:'Vocal',effect_turns:'4',expectedItems:2},
 {q:'song for you',skill_kind:'mb_live',skill_q:'140%UP',effect_target:'Vocal',effect_turns:'4',expectedItems:2},
 {q:'ウォーターパーク☆リポート',skill_q:'40%UP',effect_target:'Vocal',effect_turns:'4'},
 {q:'ウォーターパーク☆リポート',skill_q:'10%強化',effect_target:'パッシブスキル',effect_turns:'3'},
 {q:'白・架・祝・幻',skill_q:'フレキシブル',effect_target:'フレキシブル',effect_turns:'1'},
 {q:'白・架・祝・幻',skill_q:'リザレクション 30%回復',effect_target:'メンタル',effect_turns:'3'},
 {q:'春へと駈ける',skill_q:'小宮果穂 0.1倍',effect_target:'アピール値',effect_turns:'5'},
 {q:'ROOTS',skill_q:'ランダム効果'},
];
const negative=[
 {q:'song for you',skill_kind:'panel_live',skill_q:'140%UP'},
 {q:'song for you',skill_kind:'mb_live',skill_q:'Vocal 40%UP'},
 {q:'ウォーターパーク☆リポート',effect_target:'Vocal',skill_q:'10%強化'},
 {q:'ウォーターパーク☆リポート',effect_target:'パッシブスキル',effect_turns:'4'},
 {q:'ウォーターパーク☆リポート',effect_target:'交換数',effect_turns:'1'},
 {q:'ROOTS',effect_target:'アピール値'},
 {q:'ROOTS',skill_q:'0.2倍'},
 {q:'白・架・祝・幻',effect_target:'フレキシブル',skill_q:'30%回復'},
 {q:'白・架・祝・幻',effect_target:'フレキシブル',effect_turns:'2'},
 {q:'ウォーターパーク☆リポート',effect_target:'Vocal',effect_recipient:'self'},
];
const browser=await chromium.launch({headless:true,executablePath:process.env.UI_BROWSER_PATH});
try{
 for(const width of [1280,390,320]){
  const page=await browser.newPage({viewport:{width,height:900},...(width<500?{isMobile:true,hasTouch:true}:{})}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  for(let ix=0;ix<cases.length;ix++){
   const {expectedItems,...params}=cases[ix];
   await page.goto(base+'?'+new URLSearchParams({effect_type:'random_grant',...params}),{waitUntil:'networkidle'});
   assert.equal(await page.evaluate(()=>window.UI_VERSION),'ui-v22');assert.equal(await page.evaluate(()=>window.DETAIL_VERSION),pointer.detail_version);
   assert.equal(await page.locator('#count').textContent(),'1 / 1466 件',JSON.stringify(params));
   assert.equal(await page.locator('#effect-type').inputValue(),'random_grant');
   await page.locator('.detail-toggle').first().click();
   const matches=page.locator('.matched-effect');assert.ok(await matches.count()>0);
   if(expectedItems)assert.equal(await matches.count(),expectedItems);
   const text=await matches.first().textContent();
   assert.ok(text.includes('個付与'));assert.ok(text.includes('付与は保証されません'));assert.ok(text.includes('選択確率不明'));
   if(ix===7){assert.ok(text.includes('不明な候補 3件'));assert.ok(!text.includes('0.2倍'));}
   else assert.ok(text.includes('候補：'));
   assert.ok(!text.includes('undefined'));await matches.first().scrollIntoViewIfNeeded();
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   if(output&&[1,3,7].includes(ix))await page.screenshot({path:path.join(output,width+'-random-'+ix+'.png')});
   await page.reload({waitUntil:'networkidle'});assert.equal(await page.locator('#effect-type').inputValue(),'random_grant');
  }
  for(const params of negative){
   await page.goto(base+'?'+new URLSearchParams({effect_type:'random_grant',...params}),{waitUntil:'networkidle'});
   assert.equal(await page.locator('#count').textContent(),'0 / 1466 件',JSON.stringify(params));
  }
  await page.goto(base+'?effect_type=random_grant',{waitUntil:'networkidle'});
  assert.equal(await page.locator('#count').textContent(),'29 / 1466 件');
  await page.locator('#effect-type').selectOption('rate_up');
  assert.ok(!(await page.locator('#count').textContent()).startsWith('29 /'));
  await page.locator('#effect-type').selectOption('random_grant');
  assert.equal(await page.locator('#count').textContent(),'29 / 1466 件');
  await page.locator('.filter-chip').filter({hasText:'効果：ランダム効果'}).click();
  assert.equal(await page.locator('#effect-type').inputValue(),'');
  assert.equal(await page.locator('#count').textContent(),'1466 / 1466 件');
  assert.deepEqual(errors,[]);await page.close();
  console.log(width+' random8 positive/10 negative, normal/MB, same candidate, unknown, select/reload/chip/no-overflow PASS');
 }
}finally{await browser.close();if(server)await new Promise(r=>server.close(r));}

