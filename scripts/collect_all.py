"""Sequential bounded fetch of the seven explicitly listed Wiki pages.

Acquisition stores raw responses only. It never adopts candidates or publishes.
"""
import argparse
import time
import uuid
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.indexer import collect,read,write,now
p=argparse.ArgumentParser();p.add_argument('directory');a=p.parse_args()
manifest=read('source_manifest.json')
if not manifest['full_collection_enabled']:raise SystemExit('Full local acquisition disabled by source_manifest.json')
pages=manifest['pages']+manifest['audit_pages']
if len(pages)>manifest['request_limit']:raise ValueError('request cap exceeded')
name={'W02':'p-list','W03':'s-list','W04':'s-volume','W07':'collab','W08':'road','W05':'chronology','W09':'gacha'}
base=Path(a.directory)
if base.exists():raise FileExistsError('Use a fresh run directory; old input is immutable')
base.mkdir(parents=True)
run={'run_id':str(uuid.uuid4()),'started_at':now(),'status':'incomplete','pages':[]}
write(base/'run.json',run)
try:
 for i,item in enumerate(pages):
  if i:time.sleep(manifest['interval_seconds'])
  path=base/name[item['id']]
  try:
   collect(item['url'],path)
   result=read(path/'fetch.json')
   if result['status']!='fetched':raise ValueError('fetch failed')
   run['pages'].append({'id':item['id'],'status':'fetched','sha256':result['sha256']})
   write(base/'run.json',run)
  except Exception as e:
   run['pages'].append({'id':item['id'],'status':'failed','error':str(e)})
   write(base/'run.json',run)
   raise
 run['status']='fetched'
finally:
 write(base/'run.json',run)
print('Saved seven pages. Run full_transform.py with RAW_RUN_ROOT set to this directory. No master was changed.')
