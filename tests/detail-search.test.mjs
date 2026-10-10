import assert from 'node:assert/strict';
import test from 'node:test';
import {detailSearch,factText,generationParentText,detailCoverageText,activationConditionText,activationConditionType,activationConditionTypes,itemActivationCondition} from '../web/details.mjs';
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


test('coverage distinguishes uncollected cards from missing pages on hold',()=>{
 assert.equal(detailCoverageText({detail_card_count:1344,status_counts:{available_partial:1344,input_pending:75,missing_page_on_hold:47}},1466),'詳細 1344 / 1466カード収録。未収録 75件／個別ページなし 47件（保留）。数値・条件は一部のみ収録。');
});
test('all linked details no longer imply acquisition is still in progress',()=>{
 const text=detailCoverageText({detail_card_count:1419,status_counts:{available_partial:1419,missing_page_on_hold:47}},1466);
 assert.ok(text.includes('個別ページなし 47件（保留）'));
 assert.ok(!text.includes('未収録')&&!text.includes('順次取得'));
 assert.ok(text.includes('数値・条件は一部のみ収録'));
});
test('all card records still do not claim complete skill effects',()=>{
 assert.equal(detailCoverageText({detail_card_count:1466,status_counts:{available_partial:1466}},1466),'詳細 1466 / 1466カード収録。数値・条件は一部のみ収録。');
});

test('a shared normal and MB child keeps its own Plus and both searchable parents',()=>{
 const d=new Map([['P1',{items:[
  {name:'root',kind:'panel_live',mechanics:['link']},
  {name:'[MB]root(4/5)',kind:'mb_live',mechanics:['refrain']},
  {name:'child',kind:'generated_live',generated_from_name:'root',generated_from_names:['root','[MB]root(4/5)'],generation_origin_kind:'panel_live',generation_origin_kinds:['panel_live','mb_live'],mechanics:['plus']}
 ]}]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_kind=generated_live&skill_q=[MB]root(4/5)&mechanic=plus'),d),[cards[0]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_kind=generated_live&skill_q=[MB]root(4/5)&mechanic=refrain'),d),[]);
});

test('passive activation condition labels retain direction and thresholds',()=>{
 assert.equal(activationConditionText({status:'structured',expression:{field:'mental_percent',operator:'gte',value:75}}),'メンタル75%以上');
 assert.equal(activationConditionText({status:'structured',expression:{field:'turn',operator:'lte',value:3}}),'3ターン以前');
 assert.equal(activationConditionText({status:'structured',expression:{field:'status_count',status:'注目度UP',operator:'gte',value:2}}),'注目度UPが2個以上付与');
 assert.equal(activationConditionText({status:'unsupported'}),'');
 assert.equal(activationConditionType({status:'structured',expression:{field:'maximum_mental'}}),'mental');
});
test('condition and numeric search must match the same passive item',()=>{
 const d=new Map([['P1',{items:[
  {kind:'panel_passive',name:'Vocal100%UP',activation_condition:{status:'structured',expression:{field:'turn',operator:'lte',value:3}}},
  {kind:'panel_passive',name:'Vocal3%UP',activation_condition:{status:'structured',expression:{field:'mental_percent',operator:'gte',value:75}}}
 ]}]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_kind=panel_passive&skill_q=Vocal3%UP+メンタル７５％以上'),d),[cards[0]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_q=Vocal100%UP+メンタル75%以上'),d),[]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_condition=mental&skill_q=Vocal100%UP'),d),[]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_condition=turn&skill_kind=panel_passive'),d),[cards[0]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_condition=mental&mechanic=link'),d),[]);
});
test('legacy and unsupported conditions do not become condition matches',()=>{
 const d=new Map([['P1',{items:[{name:'不明',kind:'panel_passive',activation_condition:{status:'unsupported'}}]}],['S1',{items:[{name:'旧版',kind:'panel_passive'}]}]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_condition=mental'),d),[]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_kind=panel_passive'),d),cards.slice(0,2));
});
test('condition coverage reports partial support separately from card acquisition',()=>{
 const text=detailCoverageText({detail_card_count:1419,status_counts:{available_partial:1419,missing_page_on_hold:47},activation_condition_counts:{structured:4946,unsupported:944}},1466);
 assert.ok(text.includes('発動条件 4946 / 5890項目対応'));
 assert.ok(text.includes('個別ページなし 47件（保留）'));
});

