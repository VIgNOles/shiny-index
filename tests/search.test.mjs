import {test} from 'node:test';import assert from 'node:assert/strict';import{search,csv}from'../web/search.mjs';
const cards=[{card_id:'a',card_title:'【Hug？】',idol_name:'樋口円香',card_kind:'P',rarity:'SSR',first_implemented_on:'2026-09-29',series_ids:[],unknown_fields:[]},{card_id:'b',card_title:'別カード',idol_name:'樋口円香',card_kind:'S',rarity:'SR',first_implemented_on:null,series_ids:[],unknown_fields:['first_implemented_on']}];
test('NFKC and AND',()=>assert.equal(search(cards,new URLSearchParams('q=Hug? 円香')).length,1));
test('P/S and OR selection',()=>{assert.equal(search(cards,new URLSearchParams('card_kind=S'))[0].card_id,'b');assert.equal(search(cards,new URLSearchParams('card_kind=S&card_kind=P')).length,2)});
test('unknown dates last both directions',()=>{for(const d of ['asc','desc'])assert.equal(search(cards,new URLSearchParams('direction='+d))[1].card_id,'b')});
test('rarity order',()=>assert.equal(search(cards,new URLSearchParams('sort=rarity&direction=asc'))[0].rarity,'SR'));
test('date range excludes unknown',()=>assert.equal(search(cards,new URLSearchParams('from=2026-01-01')).length,1));
test('CSV formula safety',()=>assert.ok(csv([{card_title:'=1+1'}],{}).includes("'=1+1")));

test('10,000 rows filter benchmark',()=>{const data=Array.from({length:10000},(_,i)=>({...cards[i%2],card_id:String(i)}));const start=performance.now();const out=search(data,new URLSearchParams('card_kind=P&q=Hug'));assert.equal(out.length,5000);console.log('10k search ms',Math.round(performance.now()-start));});

test('Japanese series label search',()=>assert.equal(search([{...cards[0],series_ids:['casting']}],new URLSearchParams('q=キャスティング')).length,1));
