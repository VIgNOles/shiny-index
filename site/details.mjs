export const kindNames={panel_live:'パネルのライブスキル',mb_live:'MBライブスキル',generated_live:'生成ライブスキル',panel_passive:'パッシブスキル',unique_ability:'固有アビリティ',cap_increase:'上限UP',memory_appeal:'思い出アピール',possessed_live:'所持ライブスキル',support_skill:'サポートスキル',quick_skill:'クイックスキル'};
export const mechanicNames={link:'Link',plus:'Plus',change:'Change',grow:'Grow / GrowUp',refrain:'Refrain'};
export const liveKinds=new Set(['panel_live','mb_live','generated_live','possessed_live']);
const normalized=value=>String(value??'').normalize('NFKC').toLocaleLowerCase('ja');
export function factText(fact){
 const target=fact.targets?.join(' & ')??fact.target??'';
 if(fact.metric==='appeal')return target+' '+fact.value+'倍';
 if(fact.metric==='appeal_range')return target+' '+fact.minimum+'～'+fact.maximum+'倍（条件未構造化）';
 if(fact.metric==='appeal_maximum')return target+' 最大'+fact.value+'倍（条件未構造化）';
 if(fact.metric==='rate')return target+' '+fact.value+'% '+fact.direction;
 if(fact.metric==='activation_probability')return '発動確率 '+fact.value+'%';
 if(fact.metric==='activation_limit')return '最大発動 '+fact.value+'回';
 return '';
}
export const conditionNames={mental:'メンタル',turn:'ターン',position:'編成ポジション',participant:'参加アイドル',status:'付与効果',history:'アピール履歴',keyword:'所持キーワード',other:'その他の条件'};
export function itemActivationCondition(item){return item.activation_condition_v3??item.activation_condition_v2??item.activation_condition;}
export function activationConditionTypes(condition){
 if(condition?.status!=='structured'||!condition.expression)return [];
 const visit=p=>{
  if(p.terms&&['all','any'].includes(p.operator))return p.terms.flatMap(visit);
  const field=p.field;
  if(['mental_percent','maximum_mental'].includes(field))return ['mental'];
  if(['status_count','audience_status','idol_appeal_boost','unit_appeal_boost_all'].includes(field))return ['status'];
  if(['history_participant','history_participant_count','history_unit_all','history_unit_count','history_genre_count','history_memory_present'].includes(field))return ['history'];
  if(['participant','unit_all_participants','unit_participant_count','unit_only_participant'].includes(field))return ['participant'];
  if(['position','unit_all_formation'].includes(field))return ['position'];
  if(field==='turn')return ['turn'];
  if(field==='owner_keyword')return ['keyword'];
  if(['star_count','audience_count','rank','heal_count','unit_type_count','generated_live_present'].includes(field))return ['other'];
  return [];
 };
 return [...new Set(visit(condition.expression))];
}
export function activationConditionType(condition){return activationConditionTypes(condition)[0]??'';}
export function activationConditionText(condition){
 if(condition?.status!=='structured'||!condition.expression)return '';
 const format=p=>{
  if(p.terms&&['all','any'].includes(p.operator)){
   const parts=p.terms.map(format);return parts.every(Boolean)?'（'+parts.join(p.operator==='all'?' かつ ':' または ')+'）':'';
  }
  const n=p.value,suffix=p.operator==='gte'?'以上':p.operator==='lte'?'以下':'';
  if(p.field==='mental_percent')return 'メンタル'+n+'%'+suffix;
  if(p.field==='maximum_mental')return '最大メンタル'+n+suffix;
  if(p.field==='turn')return n+'ターン'+(p.operator==='lte'?'以前':'以降');
  if(p.field==='position')return ({vocal:'Vocal',dance:'Dance',visual:'Visual',center:'Center',leader:'Leader'}[n])+'担当';
  if(p.field==='owner_keyword')return 'スキル所持者のキーワード '+n;
  if(p.field==='participant')return '参加アイドル '+n;
  if(p.field==='history_participant')return 'アピール履歴 '+n;
  if(p.field==='status_count')return p.status+'が'+n+'個以上付与';
  if(p.field==='generated_live_present')return 'ライブスキル生成あり';
  if(p.field==='unit_all_participants')return n+'全員が参加';
  if(p.field==='unit_all_formation')return '編成に'+n+'全員';
  if(p.field==='unit_only_participant')return p.unit+'から'+n+'のみが参加';
  if(p.field==='unit_participant_count')return p.unit+'の参加者'+n+'人'+suffix;
  if(p.field==='history_unit_all')return '履歴に'+n+'全員';
  if(p.field==='history_unit_count')return '履歴に'+p.unit+'のアイドル'+n+'人'+suffix;
  if(p.field==='history_participant_count')return '履歴に'+p.idol+'が'+n+'個'+suffix;
  if(p.field==='history_genre_count')return '履歴に'+n+'ジャンル'+suffix;
  if(p.field==='history_memory_present')return '履歴に思い出アピール';
  if(p.field==='audience_status')return '観客に'+n+'付与';
  if(p.field==='idol_appeal_boost')return n+'のアピール倍率UPが付与';
  if(p.field==='unit_appeal_boost_all')return n+'全員のアピール倍率UPが付与';
  const labels={star_count:'スター',audience_count:'観客',rank:'順位',heal_count:'回復回数',unit_type_count:'編成ユニット種類'};
  const unit={rank:'位',heal_count:'回'};
  return labels[p.field]?(labels[p.field]+n+(unit[p.field]??'')+suffix):'';
 };
 return format(condition.expression);
}
export function generationParentText(item){return (item.generated_from_names??(item.generated_from_name?[item.generated_from_name]:[])).join(' / ');}
export function detailCoverageText(coverage,total){
 const held=coverage.status_counts.missing_page_on_hold??0;
 const conditionCounts=coverage.activation_condition_current_counts??coverage.activation_condition_search_counts??coverage.activation_condition_counts;
 const missing=Math.max(0,total-coverage.detail_card_count-held);
 const notes=[missing?'未収録 '+missing+'件':'',held?'個別ページなし '+held+'件（保留）':''].filter(Boolean);
 return '詳細 '+coverage.detail_card_count+' / '+total+'カード収録。'+(notes.length?notes.join('／')+'。':'')+'数値・条件は一部のみ収録。'+(conditionCounts?'パッシブ発動条件 '+(conditionCounts.structured??0)+' / '+Object.values(conditionCounts).reduce((a,b)=>a+b,0)+'項目対応'+(coverage.activation_condition_current_counts?'（未対応'+(conditionCounts.unsupported??0)+'項目）':'')+'。':'');
}