test('extended all and any conditions retain grouping and categories',()=>{
 const leaf=(field,value,operator='eq',extra={})=>({field,operator,value,...extra});
 const condition={status:'structured',expression:{operator:'all',terms:[leaf('turn',3,'gte'),{operator:'any',terms:[leaf('participant','櫻木真乃'),leaf('participant','風野灯織')]}]}};
 assert.equal(activationConditionText(condition),'（3ターン以降 かつ （参加アイドル 櫻木真乃 または 参加アイドル 風野灯織））');
 assert.deepEqual(activationConditionTypes(condition),['turn','participant']);
 assert.equal(activationConditionText({status:'structured',expression:leaf('unknown','private')}),'');
});
test('unit all, unit only and history counts stay distinct',()=>{
 const c=(field,value,extra={})=>({status:'structured',expression:{field,operator:'eq',value,...extra}});
 assert.equal(activationConditionText(c('unit_all_participants','コメティック')),'コメティック全員が参加');
 assert.equal(activationConditionText(c('unit_only_participant','斑鳩ルカ',{unit:'コメティック'})),'コメティックから斑鳩ルカのみが参加');
 assert.equal(activationConditionText(c('history_unit_count',4,{unit:'コメティック',operator:'gte'})),'履歴にコメティックのアイドル4人以上');
 assert.deepEqual(activationConditionTypes(c('unit_all_formation','アルストロメリア')),['position']);
});
test('extended predicates are preferred without changing legacy fields',()=>{
 const item={kind:'panel_passive',name:'Vocal100%UP',activation_condition:{status:'unsupported'},activation_condition_v2:{status:'structured',expression:{operator:'all',terms:[{field:'mental_percent',operator:'gte',value:35},{field:'mental_percent',operator:'lte',value:64}]}}};
 assert.equal(itemActivationCondition(item),item.activation_condition_v2);
 const d=new Map([['P1',{items:[item]}]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams({skill_condition:'mental',skill_q:'Vocal100%UP 35% 64% かつ'}),d),[cards[0]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_condition=turn'),d),[]);
 assert.deepEqual(item.activation_condition,{status:'unsupported'});
});
test('condition element filters find either branch and keep same-item keyword matching',()=>{
 const d=new Map([['P1',{items:[{kind:'panel_passive',name:'Vocal100%UP',activation_condition:{status:'unsupported'},activation_condition_v2:{status:'structured',expression:{operator:'any',terms:[{field:'history_participant',operator:'eq',value:'幽谷霧子'},{field:'turn',operator:'gte',value:5}]}}},{kind:'panel_passive',name:'Visual200%UP',activation_condition:{status:'structured',expression:{field:'mental_percent',operator:'gte',value:75}}}]}]]);
 for(const kind of ['turn','history'])assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_condition='+kind+'&skill_q=Vocal100%UP+または'),d),[cards[0]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_condition=mental&skill_q=Vocal100%UP'),d),[]);
});
test('extended coverage is shown while legacy counts remain available',()=>{
 const text=detailCoverageText({detail_card_count:1419,status_counts:{available_partial:1419},activation_condition_counts:{structured:4946,unsupported:944},activation_condition_search_counts:{structured:5437,unsupported:453}},1466);
 assert.ok(text.includes('5437 / 5890項目対応'));assert.ok(!text.includes('4946 /'));
});

