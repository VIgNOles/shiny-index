import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.indexer import read,verify_bundle
root=Path(sys.argv[1]);latest=read(root/'data/latest.json');v=latest['dataset_version']
assert v in (root/'index.html').read_text(encoding='utf-8')
for d in (root/'data').iterdir():
 if d.is_dir(): print(verify_bundle(d))
allowed={'index.html','style.css','app.mjs','search.mjs','data','.nojekyll'}
assert {p.name for p in root.iterdir()}<=allowed,'Unexpected files in site root'
