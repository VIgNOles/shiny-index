import {effectFactText,effectSearchMatches} from '../web/details.mjs';
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


test('live conditions and scaling stay attached to the matching effect',()=>{
 const d=new Map([['P1',{items:[{name:'複合',kind:'panel_live',effect_details:{effects:[
  {metric:'appeal',targets:['Vocal'],value:5,unit:'multiplier',scope:'base',maximum:true,restrictions:{scaling:'attention_descending'}},
  {metric:'rate_up',targets:['Dance'],value:40,unit:'percent',scope:'plus',turns:3,activation_condition:{status:'structured',expression:{field:'turn',operator:'lte',value:2}}},
  {metric:'refrain',targets:['過去のアピール'],value:2,unit:'points',scope:'refrain',activation_condition:{status:'unsupported'}}
 ]}}]}]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('effect_target=Vocal&skill_q=2ターン以前'),d),[]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('effect_target=Dance&skill_q=2ターン以前'),d),[cards[0]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('effect_type=appeal&skill_q=注目度が低いほど'),d),[cards[0]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('effect_type=refrain&skill_q=2ターン前'),d),[cards[0]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('effect_type=refrain&effect_turns=2'),d),[]);
 const text=effectFactText(d.get('P1').items[0].effect_details.effects[2]);
 assert.ok(text.includes('発動条件：未構造化'));assert.ok(!text.includes('undefined'));
});
test('instant recovery and passive strengthening do not become duration buffs',()=>{
 const d=new Map([['S1',{items:[{name:'heal',kind:'panel_live',effect_details:{effects:[
 {metric:'mental_recovery',targets:['メンタル'],value:20,unit:'percent',scope:'base'},
 {metric:'passive_boost',targets:['パッシブスキル'],value:10,unit:'percent',scope:'base',turns:3}
 ]}}]}]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('effect_type=mental_recovery'),d),[cards[1]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('effect_type=mental_recovery&effect_turns=3'),d),[]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams('effect_type=passive_boost&effect_turns=3'),d),[cards[1]]);
});

test('highlight and search use exactly the same effect and keyword predicate',()=>{
 const item={name:'test',kind:'panel_live'},params=new URLSearchParams('effect_target=Dance&skill_q=2ターン以前');
 const unconditional={metric:'rate_up',targets:['Dance'],scope:'base',unit:'percent',value:100,turns:4};
 const conditional={...unconditional,scope:'plus',activation_condition:{status:'structured',expression:{field:'turn',operator:'lte',value:2}}};
 assert.equal(effectSearchMatches(item,unconditional,params),false);
 assert.equal(effectSearchMatches(item,conditional,params),true);
});


