import assert from 'node:assert/strict';
import test from 'node:test';
import {detailSearch} from '../web/details.mjs';
const cards=[{card_id:'P1'},{card_id:'S1'},{card_id:'pending'}];
const details=new Map([
 ['P1',{items:[{name:'通常',kind:'panel_live',mechanics:['link'],numeric_facts:[]},{name:'MB限定',kind:'mb_live',mechanics:['plus'],numeric_facts:[]},{name:'思い出',kind:'memory_appeal',mechanics:['link'],numeric_facts:[]}]}],
 ['S1',{items:[{name:'Visualアピール',kind:'possessed_live',mechanics:['grow'],numeric_facts:[{metric:'appeal',targets:['Visual'],value:4.5,unit:'multiplier'}]}]}]
]);
test('no skill condition keeps all base cards',()=>assert.deepEqual(detailSearch(cards,new URLSearchParams(),details),cards));
test('kind and mechanic must match the same skill',()=>assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_kind=panel_live&mechanic=plus'),details),[]));
test('memory Link is excluded from live mechanic filters',()=>assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_kind=memory_appeal&mechanic=link'),details),[]));
test('skill search normalizes width and joins numeric facts',()=>assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_q=Ｖｉｓｕａｌ+4.5倍'),details),[cards[1]]));
test('multiple mechanics use OR and leave uncollected cards out',()=>assert.deepEqual(detailSearch(cards,new URLSearchParams('mechanic=plus&mechanic=grow'),details),cards.slice(0,2)));
test('available filter preserves base order',()=>assert.deepEqual(detailSearch(cards,new URLSearchParams('detail_status=available'),details),cards.slice(0,2)));

test('generated Change is separate from its Plus panel parent',()=>{
 const d=new Map([['P1',{items:[{name:'root',kind:'panel_live',mechanics:['plus']},{name:'child',kind:'generated_live',mechanics:['change']}]}]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_kind=generated_live&mechanic=change&skill_q=child'),d),[cards[0]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_kind=panel_live&mechanic=change'),d),[]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_kind=generated_live&mechanic=plus'),d),[]);
});

test('random option search stays on the owning live skill',()=>{
 const d=new Map([['P1',{items:[{name:'root',kind:'panel_live',mechanics:['plus'],random_effect_options:[{metric:'rate',target:'Vocal',value:200,direction:'UP'}]}]}]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_q=ランダム+200%&mechanic=plus'),d),[cards[0]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_q=ランダム&mechanic=change'),d),[]);
});
