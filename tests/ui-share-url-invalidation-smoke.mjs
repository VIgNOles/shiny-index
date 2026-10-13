import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {chromium} from 'playwright';

const root=path.resolve(process.argv[2]??'site'),output=process.env.UI_AUDIT_DIR;
const bp=JSON.parse(await readFile(path.join(root,'data/latest.json'),'utf8'));
const dp=JSON.parse(await readFile(path.join(root,'details/latest.json'),'utf8'));
const assets=new Set(['index.html','app.mjs','details.mjs','search.mjs','style.css']);
const server=createServer(async(req,res)=>{
 try{
  const url=new URL(req.url,'http://localhost'),name=url.pathname==='/'?'index.html':decodeURIComponent(url.pathname).slice(1);
  const source=process.env.UI_SOURCE_WEB==='1'&&assets.has(name)?path.resolve('web'):root;
  const file=path.resolve(source,name);if(!file.startsWith(source+path.sep))throw Error('path');
  let bytes=await readFile(file);
  if(source!==root&&name==='index.html')bytes=Buffer.from(bytes.toString().replaceAll('__VERSION__',bp.dataset_version).replaceAll('__DETAIL_VERSION__',dp.detail_version));
  res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.mjs':'text/javascript','.css':'text/css','.json':'application/json'})[path.extname(file)]??'application/octet-stream');res.end(bytes);
 }catch{res.writeHead(404);res.end();}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const base='http://127.0.0.1:'+server.address().port+'/',browser=await chromium.launch({headless:true,executablePath:process.env.UI_BROWSER_PATH});
const report=[];
const state=page=>page.evaluate(()=>({hidden:document.querySelector('#copy-link-fallback').hidden,value:document.querySelector('#copy-link-value').value,status:document.querySelector('#copy-link-status').textContent}));
const emptyState={hidden:true,value:'',status:''};
const cleared=async(page,message)=>assert.deepEqual(await state(page),emptyState,message);
const ensureOpen=async(page,id)=>{if(!await page.locator('#'+id).evaluate(e=>e.open))await page.locator('#'+id+'>summary').click();};
const manualCopy=async page=>{
 await page.locator('#copy-search-link').click();await page.locator('#copy-link-fallback').waitFor({state:'visible'});
 const current=await state(page);assert.equal(current.hidden,false);assert.equal(current.value,page.url().replace(/#.*$/,''));assert.match(current.status,/コピー/);
 assert.equal(await page.locator('#copy-link-value').getAttribute('readonly'),'');return current;
};
const initClipboard=()=>{
 const requests=[];window.__copy={mode:'deny',requests};
 Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:url=>{
  if(window.__copy.mode==='deny')return Promise.reject(Error('denied'));
  if(window.__copy.mode==='allow'){window.__copy.last=url;return Promise.resolve();}
  return new Promise((resolve,reject)=>requests.push({url,resolve,reject}));
 }}});
};
try{
 for(const width of [1280,390,320]){
  const context=await browser.newContext({viewport:{width,height:900},...(width<900?{isMobile:true,hasTouch:true}:{})});
  await context.addInitScript(initClipboard);
  const page=await context.newPage(),errors=[];page.on('pageerror',error=>errors.push(error.message));
  try{
   await page.goto(base,{waitUntil:'networkidle'});assert.equal(await page.evaluate(()=>window.UI_VERSION),process.env.UI_EXPECTED_VERSION??'ui-v27');
   const original=await manualCopy(page);
   // Read within the input event turn: the old URL must disappear before the 180 ms search timer.
   const immediate=await page.locator('#q').evaluate(input=>{
    input.value='真乃';input.dispatchEvent(new Event('input',{bubbles:true}));
    return {hidden:document.querySelector('#copy-link-fallback').hidden,value:document.querySelector('#copy-link-value').value,status:document.querySelector('#copy-link-status').textContent};
   });
   assert.deepEqual(immediate,emptyState,'q input must clear the old manual URL immediately, before debounce');
   await page.waitForFunction(()=>new URL(location.href).searchParams.get('q')==='真乃');
   const changed=await manualCopy(page);assert.notEqual(changed.value,original.value);assert.equal(new URL(changed.value).searchParams.get('q'),'真乃');
   await page.locator('#reset').click();await cleared(page,'reset clears the URL');

   await ensureOpen(page,'skill-filters');await manualCopy(page);await page.locator('#skill-kind').selectOption('panel_passive');
   await cleared(page,'select changes clear the manual URL');
   const selected=await manualCopy(page);assert.equal(new URL(selected.value).searchParams.get('skill_kind'),'panel_passive');
   await ensureOpen(page,'selected-conditions');await page.locator('.filter-chip').first().click();await cleared(page,'individual chip removal clears the URL');
   await manualCopy(page);await page.locator('#sort').selectOption('date_old');await cleared(page,'sort changes clear the URL');
   const sorted=await manualCopy(page);assert.equal(new URL(sorted.value).searchParams.get('sort'),'date_old');
   await page.goBack({waitUntil:'networkidle'});await cleared(page,'history back clears the previous URL');
   const back=await manualCopy(page);assert.notEqual(back.value,sorted.value);
   await page.goForward({waitUntil:'networkidle'});await cleared(page,'history forward clears the previous URL');
   assert.equal((await manualCopy(page)).value,sorted.value);

   // Display-only operations retain a usable URL for the current search.
   await page.locator('#reset').click();const displayCopy=await manualCopy(page);
   await page.locator('.compare-toggle').first().click();assert.deepEqual(await state(page),displayCopy,'comparison selection preserves the current URL');
   await page.locator('.detail-toggle').first().click();assert.deepEqual(await state(page),displayCopy,'detail expansion preserves the current URL');
   const firstId=await page.locator('.card').first().getAttribute('data-card-id');
   await page.locator('#more').click();assert.ok(await page.locator('.card').count()>100);assert.equal(await page.locator('.card').first().getAttribute('data-card-id'),firstId);
   assert.deepEqual(await state(page),displayCopy,'append more preserves the current URL');
   if(width<900){
    await page.locator('#open-filters').click();await page.locator('#unlock-star-max').selectOption('2');await cleared(page,'editing a mobile draft immediately invalidates the old URL');
    await page.locator('#cancel-filters').click();await page.locator('#filter-dialog').waitFor({state:'hidden'});await cleared(page,'cancel does not revive an invalidated URL');
    assert.equal(new URL(page.url()).searchParams.has('unlock_star_max'),false);
    await manualCopy(page);await page.locator('#open-filters').click();await page.locator('#unlock-star-max').selectOption('2');await page.locator('#apply-filters').click();await page.locator('#filter-dialog').waitFor({state:'hidden'});
    await cleared(page,'applying a mobile draft leaves no old manual URL');
    assert.equal(new URL((await manualCopy(page)).value).searchParams.get('unlock_star_max'),'2');
   }
   assert.deepEqual(errors,[]);report.push({width,status:'pass',cases:['immediate input','new copy','select','chip','reset','sort','back-forward','display-only',...(width<900?['draft cancel','draft apply']:[])]});
   console.log(width+' share URL invalidation, current recopy, history and display-only regressions PASS');
  }finally{await context.close();}
 }

 const context=await browser.newContext({viewport:{width:1280,height:900}});await context.addInitScript(initClipboard);
 const page=await context.newPage(),errors=[];page.on('pageerror',error=>errors.push(error.message));
 try{
  await page.goto(base,{waitUntil:'networkidle'});
  for(const settlement of ['reject','resolve']){
   await page.evaluate(()=>{window.__copy.mode='defer';window.__copy.requests.length=0;});await page.locator('#copy-search-link').click();
   await page.waitForFunction(()=>window.__copy.requests.length===1);
   const query=settlement==='reject'?'真乃':'灯織';
   const settled=await page.locator('#q').evaluate((input,{method,query})=>{
    input.value=query;input.dispatchEvent(new Event('input',{bubbles:true}));
    window.__copy.requests[0][method](method==='reject'?Error('denied'):undefined);
    return Promise.resolve().then(()=>({url:location.href,state:{hidden:document.querySelector('#copy-link-fallback').hidden,value:document.querySelector('#copy-link-value').value,status:document.querySelector('#copy-link-status').textContent}}));
   },{method:settlement,query});
   assert.notEqual(new URL(settled.url).searchParams.get('q'),query,'the clipboard result settles before the search debounce');
   assert.deepEqual(settled.state,emptyState,'a delayed '+settlement+' cannot revive the old URL before the search debounce');
   await page.waitForFunction(value=>new URL(location.href).searchParams.get('q')===value,query);
   await cleared(page,'a delayed '+settlement+' from old conditions cannot resurrect the manual URL or status');
  }
  // At identical conditions, the most recent copy wins even if an older request finishes later.
  await page.evaluate(()=>{window.__copy.mode='defer';window.__copy.requests.length=0;});
  await page.locator('#copy-search-link').click();await page.waitForFunction(()=>window.__copy.requests.length===1);
  await page.locator('#copy-search-link').click();await page.waitForFunction(()=>window.__copy.requests.length===2);
  await page.evaluate(()=>window.__copy.requests[1].resolve());await page.waitForFunction(()=>document.querySelector('#copy-link-status').textContent.includes('コピーしました'));
  const newest=await state(page);assert.equal(newest.hidden,true);assert.equal(newest.value,'');
  await page.evaluate(()=>window.__copy.requests[0].reject(Error('old denied')));assert.deepEqual(await state(page),newest,'older rejection cannot overwrite a newer successful copy');
  // A newer manual fallback also survives an older success.
  await page.evaluate(()=>{window.__copy.requests.length=0;});await page.locator('#copy-search-link').click();await page.waitForFunction(()=>window.__copy.requests.length===1);
  await page.locator('#copy-search-link').click();await page.waitForFunction(()=>window.__copy.requests.length===2);
  await page.evaluate(()=>window.__copy.requests[1].reject(Error('new denied')));await page.locator('#copy-link-fallback').waitFor({state:'visible'});const newestManual=await state(page);
  await page.evaluate(()=>window.__copy.requests[0].resolve());assert.deepEqual(await state(page),newestManual,'older success cannot overwrite a newer manual fallback');
  // Input composition must invalidate without waiting for compositionend or a timer.
  const composed=await page.locator('#q').evaluate(input=>{input.dispatchEvent(new CompositionEvent('compositionstart',{bubbles:true}));input.value='めぐる';input.dispatchEvent(new InputEvent('input',{bubbles:true,isComposing:true,data:'る'}));return {hidden:document.querySelector('#copy-link-fallback').hidden,value:document.querySelector('#copy-link-value').value,status:document.querySelector('#copy-link-status').textContent};});
  assert.deepEqual(composed,emptyState,'composing input immediately invalidates the old URL');
  await page.locator('#q').evaluate(input=>input.dispatchEvent(new CompositionEvent('compositionend',{bubbles:true})));
  assert.deepEqual(errors,[]);report.push({width:1280,status:'pass',cases:['delayed reject','delayed success','copy request order','input composition']});
  console.log('delayed clipboard results, copy request ordering and IME input PASS');
 }finally{await context.close();}
}finally{
 await browser.close();await new Promise(resolve=>server.close(resolve));
 if(output){await mkdir(output,{recursive:true});await writeFile(path.join(output,'share-url-invalidation.json'),JSON.stringify(report,null,2)+'\n');}
}