test('Grow grant events are distinct from activation states and standalone rules are searchable',()=>{
 const growth={status:'structured',role:'growth',expression:{field:'status_granted',operator:'eq',value:'VocalUP'},events_per_level:2,level_up_timing:'next_turn',carry_over:true,reset_on_use:true};
 const d=new Map([['P1',{items:[{name:'grow',kind:'panel_live',mechanics:['grow'],effect_details:{effects:[
  {metric:'appeal',scope:'base',targets:['Vocal'],unit:'multiplier',value:4}
 ],mechanic_conditions:[{scope:'grow',slot:'effect',segment:1,condition:growth}]}}]}]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams({skill_q:'Lv上昇 VocalUP 2個付与ごと 翌ターン 繰越'}),d),[cards[0]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams({effect_type:'appeal',skill_q:'2個付与ごと'}),d),[]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams({mechanic:'plus',skill_q:'VocalUP'}),d),[]);
});
test('new live count and OR rules preserve same-effect matching and legacy fallback',()=>{
 const rule={status:'structured',role:'activation',expression:{operator:'all',terms:[
  {field:'active_passive_count',operator:'gte',value:6},
  {field:'unit_all_participants',operator:'eq',value:'イルミネーションスターズ'}
 ]}};
 const e={metric:'rate_up',scope:'plus',targets:['Vocal'],value:50,unit:'percent',turns:3,activation_condition:{status:'unsupported'},mechanic_condition:rule};
 const other={metric:'rate_up',scope:'base',targets:['Dance'],value:100,unit:'percent',turns:4};
 const d=new Map([['P1',{items:[{name:'plus',kind:'panel_live',effect_details:{effects:[e,other]}}]}]]);
 const text=effectFactText(e);
 assert.ok(text.includes('現在発動中のパッシブスキル6個以上'));assert.ok(text.includes('かつ'));assert.ok(!text.includes('未構造化'));
 assert.deepEqual(detailSearch(cards,new URLSearchParams({effect_target:'Vocal',skill_q:'6個以上'}),d),[cards[0]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams({effect_target:'Dance',skill_q:'6個以上'}),d),[]);
 assert.deepEqual(e.activation_condition,{status:'unsupported'});
});
test('Grow conditions attached to effects are labelled as growth, not activation',()=>{
 const e={metric:'appeal',scope:'grow',targets:['Dance'],value:3,unit:'multiplier',maximum:true,
 activation_condition:{status:'unsupported'},mechanic_condition:{status:'structured',role:'growth',
 expression:{operator:'any',terms:[{field:'status_granted',operator:'eq',value:'DanceUP'},{field:'status_granted',operator:'eq',value:'パッシブスキル強化'}]},
 events_per_level:1,level_up_timing:'next_turn',carry_over:true,reset_on_use:true}};
 const text=effectFactText(e);
 assert.ok(text.includes('Grow Lv上昇条件：'));assert.ok(text.includes('または'));assert.ok(text.includes('使用後Lv0'));
 assert.ok(!text.includes('発動条件：'));assert.ok(text.includes('最大3倍'));
});

test('resurrection and audience clear retain delayed trigger, exclusions and no instantaneous duration',()=>{
 const res={metric:'resurrection',targets:['メンタル'],unit:'percent',scope:'memory_link',value:10,turns:3,uses:1,trigger:'mental_zero'};
 const clear={metric:'audience_status_clear',targets:['観客ステータス'],unit:'boolean',scope:'base',value:1,audience:'all',excludes:['興味変動無効']};
 const d=new Map([['P1',{items:[{name:'memory',kind:'memory_appeal',memory_link_present:true,effect_details:{effects:[res]}}]}],['S1',{items:[{name:'clear',kind:'quick_skill',effect_details:{effects:[clear]}}]}]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams({effect_type:'resurrection',skill_q:'メンタルが0 思い出Link'}),d),[cards[0]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams({effect_type:'mental_recovery'}),d),[]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams({effect_type:'audience_status_clear',effect_turns:'1'}),d),[]);
 const text=effectFactText(clear);assert.ok(text.includes('興味変動無効を除く'));assert.ok(text.includes('アビリティは解除対象外'));
});
test('duet specific person, unit and current-turn addition are searchable without borrowing',()=>{
 const duet={metric:'duet',targets:['アピール履歴'],scope:'base',unit:'boolean',value:1,duet_target:{kind:'unit',name:'放課後クライマックスガールズ'}};
 const add={...duet,metric:'duet_add',duet_target:{kind:'formation'},timing:'current_turn'};
 const d=new Map([['P1',{items:[{name:'call',kind:'panel_live',effect_details:{effects:[duet,{...duet,duet_target:{kind:'idol',name:'小宮果穂'}}]}}]}],['S1',{items:[{name:'add',kind:'quick_skill',effect_details:{effects:[add]}}]}]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams({effect_type:'duet',skill_q:'放課後クライマックスガールズ'}),d),[cards[0]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams({effect_type:'duet_add',skill_q:'このターン 編成アイドル'}),d),[cards[1]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams({effect_type:'duet',skill_q:'放課後 小宮果穂'}),d),[]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams({effect_type:'duet_add',effect_turns:'1'}),d),[]);
});
test('duration ranges use the lower bound and maximum-only duration gives no minimum guarantee',()=>{
 const es=[
 {metric:'enthusiasm',targets:['熱狂'],unit:'boolean',scope:'grow',value:1,turn_range:{minimum:2,maximum:4},grant_count_maximum:3},
 {metric:'enthusiasm',targets:['熱狂'],unit:'boolean',scope:'grow',value:1,turns_maximum:3}
 ];
 const d=new Map([['P1',{items:[{name:'grow',kind:'panel_live',effect_details:{effects:es}}]}]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams({effect_type:'enthusiasm',effect_turns:'2'}),d),[cards[0]]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams({effect_type:'enthusiasm',effect_turns:'3'}),d),[]);
 assert.deepEqual(detailSearch(cards,new URLSearchParams({effect_type:'enthusiasm',effect_turns:'1',skill_q:'最大3ターン'}),d),[]);
 assert.ok(effectFactText(es[0]).includes('2～4ターン'));assert.ok(effectFactText(es[0]).includes('最大3つ付与'));
 const min=effectFactText({metric:'interest_minimum',targets:['興味'],unit:'multiplier',scope:'grow',value:0.1,turns:2});
 assert.ok(min.includes('最小値'));assert.ok(!min.includes('0.1～'));
});


