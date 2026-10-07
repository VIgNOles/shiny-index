import{search,csv,seriesNames}from'./search.mjs';
const $=id=>document.getElementById(id);
const labels={card_kind:'P／S',rarity:'レアリティ',idol_name:'アイドル',unit_name:'ユニット',acquisition_category:'入手区分',series_ids:'シリーズ',collab_work:'コラボ作品',review_status:'確認状態',card_title:'カード名',first_implemented_on:'初回実装日'};
const display={permanent_gacha:'恒常ガシャ',limited_gacha:'期間限定',collection_gacha:'コレクション',collaboration_gacha:'コラボガシャ',event_reward:'イベント報酬',initial:'初期所持',unknown:'不明',wiki_only:'Wikiのみ確認',needs_review:'要確認',casting:'キャスティング',birthday:'誕生日'};
Object.assign(display,{...seriesNames,gacha_bonus:'ガシャ特典',other_bonus:'その他特典',mission:'ミッション',campaign:'キャンペーン・配布',exchange:'交換',other:'その他',official_checked:'公式照合済み',user_evidence_checked:'管理者資料確認済み'});
const text=v=>display[v]??v??'不明';
try{
const base=`data/${window.DATA_VERSION}/`;
const response=await fetch(base+'cards.json');if(!response.ok)throw Error('HTTP '+response.status);
const doc=await response.json();if(doc.meta.dataset_version!==window.DATA_VERSION)throw Error('版不一致');
const {cards,meta,coverage}=doc;let params=new URLSearchParams(location.search),shown=[];
const sourceNames={W02:'Pカード一覧',W03:'Sカード一覧',W04:'Sカード分冊',W05:'アイドル追加順',W07:'コラボアイドル',W08:'アイドルロード',W09:'ガシャ'};
const sourceUrls=new Map();
for(const source of doc.sources??[]){
 if(!source.url||!source.source_ref)continue;
 let url;try{url=new URL(source.url);}catch{continue;}
 if(url.protocol!=='https:'||url.hostname!=='wikiwiki.jp'||!url.pathname.startsWith('/shinycolors/'))continue;
 if(!sourceUrls.has(source.card_id))sourceUrls.set(source.card_id,new Map());
 sourceUrls.get(source.card_id).set(source.source_ref,url.href);
}

const filterFields=['card_kind','rarity','idol_name','unit_name','acquisition_category','series_ids','collab_work','review_status'];
const advancedFields=filterFields.slice(2),filterGroups=new Map(),selectionCounts=new Map();
for(const f of filterFields){
 const primary=f==='card_kind'||f==='rarity';
 const group=document.createElement(primary?'fieldset':'details');
 group.className='filter-group'+(primary?' primary-filter':'');
 if(primary){const legend=document.createElement('legend');legend.textContent=labels[f];group.append(legend);}
 else{const summary=document.createElement('summary');summary.textContent=labels[f]+' ';const count=document.createElement('span');count.className='selection-count';summary.append(count);selectionCounts.set(f,count);group.append(summary);}
 const options=document.createElement('div');options.className='filter-options';
 const values=[...new Set(cards.flatMap(c=>Array.isArray(c[f])?c[f]:[c[f]??'unknown']))].sort();
 for(const [i,v] of values.entries()){
  const label=document.createElement('label');label.className='filter-option';
  const input=document.createElement('input');input.type='checkbox';input.name=f;input.id='filter-'+f+'-'+i;input.value=v;input.dataset.filter=f;
  label.append(input,document.createTextNode(text(v)));options.append(label);
 }
 group.append(options);filterGroups.set(f,group);
 $(primary?'filters':'advanced-groups').append(group);
}
for(const f of ['first_implemented_on','card_title','idol_name','card_kind','rarity','unit_name','acquisition_category','series_ids'])$('sort').add(new Option(labels[f],f));
const controls=[...document.querySelectorAll('.controls input,.controls select')];
function restore(){
 for(const el of controls){
  if(el.dataset.filter)el.checked=params.getAll(el.name).includes(el.value);
  else if(el.type==='checkbox')el.checked=!!params.get(el.id);
  else el.value=params.get(el.id)??(el.id==='sort'?'first_implemented_on':el.id==='direction'?'desc':'');
 }
 $('advanced-filters').open=advancedFields.some(f=>params.getAll(f).length);
 for(const f of advancedFields)filterGroups.get(f).open=!!params.getAll(f).length;
}
function updateFilterSummary(){
 const parts=[];
 for(const f of filterFields){
  const selected=params.getAll(f);
  if(selectionCounts.has(f))selectionCounts.get(f).textContent=selected.length?'（'+selected.length+'件選択）':'';
  if(selected.length)parts.push(labels[f]+'：'+selected.map(text).join('・'));
 }
 const advancedCount=advancedFields.reduce((sum,f)=>sum+params.getAll(f).length,0);
 $('advanced-count').textContent=advancedCount?'（'+advancedCount+'件選択）':'';
 if(params.get('q'))parts.push('検索：'+params.get('q'));
 if(params.get('from'))parts.push('実装日から：'+params.get('from'));
 if(params.get('to'))parts.push('実装日まで：'+params.get('to'));
 if(params.get('missing'))parts.push('不明項目あり');
 $('active-filters').textContent=parts.length?'選択中：'+parts.join(' / '):'絞り込み条件なし';
}

const more=document.createElement('button');more.id='more';$('cards').after(more);
function render(limit=100){
 shown=search(cards,params);updateFilterSummary();$('count').textContent=`${shown.length} / ${cards.length} 件`;$('cards').replaceChildren();
 if(!shown.length)$('cards').textContent='条件に一致するカードはありません。';
 for(const c of shown.slice(0,limit)){const card=document.createElement('article');card.className='card';
 const add=(tag,value,cls)=>{const el=document.createElement(tag);el.textContent=value;if(cls)el.className=cls;card.append(el);return el;};
 add('div',`${c.card_kind} / ${text(c.rarity)} · ${c.variant_kind==='base'?'通常':c.variant_kind}`,'badge');add('h3',c.card_title);add('p',`${c.idol_name} / ${text(c.unit_name)}`);add('p',`${text(c.first_implemented_on)} · ${text(c.acquisition_category)}`);add('p',c.series_ids.map(text).join('・')||'シリーズ未確認');
 if(c.wiki_url){const a=add('a','Wiki個別ページ ↗');a.href=c.wiki_url;a.target='_blank';a.rel='noopener noreferrer';}else add('p','Wiki個別ページ未確認（一覧に収録）');
 add('p','確認状態：'+text(c.review_status));
 const refs=document.createElement('p');refs.className='sources';refs.append(document.createTextNode('出典：'));
 for(const [i,ref] of c.source_refs.entries()){
  if(i)refs.append(document.createTextNode(' / '));
  const url=sourceUrls.get(c.card_id)?.get(ref);
  if(url){const a=document.createElement('a');a.textContent=sourceNames[ref]??ref;a.href=url;a.target='_blank';a.rel='noopener noreferrer';refs.append(a);}
  else refs.append(document.createTextNode(sourceNames[ref]??ref));
 }
 if(!c.source_refs.length)refs.append(document.createTextNode('未確認'));
 card.append(refs);$('cards').append(card);
 }
 more.hidden=shown.length<=limit;more.textContent=`さらに表示（${Math.min(limit,shown.length)} / ${shown.length} 件表示中）`;more.onclick=()=>render(limit+100);
}
restore();render();
for(const el of controls)el.addEventListener('input',()=>{params=new URLSearchParams();for(const c of controls){if(c.dataset.filter){if(c.checked)params.append(c.name,c.value);}else if(c.type==='checkbox'){if(c.checked)params.set(c.id,'1');}else if(c.value)params.set(c.id,c.value);}history.replaceState(null,'',params.size?'?'+params:location.pathname);render();});
$('reset').onclick=()=>{params=new URLSearchParams();restore();history.replaceState(null,'',location.pathname);render();};
$('export').onclick=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv(shown,meta)],{type:'text/csv;charset=utf-8'}));a.download=`cards-${meta.dataset_version}-search.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};
const coverageBox=$('coverage');coverageBox.replaceChildren();
const coverageHeading=document.createElement('h2');coverageHeading.textContent='収録範囲';coverageBox.append(coverageHeading);
const coverageLine=(heading,value)=>{const row=document.createElement('p');const title=document.createElement('strong');title.textContent=heading+'：';row.append(title,document.createTextNode(value));coverageBox.append(row);};
coverageLine('対象',coverage.complete?'収録範囲照合済み':coverage.scope==='sample'?'少数実データの試作・全件版未完成':'enza版のWiki一覧を収録。公式全網羅は未確認');
coverageLine('件数',cards.length+'件（P '+(coverage.by_kind?.P??'—')+'件 / S '+(coverage.by_kind?.S??'—')+'件）');
coverageLine('対象期間',(coverage.target_from??coverage.min_date??'不明')+' ～ '+(coverage.target_to??coverage.max_date??'不明')+'。実装日確認範囲 '+(coverage.min_date??'不明')+' ～ '+(coverage.max_date??'不明'));
const gaps=[];
if(coverage.missing?.wiki_url)gaps.push('Wiki個別ページなし '+coverage.missing.wiki_url+'件');
if(coverage.missing?.first_implemented_on)gaps.push('初回実装日不明 '+coverage.missing.first_implemented_on+'件');
if(coverage.missing?.unit_name)gaps.push('所属未確認 '+coverage.missing.unit_name+'件');
coverageLine('欠損',gaps.join(' / ')||'主要項目の欠損なし');
coverageLine('未確認',(coverage.unverified??[]).join('、')||'なし');
$('version').textContent=`版 ${meta.dataset_version} / 生成日時 ${meta.published_at}`;
for(const [file,label]of[['cards.json','全件 JSON'],['cards.csv','全件 CSV'],['cards.xlsx','全件 Excel'],['manifest.json','版情報'],['coverage.json','収録範囲'],['sources.json','項目別出典']]){const a=document.createElement('a');a.href=base+file;a.textContent=label;$('downloads').append(a);}
$('audit').textContent=JSON.stringify(coverage,null,2);
}catch(e){$('coverage').textContent='データを読み込めませんでした。再読み込みしてください。 '+e.message;$('export').disabled=true;}
