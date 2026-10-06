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
for(const f of ['card_kind','rarity','idol_name','unit_name','acquisition_category','series_ids','collab_work','review_status']){
 const label=document.createElement('label');label.textContent=labels[f];const select=document.createElement('select');select.id=f;select.multiple=true;select.setAttribute('aria-label',labels[f]);
 for(const v of [...new Set(cards.flatMap(c=>Array.isArray(c[f])?c[f]:[c[f]??'unknown']))].sort())select.add(new Option(text(v),v));
 label.append(select);$('filters').append(label);
}
for(const f of ['first_implemented_on','card_title','idol_name','card_kind','rarity','unit_name','acquisition_category','series_ids'])$('sort').add(new Option(labels[f],f));
const controls=[...document.querySelectorAll('.controls input,.controls select')];
function restore(){for(const el of controls){if(el.multiple)for(const o of el.options)o.selected=params.getAll(el.id).includes(o.value);else if(el.type==='checkbox')el.checked=!!params.get(el.id);else el.value=params.get(el.id)??(el.id==='sort'?'first_implemented_on':el.id==='direction'?'desc':'');}}
const more=document.createElement('button');more.id='more';$('cards').after(more);
function render(limit=100){
 shown=search(cards,params);$('count').textContent=`${shown.length} / ${cards.length} 件`;$('cards').replaceChildren();
 if(!shown.length)$('cards').textContent='条件に一致するカードはありません。';
 for(const c of shown.slice(0,limit)){const card=document.createElement('article');card.className='card';
 const add=(tag,value,cls)=>{const el=document.createElement(tag);el.textContent=value;if(cls)el.className=cls;card.append(el);return el;};
 add('div',`${c.card_kind} / ${text(c.rarity)} · ${c.variant_kind==='base'?'通常':c.variant_kind}`,'badge');add('h3',c.card_title);add('p',`${c.idol_name} / ${text(c.unit_name)}`);add('p',`${text(c.first_implemented_on)} · ${text(c.acquisition_category)}`);add('p',c.series_ids.map(text).join('・')||'シリーズ未確認');
 if(c.wiki_url){const a=add('a','Wiki個別ページ ↗');a.href=c.wiki_url;a.target='_blank';a.rel='noopener noreferrer';}else add('p','Wiki未掲載');
 add('p',`出典：${c.source_refs.join(', ')} / ${text(c.review_status)}`);const source=doc.sources.find(e=>e.card_id===c.card_id&&e.url);if(source){const ref=add('a','収録元の出典 ↗');ref.href=source.url;ref.target='_blank';ref.rel='noopener noreferrer';}$('cards').append(card);
 }
 more.hidden=shown.length<=limit;more.textContent=`さらに表示（${Math.min(limit,shown.length)} / ${shown.length} 件表示中）`;more.onclick=()=>render(limit+100);
}
restore();render();
for(const el of controls)el.addEventListener('input',()=>{params=new URLSearchParams();for(const c of controls){if(c.multiple){for(const o of c.selectedOptions)params.append(c.id,o.value);}else if(c.type==='checkbox'){if(c.checked)params.set(c.id,'1');}else if(c.value)params.set(c.id,c.value);}history.replaceState(null,'','?'+params);render();});
$('reset').onclick=()=>{params=new URLSearchParams();restore();history.replaceState(null,'',location.pathname);render();};
$('export').onclick=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv(shown,meta)],{type:'text/csv;charset=utf-8'}));a.download=`cards-${meta.dataset_version}-search.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};
$('coverage').textContent=`${coverage.complete?'収録範囲照合済み':coverage.scope==='sample'?'少数実データの試作・全件版未完成':'全期間一覧のローカル収録版・公式全網羅未確認'}。${cards.length}件 / ${coverage.min_date} ～ ${coverage.max_date}。未確認：${coverage.unverified.join('、')}`;
$('version').textContent=`版 ${meta.dataset_version} / 生成日時 ${meta.published_at}`;
for(const [file,label]of[['cards.json','全件 JSON'],['cards.csv','全件 CSV'],['cards.xlsx','全件 Excel'],['manifest.json','版情報'],['coverage.json','収録範囲'],['sources.json','項目別出典']]){const a=document.createElement('a');a.href=base+file;a.textContent=label;$('downloads').append(a);}
$('audit').textContent=JSON.stringify(coverage,null,2);
}catch(e){$('coverage').textContent='データを読み込めませんでした。再読み込みしてください。 '+e.message;$('export').disabled=true;}