test('reaction search separates the watch window from the granted duration and same-effect scope',()=>{
 const e={metric:'rate_up',targets:['Visual'],unit:'percent',value:100,scope:'plus',trigger:'reaction_evaded',trigger_turns:2,turns:4,uses:3};
 const other={metric:'rate_up',targets:['Dance'],unit:'percent',value:50,scope:'base',turns:5};
 const d=new Map([['P1',{items:[{name:'反応',kind:'panel_live',effect_details:{effects:[e,other]}}]}]]);
 assert.equal(detailSearch(cards,new URLSearchParams({effect_type:'rate_up',effect_target:'Visual',effect_turns:'4',skill_q:'反応待ち期間：2ターン 回避成功時 付与後4ターン'}),d).length,1);
 assert.equal(detailSearch(cards,new URLSearchParams({effect_type:'rate_up',effect_target:'Dance',skill_q:'回避成功時'}),d).length,0);
 assert.equal(detailSearch(cards,new URLSearchParams({effect_type:'rate_up',effect_target:'Visual',effect_turns:'5'}),d).length,0);
 assert.ok(effectFactText(e).includes('付与回数上限：3回'));
});
test('melancholy distinguishes self rivals and all units from mental costs',()=>{
 const es=['self','rivals','all_units'].map(recipient=>({metric:'melancholy',targets:['メンタル'],unit:'percent',value:10,scope:'base',turns:3,recipient,trigger:'appeal_phase_start'}));
 const d=new Map([['P1',{items:[{name:'減少',kind:'panel_live',effect_details:{effects:es}}]}]]);
 assert.equal(detailSearch(cards,new URLSearchParams({effect_type:'melancholy',skill_q:'対象：ライバル 翌ターン'}),d).length,1);
 assert.equal(detailSearch(cards,new URLSearchParams({effect_type:'mental_cost',skill_q:'メランコリー'}),d).length,0);
 for(const e of es)assert.ok(!effectFactText(e).includes('undefined'));
});
test('interest reversal and restriction remain separate from numeric interest and compound limits stay shared',()=>{
 const reverse={metric:'interest_reverse',targets:['興味'],unit:'boolean',value:1,scope:'base',turns:2};
 const limit={...reverse,metric:'interest_limit',turns:1,audience:'all'};
 assert.ok(effectFactText(reverse).includes('興味反転付与'));assert.ok(!effectFactText(reverse).includes('1倍'));
 assert.ok(effectFactText(limit).includes('全観客'));
 const d=new Map([['P1',{items:[{name:'興味',kind:'panel_live',effect_details:{effects:[reverse,limit]}}]}]]);
 assert.equal(detailSearch(cards,new URLSearchParams({effect_type:'interest',skill_q:'反転'}),d).length,0);
 assert.equal(detailSearch(cards,new URLSearchParams({effect_type:'interest_limit',effect_turns:'2'}),d).length,0);
 assert.ok(effectFactText({metric:'rate_up',targets:['Dance'],unit:'percent',value:60,scope:'base',trigger:'reaction_damage',trigger_turns:3,turns:3,uses:6,shared_uses:true}).includes('共有'));
});