test('keyword ownership is explicit, searchable in the same passive, and prefers v3',()=>{
 const item={kind:'panel_passive',name:'Vocal100%UP',activation_condition:{status:'unsupported'},activation_condition_v3:{status:'structured',expression:{operator:'all',terms:[{field:'owner_keyword',operator:'eq',value:'リーダーシップ'},{field:'owner_keyword',operator:'eq',value:'カリスマ'}]}}};
 assert.equal(itemActivationCondition(item),item.activation_condition_v3);
 assert.equal(activationConditionText(item.activation_condition_v3),'（スキル所持者のキーワード リーダーシップ かつ スキル所持者のキーワード カリスマ）');
 assert.deepEqual(activationConditionTypes(item.activation_condition_v3),['keyword']);
 const d=new Map([['P1',{items:[item,{kind:'panel_passive',name:'Visual200%UP',activation_condition:{status:'structured',expression:{field:'turn',operator:'gte',value:3}}}]}]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams({skill_condition:'keyword',skill_q:'Vocal100%UP リーダーシップ カリスマ'}),d),[cards[0]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams({skill_condition:'keyword',skill_q:'Visual200%UP'}),d),[]);
 const text=detailCoverageText({detail_card_count:1419,status_counts:{available_partial:1419},activation_condition_search_counts:{structured:5881,unsupported:9},activation_condition_current_counts:{structured:5885,unsupported:5}},1466);
 assert.ok(text.includes('5885 / 5890項目対応'));assert.ok(text.includes('未対応5項目'));
});

test('all passive conditions structured still reports zero unsupported',()=>{
 const text=detailCoverageText({detail_card_count:1419,status_counts:{available_partial:1419},activation_condition_current_counts:{structured:5890}},1466);
 assert.ok(text.includes('5890 / 5890項目対応'));assert.ok(text.includes('未対応0項目'));assert.ok(text.includes('数値・条件は一部のみ収録'));
});


test('effect filters never borrow targets or turns from a different effect or skill',()=>{
 const d=new Map([['P1',{items:[{name:'multi',kind:'panel_live',effect_details:{effects:[
  {metric:'rate_up',targets:['Vocal'],value:20,unit:'percent',scope:'base',turns:3},
  {metric:'rate_up',targets:['Dance'],value:30,unit:'percent',scope:'plus',turns:7}]}},
  {name:'other',kind:'support_skill',effect_details:{effects:[{metric:'support_recovery',targets:['体力'],value:6,unit:'points',scope:'base',trigger:'vocal_lesson'}]}}]}]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('effect_target=Vocal&effect_turns=5'),d),[]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('effect_target=Dance&effect_turns=5'),d),[cards[0]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('effect_target=Dance&effect_turns=5&skill_q=Vocal'),d),[]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('effect_type=support_recovery&skill_q=ボーカルレッスン'),d),[cards[0]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('effect_target=体力&mechanic=link'),d),[]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('effect_turns=not-a-number'),d),[]);
});
test('level formulas and group restrictions are searchable without implying numeric completeness',()=>{
 const d=new Map([['P1',{items:[{name:'boost',kind:'unique_ability',effect_details:{effects:[{metric:'appeal_boost',targets:['アピール値'],value:30,unit:'percent',scope:'base',restrictions:{group:'相アイ',idols:['櫻木真乃']}}]}}]}],['S1',{items:[{name:'bond',kind:'support_skill',effect_details:{effects:[{metric:'support_bond',targets:['絆'],formula:{variable:'skill_level',coefficient:5,offset:0},unit:'points',scope:'base',trigger:'produce_start'}]}}]}]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('effect_type=appeal_boost&skill_q=相アイ+櫻木真乃'),d),[cards[0]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('skill_q=スキルLv×5+プロデュース開始時'),d),[cards[1]]);
});
test('legacy data safely does not match new effect filters',()=>{
 assert.deepEqual(detailSearch(cards,new URLSearchParams('effect_target=Vocal'),details),[]);
});
