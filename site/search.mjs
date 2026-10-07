export const seriesNames={casting:'キャスティング',twilights:'トワイライツ',parallel:'パラレル',mysongs:'マイソングス',prelude:'プレリュード',birthday:'誕生日',expansion:'エクスパンション',axe8:'AXE8',vote_selection:'投票企画選出'};
export const norm=s=>String(s??'').normalize('NFKC').toLocaleLowerCase('ja').replace(/\s+/g,' ').trim();
export function search(cards,p){
 const terms=norm(p.get('q')).split(' ').filter(Boolean);
 const fields=['card_kind','rarity','idol_name','unit_name','acquisition_category','series_ids','collab_work','review_status'];
 let rows=cards.filter(c=>terms.every(t=>norm([c.card_title,c.idol_name,c.unit_name,...c.series_ids.map(v=>v+' '+(seriesNames[v]??v))].join(' ')).includes(t))&&fields.every(f=>!p.getAll(f).length||p.getAll(f).some(v=>v==='unknown'?c[f]==null||c[f]==='unknown':Array.isArray(c[f])?c[f].includes(v):c[f]===v))&&(!p.get('from')||c.first_implemented_on&&c.first_implemented_on>=p.get('from'))&&(!p.get('to')||c.first_implemented_on&&c.first_implemented_on<=p.get('to'))&&(!p.get('missing')||c.unknown_fields.length>0));
 const sort=p.get('sort')||'first_implemented_on',direction=p.get('direction')==='asc'?1:-1;
 rows.sort((a,b)=>{
  const av=a[sort],bv=b[sort]; if(av==null&&bv!=null)return 1;if(bv==null&&av!=null)return -1;
  let cmp=sort==='rarity'?['N','R','SR','SSR','UR'].indexOf(av)-['N','R','SR','SSR','UR'].indexOf(bv):String(av??'').localeCompare(String(bv??''),'ja');
  return cmp*direction||a.card_id.localeCompare(b.card_id);
 });return rows;
}
export function csv(rows,meta){
 const fields=['dataset_version','schema_version','published_at',...Object.keys(rows[0]??{})];
 const safe=v=>{let s=v==null?'':typeof v==='object'?JSON.stringify(v):String(v);if(/^[=+\-@\t\r']|^\s+[=+\-@]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"'};
 return '\ufeff'+[fields,...rows.map(c=>fields.map(f=>c[f]??meta[f]??''))].map(r=>r.map(safe).join(',')).join('\r\n');
}