test('consumption search binds removed statuses to the same appeal and distinguishes grants',()=>{
 const consume=statuses=>({statuses,timing:'after_appeal',quantity:'all',scaling:'status_count',passive_included:false});
 const a={metric:'appeal',targets:['Dance'],value:6,minimum:1.2,unit:'multiplier',scope:'base',status_consumption:consume([{target:'Visual',direction:'UP'}])};
 const b={metric:'appeal',targets:['Visual'],value:3,unit:'multiplier',scope:'link',status_consumption:consume([{target:'Dance',direction:'DOWN'}])};
 const grant={metric:'rate_up',targets:['Visual'],value:15,unit:'percent',scope:'base',turns:6};
 const d=new Map([['P1',{items:[{name:'消去例',kind:'panel_live',effect_details:{effects:[a,b,grant]}}]}]]);
 assert.equal(detailSearch(cards,new URLSearchParams({effect_type:'appeal_consume',effect_target:'Dance',skill_q:'消去対象：VisualUP'}),d).length,1);
 assert.equal(detailSearch(cards,new URLSearchParams({effect_type:'appeal_consume',effect_target:'Visual',skill_q:'消去対象：VisualUP'}),d).length,0);
 assert.equal(detailSearch(cards,new URLSearchParams({effect_type:'appeal_consume',effect_turns:'1'}),d).length,0);
 assert.equal(detailSearch(cards,new URLSearchParams({effect_type:'rate_up',skill_q:'消去対象：VisualUP'}),d).length,0);
 assert.equal(detailSearch(cards,new URLSearchParams({effect_type:'appeal',skill_q:'消去対象：DanceDOWN Link'}),d).length,1);
 assert.ok(effectFactText(a).includes('このアピール直後'));assert.ok(effectFactText(a).includes('パッシブは対象外'));
});


test('recipient filters bind to one effect and never infer missing self scope',()=>{
 const base={unit:'percent',scope:'base',value:10,turns:3};
 const es=[{...base,metric:'rate_up',targets:['Visual'],recipient:'all_units'},
  {...base,metric:'rate_up',targets:['Dance']},
  {...base,metric:'rate_down',targets:['Visual'],recipient:'rivals'},
  {metric:'mental_cost',targets:['メンタル'],unit:'percent',scope:'base',value:10,recipient:'self'},
  {metric:'appeal',targets:['Vocal'],unit:'multiplier',scope:'base',value:3,audience:'all'}];
 const d=new Map([['P1',{items:[{name:'範囲',kind:'panel_live',effect_details:{effects:es}}]}]]);
 const count=p=>detailSearch(cards,new URLSearchParams(p),d).length;
 assert.equal(count({effect_recipient:'all_units',effect_target:'Visual',effect_type:'rate_up'}),1);
 assert.equal(count({effect_recipient:'all_units',effect_target:'Dance'}),0);
 assert.equal(count({effect_recipient:'rivals',effect_type:'mental_cost'}),0);
 assert.equal(count({effect_recipient:'self',effect_type:'mental_cost'}),1);
 assert.equal(count({effect_recipient:'self',effect_type:'rate_up'}),0);
 assert.equal(count({effect_recipient:'all_audience',effect_type:'appeal'}),1);
 assert.equal(count({effect_recipient:'all_units',effect_type:'appeal'}),0);
 assert.equal(count({effect_recipient:'rivals',skill_q:'対象：全ユニット'}),0);
});
test('delayed relax recovery remains distinct from instant mental recovery',()=>{
 const es=[{metric:'relax',targets:['リラックス'],unit:'percent',scope:'base',value:5,turns:3,recipient:'all_units',trigger:'appeal_phase_start',starts_next_turn:true},
 {metric:'mental_recovery',targets:['メンタル'],unit:'percent',scope:'base',value:10,recipient:'all_units'}];
 const d=new Map([['P1',{items:[{name:'回復',kind:'panel_live',effect_details:{effects:es}}]}]]);
 assert.equal(detailSearch(cards,new URLSearchParams({effect_recipient:'all_units',effect_type:'relax',skill_q:'翌ターン 最大メンタル アピールフェイズ開始時'}),d).length,1);
 assert.equal(detailSearch(cards,new URLSearchParams({effect_recipient:'all_units',effect_type:'mental_recovery',skill_q:'翌ターン'}),d).length,0);
 assert.ok(!effectFactText(es[1]).includes('翌ターン'));
});
