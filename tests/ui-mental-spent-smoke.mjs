
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
 {q:'夜が来ても',effect_target:'Visual',effect_turns:'4',skill_q:'最大120% 減少値',items:1,maximum:'120%'},
 {q:'雪、えとせとら',effect_target:'Dance',effect_turns:'3',skill_q:'最大80% 減少値',items:1,maximum:'80%'},
 {q:'モラトリアム・レポート',skill_kind:'mb_live',effect_target:'Visual',effect_turns:'4',skill_q:'最大240% 減少値',items:1,maximum:'240%'},
 {q:'いつか帰りたか場所',skill_kind:'mb_live',effect_target:'Dance',effect_turns:'5',skill_q:'減少値',items:2},
 {q:'DIVA',effect_target:'Vocal',effect_turns:'3',skill_q:'最大150% 減少値',items:1,maximum:'150%'},
 {q:'ダイブ・My・ハート',effect_target:'Dance',effect_turns:'4',skill_q:'減少値',items:1,maximum:'200%'},
 {q:'心に住む人',effect_target:'Vocal',effect_turns:'3',skill_q:'減少値',items:1,maximum:'80%'},
];
const negative=[
 {q:'夜が来ても',effect_target:'Dance'},
 {q:'夜が来ても',effect_target:'Visual',effect_turns:'5'},
 {q:'夜が来ても',effect_target:'Visual',effect_recipient:'self'},
 {q:'雪、えとせとら',effect_target:'Dance',skill_q:'Link： 減少値'},
 {q:'雪、えとせとら',effect_type:'appeal'},
 {q:'モラトリアム・レポート',skill_kind:'panel_live',effect_target:'Visual',skill_q:'最大240% 減少値'},
 {q:'いつか帰りたか場所',skill_kind:'panel_live',effect_target:'Dance',effect_turns:'5'},
 {q:'DIVA',effect_type:'mental_cost',effect_target:'Vocal'},
];
const browser=await chromium.launch({headless:true,executablePath:process.env.UI_BROWSER_PATH});
try{
 for(const width of [1280,390,320]){
  const page=await browser.newPage({viewport:{width,height:900},...(width<500?{isMobile:true,hasTouch:true}:{})}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  for(let ix=0;ix<cases.length;ix++){
   const {items,maximum,...params}=cases[ix];
   await page.goto(base+'?'+new URLSearchParams({effect_type:'rate_up',...params}),{waitUntil:'networkidle'});
   assert.equal(await page.evaluate(()=>window.UI_VERSION),process.env.UI_EXPECTED_VERSION??'ui-v22');assert.equal(await page.evaluate(()=>window.DETAIL_VERSION),pointer.detail_version);
   assert.equal(await page.locator('#count').textContent(),'1 / 1466 件',JSON.stringify(params));
   await page.locator('.detail-toggle').first().click();
   const matches=page.locator('.matched-effect');assert.equal(await matches.count(),items,JSON.stringify(params));
   for(const text of await matches.allTextContents()){
    assert.ok(text.includes('継続するUP効果'));assert.ok(text.includes('最大'));assert.ok(text.includes('減少値が多いほど効果UP'));assert.ok(text.includes('['+params.effect_turns+'ターン]'));
    assert.ok(!text.includes('自身のメンタル消費'));assert.ok(!text.includes('Link：'));assert.ok(!text.includes('Grow：'));assert.ok(!text.includes('undefined'));
    if(maximum)assert.ok(text.includes('最大'+maximum));
   }
   await matches.first().scrollIntoViewIfNeeded();
   if(output&&[1,2,5].includes(ix))await page.screenshot({path:path.join(output,width+'-mental-spent-'+ix+'.png')});
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   await page.reload({waitUntil:'networkidle'});assert.equal(await page.locator('#effect-target').inputValue(),params.effect_target);assert.equal(await page.locator('#skill-q').inputValue(),params.skill_q);
  }
  for(const params of negative){
   await page.goto(base+'?'+new URLSearchParams({effect_type:'rate_up',skill_q:'減少値',...params}),{waitUntil:'networkidle'});
   assert.equal(await page.locator('#count').textContent(),'0 / 1466 件',JSON.stringify(params));
  }
  for(const [kind,count] of [['',16],['P',10],['S',6]]){
   const p=new URLSearchParams({effect_type:'rate_up',skill_q:'減少値が多いほど効果UP'});if(kind)p.set('card_kind',kind);
   await page.goto(base+'?'+p,{waitUntil:'networkidle'});assert.equal(await page.locator('#count').textContent(),count+' / 1466 件');
  }
  await page.goto(base+'?effect_type=rate_up&effect_target=Dance&skill_q='+encodeURIComponent('減少値'),{waitUntil:'networkidle'});
  await page.locator('.filter-chip').filter({hasText:'効果：継続するUP効果'}).click();assert.equal(await page.locator('#effect-type').inputValue(),'');
  assert.deepEqual(errors,[]);await page.close();
  console.log(width+' mental-spent positive7/negative8, P/S, maximum/cost/turns/scopes, reload/chip/no-overflow PASS');
 }
}finally{await browser.close();if(server)await new Promise(r=>server.close(r));}
