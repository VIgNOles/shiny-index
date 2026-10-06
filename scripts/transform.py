"""Offline assertion parser for the one captured card; full list parser pending."""
import argparse
import hashlib
import sys
from pathlib import Path
from bs4 import BeautifulSoup
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.indexer import read,write,digest
p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('research_batch');p.add_argument('output');a=p.parse_args()
run=Path(a.run); fetch=read(run/'fetch.json');raw=(run/'response.html').read_bytes()
if fetch['status']!='fetched' or hashlib.sha256(raw).hexdigest()!=fetch['sha256']:raise ValueError('failed/tampered acquisition')
soup=BeautifulSoup(raw,'html.parser');batch=read(a.research_batch)
card=next(c for c in batch['cards'] if c['wiki_url']==fetch['url'])
if card['card_title']+card['idol_name'] not in soup.title.get_text():raise ValueError('unexpected title / HTTP 200 error')
expected=card['first_implemented_on'].replace('-','/')
matching=[t for t in soup.select('table') if '実装日' in t.get_text() and expected in t.get_text()]
if len(matching)!=1:raise ValueError('date table structure changed / ambiguous date')
card['wiki_link_status']='checked'
batch.update(cards=[card],run_id='http-'+fetch['sha256'][:16],observed_at=fetch['fetched_at'],scope='sample',status='validated',provenance={'response_sha256':fetch['sha256'],'research_fields':'design.md 2.3','http_checked_fields':['card_title','idol_name','first_implemented_on'],'parser_version':'sample-assertion-1'})
write(a.output,batch)
print('Validated 1 real card from saved response; kind/rarity remain research assertions')
