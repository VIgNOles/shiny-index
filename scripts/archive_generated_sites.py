"""Archive inactive generated sites, verifying every file before removal is allowed.
This command never deletes. See the generated manifest for original-path mappings.
"""
import hashlib,json,os,sys,zipfile,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 destination=Path(sys.argv[1]).resolve();destination.mkdir(parents=True,exist_ok=True)
 manifest=ROOT/'private/archive-generated-sites-20261011.json'
 if manifest.exists():raise SystemExit('Existing manifest; inspect before repeating')
 candidates=[]
 for parent in [ROOT/'private',ROOT/'private/audits']:
  for p in parent.iterdir():
   if p.is_dir() and (p/'index.html').is_file() and (p/'data/latest.json').is_file():candidates.append(p.resolve())
 for p in (ROOT/'private/recovery').glob('*/restored/site'):
  if (p/'index.html').is_file() and (p/'data/latest.json').is_file():candidates.append(p.resolve())
 protected={str(p):sha(p) for p in [ROOT/'private/master.xlsx',ROOT/'private/sheets-connection.json',ROOT/'private/details/master-r19-corrections-authoritative-20261011.json']}
 result={'archive_root':str(destination),'protected_sha256':protected,'directories':[],'complete':False,'deletion_performed':False}
 manifest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 for i,p in enumerate(sorted(set(candidates)),1):
  if not p.is_relative_to(ROOT/'private') or p.is_symlink() or p.is_junction():raise ValueError('Unsafe directory')
  files=[]
  for d,dirs,names in os.walk(p,followlinks=False):
   if any(Path(d,n).is_symlink() or Path(d,n).is_junction() for n in dirs):raise ValueError('Linked directory')
   for name in names:
    f=Path(d,name)
    if f.is_symlink():raise ValueError('Linked file')
    files.append(f)
  inventory=[{'path':f.relative_to(p).as_posix(),'bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted(files)]
  relative=p.relative_to(ROOT).as_posix()
  archive=destination/(relative.replace('/','__')+'.zip')
  if archive.exists():raise FileExistsError(archive)
  temp=archive.with_suffix('.partial.zip')
  if temp.exists():raise FileExistsError(temp)
  with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
   for f in sorted(files):z.write(f,f.relative_to(p).as_posix())
  with zipfile.ZipFile(temp) as z:
   if set(z.namelist())!={r['path'] for r in inventory}:raise ValueError('Archive file set')
   for row in inventory:
    h=hashlib.sha256()
    with z.open(row['path']) as f:
     for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    if h.hexdigest()!=row['sha256'] or z.getinfo(row['path']).file_size!=row['bytes']:raise ValueError('Archive byte mismatch')
  temp.replace(archive)
  result['directories'].append({'original':str(p),'relative':relative,'archive':str(archive),'archive_sha256':sha(archive),'verified':True,'files':inventory,'bytes':sum(r['bytes'] for r in inventory),'archive_bytes':archive.stat().st_size})
  manifest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
  print(json.dumps({'archived':i,'directory':relative,'original_mb':round(result['directories'][-1]['bytes']/1e6,1)},ensure_ascii=False),flush=True)
 for p,h in protected.items():
  if sha(Path(p))!=h:raise ValueError('Protected source changed')
 result['complete']=True
 result['bytes']=sum(r['bytes'] for r in result['directories']);result['archive_bytes']=sum(r['archive_bytes'] for r in result['directories'])
 manifest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 shutil.copy2(manifest,destination/'manifest.json')
 print(json.dumps({'complete':True,'directories':len(candidates),'original_bytes':result['bytes'],'archive_bytes':result['archive_bytes']},ensure_ascii=False))
if __name__=='__main__':main()