export const effectNames={appeal:'ライブ・思い出のアピール',support_gain:'能力・SPの獲得',support_recovery:'体力回復',support_cost_down:'体力消費軽減',support_trouble_down:'トラブル率軽減',support_rest_gain:'休む時の回復量増加',support_bond:'初期の絆',support_tension_protection:'テンション低下防止',support_presence_up:'レッスン滞在率UP',support_event_rate:'イベント発生率UP',support_knowhow_rate:'ノウハウ発現率UP',support_location_level:'施設のレベルUP',support_perfect:'パーフェクト発生',support_excellent:'エクセレント強化',support_advice_rate:'アドバイス抽選率UP',appeal_boost:'アピール値UP',memory_gain_boost:'思い出ゲージ増加量UP',base_stat_boost:'基礎能力値UP',rate_up:'継続するUP効果',rate_down:'継続するDOWN効果',rate_cut:'継続するCUT効果',interest:'興味倍率',exchange_count_up:'交換数UP',mental_recovery:'メンタル回復',mental_cost:'自身のメンタル消費',memory_gauge_gain:'思い出ゲージ増加',relax:'リラックス付与',passive_boost:'パッシブスキル強化',refrain:'リフレイン',resurrection:'リザレクション付与',audience_status_clear:'観客ステータス解除',duet:'デュエット',duet_add:'デュエット追加',interest_minimum:'興味倍率（最小値）',charm:'魅了付与',enthusiasm:'熱狂付与',interest_reverse:'興味反転付与',interest_limit:'興味限定付与',melancholy:'メランコリー付与',appeal_consume:'消去付きアピール'};
export const triggerNames={produce_start:'プロデュース開始時',missed_promise:'約束を守れなかった時',rest:'休むを選択時',lesson_or_work:'レッスン・お仕事選択時',unit_member_present:'行動場所に自分以外のユニットメンバーがいる時',tension_max:'テンション最高で一緒に行動時',audition_first:'オーディション1位',vocal_lesson:'一緒にボーカルレッスン',dance_lesson:'一緒にダンスレッスン',visual_lesson:'一緒にビジュアルレッスン',radio:'一緒にラジオ出演',talk:'一緒にトークショー出演',magazine:'一緒に雑誌撮影',talk_event:'一緒にトークイベント出演',solo_vocal_lesson:'ボーカルレッスン',solo_dance_lesson:'ダンスレッスン',solo_radio:'ラジオ出演',no_trouble:'スキル発動時に一緒に行動し、トラブルなし',excellent:'一緒に行動してエクセレント発生時',knowhow_acquired:'ノウハウブック獲得時',always:'常時',say_halo:'say "Halo"編',appeal_phase_start:'アピールフェイズ開始時',turn_2:'2ターン目',mental_zero:'メンタルが0になった時に回復',reaction_evaded:'観客のリアクションを回避成功時に付与',reaction_damage:'観客のリアクションでダメージを受けた時に付与'};
const scopeNames={base:'',link:'Link',plus:'Plus',change:'Change',grow:'Grow',refrain:'Refrain',memory_link:'思い出Link',memory_charge:'思い出チャージ'};
export function effectAmount(a,level){
 if(a.amount_unknown||a.unknown)return '量未記載';
 if(a.formula){const f=a.formula;if(level!=null)return String(f.offset+f.coefficient*level);return (f.offset?f.offset+' + ':'')+'スキルLv×'+f.coefficient;}
 return String(a.value??'');
}
export function mechanicConditionText(rule){
 if(rule?.status!=='structured'||!rule.expression)return '';
 const format=p=>{
  if(p.terms&&['all','any'].includes(p.operator)){
   const terms=p.terms.map(format);return terms.every(Boolean)?'（'+terms.join(p.operator==='all'?' かつ ':' または ')+'）':'';
  }
  if(p.field==='active_passive_count')return '現在発動中のパッシブスキル'+p.value+'個以上';
  if(p.field==='idol_appeal_boost_count')return p.idol+'のアピール倍率UPが'+p.value+'個以上付与';
  if(p.field==='status_granted')return p.value+'の付与';
  if(p.field==='idol_appeal_boost_granted')return p.value+'のアピール倍率UPの付与';
  if(p.field==='history_unit_added')return '履歴に'+p.value+'のアイドルを追加';
  if(p.field==='audience_reaction_targeted')return '観客のリアクション対象になる';
  return activationConditionText({status:'structured',expression:p});
 };
 const text=format(rule.expression);if(!text)return '';
 if(rule.role==='activation')return '発動条件：'+text;
 if(rule.role==='growth'){
  const grants=p=>p.terms?p.terms.every(grants):['status_granted','idol_appeal_boost_granted'].includes(p.field);
  return 'Grow Lv上昇条件：'+text+' / '+rule.events_per_level+(grants(rule.expression)?'個付与ごと':'回ごと')+'にLv上昇（翌ターン反映・端数は繰越・使用後Lv0）';
 }
 return '';
}
export function mechanicRuleText(rule){return (scopeNames[rule.scope]??'')+'：'+mechanicConditionText(rule.condition);}
export function mechanicRuleMatches(item,rule,params){
 if(hasEffectFilters(params))return false;
 const words=normalized(params.get('skill_q')).trim().split(/\s+/).filter(Boolean);
 return words.every(word=>normalized([...itemSearchParts(item),mechanicRuleText(rule)].join(' ')).includes(word));
}

