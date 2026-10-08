import {search,csv,seriesNames} from './search.mjs';

const $=id=>document.getElementById(id);
const labels={
 card_kind:'P／S',rarity:'レアリティ',idol_name:'アイドル',unit_name:'ユニット',
 acquisition_category:'入手区分',series_ids:'シリーズ・企画',collab_work:'コラボ作品',
 review_status:'確認状態',card_title:'カード名',first_implemented_on:'初回実装日'
};
const display={
 permanent_gacha:'恒常ガシャ',limited_gacha:'期間限定',collection_gacha:'コレクション',
 collaboration_gacha:'コラボガシャ',event_reward:'イベント報酬',initial:'初期所持',
 unknown:'不明',wiki_only:'Wikiのみ確認',needs_review:'要確認',
 birthday:'誕生日',
 ...seriesNames,gacha_bonus:'ガシャ特典',other_bonus:'その他特典',
 mission:'ミッション',campaign:'キャンペーン・配布',exchange:'交換',
 other:'その他',official_checked:'公式照合済み',
 user_evidence_checked:'管理者資料確認済み'
};
const text=value=>display[value]??value??'不明';

try {
 const base=`data/${window.DATA_VERSION}/`;
 const response=await fetch(base+'cards.json');
 if(!response.ok)throw Error('HTTP '+response.status);
 const doc=await response.json();
 if(doc.meta.dataset_version!==window.DATA_VERSION)throw Error('版不一致');
 const {cards,meta,coverage}=doc;
 let params=new URLSearchParams(location.search);
 if(params.has('missing')){params.delete('missing');history.replaceState(null,'',params.size?'?'+params:location.pathname);}
 let shown=[];
 const sourceNames={
  W02:'Pカード一覧',W03:'Sカード一覧',W04:'Sカード分冊',
  W05:'アイドル追加順',W07:'コラボアイドル',W08:'アイドルロード',W09:'ガシャ'
 };
 const sourceUrls=new Map();
 for(const source of doc.sources??[]){
  if(!source.url||!source.source_ref)continue;
  let url;
  try{url=new URL(source.url);}catch{continue;}
  if(url.protocol!=='https:'||url.hostname!=='wikiwiki.jp'||!url.pathname.startsWith('/shinycolors/'))continue;
  if(!sourceUrls.has(source.card_id))sourceUrls.set(source.card_id,new Map());
  sourceUrls.get(source.card_id).set(source.source_ref,url.href);
 }

 const filterFields=[
  'card_kind','rarity','idol_name','unit_name','acquisition_category',
  'series_ids','collab_work','review_status'
 ];
 const advancedFields=filterFields.slice(2);
 const filterOrder={rarity:['UR','SSR','SR','R','N'],series_ids:['twilights','casting','mysongs','parallel','prelude','birthday','vote_selection','expansion','axe8']};
 const filterGroups=new Map();
 const selectionCounts=new Map();
 for(const field of filterFields){
  const primary=field==='card_kind'||field==='rarity';
  const group=document.createElement(primary?'fieldset':'details');
  group.className='filter-group'+(primary?' primary-filter':'');
  if(primary){
   const legend=document.createElement('legend');
   legend.textContent=labels[field];
   group.append(legend);
  }else{
   const summary=document.createElement('summary');
   summary.textContent=labels[field]+' ';
   const count=document.createElement('span');
   count.className='selection-count';
   summary.append(count);
   selectionCounts.set(field,count);
   group.append(summary);
  }
  const options=document.createElement('div');
  options.className='filter-options';
  const order=filterOrder[field];
  const values=[...new Set(cards.flatMap(card=>Array.isArray(card[field])?card[field]:[card[field]??'unknown']))].sort((a,b)=>{
   if(order){
    const ai=order.indexOf(a),bi=order.indexOf(b);
    if(ai!==bi)return (ai<0?order.length:ai)-(bi<0?order.length:bi);
   }
   return text(a).localeCompare(text(b),'ja');
  });
  for(const [index,value] of values.entries()){
   const label=document.createElement('label');
   label.className='filter-option';
   const input=document.createElement('input');
   input.type='checkbox';
   input.name=field;
   input.id='filter-'+field+'-'+index;
   input.value=value;
   input.dataset.filter=field;
   label.append(input,document.createTextNode(text(value)));
   options.append(label);
  }
  group.append(options);
  filterGroups.set(field,group);
  $(primary?'filters':'advanced-groups').append(group);
 }
 for(const field of [
  'first_implemented_on','card_title','idol_name','card_kind','rarity',
  'unit_name','acquisition_category','series_ids'
 ])$('sort').add(new Option(labels[field],field));

 const controls=[...document.querySelectorAll('.controls input,.controls select,.result-tools select')];
 function restore(){
  for(const element of controls){
   if(element.dataset.filter)element.checked=params.getAll(element.name).includes(element.value);
   else if(element.type==='checkbox')element.checked=!!params.get(element.id);
   else element.value=params.get(element.id)??(element.id==='sort'?'first_implemented_on':element.id==='direction'?'desc':'');
  }
  $('advanced-filters').open=advancedFields.some(field=>params.getAll(field).length)||!!(params.get('from')||params.get('to'));
  for(const field of advancedFields)filterGroups.get(field).open=!!params.getAll(field).length;
 }
 function updateFilterSummary(){
  const parts=[];
  for(const field of filterFields){
   const selected=params.getAll(field);
   if(selectionCounts.has(field))selectionCounts.get(field).textContent=selected.length?'（'+selected.length+'件選択）':'';
   if(selected.length)parts.push(labels[field]+'：'+selected.map(text).join('・'));
  }
  const advancedCount=advancedFields.reduce((sum,field)=>sum+params.getAll(field).length,0)
   +Number(!!params.get('from'))+Number(!!params.get('to'));
  $('advanced-count').textContent=advancedCount?'（'+advancedCount+'条件）':'';
  if(params.get('q'))parts.push('検索：'+params.get('q'));
  if(params.get('from'))parts.push('実装日から：'+params.get('from'));
  if(params.get('to'))parts.push('実装日まで：'+params.get('to'));
 $('active-filters').textContent=parts.length?'選択中：'+parts.join(' / '):'絞り込み条件なし';
 }

 const more=document.createElement('button');
 more.id='more';
 more.type='button';
 $('cards').after(more);
 function add(parent,tag,value,className){
  const element=document.createElement(tag);
  element.textContent=value;
  if(className)element.className=className;
  parent.append(element);
  return element;
 }
 function render(limit=100){
  shown=search(cards,params);
  updateFilterSummary();
  $('count').textContent=`${shown.length} / ${cards.length} 件`;
  $('cards').replaceChildren();
  if(!shown.length){
   const empty=add($('cards'),'li','条件に一致するカードはありません。','empty-state');
   const reset=add(empty,'button','条件をリセット');
   reset.type='button';
   reset.onclick=()=>$('reset').click();
  }
  for(const cardData of shown.slice(0,limit)){
   const card=add($('cards'),'li','','card');
   const type=cardData.variant_kind==='base'?'通常':'アイドルロード派生';
   add(card,'div',`${cardData.card_kind} / ${text(cardData.rarity)} · ${type}`,'badge');
   add(card,'h3',cardData.card_title,'card-title');
   add(card,'p',`${cardData.idol_name} · ${cardData.unit_name??'ユニット欄空欄'}`,'card-person');
   add(card,'p',`${text(cardData.first_implemented_on)} · ${text(cardData.acquisition_category)}`,'card-meta');
   if(cardData.series_ids.length)add(card,'p',cardData.series_ids.map(text).join('・'),'card-series');
   const action=document.createElement('div');
   action.className='card-action';
   if(cardData.wiki_url){
    const link=add(action,'a','Wiki個別ページへ ↗');
    link.href=cardData.wiki_url;
    link.target='_blank';
    link.rel='noopener noreferrer';
    link.setAttribute('aria-label',cardData.card_title+cardData.idol_name+'のWiki個別ページ（外部サイト）');
   }else add(action,'span','Wiki個別ページ未確認（一覧に収録）','no-wiki');
   card.append(action);
   add(card,'p','確認状態：'+text(cardData.review_status),'card-review');
   const refs=document.createElement('p');
   refs.className='sources';
   refs.append(document.createTextNode('出典：'));
   for(const [index,ref] of cardData.source_refs.entries()){
    if(index)refs.append(document.createTextNode(' / '));
    const url=sourceUrls.get(cardData.card_id)?.get(ref);
    if(url){
     const link=document.createElement('a');
     link.textContent=sourceNames[ref]??ref;
     link.href=url;
     link.target='_blank';
     link.rel='noopener noreferrer';
     link.setAttribute('aria-label',cardData.card_title+cardData.idol_name+'の出典：'+(sourceNames[ref]??ref)+'（外部サイト）');
     refs.append(link);
    }else refs.append(document.createTextNode(sourceNames[ref]??ref));
   }
   if(!cardData.source_refs.length)refs.append(document.createTextNode('未確認'));
   card.append(refs);
  }
  more.hidden=shown.length<=limit;
  more.textContent=`さらに表示（${Math.min(limit,shown.length)} / ${shown.length} 件表示中）`;
  more.onclick=()=>render(limit+100);
 }
 restore();
 render();
 for(const element of controls)element.addEventListener('input',()=>{
  params=new URLSearchParams();
  for(const control of controls){
   if(control.dataset.filter){
    if(control.checked)params.append(control.name,control.value);
   }else if(control.type==='checkbox'){
    if(control.checked)params.set(control.id,'1');
   }else if(control.value)params.set(control.id,control.value);
  }
  history.replaceState(null,'',params.size?'?'+params:location.pathname);
  render();
 });
 $('q').addEventListener('keydown',event=>{
  if(event.key==='Enter'){
   event.preventDefault();
   $('results-heading').scrollIntoView({block:'start'});
  }
 });
 $('reset').onclick=()=>{
  params=new URLSearchParams();
  restore();
  history.replaceState(null,'',location.pathname);
  render();
 };
 $('export').onclick=()=>{
  const link=document.createElement('a');
  link.href=URL.createObjectURL(new Blob([csv(shown,meta)],{type:'text/csv;charset=utf-8'}));
  link.download=`cards-${meta.dataset_version}-search.csv`;
  link.click();
  setTimeout(()=>URL.revokeObjectURL(link.href),1000);
 };

 const summary=$('coverage-summary');
 summary.textContent=`${cards.length}件収録（P ${coverage.by_kind?.P??'—'}件 / S ${coverage.by_kind?.S??'—'}件） · ${coverage.target_to??'確認日不明'}まで · 公式全網羅未確認`;
 const coverageBody=$('coverage-body');
 const coverageLine=(heading,value)=>{
  const row=document.createElement('div');
  const term=add(row,'dt',heading);
  const description=add(row,'dd',value);
  coverageBody.append(row);
  return [term,description];
 };
 coverageLine('対象',coverage.complete?'収録範囲照合済み':coverage.scope==='sample'?'少数実データの試作・全件版未完成':'enza版のWiki一覧を収録。公式全網羅は未確認');
 coverageLine('件数',cards.length+'件（P '+(coverage.by_kind?.P??'—')+'件 / S '+(coverage.by_kind?.S??'—')+'件）');
 coverageLine('対象期間',(coverage.target_from??coverage.min_date??'不明')+' ～ '+(coverage.target_to??coverage.max_date??'不明')+'。実装日確認範囲 '+(coverage.min_date??'不明')+' ～ '+(coverage.max_date??'不明'));
 const gaps=[];
 if(coverage.missing?.wiki_url)gaps.push('Wiki個別ページなし '+coverage.missing.wiki_url+'件');
 if(coverage.missing?.first_implemented_on)gaps.push('初回実装日不明 '+coverage.missing.first_implemented_on+'件');
 if(coverage.missing?.unit_name)gaps.push('ユニット欄空欄 '+coverage.missing.unit_name+'件');
 coverageLine('欠損',gaps.join(' / ')||'主要項目の欠損なし');
 coverageLine('未確認',(coverage.unverified??[]).join('、')||'なし');
 $('version').textContent=`UI版 ${window.UI_VERSION} / データ版 ${meta.dataset_version} / 生成日時 ${meta.published_at}`;
 for(const [file,label] of [
  ['cards.json','全件 JSON'],['cards.csv','全件 CSV'],['cards.xlsx','全件 Excel'],
  ['manifest.json','版情報'],['coverage.json','収録範囲'],['sources.json','項目別出典']
 ]){
  const link=document.createElement('a');
  link.href=base+file;
  link.textContent=label;
  $('downloads').append(link);
 }
 $('audit').textContent=JSON.stringify(coverage,null,2);
}catch(error){
 $('coverage-summary').textContent='データを読み込めませんでした。再読み込みしてください。 '+error.message;
 $('coverage-details').hidden=true;
 $('count').textContent='読み込み失敗';
 $('export').disabled=true;
}