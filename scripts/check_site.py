"""Verify the exact static artifact tree before any public deployment."""
import re
import sys
from collections import defaultdict
from urllib.parse import urlsplit, unquote
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.indexer import read, verify_bundle


def check_provenance(bundle):
    doc=read(bundle/'cards.json')
    cards=doc['cards']
    by_id=defaultdict(list)
    ids={card['card_id'] for card in cards}
    for row in doc['sources']:
        if row['card_id'] not in ids: raise ValueError('orphan source evidence')
        url=row.get('url')
        if url:
            parsed=urlsplit(url)
            if parsed.scheme!='https' or parsed.netloc!='wikiwiki.jp' or not unquote(parsed.path).startswith('/shinycolors/'):
                raise ValueError('unsafe source evidence URL')
        by_id[row['card_id']].append(row)
    for card in cards:
        evidence=by_id[card['card_id']]
        if not evidence or not card['source_refs']:
            raise ValueError('card missing provenance')
        if set(card['source_refs'])-{row['source_ref'] for row in evidence}:
            raise ValueError('card source reference missing evidence')
        for field in ('card_kind','card_title','idol_name'):
            if not any(row['field_name']==field and row['value']==card[field] for row in evidence):
                raise ValueError('card core field lacks matching evidence')
        if card['review_status']=='wiki_only' and not any(row.get('url') for row in evidence):
            raise ValueError('wiki-only card lacks linked source')


def check(root):
    root=Path(root)
    if not root.is_dir() or root.is_symlink(): raise ValueError('site root is missing or a symlink')
    if any(p.is_symlink() for p in root.rglob('*')): raise ValueError('symlink in site')
    required={'index.html','style.css','app.mjs','search.mjs','data'}
    present={p.name for p in root.iterdir()}
    if not required<=present or present-required-{'.nojekyll'}: raise ValueError('missing or unexpected site root file')
    data=root/'data'
    if not data.is_dir(): raise ValueError('data directory missing')
    entries=list(data.iterdir())
    versions={p.name for p in entries if p.is_dir()}
    if not versions or {p.name for p in entries}!={'latest.json'}|versions or any(not re.fullmatch(r'v1-[0-9a-f]{16}',v) for v in versions):
        raise ValueError('unexpected data entry')
    latest=read(data/'latest.json')
    version=latest.get('dataset_version')
    if set(latest)!={'dataset_version','manifest'} or version not in versions or latest['manifest']!=version+'/manifest.json':
        raise ValueError('invalid latest pointer')
    html=(root/'index.html').read_text(encoding='utf-8')
    match=re.findall(r"window\.DATA_VERSION='(v1-[0-9a-f]{16})'",html)
    if match!=[version] or '__VERSION__' in html: raise ValueError('HTML version mismatch')
    results=[]
    for name in sorted(versions):
        result=verify_bundle(data/name)
        check_provenance(data/name)
        if result['version']!=name: raise ValueError('bundle directory version mismatch')
        results.append(result)
    return results


if __name__=='__main__':
    for result in check(sys.argv[1]): print(result)
