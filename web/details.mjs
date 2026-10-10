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
export function generationParentText(item){return (item.generated_from_names??(item.generated_from_name?[item.generated_from_name]:[])).join(' / ');}
export function detailCoverageText(coverage,total){
 const held=coverage.status_counts.missing_page_on_hold??0;
 const missing=Math.max(0,total-coverage.detail_card_count-held);
 const notes=[missing?'未収録 '+missing+'件':'',held?'個別ページなし '+held+'件（保留）':''].filter(Boolean);
 return '詳細 '+coverage.detail_card_count+' / '+total+'カード収録。'+(notes.length?notes.join('／')+'。':'')+'数値・条件は一部のみ収録。';
}
export function detailSearch(cards,params,details){
 const q=normalized(params.get('skill_q')).trim().split(/\s+/).filter(Boolean);
 const kinds=params.getAll('skill_kind'),mechanics=params.getAll('mechanic');
 const only=params.get('detail_status')==='available';
 if(!q.length&&!kinds.length&&!mechanics.length&&!only)return cards;
 return cards.filter(card=>{
  const detail=details.get(card.card_id);
  if(!detail)return false;
  if(!q.length&&!kinds.length&&!mechanics.length)return true;
  return detail.items.some(item=>{
   if(kinds.length&&!kinds.includes(item.kind))return false;
   if(mechanics.length&&(!liveKinds.has(item.kind)||!mechanics.some(value=>(item.mechanics??[]).includes(value))))return false;
   const common=[item.name,kindNames[item.kind],...(item.mechanics??[]).map(m=>mechanicNames[m]),...(item.cap_targets??[]),...(item.kind==='generated_live'?[generationParentText(item)]:[])];
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
