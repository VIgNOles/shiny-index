"""Parse saved Wiki list HTML. No network; audit every card anchor independently."""
import copy
import os
import re
import sys
from pathlib import Path
from urllib.parse import urljoin,unquote,parse_qs,urlsplit
from collections import Counter
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.indexer import read,write,digest,key
RAW_ROOT=Path(os.environ.get('RAW_RUN_ROOT','private/raw'))
OUTPUT_ROOT=Path(os.environ.get('TRANSFORM_OUTPUT_ROOT','private'))
SEED_ROOT=Path(os.environ.get('TRANSFORM_SEED_ROOT','private'))
SCOPE=os.environ.get('TRANSFORM_SCOPE','initial-full')
if SCOPE not in ('initial-full','full'):raise ValueError('TRANSFORM_SCOPE must be initial-full or full')
if RAW_ROOT!=Path('private/raw') and 'TRANSFORM_OUTPUT_ROOT' not in os.environ:
 raise SystemExit('Set TRANSFORM_OUTPUT_ROOT for a new raw run; existing candidates must not be overwritten')
OUTPUT_ROOT.mkdir(parents=True,exist_ok=True)

BASE='https://wikiwiki.jp'
UNITS={'イルミネ':'イルミネーションスターズ','アンティーカ':'アンティーカ','放クラ':'放課後クライマックスガールズ','アルスト':'アルストロメリア','ストレイ':'ストレイライト','ノクチル':'ノクチル','シーズ':'シーズ','コメティック':'コメティック'}
def clean(el):
 c=copy.copy(el)
 for n in c.select('.note_super'):n.decompose()
 return re.sub(r'\s+','',c.get_text())
def grid(table):
 spans={};out=[]
 for ri,tr in enumerate(table.find_all('tr')):
  row={};ci=0
  for (r,c),el in list(spans.items()):
   if r==ri:row[c]=el
  for cell in tr.find_all(['td','th'],recursive=False):
   while ci in row:ci+=1
   for r in range(ri,ri+int(cell.get('rowspan',1))):
    for c in range(ci,ci+int(cell.get('colspan',1))):
     spans[r,c]=cell
     if r==ri:row[c]=cell
   ci+=int(cell.get('colspan',1))
  out.append([row.get(c) for c in range(max(row,default=-1)+1)])
 return out
def cardlink(a):return a.get('href','').startswith('/shinycolors/') and bool(re.match(r'^【.+】.+',a.get_text(strip=True)))
def readpage(name):
 folder=RAW_ROOT/name;meta=read(folder/'fetch.json');raw=(folder/'response.html').read_bytes()
 import hashlib
 assert meta['status']=='fetched' and hashlib.sha256(raw).hexdigest()==meta['sha256']
 return BeautifulSoup(raw,'html.parser'),meta
seed=read(SEED_ROOT/'sample-batch.json')['cards'];idols={c['idol_name']:c['idol_id'] for c in seed}
idpath=OUTPUT_ROOT/'idol-registry.json'
registry_source=idpath if idpath.exists() else SEED_ROOT/'idol-registry.json'
if registry_source.exists():idols.update(read(registry_source))
def idol_id(name):
 if name not in idols:
  import uuid
  idols[name]='idol_'+str(uuid.uuid4())
 return idols[name]
def category(raw,section):
 series=[];cat='unknown'
 if raw.startswith('プラチナ'):cat='permanent_gacha'
 elif raw in ['キャスコレ','トワコレ','パラコレ','マイコレ','プレコレ']:cat='collection_gacha';series=[{'キャスコレ':'casting','トワコレ':'twilights','パラコレ':'parallel','マイコレ':'mysongs','プレコレ':'prelude'}[raw]]
 elif raw in ['期間限定','期間限定ガシャ','限定-誕','限定-囁','限定-特','期間-特']:cat='limited_gacha';series=['birthday'] if raw=='限定-誕' else []
 elif raw=='限定-XPN':cat='limited_gacha';series=['expansion']
 elif raw=='AXE8':cat='limited_gacha';series=['axe8']
 elif raw=='限定-投':cat='limited_gacha';series=['vote_selection']
 elif raw=='プラ-投':cat='permanent_gacha';series=['vote_selection']
 elif raw.startswith('コラボ'):cat='collaboration_gacha'
 elif raw=='初期所持':cat='initial'
 elif raw=='ガシャ特典':cat='gacha_bonus'
 elif raw.startswith('CP'):cat='campaign'
 elif raw in ['パッケージ','BD特典','劇場特典','CD特典']:cat='other_bonus'
 elif raw=='ミッション':cat='mission'
 elif raw=='グレフェス':cat='exchange'
 elif 'イベント報酬' in section:cat='event_reward'
 return cat,series
