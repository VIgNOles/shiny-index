import {detailSearch,loadDetails,detailCoverageText,generationParentText,activationConditionText,conditionNames,kindNames,mechanicNames,factText} from './details.mjs';
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
 let shown=[];
 let expandedIds=new Set();
 let startupWarning='';
 let changedUrl=false;
 if(params.has('missing')){params.delete('missing');changedUrl=true;}
 for(const key of ['from','to']){
  if(params.has(key)&&!parseDatePart(params.get(key))){
   params.delete(key);changedUrl=true;startupWarning='無効な日付条件を除外しました。';
  }
 }
 if(params.has('from')&&params.has('to')&&
  parseDatePart(params.get('from')).start>parseDatePart(params.get('to')).end){
  params.delete('from');params.delete('to');changedUrl=true;
  startupWarning='開始日が終了日より後だったため、日付条件を解除しました。';
 }
 const urlForParams=()=>location.pathname+(params.size?'?'+params.toString():'')+location.hash;
 if(changedUrl)history.replaceState(null,'',urlForParams());
 const commitParams=(mode='push')=>{
  const next=urlForParams();
  if(next!==location.pathname+location.search+location.hash)
   history[mode==='replace'?'replaceState':'pushState'](null,'',next);
  render();
 };

 for(const [value,label] of Object.entries(conditionNames))$('skill-condition').add(new Option(label,value));
 for(const [value,label] of Object.entries(kindNames))$('skill-kind').add(new Option(label,value));
 for(const [value,label] of Object.entries(mechanicNames)){
  const wrapper=add($('skill-mechanics'),'label','','filter-option');
  const input=document.createElement('input');input.type='checkbox';input.value=value;input.name='mechanic';
  wrapper.append(input,document.createTextNode(label));
 }
 $('skill-q').addEventListener('input',event=>{
  if(event.target.value)params.set('skill_q',event.target.value);else params.delete('skill_q');commitParams('replace');
 });
 $('skill-kind').addEventListener('change',event=>{
  params.delete('skill_kind');if(event.target.value)params.set('skill_kind',event.target.value);commitParams();
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
 $('skill-filters').open=['skill_q','skill_kind','skill_condition','mechanic','detail_status'].some(key=>params.has(key));

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
 const peopleControls=new Map();
 const currentPeopleTokens=()=>{
  const tokens=new Set(params.getAll('person'));
  if(tokens.size)return tokens;
  for(const group of peopleGroups){
   if(params.getAll('unit_name').includes(group.name))tokens.add('unit:'+group.id);
   for(const idol of group.idols){
    if(params.getAll('idol_name').includes(idol.name))tokens.add('idol:'+idol.id);
   }
  }
  return tokens;
 };
 const savePeopleTokens=tokens=>{
  params.delete('unit_name');params.delete('idol_name');params.delete('person');
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
  const legacy=tokens.size===0&&
   (params.getAll('unit_name').length||params.getAll('idol_name').length);
  $('legacy-people-note').hidden=!legacy;
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
   $('date-error').hidden=true;
  };
  for(const id of ['year','month','day'])$(kind+'-'+id).addEventListener('change',onSelect);
  $(kind+'-native').addEventListener('change',event=>{
   dateDraft[kind]=event.target.value;
   renderDateBound(kind);
   $('date-error').hidden=true;
  });
  renderDateBound(kind);
 }
 const showDateError=message=>{
  $('date-error').textContent=message;$('date-error').hidden=false;
 };
 if(startupWarning)showDateError(startupWarning);
 $('date-apply').addEventListener('click',()=>{
  const from=dateDraft.from?parseDatePart(dateDraft.from):null;
  const to=dateDraft.to?parseDatePart(dateDraft.to):null;
  if(dateDraft.from&&!from||dateDraft.to&&!to){
   showDateError('実在する年月日を選んでください。');return;
  }
  if(from&&to&&from.start>to.end){
   showDateError('開始日を終了日以前にしてください。');return;
  }
  $('date-error').hidden=true;
  for(const kind of ['from','to']){
   if(dateDraft[kind])params.set(kind,dateDraft[kind]);
   else params.delete(kind);
  }
  commitParams();
 });

 const active=$('active-filters');
 const addChip=(label,field,value)=>{
  const button=add(active,'button',label+' ×');
  button.type='button';button.className='filter-chip';
  button.setAttribute('aria-label',label+'を解除');
  button.addEventListener('click',()=>{
   if(value===null)params.delete(field);
   else{
    const remaining=params.getAll(field).filter(item=>item!==value);
    params.delete(field);
    for(const item of remaining)params.append(field,item);
   }
   if(field==='q')$('q').value='';
   if(field==='from'||field==='to'){
    dateDraft[field]='';renderDateBound(field);
   }
   commitParams();
  });
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
 const renderActive=()=>{
  active.replaceChildren();
  let count=0;
  for(const value of params.getAll('browse')){
   const label=browseOptions.find(([id])=>id===value)?.[1]??value;
   addChip('区分：'+label,'browse',value);count++;
  }
  for(const field of filterFields.concat(['collab_work','review_status'])){
   for(const value of params.getAll(field)){
    addChip(labels[field]+'：'+(field==='series_ids'?seriesText(value):text(value)),field,value);count++;
   }
  }
  for(const value of params.getAll('person')){addChip(personName(value),'person',value);count++;}
  for(const field of ['unit_name','idol_name']){
   for(const value of params.getAll(field)){addChip('旧条件：'+value,field,value);count++;}
  }
  if(params.get('q')){addChip('検索：'+params.get('q'),'q',null);count++;}
  for(const field of ['from','to']){
   if(params.get(field)){
    addChip((field==='from'?'実装日から：':'実装日まで：')+params.get(field),field,null);
    count++;
   }
  }
  if(params.get('skill_q')){addChip('スキル検索：'+params.get('skill_q'),'skill_q',null);count++;}
  for(const value of params.getAll('skill_kind')){addChip(kindNames[value]??value,'skill_kind',value);count++;}
  for(const value of params.getAll('mechanic')){addChip(mechanicNames[value]??value,'mechanic',value);count++;}
  if(params.get('skill_condition')){addChip('発動条件：'+(conditionNames[params.get('skill_condition')]??params.get('skill_condition')),'skill_condition',null);count++;}
  if(params.get('detail_status')==='available'){addChip('詳細収録済み','detail_status',null);count++;}
  if(!count)active.textContent='絞り込み条件なし';
  const advancedCount=params.getAll('series_ids').length+
   params.getAll('acquisition_category').length+params.getAll('person').length+
   params.getAll('unit_name').length+params.getAll('idol_name').length+
   Number(!!params.get('from'))+Number(!!params.get('to'));
  $('advanced-count').textContent=advancedCount?'（'+advancedCount+'条件）':'';
  for(const field of ['series_ids','acquisition_category']){
   const span=filterGroups.get(field).querySelector('.selection-count');
   const selected=params.getAll(field).length;
   span.textContent=selected?'（'+selected+'件選択）':'';
  }
 };
 const renderControls=()=>{
  $('skill-q').value=params.get('skill_q')??'';
  $('skill-kind').value=params.get('skill_kind')??'';
  $('skill-condition').value=params.get('skill_condition')??'';
  $('detail-available').checked=params.get('detail_status')==='available';
  for(const input of $('skill-mechanics').querySelectorAll('input'))input.checked=params.getAll('mechanic').includes(input.value);
  for(const field of filterFields){
   const selected=params.getAll(field);
   for(const input of filterGroups.get(field).querySelectorAll('input'))
    input.checked=selected.includes(input.value);
  }
  for(const button of $('series-shortcuts').querySelectorAll('button'))
   button.setAttribute('aria-pressed',String(params.getAll('browse').includes(button.dataset.browseShortcut)));
  renderPeople();renderActive();
  if($('q').value!==(params.get('q')??''))$('q').value=params.get('q')??'';
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
  for(const [kind,label] of Object.entries(kindNames)){
   const items=card.items.filter(item=>item.kind===kind);if(!items.length)continue;
   const group=add(section,'details','','skill-section');add(group,'summary',label+'（'+items.length+'件）');
   const list=add(group,'ul','','skill-list');
   for(const item of items){
    const row=add(list,'li','','skill-item');add(row,'strong',item.name);
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
    if(item.cap_delta!=null)add(row,'p',item.cap_targets.join(' / ')+' 上限 +'+item.cap_delta);
    if(item.activation_condition){
     const conditionText=activationConditionText(item.activation_condition);
     add(row,'p',conditionText?'発動条件：'+conditionText:'発動条件：未対応（Wikiで確認してください）','skill-values activation-condition');
    }
    if(item.numeric_facts.length)add(row,'p','参考数値：'+item.numeric_facts.map(factText).join(' / '),'skill-values');
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
  const row=add($('cards'),'li','','card');
  const head=add(row,'div','','card-head');
  add(head,'span',cardData.card_kind+' / '+text(cardData.rarity),'badge');
  add(head,'h3',cardData.card_title,'card-title');
  add(head,'p',cardData.idol_name,'card-person');
  const shortLabel=cardData.series_ids.length?cardData.series_ids.map(seriesText).join('・'):
   text(cardData.acquisition_category);
  add(head,'p',shortLabel+' · '+(cardData.first_implemented_on??'日付未確認'),'card-meta');
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
  shown=detailSearch(search(cards,params),params,detailMap);
  const ids=new Set(shown.map(card=>card.card_id));
  expandedIds=new Set([...expandedIds].filter(id=>ids.has(id)));
  renderControls();
  $('count').textContent=shown.length+' / '+cards.length+' 件';
  $('cards').replaceChildren();
  if(!shown.length){
   const empty=add($('cards'),'li','条件に一致するカードはありません。','empty-state');
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
 $('q').addEventListener('input',event=>{
  if(event.target.value)params.set('q',event.target.value);
  else params.delete('q');
  commitParams('replace');
 });
 $('q').addEventListener('keydown',event=>{
  if(event.key==='Enter'){
   event.preventDefault();$('results-heading').scrollIntoView({block:'start'});
  }
 });
 $('sort').addEventListener('change',event=>{
  params.set('sort',event.target.value);params.delete('direction');commitParams();
 });
 $('reset').addEventListener('click',()=>{
  params=new URLSearchParams();dateDraft={from:'',to:''};
  for(const kind of ['from','to'])renderDateBound(kind);
  $('date-error').hidden=true;
  $('advanced-filters').open=false;
  commitParams();
 });

 $('advanced-filters').open=!!(
  params.getAll('person').length||params.getAll('unit_name').length||params.getAll('idol_name').length||
  params.getAll('series_ids').length||params.getAll('acquisition_category').length||
  params.get('from')||params.get('to')
 );
 $('people-filter').open=!!(
  params.getAll('person').length||params.getAll('unit_name').length||params.getAll('idol_name').length
 );
 for(const field of ['series_ids','acquisition_category'])
  filterGroups.get(field).open=!!params.getAll(field).length;
 render();
 window.addEventListener('popstate',()=>{
  params=new URLSearchParams(location.search);
  dateDraft={from:params.get('from')??'',to:params.get('to')??''};
  for(const kind of ['from','to'])renderDateBound(kind);
  $('date-error').hidden=true;
  render();
 });

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