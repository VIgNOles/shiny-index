import {effectGroups,filterCatalog,applicableItems,performanceIssues,liveKinds,searchEffects,detailMatches,matchDetailItem,hasSkillConditions,mechanicRuleText,mechanicRuleMatches,recipientNames,effectNames,effectTargets,effectFactText,effectMatches,effectSearchMatches,hasEffectFilters,detailSearch,loadDetails,detailCoverageText,generationParentText,activationConditionText,itemActivationCondition,conditionNames,kindNames,mechanicNames,factText} from './details.mjs';
import {search,seriesNames,browseOptions,officialUnits,parseDatePart} from './search.mjs';

const $=id=>document.getElementById(id);
const labels={
 card_kind:'P／S',rarity:'レアリティ',acquisition_category:'入手区分',
 series_ids:'シリーズ・企画',review_status:'確認状態',collab_work:'コラボ作品'
};
const display={
 permanent_gacha:'恒常ガシャ',limited_gacha:'期間限定',collection_gacha:'コレクションガシャ',
 collaboration_gacha:'コラボガシャ',event_reward:'イベント報酬',initial:'初期所持',
 gacha_bonus:'ガシャ特典',other_bonus:'その他特典',mission:'ミッション',
 campaign:'キャンペーン・配布',exchange:'交換',other:'その他',
 unknown:'不明',wiki_only:'Wikiのみ確認',needs_review:'要確認',
 official_checked:'公式照合済み',user_evidence_checked:'管理者資料確認済み',
 ...seriesNames
};
const text=value=>display[value]??value??'不明';
const seriesText=value=>seriesNames[value]??'その他（'+value+'）';
const add=(parent,tag,value,className)=>{
 const element=document.createElement(tag);
 element.textContent=value;
 if(className)element.className=className;
 parent.append(element);
 return element;
};
const sourceNames={
 W02:'Pカード一覧',W03:'Sカード一覧',W04:'Sカード分冊',
 W05:'アイドル追加順',W07:'コラボアイドル',W08:'アイドルロード',W09:'ガシャ'
};
const wikiLink=value=>{
 if(!value)return null;
 try{
  const url=new URL(value);
  return url.protocol==='https:'&&url.hostname==='wikiwiki.jp'&&
   url.pathname.startsWith('/shinycolors/')?url.href:null;
 }catch{return null;}
};