cards={};sections=[];duplicates=[];unknown=[];expectations=[]
for name,kind,sid in [('p-list','P','W02'),('s-list','S','W03'),('s-volume','S','W04')]:
 soup,meta=readpage(name)
 for ti,table in enumerate(soup.select('table')):
  h=table.find_previous(['h2','h3','h4']);section=clean(h) if h else ''
  rarity=re.match(r'^(UR|SSR|SR|R|N)(?:\(|$)',section)
  if not rarity:continue
  rows=grid(table);headers=None;count=0
  # Audit anchors separately from header-based row extraction.
  expected=[a for tr in table.find_all('tr') for cell in tr.find_all(['td','th'],recursive=False) for a in cell.find_all('a',href=True) if cardlink(a)]
  expected+=table.select('.noexists')
  if not expected:continue
  for ri,row in enumerate(rows):
   names=[clean(c) if c else '' for c in row]
   if names and 'カード名' in names[0] and any('追加日' in s for s in names):headers=names;continue
   links=[a for c in row if c for a in c.find_all('a',href=True) if cardlink(a)]
   missing=[n for c in row if c for n in c.select('.noexists')]
   if not links and not missing:continue
   if headers is None:raise ValueError(f'missing header {name}:{ti}:{ri}')
   if len(links)+len(missing)!=1:raise ValueError('ambiguous row card links')
   a=links[0] if links else missing[0]
   if missing:
    page_name=parse_qs(urlsplit(a.select_one('a')['href']).query)['page'][0]
    title,name_id=re.fullmatch(r'(【.+】)(.+)',page_name).groups()
   else:title,name_id=re.fullmatch(r'(【.+】)(.+)',a.get_text(strip=True)).groups()
   def field(label):
    indices=[i for i,h in enumerate(headers) if h.startswith(label)]
    if len(indices)!=1:raise ValueError(f'header {label}: {headers}')
    return names[indices[0]] if indices[0]<len(names) else ''
   d=field('追加日');dateval=d.replace('/','-') if re.fullmatch(r'\d{4}/\d{2}/\d{2}',d) else None
   unit=field('ユニット');unitname=UNITS.get(unit)
   raw=field('ガシャ') if any(x.startswith('ガシャ') for x in headers) else field('入手')
   cat,series=category(raw,section)
   if cat=='unknown':unknown.append({'source':sid,'section':section,'title':title+name_id,'raw':raw})
   c=dict(card_title=title,idol_id=idol_id(name_id),idol_name=name_id,card_kind=kind,rarity=rarity[1],unit_id='unit_'+str(list(UNITS).index(unit)+1) if unitname else None,unit_name=unitname,first_implemented_on=dateval,acquisition_category=cat,series_ids=series,series_status='known' if series else 'unknown',collab_work='【推しの子】' if name_id in ['ルビー','MEMちょ','有馬かな','黒川あかね'] else None,wiki_url=urljoin(BASE,a['href']) if links else None,wiki_link_status='observed' if links else 'not_found',variant_kind='base',review_status='wiki_only',source_ref=sid,source_page=meta['url'],source_locator=f'{section}; table {ti}; row {ri}',source_hash=meta['sha256'],raw_acquisition=raw)
   if missing:c['source_key']='wikiwiki:https://wikiwiki.jp/shinycolors/'+page_name+':base'
   k=key(c);expectations.append({'source':sid,'table':ti,'row':ri,'key':k});count+=1
   if k in cards:
    previous=cards[k]
    if any(previous[f]!=c[f] for f in ['card_kind','rarity','card_title','idol_name','first_implemented_on']):raise ValueError('conflicting duplicate '+k)
    duplicates.append({'key':k,'source':sid})
   else:cards[k]=c
  if count!=len(expected):raise ValueError(f'unparsed anchors {name} {section}: {count}/{len(expected)}')
  sections.append({'source':sid,'section':section,'expected':len(expected),'parsed':count})

# A lost table or changed heading must fail, not silently shrink the scope.
contracts={'W02':{'UR(ガシャ)','SSR(ガシャ)','SR(ガシャ)','SR(イベント報酬など)','R(アイドルロード)'},'W03':{'UR(ガシャ)','SSR(ガシャ)','SSR(イベント報酬など)','SSR(キャンペーン報酬／ガシャ特典など)','SR(イベント報酬)','SR(キャンペーン報酬／ガシャ特典など)','SR(ガシャ)','R','N'},'W04':{'SR(イベント報酬)','SR(キャンペーン報酬／ガシャ特典など)','SR(ガシャ)','R','N'}}
for source,expected_sections in contracts.items():
 actual={x['section'] for x in sections if x['source']==source}
 if actual!=expected_sections:raise ValueError(f'Section contract changed: {source} {actual ^ expected_sections}')

