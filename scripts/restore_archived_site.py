"""Restore one archived generated site into a new project directory."""
import argparse,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def restore(manifest,relative,output):
 doc=json.loads(Path(manifest).read_text(encoding='utf-8-sig'))
 rows=[r for r in doc['directories'] if r['relative']==relative]
 if len(rows)!=1 or not rows[0]['verified']:raise ValueError('Unknown or unverified archive')
 row=rows[0];archive=Path(row['archive']);out=Path(output).resolve()
 if out.exists() or not out.is_relative_to(ROOT/'private'):raise ValueError('Restore to a fresh private project directory')
 if hashlib.sha256(archive.read_bytes()).hexdigest()!=row['archive_sha256']:raise ValueError('Archive changed')
 with zipfile.ZipFile(archive) as z:
  if set(z.namelist())!={r['path'] for r in row['files']}:raise ValueError('Archive file set mismatch')
  for f in row['files']:
   target=(out/f['path']).resolve()
   if not target.is_relative_to(out):raise ValueError('Unsafe archive path')
   data=z.read(f['path'])
   if len(data)!=f['bytes'] or hashlib.sha256(data).hexdigest()!=f['sha256']:raise ValueError('Archive file bytes mismatch')
  for f in row['files']:
   target=out/f['path'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(f['path']))
 return {'original':relative,'restored':str(out),'files':len(row['files'])}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('relative');p.add_argument('output');p.add_argument('--manifest',default='private/archive-generated-sites-20261011.json');a=p.parse_args()
 print(json.dumps(restore(a.manifest,a.relative,a.output),ensure_ascii=False))
