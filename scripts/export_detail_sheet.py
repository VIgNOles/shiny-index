"""Validate/export the authoritative native detail Sheet snapshot into a new site candidate."""
import argparse,json,sys,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.detail_master import from_workbook
from src.detail_public import prepare
from scripts.transform_detail_html import load_cards
from src.indexer import ROOT,write,read
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('sheet_export');p.add_argument('site_candidate');p.add_argument('--master-snapshot');a=p.parse_args()
 m=from_workbook(a.sheet_export)
 root=Path(a.site_candidate);base_version=read(root/'data/latest.json')['dataset_version']
 d=prepare(m,read(root/'data'/base_version/'cards.json')['cards'],root,base_version)
 html=(root/'index.html').read_text(encoding='utf-8')
 html,n=re.subn(r"window\.DETAIL_VERSION='[^']*'","window.DETAIL_VERSION='"+d['meta']['detail_version']+"'",html)
 if n!=1:raise ValueError('Expected one detail version marker')
 (root/'index.html').write_text(html,encoding='utf-8')
 from scripts.check_site import check
 check(root)
 if a.master_snapshot:write(a.master_snapshot,m)
 print(json.dumps({'version':d['meta']['detail_version'],'cards':len(d['cards']),'items':d['coverage']['detail_item_count']},ensure_ascii=False))