# Road page explicitly lists eligible idols; add only names present there.
road,roadmeta=readpage('road');roadnames={re.sub(r'^【アイドルロード】','',a.get_text(strip=True)) for a in road.select('table a[href]') if a.get_text(strip=True).startswith('【アイドルロード】')}
road_count=0
for c in list(cards.values()):
 if c['card_kind']=='P' and c['rarity']=='R' and c['idol_name'] in roadnames:
  for rare,variant in [('SR','idol_road_sr'),('SSR','idol_road_ssr')]:
   v=copy.deepcopy(c);v.update(rarity=rare,variant_kind=variant,card_title='【アイドルロード】' if rare=='SSR' else c['card_title'],first_implemented_on=None,acquisition_category='mission',source_ref='W08',source_page=roadmeta['url'],source_hash=roadmeta['sha256'],source_locator='対象アイドル・レアリティ上昇・特化属性一覧')
   cards[key(v)]=v;road_count+=1

# Keep missing collab links visible; classify only when another captured source proves them.
collab,cm=readpage('collab');collablinks={unquote(urljoin(BASE,a['href'])):a.get_text(strip=True) for a in collab.select('#content a[href]') if cardlink(a)}
knownurls={unquote(c['wiki_url']) for c in cards.values() if c['wiki_url']}
missing_collab={u:n for u,n in collablinks.items() if u not in knownurls}
chron,chrono=readpage('chronology');chronlinks={unquote(urljoin(BASE,a['href'])):a.get_text(strip=True) for a in chron.select('#content a[href]') if cardlink(a)}
missing_chron={u:n for u,n in chronlinks.items() if u not in knownurls}
gacha,gm=readpage('gacha');gacha_text=clean(gacha)
if 'AXE8シリーズ限定アイドル' not in gacha_text:raise ValueError('AXE8 limited-series explanation missing from W09')
for c in cards.values():
 if c['raw_acquisition']=='AXE8':
  if re.sub(r'\s+','',c['card_title']+c['idol_name']) not in gacha_text:raise ValueError('AXE8 card missing from W09')
  c['field_sources']={f:{'source_ref':'W09','url':gm['url'],'response_hash':gm['sha256'],'locator':'AXE8シリーズ限定アイドル'} for f in ['acquisition_category','series_ids','series_status']}
fetched=[datetime.fromisoformat(read(RAW_ROOT/name/'fetch.json')['fetched_at']) for name in ['p-list','s-list','s-volume','collab','road','chronology','gacha']]
observed=max(fetched).astimezone(timezone(timedelta(hours=9))).date().isoformat()
coverage={'scope':'full-list-candidate','complete':False,'target_from':'2018-04-24','target_to':observed,'sections':sections,'expected_listing_rows':len(expectations),'deduplicated_listing_rows':len(cards)-road_count,'duplicate_inclusions':len(duplicates),'road_expansion':road_count,'missing_collab':missing_collab,'missing_chronology':missing_chron,'unknown_classifications':len(unknown),'unverified':['ゲーム全網羅・公式独立照合','各派生の個別初回日','特殊分類の意味','最新追加漏れ（別日の取得との照合未実施）']}
batch={'status':'validated','scope':SCOPE,'run_id':'full-'+digest({'cards':list(cards.values()),'source_hashes':[read(RAW_ROOT/name/'fetch.json')['sha256'] for name in ['p-list','s-list','s-volume','collab','road','chronology','gacha']],'observed_at':observed,'scope':SCOPE})[:16],'observed_at':observed,'cards':list(cards.values()),'coverage':coverage,'parser_version':'html-lists-3','dictionaries':[{'type':'idol','id':v,'name':k} for k,v in idols.items()]+[{'type':'unit','id':'unit_'+str(i+1),'name':v,'source':'W02/W08'} for i,(k,v) in enumerate(UNITS.items())]}
outputs=[(OUTPUT_ROOT/'full-batch.json',batch),(OUTPUT_ROOT/'full-audit.json',{'coverage':coverage,'expectations':expectations,'duplicates':duplicates,'unknown_classifications':unknown,'classification_sources':[{'source_ref':'W09','url':gm['url'],'sha256':gm['sha256'],'purpose':'AXE8 limited-series classification'}]}),(idpath,idols)]
for path,value in outputs:
 if path.exists() and read(path)!=value:raise FileExistsError(f'Candidate already exists with different content: {path}')
for path,value in outputs:
 if not path.exists():write(path,value)
print('Candidates',len(cards),'sections',sections,'missing collab',missing_collab,'missing chronology',len(missing_chron),'unknown labels',dict(Counter(x['raw'] for x in unknown)))
