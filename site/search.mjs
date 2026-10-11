export const seriesNames={
 casting:'キャスコレ',twilights:'トワコレ',parallel:'パラコレ',
 mysongs:'マイコレ',prelude:'プレコレ',birthday:'誕生日',
 expansion:'エクスパンション',axe8:'AXE8',vote_selection:'投票企画選出'
};
export const browseOptions=[
 ['prelude','プレコレ'],['casting','キャスコレ'],['parallel','パラコレ'],
 ['twilights','トワコレ'],['mysongs','マイコレ'],
 ['limited_gacha','期間限定'],['permanent_gacha','恒常'],['other','その他']
];
const browseSeries=new Set(browseOptions.slice(0,5).map(([value])=>value));
export function matchesBrowse(card,value){
 if(browseSeries.has(value))return card.series_ids.includes(value);
 if(value==='limited_gacha'||value==='permanent_gacha')
  return card.acquisition_category===value;
 if(value==='other')return !card.series_ids.some(id=>browseSeries.has(id))&&
  card.acquisition_category!=='limited_gacha'&&
  card.acquisition_category!=='permanent_gacha';
 return false;
}
const seriesAliases={
 casting:'キャスティング',twilights:'トワイライツ',parallel:'パラレル',
 mysongs:'マイソングス',prelude:'プレリュード'
};
export const officialUnits=[
 {name:'イルミネーションスターズ',idols:['櫻木真乃','風野灯織','八宮めぐる']},
 {name:'アンティーカ',idols:['月岡恋鐘','幽谷霧子','三峰結華','田中摩美々','白瀬咲耶']},
 {name:'放課後クライマックスガールズ',idols:['小宮果穂','園田智代子','西城樹里','杜野凛世','有栖川夏葉']},
 {name:'アルストロメリア',idols:['桑山千雪','大崎甘奈','大崎甜花']},
 {name:'ストレイライト',idols:['芹沢あさひ','黛冬優子','和泉愛依']},
 {name:'ノクチル',idols:['浅倉透','樋口円香','福丸小糸','市川雛菜']},
 {name:'シーズ',idols:['七草にちか','緋田美琴']},
 {name:'コメティック',idols:['斑鳩ルカ','鈴木羽那','郁田はるき']}
];
const unitRanks=new Map(officialUnits.map((unit,index)=>[unit.name,index]));
const idolRanks=new Map(officialUnits.flatMap((unit,unitIndex)=>unit.idols.map((idol,idolIndex)=>[idol,unitIndex*10+idolIndex])));
const rarityRanks=new Map(['UR','SSR','SR','R','N'].map((rarity,index)=>[rarity,index]));
export const norm=value=>String(value??'').normalize('NFKC').toLocaleLowerCase('ja').replace(/\s+/g,' ').trim();

export function parseDatePart(value){
 if(!value)return null;
 const match=/^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$/.exec(value);
 if(!match)return null;
 const year=Number(match[1]),month=match[2]?Number(match[2]):null,day=match[3]?Number(match[3]):null;
 if(year<1||month!==null&&(month<1||month>12))return null;
 const lastDay=month===null?31:new Date(Date.UTC(year,month,0)).getUTCDate();
 if(day!==null&&(day<1||day>lastDay))return null;
 const start=value.length===4?value+'-01-01':value.length===7?value+'-01':value;
 const end=value.length===4?value+'-12-31':value.length===7?value+'-'+String(lastDay).padStart(2,'0'):value;
 return {value,start,end,precision:value.length===4?'year':value.length===7?'month':'day'};
}
const rank=(map,value)=>map.get(value)??Number.MAX_SAFE_INTEGER;
const byDateDesc=(a,b)=>a.first_implemented_on&&b.first_implemented_on?
 b.first_implemented_on.localeCompare(a.first_implemented_on):a.first_implemented_on?-1:b.first_implemented_on?1:0;
const byDateAsc=(a,b)=>a.first_implemented_on&&b.first_implemented_on?
 a.first_implemented_on.localeCompare(b.first_implemented_on):a.first_implemented_on?-1:b.first_implemented_on?1:0;
