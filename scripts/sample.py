"""Extract the supplied research table, not fabricated test card data."""
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.indexer import write,digest
from bs4 import BeautifulSoup
doc=Path('design.md').read_text(encoding='utf-8')
links={k:url for k,url in re.findall(r'\| (C\d+) \| \[[^\]]+\]\((https://[^)]+)\)',doc)}
cards=[]
categories=['permanent_gacha','permanent_gacha','collection_gacha','permanent_gacha','limited_gacha','permanent_gacha','collaboration_gacha','initial','event_reward']
for line in doc.splitlines():
 if re.match(r'\| S\d\d \|',line):
  x=[v.strip() for v in line.split('|')[1:-1]]; i=int(x[0][1:])-1
  kind,rarity=re.match(r'([PS])・(UR|SSR|SR|R|N)',x[3]).groups()
  cards.append(dict(card_title=x[1],idol_id='idol_'+str(['櫻木真乃','樋口円香','浅倉透','鈴木羽那','ルビー','田中摩美々','園田智代子'].index(x[2])+1),idol_name=x[2],card_kind=kind,rarity=rarity,unit_id=None,unit_name=None,first_implemented_on=x[5],acquisition_category=categories[i],series_ids=['casting'] if i==2 else ['birthday'] if i==4 else [],series_status='known' if i in [2,4] else 'unknown',collab_work='【推しの子】' if i==6 else None,wiki_url=links[f'C{i+1:02}'],wiki_link_status='observed',variant_kind='base',review_status='wiki_only',source_ref=f'design-C{i+1:02}'))
assert len(cards)==9
soup=BeautifulSoup(Path('private/raw/sample.html').read_text(encoding='utf-8'),'html.parser')
text=soup.get_text(' ',strip=True)
assert '【ほわっとスマイル】櫻木真乃' in soup.title.text
assert '2018/04/24' in text
cards[0]['wiki_link_status']='checked'
batch={'status':'validated','scope':'sample','observed_at':'2026-10-07','cards':cards,'provenance':'design.md section 2.3; C01 additionally checked against saved HTTP response','run_id':'sample-'+digest(cards)[:16]}
write('private/sample-batch.json',batch)
print('9 research records; 1 saved HTTP response checked; full coverage not verified')
