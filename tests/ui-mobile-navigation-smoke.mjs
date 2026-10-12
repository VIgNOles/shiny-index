import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {chromium} from 'playwright';
const root=path.resolve(process.argv[2]??'site');
const server=createServer(async(req,res)=>{
 try{const u=new URL(req.url,'http://localhost'),p=path.resolve(root,u.pathname==='/'?'index.html':decodeURIComponent(u.pathname).slice(1));if(!p.startsWith(root+path.sep))throw Error('path');res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.mjs':'text/javascript','.css':'text/css','.json':'application/json'})[path.extname(p)]??'application/octet-stream');res.end(await readFile(p));}catch{res.writeHead(404);res.end();}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const base='http://127.0.0.1:'+server.address().port+'/';
const browser=await chromium.launch({headless:true,executablePath:process.env.UI_BROWSER_PATH});
try{
 for(const width of [390,320,899,900]){
  const page=await browser.newPage({viewport:{width,height:800},...(width<900?{hasTouch:true,isMobile:true}:{})}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+'?q=真乃&card_kind=P',{waitUntil:'networkidle'});
  const mobile=width<900;
  assert.equal(await page.locator('#mobile-results-nav').isVisible(),mobile);
  assert.equal(await page.locator('#selected-conditions').evaluate(e=>e.open),!mobile);
  assert.match(await page.locator('#selected-conditions-summary').textContent(),/2/);
  assert.equal(await page.locator('#reset').isVisible(),true,'reset remains outside collapsed conditions');
  for(const id of ['people-filter','series-shortcuts','skill-filters'])assert.equal(await page.locator('#'+id).evaluate(e=>!!e.closest('dialog')),false);
  if(mobile){
   const before=new URL(page.url()).search;
   await page.locator('#mobile-results-nav a[href="#results-heading"]').click();
   assert.equal(await page.evaluate(()=>document.activeElement.id),'results-heading');
   assert.ok(await page.locator('#results-heading').evaluate(e=>e.getBoundingClientRect().top>=0&&e.getBoundingClientRect().top<100));
   await page.locator('#selected-conditions-summary').click();
   assert.equal(await page.locator('.filter-chip').first().isVisible(),true);
   await page.locator('.filter-chip').filter({hasText:'真乃'}).click();
   assert.equal(new URL(page.url()).searchParams.has('q'),false);
   await page.locator('#mobile-results-nav a[href="#search-controls"]').click();
   assert.equal(await page.evaluate(()=>document.activeElement.id),'search-controls');
   assert.equal(new URL(page.url()).searchParams.get('card_kind'),'P');
   await page.locator('#mobile-results-nav a[href="#results-heading"]').click();
   await page.locator('#reset').click();assert.equal(new URL(page.url()).search,'');
   await page.locator('#open-filters').click();assert.equal(await page.locator('#mobile-results-nav').isVisible(),false);
   await page.keyboard.press('Escape');
   assert.equal(await page.locator('#mobile-results-nav').isVisible(),true);
   assert.ok(before.length>1);
   await page.setViewportSize({width:1280,height:800});
   assert.equal(await page.locator('#selected-conditions').evaluate(e=>e.open),true);
  }
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  assert.deepEqual(errors,[]);
  console.log(width+' mobile movement, focus, compact conditions, persistent reset and desktop recovery PASS');
  await page.close();
 }
}finally{await browser.close();await new Promise(r=>server.close(r));}
