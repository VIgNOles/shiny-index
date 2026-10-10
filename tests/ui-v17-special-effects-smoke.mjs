import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {chromium} from 'playwright';
const root=path.resolve(process.argv[2]??'site');
const pointer=JSON.parse(await readFile(path.join(root,'details/latest.json'),'utf8'));
const doc=JSON.parse(await readFile(path.join(root,'details',pointer.detail_version,'details.json'),'utf8'));
const total=doc.coverage.base_card_count;
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
 {type:'resurrection',q:'思い出Link',check:e=>e.metric==='resurrection'&&e.scope==='memory_link'},
 {type:'resurrection',q:'Change 斑鳩ルカ',check:e=>e.metric==='resurrection'&&e.scope==='change'},
 {type:'audience_status_clear',q:'興味変動無効を除く',kind:'quick_skill',check:e=>e.metric==='audience_status_clear'},
 {type:'duet_add',q:'このターンのアピールに追加',kind:'quick_skill',check:e=>e.metric==='duet_add'},
 {type:'duet',q:'対象：放課後クライマックスガールズ',check:e=>e.metric==='duet'&&e.duet_target?.kind==='unit'&&e.duet_target.name==='放課後クライマックスガールズ'},
 {type:'duet',q:'対象：小宮果穂',check:e=>e.metric==='duet'&&e.duet_target?.kind==='idol'&&e.duet_target.name==='小宮果穂'},
 {type:'charm',q:'全観客',check:e=>e.metric==='charm'&&e.audience==='all'},
 {type:'enthusiasm',q:'最大3つ付与',check:e=>e.metric==='enthusiasm'&&e.grant_count_maximum===3},
 {type:'enthusiasm',q:'2～4ターン',turns:'2',check:e=>e.metric==='enthusiasm'&&e.turn_range?.minimum===2&&e.turn_range.maximum===4},
 {type:'interest_minimum',q:'最小値',turns:'2',check:e=>e.metric==='interest_minimum'&&e.turns===2},
 {type:'charm',q:'Grow Lv上昇条件',check:e=>e.metric==='charm'&&e.mechanic_condition?.role==='growth'},
];
const browser=await chromium.launch({headless:true,executablePath:process.env.UI_BROWSER_PATH});
try{
 for(const width of [1280,390,320]){
  const page=await browser.newPage({viewport:{width,height:900},...(width<500?{isMobile:true,hasTouch:true}:{})}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  for(let index=0;index<cases.length;index++){
   const c=cases[index],params=new URLSearchParams({skill_q:c.q});if(c.type)params.set('effect_type',c.type);if(c.kind)params.set('skill_kind',c.kind);
   if(c.turns)params.set('effect_turns',c.turns);
   const expected=doc.cards.filter(card=>card.items.some(i=>(!c.kind||i.kind===c.kind)&&i.effect_details?.effects.some(c.check))).length;assert.ok(expected>0);
   await page.goto(base+'?'+params,{waitUntil:'networkidle'});
   assert.equal(await page.evaluate(()=>window.UI_VERSION),process.env.UI_EXPECTED_VERSION??'ui-v17');assert.equal(await page.evaluate(()=>window.DETAIL_VERSION),pointer.detail_version);
   assert.equal(await page.locator('#count').textContent(),expected+' / '+total+' 件',width+' case '+index+' '+c.q);
   await page.locator('.detail-toggle').first().click();const match=page.locator('.matched-effect').first();assert.ok(await match.isVisible(),width+' case '+index+' '+c.q);await match.scrollIntoViewIfNeeded();
   const text=await match.textContent();
   for(const word of c.q.split(' '))assert.ok(text.includes(word),word+' missing in '+text);
   assert.ok(!text.includes('未構造化'));assert.ok(!text.includes('undefined'));
   if(c.q==='ダメージを受けるまで')assert.ok(!/\\[\\d+ターン\\]/.test(text));
   if(c.q.startsWith('Grow')){assert.ok(!text.includes('発動条件：'));assert.ok(text.includes('翌ターン反映'));assert.ok(text.includes('使用後Lv0'));}
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   if(output&&[2,7,8].includes(index))await page.screenshot({path:path.join(output,width+'-special-'+index+'.png')});
   await page.reload({waitUntil:'networkidle'});assert.equal(await page.locator('#skill-q').inputValue(),c.q);
  }
  for(const p of [
   {effect_type:'enthusiasm',effect_turns:'3',skill_q:'2～4ターン'},
   {effect_type:'enthusiasm',effect_turns:'1',skill_q:'最大3ターン'},
   {effect_type:'audience_status_clear',effect_turns:'1'},
   {effect_type:'duet_add',effect_turns:'1'},
   {effect_type:'mental_recovery',skill_q:'リザレクション'}
  ]){
   await page.goto(base+'?'+new URLSearchParams(p),{waitUntil:'networkidle'});
   assert.equal(await page.locator('#count').textContent(),'0 / '+total+' 件',JSON.stringify(p));
  }
  await page.locator('#reset').click();assert.equal(await page.locator('#count').textContent(),total+' / '+total+' 件');
  assert.deepEqual(errors,[]);await page.close();console.log(width+' special effects, exact exclusions, duration bounds PASS');
 }
}finally{await browser.close();if(server)await new Promise(r=>server.close(r));}
