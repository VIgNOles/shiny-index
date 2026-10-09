import assert from 'node:assert/strict';
import test from 'node:test';
import {detailSearch,factText,generationParentText} from '../web/details.mjs';
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


test('memory extra facts are searchable without becoming a live Link',()=>{
 const d=new Map([['P1',{items:[{name:'思い出',kind:'memory_appeal',numeric_facts:[],memory_link_present:true,memory_link_facts:[{metric:'appeal',targets:['Dance'],value:3}],memory_charge_present:true,memory_charge_facts:[{metric:'appeal',targets:['Visual'],value:4}]}]}]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_kind=memory_appeal&skill_q=Link+Dance+3倍'),d),[cards[0]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_kind=memory_appeal&skill_q=チャージ+Visual+4倍'),d),[cards[0]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('mechanic=link&skill_q=Dance'),d),[]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_kind=memory_appeal&skill_q=Link+Visual+4倍'),d),[]);
});

test('maximum appeal label retains its condition limitation',()=>assert.equal(factText({metric:'appeal_maximum',targets:['Dance'],value:3.5}),'Dance 最大3.5倍（条件未構造化）'));


test('memory range search keeps both bounds and normalizes wave width',()=>{
 const d=new Map([['P1',{items:[{name:'思い出',kind:'memory_appeal',memory_link_present:true,memory_link_facts:[{metric:'appeal_range',targets:['Vocal'],minimum:0.4,maximum:2}]}]}]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_kind=memory_appeal&skill_q=Link+Vocal+0.4~2倍'),d),[cards[0]]);
 assert.equal(factText(d.get('P1').items[0].memory_link_facts[0]),'Vocal 0.4～2倍（条件未構造化）');
});

test('shared generated skill searches both parents without mixing panel mechanics',()=>{
 const item={name:'child',kind:'generated_live',generated_from_name:'root A',generated_from_names:['root A','root B(☆4)'],mechanics:['change']};
 const d=new Map([['P1',{items:[item]}]]);
 assert.equal(generationParentText(item),'root A / root B(☆4)');
 assert.equal(generationParentText({generated_from_name:'root'}),'root');
 assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_kind=generated_live&skill_q=root+B(☆4)&mechanic=change'),d),[cards[0]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_kind=panel_live&skill_q=root+B(☆4)'),d),[]);
});
