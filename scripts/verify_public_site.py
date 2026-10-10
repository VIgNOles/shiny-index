"""Compare a deployed static site anonymously with every local release file."""
import argparse, hashlib, json, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote, urlsplit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.indexer import ROOT, write

def verify(site,base_url,output,*,expected_detail=None,workers=2):
 site=Path(site).resolve();output=Path(output)
 url=urlsplit(base_url)
 if url.scheme!='https' or not url.hostname or url.username or url.password or url.query or url.fragment:
  raise ValueError('Expected a public HTTPS site URL without credentials or query')
 if url.hostname=='wikiwiki.jp':raise ValueError('This verifies deployments, not Wiki pages')
 if not output.resolve().is_relative_to((ROOT/'private').resolve()):raise ValueError('Save verification evidence under private/')
 if not 1<=workers<=3:raise ValueError('Use at most three concurrent public file checks')
 base_url=base_url.rstrip('/')+'/'
 def request(path):
  return urllib.request.urlopen(urllib.request.Request(base_url+quote(path,safe='/'),
    headers={'User-Agent':'shiny-index-public-verification','Cache-Control':'no-cache'}),timeout=45)
 with request('details/latest.json') as response:
  pointer=json.load(response)
 if expected_detail and pointer.get('detail_version')!=expected_detail:
  raise ValueError('Deployment has not reached the expected detail version')
 local_pointer=json.loads((site/'details/latest.json').read_text(encoding='utf-8'))
 if pointer!=local_pointer:raise ValueError('Public and local detail pointers differ')
 paths=sorted(p for p in site.rglob('*') if p.is_file())
 if any(not p.resolve().is_relative_to(site) for p in paths):raise ValueError('File escapes site root')
 def one(path):
  rel=path.relative_to(site).as_posix()
  try:
   with request(rel) as response:
    remote=response.read();status=response.status
   local=path.read_bytes()
   return {'file':rel,'status':status,'bytes':len(remote),'sha256':hashlib.sha256(remote).hexdigest(),
           'bytes_equal':status==200 and remote==local}
  except Exception as error:return {'file':rel,'bytes_equal':False,'error':type(error).__name__+': '+str(error)}
 with ThreadPoolExecutor(max_workers=workers) as pool:rows=list(pool.map(one,paths))
 report={'base_url':base_url,'detail_version':pointer['detail_version'],'files':len(rows),
   'matching_files':sum(r['bytes_equal'] for r in rows),'anonymous':True,'workers':workers,'results':rows}
 write(output,report)
 if report['matching_files']!=len(rows):raise ValueError('Public file mismatch; see private verification evidence')
 return {k:v for k,v in report.items() if k!='results'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('site');p.add_argument('base_url');p.add_argument('output')
 p.add_argument('--expected-detail');p.add_argument('--workers',type=int,default=2);a=p.parse_args()
 print(json.dumps(verify(a.site,a.base_url,a.output,expected_detail=a.expected_detail,workers=a.workers),ensure_ascii=False))