try{
 const base='data/'+window.DATA_VERSION+'/';
 const response=await fetch(base+'cards.json');
 if(!response.ok)throw Error('HTTP '+response.status);
 const doc=await response.json();
 if(doc.meta.dataset_version!==window.DATA_VERSION)throw Error('版不一致');
 const {cards,meta,coverage}=doc;
 let detailDoc=null,detailError='';
 try{detailDoc=await loadDetails(window.DATA_VERSION,window.DETAIL_VERSION);}
 catch(error){detailError=error.message;}
 const detailMap=new Map((detailDoc?.cards??[]).map(card=>[card.card_id,card]));
 $('detail-coverage').textContent=detailDoc?
  detailCoverageText(detailDoc.coverage,cards.length):
  '詳細情報を読み込めませんでした：'+detailError+'。基本情報の検索は利用できます。';
 $('skill-controls').disabled=!detailDoc;
 const effectCounts=detailDoc?.coverage.effect_detail_counts;
 $('effect-coverage-text').textContent=effectCounts?
  'サポートスキル '+(effectCounts.support_skill?.structured??0)+'項目、固有アビリティ '+(effectCounts.unique_ability?.structured??0)+'項目の効果を検索できます。ライブ・思い出はアピール倍率や、継続ターンを読み取れた効果が対象です。未対応の複合効果もあるため、検索結果が0件でも該当カードがないとは限りません。':
  'このデータ版は効果の種類・対象・継続ターンの検索に未対応です。';
 if(detailDoc){
  $('detail-version').textContent='詳細データ版 '+detailDoc.meta.detail_version+' / 更新日時 '+detailDoc.meta.published_at;
  for(const [file,label] of [['details.json','詳細 JSON'],['manifest.json','詳細の版情報']]){
   const link=add($('detail-downloads'),'a',label);link.href='details/'+detailDoc.meta.detail_version+'/'+file;
  }
 }

 const sourceUrls=new Map();
 for(const source of doc.sources??[]){
  const url=wikiLink(source.url);
  if(!url||!source.source_ref)continue;
  if(!sourceUrls.has(source.card_id))sourceUrls.set(source.card_id,new Map());
  sourceUrls.get(source.card_id).set(source.source_ref,url);
 }
 let params=new URLSearchParams(location.search);
 let editing=false,appliedParams=null,panelClosing=false,cancelMessage='';
 const pendingSearch=new Map();
 const cancelPending=()=>{for(const pending of pendingSearch.values())clearTimeout(pending.timer);pendingSearch.clear();};
 const flushPending=()=>{const tasks=[...pendingSearch.values()];cancelPending();for(const task of tasks)task.apply();};
 let shown=[];
 let expandedIds=new Set();
 if(params.has('missing')){params.delete('missing');history.replaceState(null,'',location.pathname+(params.size?'?'+params:'')+location.hash);}
 const urlForParams=()=>location.pathname+(params.size?'?'+params.toString():'')+location.hash;
 const commitParams=(mode='push')=>{
  if(editing){renderControls();renderPreview();return;}
  const next=urlForParams();
  if(next!==location.pathname+location.search+location.hash)
   history[mode==='replace'?'replaceState':'pushState'](null,'',next);
  render();
 };

 const catalog=filterCatalog(cards,detailMap);
 const availableEffects=[...(detailMap.values())].flatMap(c=>c.items.flatMap(i=>searchEffects(i)));
 for(const [id,key] of [['effect-type','effect_type'],['effect-target','effect_target'],['effect-turns','effect_turns'],['effect-recipient','effect_recipient']]){
  $(id).addEventListener('change',event=>{if(event.target.value)params.set(key,event.target.value);else params.delete(key);commitParams();});
 }
 for(const [value,label] of Object.entries(conditionNames))$('skill-condition').add(new Option(label,value));
 for(const [value,label] of [['live','ライブスキル'],['panel_passive','パッシブスキル'],['support_skill','育成サポートスキル'],['memory_appeal','思い出アピール'],['cap_increase','ステータス上限UP'],['unique_ability','固有アビリティ'],['quick_skill','クイックスキル']])$('skill-kind').add(new Option(label,value));
 for(const value of liveKinds){const label=add($('live-origin-options'),'label','','filter-option'),input=document.createElement('input');input.type='checkbox';input.value=value;input.name='live_origin';label.append(input,document.createTextNode(kindNames[value]));}
 $('live-origin-options').addEventListener('change',()=>{params.delete('skill_kind');const values=[...$('live-origin-options').querySelectorAll('input:checked')].map(i=>i.value);for(const v of values.length?values:liveKinds)params.append('skill_kind',v);commitParams();});
 for(const [value,label] of Object.entries(mechanicNames)){
  const wrapper=add($('skill-mechanics'),'label','','filter-option');
  const input=document.createElement('input');input.type='checkbox';input.value=value;input.name='mechanic';
  wrapper.append(input,document.createTextNode(label));
 }
 const bindSearch=(id,key)=>{
  let composing=false;const input=$(id);
  const cancel=()=>{if(pendingSearch.has(id)){clearTimeout(pendingSearch.get(id).timer);pendingSearch.delete(id);}};
  const apply=()=>{if(input.value)params.set(key,input.value);else params.delete(key);commitParams('replace');};
  const schedule=()=>{cancel();const timer=setTimeout(()=>{pendingSearch.delete(id);apply();},180);pendingSearch.set(id,{timer,apply});};
  input.addEventListener('compositionstart',()=>{composing=true;cancel();});
  input.addEventListener('compositionend',()=>{composing=false;schedule();});
  input.addEventListener('input',event=>{if(!composing&&!event.isComposing)schedule();});
 };
 bindSearch('skill-q','skill_q');
 $('skill-kind').addEventListener('change',event=>{
  if(event.target.value==='__mixed__')return;params.delete('skill_kind');if(event.target.value==='live')for(const v of liveKinds)params.append('skill_kind',v);else if(event.target.value)params.set('skill_kind',event.target.value);commitParams();
 });
 $('skill-condition').addEventListener('change',event=>{
  if(event.target.value)params.set('skill_condition',event.target.value);else params.delete('skill_condition');commitParams();
 });
 $('skill-mechanics').addEventListener('change',()=>{
  params.delete('mechanic');for(const input of $('skill-mechanics').querySelectorAll('input:checked'))params.append('mechanic',input.value);commitParams();
 });
 $('detail-available').addEventListener('change',event=>{
  if(event.target.checked)params.set('detail_status','available');else params.delete('detail_status');commitParams();
 });
 $('skill-filters').open=['skill_q','skill_kind','skill_condition','mechanic','detail_status','effect_type','effect_target','effect_turns','effect_recipient'].some(key=>params.has(key));

 const filterOrder={
  card_kind:['P','S'],rarity:['UR','SSR','SR','R','N'],
  series_ids:['twilights','casting','mysongs','parallel','prelude','birthday','vote_selection','expansion','axe8'],
  acquisition_category:['permanent_gacha','limited_gacha','collection_gacha','collaboration_gacha',
   'event_reward','gacha_bonus','mission','campaign','exchange','other_bonus','initial']
 };
 const filterFields=['card_kind','rarity','series_ids','acquisition_category'];
 const filterGroups=new Map();
 for(const field of filterFields){
  const primary=field==='card_kind'||field==='rarity';
  const group=document.createElement(primary?'fieldset':'details');
  group.className='filter-group'+(primary?' primary-filter':'');
  if(primary)add(group,'legend',labels[field]);
  else{
   const summary=add(group,'summary',labels[field]+' ');
   add(summary,'span','','selection-count');
  }
  const options=add(group,'div','','filter-options');
  const values=field==='rarity'?filterOrder.rarity:
   [...new Set(cards.flatMap(card=>Array.isArray(card[field])?card[field]:[card[field]??'unknown']))]
    .sort((a,b)=>{
     const order=filterOrder[field]??[];
     const ai=order.indexOf(a),bi=order.indexOf(b);
     if(ai!==bi)return (ai<0?order.length:ai)-(bi<0?order.length:bi);
     return text(a).localeCompare(text(b),'ja');
    });
  for(const [index,value] of values.entries()){
   const label=add(options,'label','');
   label.className='filter-option';
   const input=document.createElement('input');
   input.type='checkbox';input.name=field;input.value=value;
   input.id='filter-'+field+'-'+index;
   input.dataset.filter=field;
   label.append(input,document.createTextNode(field==='series_ids'?seriesText(value):text(value)));
  }
  group.addEventListener('change',event=>{
   if(event.target.dataset.filter!==field)return;
   params.delete(field);
   for(const input of options.querySelectorAll('input:checked'))params.append(field,input.value);
   commitParams();
  });
  filterGroups.set(field,group);
  $(primary?'filters':'advanced-groups').append(group);
 }
 for(const [value,label] of browseOptions){
  const button=add($('series-shortcuts'),'button',label);
  button.type='button';button.dataset.browseShortcut=value;
  button.setAttribute('aria-pressed','false');
  button.addEventListener('click',()=>{
   const selected=params.getAll('browse');
   params.delete('browse');
   for(const item of selected.filter(item=>item!==value))params.append('browse',item);
   if(!selected.includes(value))params.append('browse',value);
   commitParams();
  });
 }

 const byUnit=new Map();
 for(const card of cards){
  const key=card.unit_id??'none';
  if(!byUnit.has(key))byUnit.set(key,{
   id:key,name:card.unit_name??'その他・ユニット欄空欄',idols:new Map()
  });
  byUnit.get(key).idols.set(card.idol_id,card.idol_name);
 }
 const peopleGroups=[...byUnit.values()].sort((a,b)=>{
  if(a.id==='none')return 1;if(b.id==='none')return -1;
  const ai=officialUnits.findIndex(unit=>unit.name===a.name);
  const bi=officialUnits.findIndex(unit=>unit.name===b.name);
  return (ai<0?99:ai)-(bi<0?99:bi)||a.name.localeCompare(b.name,'ja');
 }).map(group=>{
  const order=officialUnits.find(unit=>unit.name===group.name)?.idols??[];
  group.idols=[...group.idols].map(([id,name])=>({id,name}))
   .sort((a,b)=>{
    const ai=order.indexOf(a.name),bi=order.indexOf(b.name);
    return (ai<0?99:ai)-(bi<0?99:bi)||a.name.localeCompare(b.name,'ja');
   });
  return group;
 });
 const peopleClear=add($('people-filter'),'button','人物だけ解除','group-clear');peopleClear.type='button';peopleClear.onclick=()=>clearFields(['person','unit_name','idol_name']);
 const peopleControls=new Map();
 const currentPeopleTokens=()=>{
  const tokens=new Set(params.getAll('person'));
  return tokens;
 };
 const savePeopleTokens=tokens=>{
  params.delete('person');
  for(const token of tokens)params.append('person',token);
  commitParams();
 };
 for(const group of peopleGroups){
  const fieldset=add($('people-groups'),'fieldset','','people-unit');
  add(fieldset,'legend',group.name);
  const header=add(fieldset,'div','','people-unit-header');
  const allLabel=add(header,'label','','filter-option unit-all');
  const all=document.createElement('input');
  all.type='checkbox';all.dataset.personUnit=group.id;
  allLabel.append(all,document.createTextNode('ユニット全員'));
  const state=add(header,'span','','people-unit-state');
  const children=add(fieldset,'div','','people-children');
  const childInputs=new Map();
  for(const idol of group.idols){
   const label=add(children,'label','','filter-option');
   const input=document.createElement('input');
   input.type='checkbox';input.dataset.personIdol=idol.id;
   label.append(input,document.createTextNode(idol.name));
   childInputs.set(idol.id,input);
   input.addEventListener('change',()=>{
    const tokens=currentPeopleTokens(),unitToken='unit:'+group.id;
    if(tokens.has(unitToken)){
     tokens.delete(unitToken);
     for(const member of group.idols){
      if(member.id!==idol.id)tokens.add('idol:'+member.id);
     }
    }else if(input.checked)tokens.add('idol:'+idol.id);
    else tokens.delete('idol:'+idol.id);
    if(group.idols.every(member=>tokens.has('idol:'+member.id))){
     for(const member of group.idols)tokens.delete('idol:'+member.id);
     tokens.add(unitToken);
    }
    savePeopleTokens(tokens);
   });
  }
  all.addEventListener('change',()=>{
   const tokens=currentPeopleTokens();
   tokens.delete('unit:'+group.id);
   for(const idol of group.idols)tokens.delete('idol:'+idol.id);
   if(all.checked)tokens.add('unit:'+group.id);
   savePeopleTokens(tokens);
  });
  peopleControls.set(group.id,{all,state,childInputs});
 }
 const renderPeople=()=>{
  const tokens=new Set(params.getAll('person'));
  const legacy=params.has('unit_name')||params.has('idol_name');
  for(const input of $('people-groups').querySelectorAll('input'))input.disabled=legacy;
  $('legacy-people-note').hidden=!legacy;
  $('legacy-people-note').textContent=params.has('person')?'この旧リンクには両方式の人物条件があります。元の評価どおり、新方式の人物選択を優先しています。旧指定は互換欄から解除できます。':'リンクの人物条件を下の互換欄で編集中です。解除後、ユニット・アイドルを選べます。';
  for(const group of peopleGroups){
   const control=peopleControls.get(group.id);
   const allSelected=tokens.has('unit:'+group.id)||
    legacy&&params.getAll('unit_name').includes(group.name);
   control.all.checked=!!allSelected;
   let selectedChildren=0;
   for(const idol of group.idols){
    const checked=!!allSelected||tokens.has('idol:'+idol.id)||
     legacy&&params.getAll('idol_name').includes(idol.name);
    control.childInputs.get(idol.id).checked=!!checked;
    if(checked)selectedChildren++;
   }
   control.all.indeterminate=!allSelected&&selectedChildren>0;
   control.state.textContent=control.all.indeterminate?'一部選択':'';
  }
  const count=tokens.size||params.getAll('unit_name').length+params.getAll('idol_name').length;
  $('people-count').textContent=count?'（'+count+'件選択）':'';
 };

 const sortOptions=[
  ['date_new','初回実装日：新しい順'],['date_old','初回実装日：古い順'],
  ['rarity_high','レアリティ：URから'],['rarity_low','レアリティ：Nから'],
  ['unit_official','公式ユニット順'],['idol_official','公式アイドル順'],
  ['title','カード名順']
 ];
 for(const [value,label] of sortOptions)$('sort').add(new Option(label,value));
 const sortFromParams=()=>{
  const value=params.get('sort')??'date_new';
  if(value==='first_implemented_on')return params.get('direction')==='asc'?'date_old':'date_new';
  if(value==='rarity')return params.get('direction')==='asc'?'rarity_low':'rarity_high';
  if(value==='card_title'&&params.get('direction')!=='desc')return 'title';
  if(!sortOptions.some(option=>option[0]===value)&&
   ![...$('sort').options].some(option=>option.value===value)){
   $('sort').add(new Option('旧リンクの並び：'+value,value));
  }
  return value;
 };

 let dateDraft={from:params.get('from')??'',to:params.get('to')??''};
 const dateYears=()=>{
  const first=Number((coverage.target_from??'2018').slice(0,4));
  const last=Math.max(new Date().getFullYear()+1,Number((coverage.target_to??'2026').slice(0,4)));
  return {first,last};
 };
 const addOption=(select,value,label)=>select.add(new Option(label,value));
 const updateDayOptions=(kind,selected)=>{
  const year=$(kind+'-year').value,month=$(kind+'-month').value,day=$(kind+'-day');
  day.replaceChildren();addOption(day,'','指定なし');
  if(year&&month){
   const last=new Date(Date.UTC(Number(year),Number(month),0)).getUTCDate();
   for(let value=1;value<=last;value++)addOption(day,String(value).padStart(2,'0'),value+'日');
  }
  day.disabled=!year||!month;
  if(selected&&[...day.options].some(option=>option.value===selected))day.value=selected;
 };
 const renderDateBound=kind=>{
  const value=dateDraft[kind],parts=value.split('-');
  const year=$(kind+'-year'),month=$(kind+'-month'),day=$(kind+'-day');
  if(parts[0]&&![...year.options].some(option=>option.value===parts[0]))
   addOption(year,parts[0],parts[0]+'年');
  year.value=parts[0]??'';
  month.disabled=!year.value;
  month.value=parts[1]??'';
  updateDayOptions(kind,parts[2]??'');
  $(kind+'-native').value=value.length===10?value:'';
  $(kind+'-summary').textContent=value?
   parts[0]+'年'+(parts[1]?Number(parts[1])+'月':'')+
   (parts[2]?Number(parts[2])+'日':''):'指定なし';
 };
 for(const kind of ['from','to']){
  const year=$(kind+'-year'),month=$(kind+'-month');
  addOption(year,'','指定なし');
  const {first,last}=dateYears();
  for(let value=last;value>=first;value--)addOption(year,String(value),value+'年');
  addOption(month,'','指定なし');
  for(let value=1;value<=12;value++)addOption(month,String(value).padStart(2,'0'),value+'月');
  const onSelect=()=>{
   const y=year.value,m=y?month.value:'';
   if(!y)month.value='';
   updateDayOptions(kind,$(kind+'-day').value);
   const d=m?$(kind+'-day').value:'';
   dateDraft[kind]=y+(m?'-'+m:'')+(d?'-'+d:'');
   renderDateBound(kind);
   $('date-error').hidden=true;applyDates();
  };
  for(const id of ['year','month','day'])$(kind+'-'+id).addEventListener('change',onSelect);
  $(kind+'-native').addEventListener('change',event=>{
   if(event.target.validity.badInput||event.target.validity.typeMismatch){showDateError('日付を最後まで入力してください。');return;}
   dateDraft[kind]=event.target.value;
   renderDateBound(kind);
   $('date-error').hidden=true;applyDates();
  });
  renderDateBound(kind);
 }
 const showDateError=message=>{
  $('date-error').textContent=message;$('date-error').hidden=false;
 };
 const applyDates=()=>{
  for(const kind of ['from','to']){if(dateDraft[kind])params.set(kind,dateDraft[kind]);else params.delete(kind);}commitParams();
 };
 document.querySelector('.date-mode').addEventListener('change',event=>{
  const calendar=event.target.value==='calendar';
  for(const el of document.querySelectorAll('.calendar-input'))el.hidden=!calendar;
  for(const el of document.querySelectorAll('.date-selects'))el.hidden=calendar;
 });

 const active=$('active-filters');
 const conditionGroups=[['カード',['q','card_kind','rarity','person','unit_name','idol_name','from','to','collab_work','review_status','detail_status']],['シリーズ・入手',['browse','series_ids','acquisition_category']],['スキル・性能',['skill_kind','effect_type','effect_target','skill_q']],['詳しい条件',['mechanic','skill_condition','effect_recipient','effect_turns']]];
 const clearFields=fields=>{for(const field of fields)params.delete(field);dateDraft={from:params.get('from')??'',to:params.get('to')??''};for(const k of ['from','to'])renderDateBound(k);commitParams();$(editing?'filter-dialog-heading':'results-heading').focus({preventScroll:true});};
 const addChip=(parent,label,field,value)=>{
  const button=add(parent,'button',label+' ×','filter-chip');button.type='button';button.setAttribute('aria-label',label+'を解除');
  button.onclick=()=>{if(value===null)params.delete(field);else{const rest=params.getAll(field).filter(v=>v!==value);params.delete(field);for(const v of rest)params.append(field,v);}dateDraft={from:params.get('from')??'',to:params.get('to')??''};for(const k of ['from','to'])renderDateBound(k);commitParams();$(editing?'filter-dialog-heading':'results-heading').focus({preventScroll:true});};
 };
 const personName=token=>{
  const [type,id]=token.split(':');
  if(type==='unit'){
   const group=peopleGroups.find(item=>item.id===id);
   return (group?.name??token)+'全員';
  }
  if(type==='idol'){
   const idol=peopleGroups.flatMap(group=>group.idols).find(item=>item.id===id);
   return idol?.name??token;
  }
  return token;
 };
 const chipText=(key,value)=>{
  if(key==='browse')return '区分：'+(browseOptions.find(([id])=>id===value)?.[1]??value);
  if(key==='person')return personName(value);
  if(key==='skill_kind')return kindNames[value]??value;
  if(key==='mechanic')return mechanicNames[value]??value;
  if(key==='skill_condition')return '発動条件の要素：'+(conditionNames[value]??value);
  if(key==='effect_type')return '効果：'+(effectNames[value]??value);
  if(key==='effect_recipient')return '効果の対象：'+(recipientNames[value]??value);
  if(key==='effect_turns')return '継続：'+value+'ターン以上';
  if(key==='effect_target')return '属性・能力：'+value;
  if(key==='detail_status')return value==='available'?'詳細収録済み':value;
  const names={q:'カード検索',skill_q:'スキル検索',from:'実装日から',to:'実装日まで',unit_name:'リンクのユニット',idol_name:'リンクのアイドル',...labels};
  return (names[key]??key)+'：'+(key==='series_ids'?seriesText(value):text(value));
 };
 const conditionCount=()=>conditionGroups.flatMap(([,keys])=>keys).reduce((n,k)=>n+params.getAll(k).filter(Boolean).length,0);
 const renderActive=()=>{
  active.replaceChildren();
  for(const [name,keys] of conditionGroups){
   if(!keys.some(k=>params.get(k)))continue;
   const group=add(active,'section','','active-group');group.setAttribute('aria-label',name+'の条件');
   add(group,'strong',name);const clear=add(group,'button',name+'だけ解除','group-clear');clear.type='button';clear.onclick=()=>clearFields(keys);
   for(const key of keys){const values=params.getAll(key).filter(Boolean);if(!values.length)continue;
    const field=add(group,'div','','active-field');if(values.length>1)add(field,'span','または','or-label');
    for(const value of values)addChip(field,chipText(key,value),key,value);
   }
  }
  if(!conditionCount())active.textContent='絞り込み条件なし';
  $('advanced-count').textContent=['from','to','detail_status'].some(k=>params.get(k))?'（指定あり）':'';
  for(const field of ['series_ids','acquisition_category']){const n=params.getAll(field).length;filterGroups.get(field).querySelector('.selection-count').textContent=n?'（'+n+'件選択）':'';}
  $('open-filters').textContent='絞り込み（'+conditionCount()+'）';
 };
 const retainOption=(select,value)=>{if(value&&![...select.options].some(o=>o.value===value))select.add(new Option('選択中：'+(effectNames[value]??recipientNames[value]??(select.id==='effect-turns'?value+'ターン以上':value)),value));};
 const populateEffects=()=>{
  const items=applicableItems(params,catalog),effects=items.flatMap(i=>i.effects),type=params.get('effect_type');
  const names={appeal:'アピール・ライブの機能',status:'能力・ステータスの変化',recovery_gauge:'回復・ゲージ',audience:'観客への効果',produce:'育成サポート',random:'ランダム候補',passive:'パッシブの効果',cap:'ステータス上限'};
  $('effect-type').replaceChildren(new Option('指定なし',''));
  for(const [key,values] of Object.entries(effectGroups)){
   const available=values.filter(value=>effects.some(e=>effectMatches(e,new URLSearchParams({effect_type:value}))));if(!available.length)continue;
   const group=document.createElement('optgroup');group.label=names[key];for(const v of available)group.append(new Option(effectNames[v],v));$('effect-type').append(group);
  }
  retainOption($('effect-type'),type);
  const typed=type?effects.filter(e=>effectMatches(e,new URLSearchParams({effect_type:type}))):effects;
  const targets=[...new Set(typed.flatMap(effectTargets))],order=['Vocal','Dance','Visual','メンタル','SP','体力','アピール値','アピール倍率','思い出ゲージ','パッシブスキル発動率','パッシブスキル','注目度','リアクション回避率'];
  targets.sort((a,b)=>(order.includes(a)?order.indexOf(a):99)-(order.includes(b)?order.indexOf(b):99)||a.localeCompare(b,'ja'));
  $('effect-target').replaceChildren(new Option('指定なし',''));for(const v of targets)$('effect-target').add(new Option(v==='Excellent'?'Excellent（英字表記の効果対象）':v==='エクセレント'?'エクセレント（育成サポート）':v,v));retainOption($('effect-target'),params.get('effect_target'));
  $('effect-recipient').replaceChildren(new Option('指定なし',''));for(const [v,label] of Object.entries(recipientNames))if(typed.some(e=>effectMatches(e,new URLSearchParams({effect_recipient:v}))))$('effect-recipient').add(new Option(label,v));retainOption($('effect-recipient'),params.get('effect_recipient'));
  const kinds=params.getAll('skill_kind'),isLive=kinds.length&&kinds.every(k=>liveKinds.has(k));
  $('live-origins').hidden=!isLive;
  for(const input of $('live-origin-options').querySelectorAll('input'))input.checked=kinds.length<4&&kinds.includes(input.value);
  $('mechanic-control').hidden=!params.has('mechanic')&&!items.some(i=>liveKinds.has(i.kind));
  $('condition-control').hidden=!params.has('skill_condition')&&!items.some(i=>i.kind==='panel_passive');
  $('recipient-control').hidden=!params.has('effect_recipient')&&$('effect-recipient').options.length===1;
  $('turns-control').hidden=!params.has('effect_turns')&&!typed.some(e=>e.turns||e.turn_range?.minimum||e.random_pool?.options?.some(o=>o.turns));
  $('effect-context').textContent=type==='random_grant'?'同じランダム候補で照合します。候補の付与は保証されません。':type?.startsWith('passive_')?'発動確率・回数を効果値には含めません。発動条件と特訓段階を詳細で確認してください。':type==='cap_increase'?'1つのパネルの上限UPです。カード全体の合計上限ではありません。':'';
 };
 const legacyFields=['unit_name','idol_name','collab_work','review_status'];
 const legacyControls=new Map();
 for(const field of legacyFields){
  const group=add($('legacy-groups'),'fieldset','','legacy-group');add(group,'legend',({unit_name:'ユニット指定（旧リンク）',idol_name:'アイドル指定（旧リンク）',...labels})[field]);
  const values=[...new Set(cards.map(c=>c[field]??'unknown'))].sort((a,b)=>a.localeCompare(b,'ja'));
  for(const v of values){const label=add(group,'label','','filter-option'),input=document.createElement('input');input.type='checkbox';input.value=v;input.name=field;label.append(input,document.createTextNode(text(v)));}
  group.addEventListener('change',()=>{params.delete(field);for(const input of group.querySelectorAll('input:checked'))params.append(field,input.value);commitParams();});legacyControls.set(field,group);
 }
 const renderLegacy=()=>{
  let visible=false;
  for(const field of ['series_ids','acquisition_category']){
   const duplicates=field==='series_ids'?['twilights','casting','mysongs','parallel','prelude']:['permanent_gacha','limited_gacha'];
   const legacy=params.getAll(field).some(v=>duplicates.includes(v)),group=filterGroups.get(field);group.dataset.legacy=String(legacy);
   const parent=$(legacy?'legacy-groups':'advanced-groups');if(group.parentElement!==parent)parent.append(group);
   group.querySelector('summary').firstChild.textContent=(legacy?labels[field]+'（リンク条件）':field==='series_ids'?'企画タグ':'詳しい入手方法')+' ';
   for(const input of group.querySelectorAll('input'))input.parentElement.hidden=!legacy&&duplicates.includes(input.value);
   if(legacy){visible=true;group.open=true;}
  }
  for(const [field,group] of legacyControls){group.hidden=!params.has(field);visible||=params.has(field);for(const input of group.querySelectorAll('input'))input.checked=params.getAll(field).includes(input.value);}
  $('legacy-filters').hidden=!visible;if(visible)$('legacy-filters').open=true;
  $('legacy-filters').querySelector('.filter-help').textContent='元のリンクの式を保持しています。同じ欄は「または」、異なる欄は「すべて満たす」です。'+(params.has('person')&&(params.has('unit_name')||params.has('idol_name'))?'このリンクの人物は新方式が優先され、旧ユニット・アイドル指定は評価されません。':'旧ユニット・アイドル指定は両方満たします。');
 };
 const issuesFor=()=>{
  const issues=performanceIssues(params,catalog,!!detailDoc);
  for(const key of ['from','to'])if(params.get(key)&&!parseDatePart(params.get(key)))issues.push({key,message:'実在する年月日を指定してください：'+params.get(key)});
  if(parseDatePart(params.get('from'))?.start>parseDatePart(params.get('to'))?.end)issues.push({key:'from',message:'開始日を終了日以前にしてください。'});
  for(const key of ['card_kind','rarity','series_ids','acquisition_category','browse','person',...legacyFields]){
   const allowed=key==='browse'?browseOptions.map(([v])=>v):key==='person'?peopleGroups.flatMap(g=>['unit:'+g.id,...g.idols.map(i=>'idol:'+i.id)]):key==='rarity'?filterOrder.rarity:[...new Set(cards.flatMap(c=>Array.isArray(c[key])?c[key]:[c[key]??'unknown']))];
   for(const value of params.getAll(key))if(!allowed.includes(value))issues.push({key,message:'未対応の条件を解除または変更してください：'+chipText(key,value)});
  }
  return issues;
 };
 const renderIssues=issues=>{
  $('filter-issues').hidden=!issues.length;$('filter-issues').replaceChildren();
  if(issues.length){add($('filter-issues'),'strong','条件を適用できません');for(const issue of issues){add($('filter-issues'),'p',issue.message);const b=add($('filter-issues'),'button','この条件を解除');b.type='button';b.onclick=()=>clearFields(issue.key==='performance'?['detail_status',...conditionGroups.slice(2).flatMap(([,keys])=>keys)]:[issue.key]);}}
 };
 const renderControls=()=>{
  populateEffects();renderLegacy();
  for(const [id,key] of [['effect-type','effect_type'],['effect-target','effect_target'],['effect-turns','effect_turns'],['effect-recipient','effect_recipient']]){retainOption($(id),params.get(key));$(id).value=params.get(key)??'';}
  if(!pendingSearch.has('skill-q'))$('skill-q').value=params.get('skill_q')??'';
  const kinds=params.getAll('skill_kind');const parent=kinds.length&&kinds.every(k=>liveKinds.has(k))?'live':kinds.length===1&&[...$('skill-kind').options].some(o=>o.value===kinds[0])?kinds[0]:kinds.length?'__mixed__':'';retainOption($('skill-kind'),parent);if(parent==='__mixed__')$('skill-kind').querySelector('option[value="__mixed__"]').textContent='リンクの情報条件（複数指定）';$('skill-kind').value=parent;
  retainOption($('skill-condition'),params.get('skill_condition'));$('skill-condition').value=params.get('skill_condition')??'';
  $('detail-available').checked=params.get('detail_status')==='available';
  for(const input of $('skill-mechanics').querySelectorAll('input'))input.checked=params.getAll('mechanic').includes(input.value);
  for(const field of filterFields){
   const selected=params.getAll(field);
   for(const input of filterGroups.get(field).querySelectorAll('input'))
    input.checked=selected.includes(input.value);
  }
  for(const button of $('series-shortcuts').querySelectorAll('button'))
   button.setAttribute('aria-pressed',String(params.getAll('browse').includes(button.dataset.browseShortcut)));
  renderPeople();if(!editing)renderActive();
  if(!pendingSearch.has('q')&&$('q').value!==(params.get('q')??''))$('q').value=params.get('q')??'';
  $('sort').value=sortFromParams();
  $('date-hint').hidden=!(params.has('from')||params.has('to'));
  $('date-hint').textContent='実装日未確認の'+(coverage.missing?.first_implemented_on??0)+'件は期間指定の結果に含まれません。';
 };

 const more=document.createElement('button');
 more.id='more';more.type='button';
 $('cards').after(more);
 const detailLine=(list,term,value)=>{
  const row=add(list,'div','','detail-row');
  add(row,'dt',term);add(row,'dd',value);
 };
 const performanceNode=(parent,baseCard)=>{
  const section=add(parent,'section','','performance');
  add(section,'h4','スキル・詳細情報');
  const card=detailMap.get(baseCard.card_id);
  if(!card){add(section,'p',baseCard.wiki_url?'詳細は未収録です。取得・確認を順次進めています。':'個別ページ未確認のため詳細収録は保留中です。','detail-note');return;}
  if(card.traits){
   const list=add(section,'dl','','card-facts');
   detailLine(list,'アイデア',card.traits.idea);detailLine(list,'ひらめき',card.traits.inspiration);
   detailLine(list,'楽曲熟練度',card.traits.music_proficiencies.join('・'));
   const stats=card.max_status;
   detailLine(list,'最大Lv '+stats.level,['Vo','Da','Vi','Me'].map((label,i)=>label+' '+(stats[['vocal','dance','visual','mental'][i]]??'未記載')).join(' / '));
  }
  add(section,'p','効果は参考数値の一部を表示しています。パッシブの発動条件は対応分を表示します。未対応の条件・複合効果はWikiで確認してください。','detail-note');
  const matchingKinds=new Set(detailMatches(card,params).map(m=>m.item.kind));
  for(const [kind,label] of Object.entries(kindNames).sort(([a],[b])=>Number(matchingKinds.has(b))-Number(matchingKinds.has(a)))){
   const items=card.items.filter(item=>item.kind===kind);if(!items.length)continue;
   const matches=new Map(detailMatches({items},params).map(m=>[m.item.detail_id,m]));
   const matchedIds=new Set(matches.keys());
   if(matchedIds.size)items.sort((a,b)=>Number(matchedIds.has(b.detail_id))-Number(matchedIds.has(a.detail_id)));
   const group=add(section,'details','','skill-section');if(matchedIds.size)group.open=true;add(group,'summary',label+'（'+items.length+'件'+(matchedIds.size?' / 一致 '+matchedIds.size+'件':'')+'）');
   const list=add(group,'ul','','skill-list');
   for(const item of items){
    const row=add(list,'li','','skill-item');row.dataset.detailId=item.detail_id;if(matchedIds.has(item.detail_id))row.classList.add('matched-skill');add(row,'strong',item.name);
    const attrs=[];
    if(item.sp!=null)attrs.push('SP '+item.sp);
    if(item.unlock_star!=null)attrs.push('特訓 '+item.unlock_star);
    if(item.unlock_event)attrs.push('イベント解放');
    if(item.generation_stage)attrs.push('生成 '+item.generation_stage+'連目 / 生成元 '+generationParentText(item));
    if(item.mb_stage)attrs.push('MB '+item.mb_stage+(item.mb_total_stages?'/'+item.mb_total_stages:''));
    if(item.level!=null)attrs.push('Lv '+item.level);
    if(item.acquired_at_level!=null)attrs.push('取得Lv '+item.acquired_at_level);
    if(item.energy_cost!=null)attrs.push('気力 '+item.energy_cost);
    attrs.push(...(item.mechanics??[]).map(value=>mechanicNames[value]));
    if(attrs.length)add(row,'p',attrs.join(' · '),'skill-meta');
    if(item.cap_delta!=null)add(row,'p',item.cap_targets.join(' / ')+' 上限 +'+item.cap_delta,matches.get(item.detail_id)?.effects.some(e=>e.source_field==='cap_delta')?'skill-values matched-effect':'skill-values');
    if(itemActivationCondition(item)){
     const conditionText=activationConditionText(itemActivationCondition(item));
     add(row,'p',conditionText?'発動条件：'+conditionText:'発動条件：未対応（Wikiで確認してください）','skill-values activation-condition');
    }
    if(item.effect_details?.mechanic_conditions?.length){
     const rules=add(row,'ul','','skill-effect-rules');
     for(const rule of item.effect_details.mechanic_conditions){
      const fact=add(rules,'li',mechanicRuleText(rule),'skill-values');
      if(matchedIds.has(item.detail_id)&&(params.get('skill_q')??'').trim()&&mechanicRuleMatches(item,rule,params)){fact.classList.add('matched-effect');group.open=true;}
     }
    }
    if(item.effect_details?.effects.length){
     const facts=add(row,'ul','','effect-facts');
     for(const e of item.effect_details.effects){
      const fact=add(facts,'li',effectFactText(e),'skill-values');
      if(matches.get(item.detail_id)?.effects.some(m=>m.source_field==='effect_details'&&m.source_index===item.effect_details.effects.indexOf(e))){fact.classList.add('matched-effect');group.open=true;}
     }
     if(item.kind==='support_skill'){
      const levels=(item.progression??[]).map(p=>p.skill_level).filter(n=>Number.isFinite(n));
      const top=levels.length?Math.max(...levels):null;
      if(top!=null&&item.effect_details.effects.some(e=>e.formula||e.probability?.formula))add(row,'p','取得表の最大スキルLv '+top+'：'+item.effect_details.effects.map(e=>effectFactText(e,top)).join(' / '),'skill-meta');
     }
    }
    for(const [index,fact] of (item.numeric_facts??[]).entries())add(row,'p','参考数値：'+factText(fact),matches.get(item.detail_id)?.effects.some(e=>e.source_field==='numeric_facts'&&e.source_index===index)?'skill-values matched-effect':'skill-values');
    for(const [slot,label] of [['link','Link追加効果'],['charge','チャージ追加効果']]){
     if(item['memory_'+slot+'_present']){
      const facts=item['memory_'+slot+'_facts']??[];
      add(row,'p',label+'（参考数値）：'+(facts.length?facts.map(factText).join(' / '):'数値を未構造化。Wikiで確認してください。'),'skill-values memory-'+slot);
     }
    }
    if(item.random_effect_options?.length)add(row,'p','ランダム効果の候補（確率未収録）：'+item.random_effect_options.map(option=>factText(option)+' ['+option.turns+'ターン]').join(' / '),'skill-values');
    if(item.progression?.length)add(row,'p','取得Lv → スキルLv：'+item.progression.map(step=>step.support_level+' → '+step.skill_level).join(' / '),'skill-values');
   }
  }
  add(section,'p','Wiki取得日 '+card.fetched_at.slice(0,10)+'。Pステージ・適正、Sファイトは今回の収録対象外です。','detail-note');
 };
 const cardNode=cardData=>{
  const row=add($('cards'),'li','','card');row.dataset.cardId=cardData.card_id;
  const head=add(row,'div','','card-head');
  add(head,'span',cardData.card_kind+' / '+text(cardData.rarity),'badge');
  add(head,'h3',cardData.card_title,'card-title');
  add(head,'p',cardData.idol_name,'card-person');
  const shortLabel=cardData.series_ids.length?cardData.series_ids.map(seriesText).join('・'):
   text(cardData.acquisition_category);
  add(head,'p',shortLabel+' · '+(cardData.first_implemented_on??'日付未確認'),'card-meta');
  const matching=detailMatches(detailMap.get(cardData.card_id),params);
  if(matching.length){
   const first=matching[0],effect=first.effects[0];
   add(head,'p','一致：'+kindNames[first.item.kind]+' / '+first.item.name+(first.item.unlock_star!=null?'（特訓'+first.item.unlock_star+'）':'')+(first.item.level!=null?'（Lv'+first.item.level+'）':'')+(first.item.sp!=null?'（SP'+first.item.sp+'）':'')+(effect?' · '+effectFactText(effect):'')+(matching.length>1?'（ほか'+(matching.length-1)+'件）':''),'match-reason');
  }
  const detailId='card-details-'+cardData.card_id;
  const button=add(head,'button',expandedIds.has(cardData.card_id)?'詳細を閉じる':'詳細を見る','detail-toggle');
  button.type='button';button.setAttribute('aria-controls',detailId);
  button.setAttribute('aria-expanded',String(expandedIds.has(cardData.card_id)));
  const detail=add(row,'div','','card-detail');
  detail.id=detailId;detail.hidden=!expandedIds.has(cardData.card_id);
  const list=add(detail,'dl','','card-facts');
  detailLine(list,'カード名',cardData.card_title);
  detailLine(list,'アイドル',cardData.idol_name);
  detailLine(list,'ユニット',cardData.unit_name??'ユニット欄空欄');
  detailLine(list,'種別・レアリティ',cardData.card_kind+' / '+text(cardData.rarity));
  detailLine(list,'入手区分',text(cardData.acquisition_category));
  detailLine(list,'シリーズ・企画',cardData.series_ids.length?cardData.series_ids.map(seriesText).join('・'):'該当なし');
  detailLine(list,'初回実装日',cardData.first_implemented_on??'日付未確認');
  detailLine(list,'確認状態',text(cardData.review_status));
  if(cardData.collab_work)detailLine(list,'コラボ作品',cardData.collab_work);
  if(cardData.variant_kind!=='base')detailLine(list,'派生種別','アイドルロード派生');
  performanceNode(detail,cardData);
  const action=add(detail,'div','','card-action');
  const wiki=wikiLink(cardData.wiki_url);
  if(wiki){
   const link=add(action,'a','Wiki個別ページへ ↗');
   link.href=wiki;link.target='_blank';link.rel='noopener noreferrer';
   link.setAttribute('aria-label',cardData.card_title+cardData.idol_name+'のWiki個別ページ（外部サイト）');
  }else add(action,'span','Wiki個別ページ未確認（一覧に収録）','no-wiki');
  const sources=add(detail,'details','','card-sources');
  add(sources,'summary','データの根拠を見る');
  const refs=add(sources,'p','');
  if(!cardData.source_refs.length)refs.textContent='出典未確認';
  for(const [index,ref] of cardData.source_refs.entries()){
   if(index)refs.append(document.createTextNode(' / '));
   const url=sourceUrls.get(cardData.card_id)?.get(ref);
   if(url){
    const link=add(refs,'a',sourceNames[ref]??ref);
    link.href=url;link.target='_blank';link.rel='noopener noreferrer';
    link.setAttribute('aria-label',cardData.card_title+cardData.idol_name+'の出典：'+(sourceNames[ref]??ref)+'（外部サイト）');
   }else refs.append(document.createTextNode(sourceNames[ref]??ref));
  }
  button.addEventListener('click',()=>{
   const opening=detail.hidden;
   detail.hidden=!opening;
   button.setAttribute('aria-expanded',String(opening));
   button.textContent=opening?'詳細を閉じる':'詳細を見る';
   if(opening)expandedIds.add(cardData.card_id);
   else expandedIds.delete(cardData.card_id);
  });
  return row;
 };
 function render(limit=100){
  const issues=issuesFor();renderIssues(issues);
  shown=issues.length?[]:detailSearch(search(cards,params),params,detailMap);
  const ids=new Set(shown.map(card=>card.card_id));
  expandedIds=new Set([...expandedIds].filter(id=>ids.has(id)));
  renderControls();
  $('count').textContent=issues.length?'条件を適用できません':shown.length+' / '+cards.length+' 件';
  $('cards').replaceChildren();
  if(!shown.length){
   const empty=add($('cards'),'li',issues.length?'条件を適用できません。選択中の条件を変更・部分解除してください。':'条件に一致するカードはありません。条件を減らすと見つかる可能性があります。スキル未収録・検索未対応の範囲もあります。','empty-state');
   if(issues.length)for(const issue of issues){add(empty,'p',issue.message);const b=add(empty,'button','条件を解除：'+issue.key);b.type='button';b.onclick=()=>clearFields(issue.key==='performance'?['detail_status',...conditionGroups.slice(2).flatMap(([,keys])=>keys)]:[issue.key]);}
   const reset=add(empty,'button','条件をリセット');
   reset.type='button';reset.onclick=()=>$('reset').click();
  }
  for(const card of shown.slice(0,limit))cardNode(card);
  more.hidden=shown.length<=limit;
  more.textContent='さらに表示（'+Math.min(limit,shown.length)+' / '+shown.length+' 件表示中）';
  more.onclick=()=>{
   render(limit+100);
   const firstAdded=$('cards').children[limit]?.querySelector('.detail-toggle');
   if(firstAdded)firstAdded.focus();
  };
 }
 bindSearch('q','q');
 $('q').addEventListener('keydown',event=>{
  if(event.key==='Enter'&&!event.isComposing){
   flushPending();
   event.preventDefault();$('results-heading').scrollIntoView({block:'start'});
  }
 });
 $('sort').addEventListener('change',event=>{
  params.set('sort',event.target.value);params.delete('direction');commitParams();
 });
 $('reset').addEventListener('click',()=>{
  cancelPending();
  const kept=new URLSearchParams();for(const key of ['sort','direction'])for(const v of params.getAll(key))kept.append(key,v);params=kept;dateDraft={from:'',to:''};
  for(const kind of ['from','to'])renderDateBound(kind);
  $('date-error').hidden=true;
  $('advanced-filters').open=false;
  commitParams();
 });

 $('advanced-filters').open=!!(
  params.get('from')||params.get('to')||params.get('detail_status')
 );
 $('people-filter').open=!!(
  params.getAll('person').length||params.getAll('unit_name').length||params.getAll('idol_name').length
 );
 for(const field of ['series_ids','acquisition_category'])
  filterGroups.get(field).open=!!params.getAll(field).length;
 $('performance-advanced').open=['mechanic','skill_condition','effect_recipient','effect_turns'].some(k=>params.has(k))||params.getAll('skill_kind').some(k=>liveKinds.has(k))&&params.getAll('skill_kind').length<4;
 render();
 const mobile=matchMedia('(max-width:899px)'),dialog=$('filter-dialog'),panel=$('filter-panel');
 const movePanel=()=>{
  const parent=mobile.matches?$('dialog-filter-body'):document.querySelector('.controls');
  if(panel.parentElement!==parent)parent.append(panel);
  $('open-filters').hidden=!mobile.matches;
 };
 function renderPreview(){
  const issues=issuesFor();renderIssues(issues);const n=issues.length?0:detailSearch(search(cards,params),params,detailMap).length;
  $('draft-count').textContent=issues.length?'条件を変更・部分解除してください。':n===0?'0件です。条件を減らすと見つかる可能性があります。':n+'件のカードが候補になります。';
  $('apply-filters').textContent=issues.length?'条件を適用できません':n+'件を表示';$('apply-filters').disabled=!!issues.length;
 }
 const closePanel=()=>{
  dialog.close();document.body.classList.remove('filter-dialog-open');editing=false;appliedParams=null;panelClosing=false;movePanel();
 };
 $('open-filters').onclick=()=>{
  flushPending();appliedParams=new URLSearchParams(params);params=new URLSearchParams(params);editing=true;
  history.pushState({filterPanel:true},'',location.href);dialog.showModal();document.body.classList.add('filter-dialog-open');renderControls();renderPreview();$('filter-dialog-heading').focus();
 };
 const cancelPanel=(message='')=>{
  if(!editing||panelClosing)return;panelClosing=true;cancelMessage=message;cancelPending();history.back();
 };
 $('cancel-filters').onclick=()=>cancelPanel();
 dialog.addEventListener('cancel',event=>{event.preventDefault();cancelPanel();});
 $('apply-filters').onclick=()=>{
  flushPending();if(issuesFor().length){renderPreview();return;}
  history.replaceState(null,'',urlForParams());closePanel();render();$('results-heading').focus();$('results-heading').scrollIntoView({block:'start'});
 };
 mobile.addEventListener('change',()=>{
  if(editing){cancelPanel('画面幅が変わったため、未適用の編集を取り消しました。');return;}movePanel();
 });
 window.addEventListener('popstate',()=>{
  cancelPending();
  if(editing){params=new URLSearchParams(location.search);closePanel();dateDraft={from:params.get('from')??'',to:params.get('to')??''};for(const kind of ['from','to'])renderDateBound(kind);render();if(mobile.matches)$('open-filters').focus();else $('results-heading').focus();$('filter-announcement').textContent=cancelMessage;cancelMessage='';return;}
  if(history.state?.filterPanel)history.replaceState(null,'',location.href);
  params=new URLSearchParams(location.search);dateDraft={from:params.get('from')??'',to:params.get('to')??''};
  for(const kind of ['from','to'])renderDateBound(kind);$('date-error').hidden=true;render();
 });
 movePanel();

 $('coverage-summary').textContent=cards.length+'件収録（P '+(coverage.by_kind?.P??'—')+
  '件 / S '+(coverage.by_kind?.S??'—')+'件） · '+(coverage.target_to??'確認日不明')+
  'まで · 公式全網羅未確認';
 const coverageBody=$('coverage-body');
 const coverageLine=(heading,value)=>{
  const row=add(coverageBody,'div','');
  add(row,'dt',heading);add(row,'dd',value);
 };
 coverageLine('対象',coverage.complete?'収録範囲照合済み':
  coverage.scope==='sample'?'少数実データの試作・全件版未完成':
  'enza版のWiki一覧を収録。公式全網羅は未確認');
 coverageLine('件数',cards.length+'件（P '+(coverage.by_kind?.P??'—')+
  '件 / S '+(coverage.by_kind?.S??'—')+'件）');
 coverageLine('対象期間',(coverage.target_from??coverage.min_date??'不明')+' ～ '+
  (coverage.target_to??coverage.max_date??'不明')+'。実装日確認範囲 '+
  (coverage.min_date??'不明')+' ～ '+(coverage.max_date??'不明'));
 const gaps=[];
 if(coverage.missing?.wiki_url)gaps.push('Wiki個別ページなし '+coverage.missing.wiki_url+'件');
 if(coverage.missing?.first_implemented_on)gaps.push('初回実装日不明 '+coverage.missing.first_implemented_on+'件');
 if(coverage.missing?.unit_name)gaps.push('ユニット欄空欄 '+coverage.missing.unit_name+'件');
 coverageLine('欠損',gaps.join(' / ')||'主要項目の欠損なし');
 coverageLine('未確認',(coverage.unverified??[]).join('、')||'なし');
 $('version').textContent='UI版 '+window.UI_VERSION+' / データ版 '+
  meta.dataset_version+' / 生成日時 '+meta.published_at;
 for(const [file,label] of [
  ['cards.json','全件 JSON'],['cards.xlsx','全件 Excel'],
  ['manifest.json','版情報'],['coverage.json','収録範囲'],['sources.json','項目別出典']
 ]){
  const link=add($('downloads'),'a',label);
  link.href=base+file;
 }
 $('audit').textContent=JSON.stringify(coverage,null,2);
}catch(error){
 $('coverage-summary').textContent=error.message==='版不一致'?
  'データ版が一致しません。再読み込みしてください。':
  'データを読み込めませんでした。再読み込みしてください。 '+error.message;
 $('coverage-details').hidden=true;
 $('count').textContent='読み込み失敗';
}