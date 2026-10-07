"""Stage a minimal, verified Pages artifact without publishing it."""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.check_site import check
from src.indexer import read


def stage(source, target, previous=None):
    source=Path(source);target=Path(target);previous=Path(previous) if previous else None
    check(source)
    if previous:
        if previous.resolve()==source.resolve(): raise ValueError('previous release must be separate from source history')
        check(previous)
    latest=read(source/'data/latest.json')['dataset_version']
    if target.exists(): raise FileExistsError('stage in a fresh directory')
    resolved_target=target.resolve()
    if resolved_target.is_relative_to(source.resolve()) or (previous and resolved_target.is_relative_to(previous.resolve())):
        raise ValueError('target must be outside existing artifacts')
    target.mkdir(parents=True)
    for name in ['index.html','style.css','app.mjs','search.mjs']:
        shutil.copy2(source/name,target/name)
    if (source/'.nojekyll').exists(): shutil.copy2(source/'.nojekyll',target/'.nojekyll')
    data=target/'data';data.mkdir()
    if previous:
        for old in (previous/'data').iterdir():
            if old.is_dir(): shutil.copytree(old,data/old.name)
    if not (data/latest).exists(): shutil.copytree(source/'data'/latest,data/latest)
    shutil.copy2(source/'data/latest.json',data/'latest.json')
    check(target)
    return {'latest':latest,'versions':sorted(p.name for p in data.iterdir() if p.is_dir())}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('source');parser.add_argument('target')
    parser.add_argument('--previous-site')
    args=parser.parse_args()
    print(stage(args.source,args.target,args.previous_site))
