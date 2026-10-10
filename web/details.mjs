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
export const conditionNames={mental:'メンタル',turn:'ターン',position:'編成ポジション',participant:'参加アイドル',status:'付与効果',history:'アピール履歴',other:'その他の条件'};
export function itemActivationCondition(item){return item.activation_condition_v2??item.activation_condition;}
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
 const conditionCounts=coverage.activation_condition_search_counts??coverage.activation_condition_counts;
 const missing=Math.max(0,total-coverage.detail_card_count-held);
 const notes=[missing?'未収録 '+missing+'件':'',held?'個別ページなし '+held+'件（保留）':''].filter(Boolean);
 return '詳細 '+coverage.detail_card_count+' / '+total+'カード収録。'+(notes.length?notes.join('／')+'。':'')+'数値・条件は一部のみ収録。'+(conditionCounts?'パッシブ発動条件 '+(conditionCounts.structured??0)+' / '+Object.values(conditionCounts).reduce((a,b)=>a+b,0)+'項目対応。':'');
}
export function detailSearch(cards,params,details){
 const q=normalized(params.get('skill_q')).trim().split(/\s+/).filter(Boolean);
 const kinds=params.getAll('skill_kind'),mechanics=params.getAll('mechanic');
 const condition=params.get('skill_condition')??'';
 const only=params.get('detail_status')==='available';
 if(!q.length&&!kinds.length&&!mechanics.length&&!only&&!condition)return cards;
 return cards.filter(card=>{
  const detail=details.get(card.card_id);
  if(!detail)return false;
  if(!q.length&&!kinds.length&&!mechanics.length&&!condition)return true;
  return detail.items.some(item=>{
   if(kinds.length&&!kinds.includes(item.kind))return false;
   if(condition&&!activationConditionTypes(itemActivationCondition(item)).includes(condition))return false;
   if(mechanics.length&&(!liveKinds.has(item.kind)||!mechanics.some(value=>(item.mechanics??[]).includes(value))))return false;
   const common=[item.name,kindNames[item.kind],activationConditionText(itemActivationCondition(item)),...(item.mechanics??[]).map(m=>mechanicNames[m]),...(item.cap_targets??[]),...(item.kind==='generated_live'?[generationParentText(item)]:[])];
   const views=[[...common,...(item.numeric_facts??[]).map(factText),...(item.random_effect_options?.length?['ランダム',...item.random_effect_options.map(factText)]:[])]];
   if(item.memory_link_present)views.push([...common,'Link追加効果',...(item.memory_link_facts??[]).map(factText)]);
   if(item.memory_charge_present)views.push([...common,'チャージ追加効果',...(item.memory_charge_facts??[]).map(factText)]);
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
