import {test} from 'node:test';import assert from 'node:assert/strict';import{search,csv}from'../web/search.mjs';
const cards=[{card_id:'a',card_title:'【Hug？】',idol_name:'樋口円香',card_kind:'P',rarity:'SSR',first_implemented_on:'2026-09-29',series_ids:[],unknown_fields:[]},{card_id:'b',card_title:'別カード',idol_name:'樋口円香',card_kind:'S',rarity:'SR',first_implemented_on:null,series_ids:[],unknown_fields:['first_implemented_on']}];
test('NFKC and AND',()=>assert.equal(search(cards,new URLSearchParams('q=Hug? 円香')).length,1));
test('P/S and OR selection',()=>{assert.equal(search(cards,new URLSearchParams('card_kind=S'))[0].card_id,'b');assert.equal(search(cards,new URLSearchParams('card_kind=S&card_kind=P')).length,2)});
test('unknown dates last both directions',()=>{for(const d of ['asc','desc'])assert.equal(search(cards,new URLSearchParams('direction='+d))[1].card_id,'b')});
test('rarity order',()=>assert.equal(search(cards,new URLSearchParams('sort=rarity&direction=asc'))[0].rarity,'SR'));
test('date range excludes unknown',()=>assert.equal(search(cards,new URLSearchParams('from=2026-01-01')).length,1));
test('CSV formula safety',()=>assert.ok(csv([{card_title:'=1+1'}],{}).includes("'=1+1")));

test('10,000 rows filter benchmark',()=>{const data=Array.from({length:10000},(_,i)=>({...cards[i%2],card_id:String(i)}));const start=performance.now();const out=search(data,new URLSearchParams('card_kind=P&q=Hug'));assert.equal(out.length,5000);console.log('10k search ms',Math.round(performance.now()-start));});

test('new and legacy Japanese series labels remain searchable',()=>{const rows=[{...cards[0],series_ids:['casting']}];for(const q of ['キャスコレ','キャスティング'])assert.equal(search(rows,new URLSearchParams('q='+q)).length,1)});
test('removed missing marker does not hide cards',()=>assert.equal(search(cards,new URLSearchParams('missing=1')).length,2));

test('partial dates include complete selected month and year',()=>{
 const rows=[
  {...cards[0],card_id:'m1',first_implemented_on:'2024-02-01'},
  {...cards[0],card_id:'m2',first_implemented_on:'2024-02-29'},
  {...cards[0],card_id:'m3',first_implemented_on:'2024-03-01'},
  {...cards[0],card_id:'m4',first_implemented_on:null}
 ];
 assert.deepEqual(search(rows,new URLSearchParams('from=2024-02&to=2024-02')).map(c=>c.card_id),['m2','m1']);
 assert.equal(search(rows,new URLSearchParams('to=2024')).length,3);
});
test('person tokens use OR and legacy person fields keep AND',()=>{
 const rows=[
  {...cards[0],card_id:'i1',unit_id:'unit_1',unit_name:'イルミネーションスターズ',idol_id:'idol_1',idol_name:'櫻木真乃'},
  {...cards[0],card_id:'i2',unit_id:'unit_2',unit_name:'アンティーカ',idol_id:'idol_2',idol_name:'月岡恋鐘'},
  {...cards[0],card_id:'i3',unit_id:null,unit_name:null,idol_id:'idol_3',idol_name:'七草はづき'}
 ];
 assert.equal(search(rows,new URLSearchParams('person=unit:unit_1&person=idol:idol_2')).length,2);
 assert.equal(search(rows,new URLSearchParams('person=unit:none')).length,1);
 assert.equal(search(rows,new URLSearchParams('unit_name=イルミネーションスターズ&idol_name=月岡恋鐘')).length,0);
});
test('official order and rarity priority',()=>{
 const rows=[
  {...cards[0],card_id:'c',idol_name:'斑鳩ルカ',unit_name:'コメティック',rarity:'UR'},
  {...cards[0],card_id:'a',idol_name:'櫻木真乃',unit_name:'イルミネーションスターズ',rarity:'N'},
  {...cards[0],card_id:'b',idol_name:'月岡恋鐘',unit_name:'アンティーカ',rarity:'SSR'}
 ];
 assert.deepEqual(search(rows,new URLSearchParams('sort=unit_official')).map(c=>c.card_id),['a','b','c']);
 assert.deepEqual(search(rows,new URLSearchParams('sort=rarity_high')).map(c=>c.card_id),['c','b','a']);
});
test('browse buckets use OR and remain distinct from detailed facets',()=>{
 const rows=[
  {...cards[0],card_id:'p',series_ids:['prelude'],acquisition_category:'collection_gacha'},
  {...cards[0],card_id:'t',series_ids:['twilights'],acquisition_category:'collection_gacha'},
  {...cards[0],card_id:'l',series_ids:['birthday'],acquisition_category:'limited_gacha'},
  {...cards[0],card_id:'c',series_ids:[],acquisition_category:'permanent_gacha'},
  {...cards[0],card_id:'o',series_ids:[],acquisition_category:'event_reward'}
 ];
 assert.deepEqual(search(rows,new URLSearchParams('browse=prelude&browse=limited_gacha'))
  .map(card=>card.card_id),['l','p']);
 assert.deepEqual(search(rows,new URLSearchParams('browse=other'))
  .map(card=>card.card_id),['o']);
 assert.deepEqual(search(rows,new URLSearchParams('browse=limited_gacha&series_ids=birthday'))
  .map(card=>card.card_id),['l']);
 assert.equal(search(rows,new URLSearchParams('series_ids=twilights')).length,1);
});