function compareCards(a,b,sort,direction){
 if(sort==='date_new'||sort==='first_implemented_on'&&direction!=='asc')return byDateDesc(a,b);
 if(sort==='date_old'||sort==='first_implemented_on'&&direction==='asc')return byDateAsc(a,b);
 if(sort==='rarity_high'||sort==='rarity'&&direction!=='asc')return rank(rarityRanks,a.rarity)-rank(rarityRanks,b.rarity)||byDateDesc(a,b);
 if(sort==='rarity_low'||sort==='rarity'&&direction==='asc')return rank(rarityRanks,b.rarity)-rank(rarityRanks,a.rarity)||byDateDesc(a,b);
 if(sort==='unit_official')return rank(unitRanks,a.unit_name)-rank(unitRanks,b.unit_name)||
  rank(idolRanks,a.idol_name)-rank(idolRanks,b.idol_name)||byDateDesc(a,b);
 if(sort==='idol_official')return rank(idolRanks,a.idol_name)-rank(idolRanks,b.idol_name)||byDateDesc(a,b);
 if(sort==='title'||sort==='card_title')return a.card_title.localeCompare(b.card_title,'ja')*(direction==='desc'?-1:1)||byDateDesc(a,b);
 const av=a[sort],bv=b[sort];
 if(av==null&&bv!=null)return 1;
 if(bv==null&&av!=null)return -1;
 return String(av??'').localeCompare(String(bv??''),'ja')*(direction==='asc'?1:-1)||byDateDesc(a,b);
}
export function search(cards,params){
 const terms=norm(params.get('q')).split(' ').filter(Boolean);
 const fields=['card_kind','rarity','acquisition_category','series_ids','collab_work','review_status'];
 const browse=params.getAll('browse');
 const people=params.getAll('person');
 const legacyUnits=params.getAll('unit_name'),legacyIdols=params.getAll('idol_name');
 const from=parseDatePart(params.get('from')),to=parseDatePart(params.get('to'));
 const sort=params.get('sort')||'date_new',direction=params.get('direction');
 const rows=cards.filter(card=>{
  const searchable=[
   card.card_title,card.idol_name,card.unit_name,card.collab_work,card.acquisition_category,
   ...card.series_ids.flatMap(id=>[id,seriesNames[id],seriesAliases[id]])
  ].join(' ');
  if(!terms.every(term=>norm(searchable).includes(term)))return false;
  if(browse.length&&!browse.some(value=>matchesBrowse(card,value)))return false;
  if(!fields.every(field=>!params.getAll(field).length||params.getAll(field).some(value=>
   value==='unknown'?card[field]==null||card[field]==='unknown':
   Array.isArray(card[field])?card[field].includes(value):card[field]===value)))return false;
  if(people.length){
   if(!people.some(value=>value==='unit:none'?card.unit_id==null:
    value.startsWith('unit:')?card.unit_id===value.slice(5):
    value.startsWith('idol:')?card.idol_id===value.slice(5):false))return false;
  }else{
   if(legacyUnits.length&&!legacyUnits.includes(card.unit_name??'unknown'))return false;
   if(legacyIdols.length&&!legacyIdols.includes(card.idol_name??'unknown'))return false;
  }
  if(from&&(!card.first_implemented_on||card.first_implemented_on<from.start))return false;
  if(to&&(!card.first_implemented_on||card.first_implemented_on>to.end))return false;
  return true;
 });
 rows.sort((a,b)=>compareCards(a,b,sort,direction)||a.card_id.localeCompare(b.card_id));
 return rows;
}
export function csv(rows,meta){
 const fields=['dataset_version','schema_version','published_at',...Object.keys(rows[0]??{})];
 const safe=value=>{
  let result=value==null?'':typeof value==='object'?JSON.stringify(value):String(value);
  if(/^[=+\-@\t\r']|^\s+[=+\-@]/.test(result))result="'"+result;
  return '"'+result.replaceAll('"','""')+'"';
 };
 return '\ufeff'+[fields,...rows.map(card=>fields.map(field=>card[field]??meta[field]??''))]
  .map(row=>row.map(safe).join(',')).join('\r\n');
}