export function effectFactText(e,level){
 const target=e.targets.join(' / '),unit=e.metric==='refrain'?'ターン前':{points:'',percent:'%',multiplier:'倍',boolean:''}[e.unit];
 let result=(scopeNames[e.scope]?scopeNames[e.scope]+'：':'')+(effectNames[e.metric]??e.metric)+' · '+target+(e.cap?'上限':'');
 if(e.unit!=='boolean')result+=' '+(e.maximum?'最大':'')+(e.minimum!=null?e.minimum+'～':'')+effectAmount(e,level)+(e.amount_unknown?'':unit);
 if(e.status_consumption){
  const c=e.status_consumption;
  result+=' / 消去対象：'+c.statuses.map(s=>s.target+s.direction).join('・');
  result+=' / このアピール直後に対象を全て消去（残りターン数に関係なし）';
  result+=' / 対象ステータス効果の合計数で倍率UP（パッシブは対象外）';
 }
 if(e.appeal_order)result+=' / 必ず'+(e.appeal_order==='first'?'最初':'最後')+'にアピール';
 if(e.audience==='all')result+=' / 全観客';
 if(e.turns)result+=e.trigger_turns?' / 付与後'+e.turns+'ターン':' ['+e.turns+'ターン]';
 if(e.turn_range)result+=' ['+e.turn_range.minimum+'～'+e.turn_range.maximum+'ターン]';
 if(e.turns_maximum)result+=' [最大'+e.turns_maximum+'ターン]';
 if(e.grant_count_maximum)result+=' / 最大'+e.grant_count_maximum+'つ付与';
 if(e.excludes)result+=' / '+e.excludes.join('・')+'を除く（アビリティは解除対象外）';
 if(e.duet_target){
  const t=e.duet_target;
  result+=' / 対象：'+(t.kind==='formation'?'編成アイドル':t.name);
  result+=t.kind==='idol'?'（参加中の指定アイドル）':'（参加中の使用者以外から1人）';
 }
 if(e.timing==='current_turn')result+=' / このターンのアピールに追加';

 if(e.recipient)result+=' / 対象：'+{self:'自身',rivals:'ライバル',all_units:'全ユニット'}[e.recipient];
 if(e.metric==='melancholy')result+=' / 付与の翌ターンから現在メンタルに対する減少';
 if(e.trigger_turns)result+=' / 反応待ち期間：'+e.trigger_turns+'ターン';
 if(e.trigger)result+=' / '+triggerNames[e.trigger];
 if(e.probability)result+=' / '+(e.probability.unknown?'発動確率未記載':effectAmount(e.probability,level)+'%の確率');
 if(e.per_member)result+=' / 1人につき';
 if(e.advice)result+=' / '+e.advice+'アドバイス（'+(e.degree==='large'?'大きく':'少し')+'増加、スキルLv依存）';
 if(e.source_notation)result+=' / 原文の助詞表記に誤記あり（取得原文は保持）';
 if(e.uses)result+=' / '+(e.trigger_turns?'付与回数上限：':'')+e.uses+'回'+(e.shared_uses?'（同じ反応効果の付与で共有）':'');
 const r=e.restrictions??{};
 if(r.group)result+=' / グループ：'+r.group;
 if(r.idols)result+=' / 対象アイドル：'+r.idols.join('・');
 if(r.unit_types_min)result+=' / 編成ユニット'+r.unit_types_min+'種類以上';
 if(r.unit_types_max)result+=' / 編成ユニット'+r.unit_types_max+'種類以下';
 if(r.history_genres)result+=' / 履歴'+r.history_genres+'ジャンルのみ';
 if(r.ignore_interest)result+=' / 興味無視';
 if(r.until_damage)result+=' / ダメージを受けるまで';
 if(r.scaling)result+=' / '+{turns_descending:'経過ターンが短いほど効果UP',turns_ascending:'経過ターンが長いほど効果UP',memory:'思い出ゲージが多いほど効果UP',history:'履歴が多いほど効果UP',mental:'メンタルが多いほど効果UP',mental_descending:'メンタルが少ないほど効果UP',attention:'注目度が高いほど効果UP',attention_descending:'注目度が低いほど効果UP',heal_count:'回復回数増加で効果UP',evasion:'回避率が高いほど効果UP',unit_types:'所属ユニットが多いほど効果UP',mental_spent:'減少値が多いほど効果UP'}[r.scaling];
 if(e.mechanic_condition)result+=' / '+mechanicConditionText(e.mechanic_condition);
 else if(e.activation_condition)result+=' / 発動条件：'+(activationConditionText(e.activation_condition)||'未構造化。Wikiで確認');
 if(e.restriction_status==='partial')result+=' / 追加条件はWikiで確認';
 return result;
}
export function hasEffectFilters(params){return ['effect_type','effect_target','effect_turns'].some(k=>params.has(k)&&params.get(k));}
export function effectMatches(e,params){
 const type=params.get('effect_type');
 if(type==='appeal_consume'){if(e.metric!=='appeal'||!e.status_consumption)return false;}
 else if(type&&e.metric!==type)return false;
 if(params.get('effect_target')&&!e.targets.includes(params.get('effect_target')))return false;
 if(params.get('effect_turns')){const n=Number(params.get('effect_turns'));const guaranteed=e.turns??e.turn_range?.minimum;if(!Number.isInteger(n)||n<1||!guaranteed||guaranteed<n)return false;}
 return true;
}

