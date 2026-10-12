import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {chromium} from 'playwright';

const root=path.resolve(process.argv[2]??'site');
const read=async name=>JSON.parse(await readFile(path.join(root,name),'utf8'));
const basePointer=await read('data/latest.json');
const detailPointer=await read('details/latest.json');
const total=(await read(`data/${basePointer.dataset_version}/cards.json`)).cards.length;

// Fixed card IDs and expectations from the approved source, independent of search.
const present='44939583-5f1e-43cb-8782-615453e9d7a8';
const stellar='3755c28c-6c1b-435b-9c3d-f39be28e4485';
const cases=[
 ...['Vocal','Dance','Visual'].map(target=>({title:'Present Present',id:present,target,word:'30%UP',match:true})),
 {title:'Present Present',id:present,target:'Vocal',word:'20%UP',match:false},
 ...['Vocal','Dance'].map(target=>({title:'interStellar-Stella',id:stellar,target,word:'30%UP',match:true})),
 {title:'interStellar-Stella',id:stellar,target:'Visual',word:'60%UP',match:true},
 ...['Vocal','Dance'].map(target=>({title:'interStellar-Stella',id:stellar,target,word:'60%UP',match:false})),
 {title:'interStellar-Stella',id:stellar,target:'Visual',word:'30%UP',match:false},
 {title:'interStellar-Stella',id:stellar,target:'Vocal',word:'20%UP',match:false},
];
const server=process.env.UI_BASE_URL?null:createServer(async(req,res)=>{
 try{
  const url=new URL(req.url,'http://127.0.0.1');
  const file=path.resolve(root,url.pathname==='/'?'index.html':decodeURIComponent(url.pathname).slice(1));
  if(!file.startsWith(root+path.sep))throw Error('path');
  res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.mjs':'text/javascript','.css':'text/css','.json':'application/json'})[path.extname(file)]??'application/octet-stream');
  res.end(await readFile(file));
 }catch{res.writeHead(404);res.end();}
});
let browser;
try{
 if(server)await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const base=process.env.UI_BASE_URL??'http://127.0.0.1:'+server.address().port+'/';
 browser=await chromium.launch({headless:true,executablePath:process.env.UI_BROWSER_PATH});
 for(const width of [1280,390,320]){
  const page=await browser.newPage({viewport:{width,height:900},...(width<500?{isMobile:true,hasTouch:true}:{})});
  const errors=[],requested=new Set(),assets=new Set(['app.mjs','details.mjs','search.mjs','style.css']);
  page.on('pageerror',error=>errors.push(error.message));
  page.on('request',request=>{
   const url=new URL(request.url()),name=url.pathname.split('/').at(-1);
   if(assets.has(name))requested.add(url.href);
  });
  try{
   for(const item of cases){
    const params=new URLSearchParams({q:item.title,skill_kind:'panel_passive',effect_type:'passive_up',effect_target:item.target,skill_q:item.word});
    await page.goto(base+'?'+params,{waitUntil:'networkidle'});
    assert.equal(await page.evaluate(()=>window.UI_VERSION),process.env.UI_EXPECTED_VERSION??'ui-v27');
    assert.equal(await page.evaluate(()=>window.DETAIL_VERSION),detailPointer.detail_version);
    assert.equal(await page.locator('#count').textContent(),`${item.match?1:0} / ${total} 件`,params.toString());
    assert.deepEqual(await page.locator('.card').evaluateAll(nodes=>nodes.map(node=>node.dataset.cardId)),item.match?[item.id]:[],params.toString());
    assert.equal(await page.locator('#effect-target').inputValue(),item.target);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   }
   assert.deepEqual(new Set([...requested].map(value=>new URL(value).pathname.split('/').at(-1))),assets,'all revised UI assets loaded');
   for(const value of requested){
    const url=new URL(value);
    assert.equal(url.searchParams.get('ui'),'27',value);
    assert.equal(url.searchParams.get('rev'),null,'stale asset query: '+value);
   }
   assert.deepEqual(errors,[]);
   console.log(`${width} compound passive fixed-ID positive6/negative5 and revised assets PASS`);
  }finally{await page.close();}
 }
}finally{
 if(browser)await browser.close();
 if(server?.listening)await new Promise(resolve=>server.close(resolve));
}