const itemSearchParts=item=>[item.name,kindNames[item.kind],activationConditionText(itemActivationCondition(item)),...(item.mechanics??[]).map(m=>mechanicNames[m]),...(item.cap_targets??[]),...(item.kind==='generated_live'?[generationParentText(item)]:[])];
export function effectSearchMatches(item,e,params){
 const words=normalized(params.get('skill_q')).trim().split(/\s+/).filter(Boolean);
 return effectMatches(e,params)&&words.every(word=>normalized([...itemSearchParts(item),effectFactText(e)].join(' ')).includes(word));
}

export function detailSearch(cards,params,details){
 const q=normalized(params.get('skill_q')).trim().split(/\s+/).filter(Boolean);
 const kinds=params.getAll('skill_kind'),mechanics=params.getAll('mechanic');
 const condition=params.get('skill_condition')??'';
 const only=params.get('detail_status')==='available';
 const effectFilter=hasEffectFilters(params);
 if(!q.length&&!kinds.length&&!mechanics.length&&!only&&!condition&&!effectFilter)return cards;
 return cards.filter(card=>{
  const detail=details.get(card.card_id);
  if(!detail)return false;
  if(!q.length&&!kinds.length&&!mechanics.length&&!condition&&!effectFilter)return true;
  return detail.items.some(item=>{
   if(kinds.length&&!kinds.includes(item.kind))return false;
   if(condition&&!activationConditionTypes(itemActivationCondition(item)).includes(condition))return false;
   if(mechanics.length&&(!liveKinds.has(item.kind)||!mechanics.some(value=>(item.mechanics??[]).includes(value))))return false;
   const common=itemSearchParts(item);
   const effects=item.effect_details?.effects??[];
   if(effectFilter)return effects.some(e=>effectSearchMatches(item,e,params));
   const rules=item.effect_details?.mechanic_conditions??[];
   const baseEffects=effects.filter(e=>!['memory_link','memory_charge'].includes(e.scope)).map(e=>effectFactText(e));
   const views=[[...common,...baseEffects,...rules.filter(r=>r.slot==='effect').map(mechanicRuleText),...(item.numeric_facts??[]).map(factText),...(item.random_effect_options?.length?['ランダム',...item.random_effect_options.map(factText)]:[])]];
   if(item.memory_link_present)views.push([...common,'Link追加効果',...effects.filter(e=>e.scope==='memory_link').map(e=>effectFactText(e)),...rules.filter(r=>r.slot==='link').map(mechanicRuleText),...(item.memory_link_facts??[]).map(factText)]);
   if(item.memory_charge_present)views.push([...common,'チャージ追加効果',...effects.filter(e=>e.scope==='memory_charge').map(e=>effectFactText(e)),...rules.filter(r=>r.slot==='charge').map(mechanicRuleText),...(item.memory_charge_facts??[]).map(factText)]);
   return views.some(parts=>{const text=normalized(parts.join(' '));return q.every(word=>text.includes(word));});
  });
 });
}
export async function loadDetails(baseVersion,version){
 if(!/^d1-[0-9a-f]{16}$/.test(version??''))throw Error('詳細版未指定');
 const base='details/'+version+'/';
 const manifestResponse=await fetch(base+'manifest.json');
 if(!manifestResponse.ok)throw Error('詳細版情報を取得できません');
 const manifest=await manifestResponse.json();
 if(manifest.detail_version!==version||manifest.base_dataset_version!==baseVersion)throw Error('詳細データの版不一致');
 const response=await fetch(base+'details.json');
 if(!response.ok)throw Error('詳細データを取得できません');
 const bytes=await response.arrayBuffer();
 const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
 if(hash!==manifest.files['details.json'])throw Error('詳細データの検証に失敗');
 const doc=JSON.parse(new TextDecoder().decode(bytes));
 if(doc.meta.detail_schema!=='1.0'||doc.meta.detail_version!==version||doc.meta.base_dataset_version!==baseVersion)throw Error('詳細データの版不一致');
 return doc;
}
