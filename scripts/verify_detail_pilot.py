"""Verify the four saved real-HTML inputs and compare the earlier cache pilot offline."""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.card_details import transform_run
from src.indexer import ROOT, read
from scripts.transform_detail_html import load_cards, save_candidate


def normalize(value):
    if isinstance(value,str):
        return re.sub(r'\s+','',value)
    if isinstance(value,list):
        return [normalize(x) for x in value]
    if isinstance(value,dict):
        return {k:normalize(v) for k,v in value.items()}
    return value


def compare_card(cached, actual):
    differences, gaps = [], []
    checked = 0
    def check(path, left, right):
        nonlocal checked
        checked += 1
        if normalize(left) != normalize(right):
            differences.append({'field':path,'cached_private':left,'html_private':right})

    check('panel_counts',dict(Counter(n['kind'] for n in cached['panel_nodes'])),
          dict(Counter(n['kind'] for n in actual['panel_nodes'])))
    # PukiWiki's > marker points at the end of a colspan; HTML points at its start.
    # Compare node order within SP tiers, then every fact, rather than equating coordinates.
    left_nodes=sorted(cached['panel_nodes'],key=lambda n:(n['sp'],n['panel_column']))
    right_nodes=sorted(actual['panel_nodes'],key=lambda n:(n['sp'],n['source_positions'][0]['column']))
    check('panel_sp_tier_counts',dict(Counter(n['sp'] for n in left_nodes)),
          dict(Counter(n['sp'] for n in right_nodes)))
    for i,(left,right) in enumerate(zip(left_nodes,right_nodes)):
        for field in ('sp','kind','name','effect_private','mechanics','unlock_star','cap_delta','energy_cost'):
            check(f'panel[{i}].{field}',left.get(field),right.get(field))
    if actual['card_kind']=='P':
        check('mb_count',len(cached['mb_live']),len(actual['mb_live']))
        for i,(left,right) in enumerate(zip(cached['mb_live'],actual['mb_live'])):
            for field in ('name','mb_stage','mb_total_stages','effect_private','mechanics'):
                check(f'mb[{i}].{field}',left[field],right[field])
        left_mem={n['level']:n for n in cached['memory_appeals']}
        right_mem={n['level']:n for n in actual['memory_appeals']}
        check('memory_levels',sorted(left_mem),sorted(right_mem))
        for level in left_mem.keys() & right_mem.keys():
            left,right=left_mem[level],right_mem[level]
            for field,index in (('name',0),('effect_private',1),('link_appeal_private',2),('charge_appeal_private',3)):
                expected,observed=left.get(field),right.get(field)
                positions=right['source_positions']
                # Cache markup uses ~ for a carried cell; prove inheritance in real HTML.
                if not expected and observed and index<len(positions) and positions[index]['row']<positions[1]['row']:
                    gaps.append({'level':level,'field':field,'html_source_position':positions[index]})
                else:
                    check(f'memory[{level}].{field}',expected,observed)
    else:
        for field in ('idea','inspiration','music_proficiencies'):
            check('traits.'+field,cached['traits'][field],actual['traits'][field])
        for field in ('level','limit_break','vocal','dance','visual','mental'):
            check('max_status.'+field,cached['max_status'][field],actual['max_status'][field])
        check('possessed_count',len(cached['possessed_live']),len(actual['possessed_live']))
        for i,(left,right) in enumerate(zip(cached['possessed_live'],actual['possessed_live'])):
            for field in ('name','effect_private','acquired_at_level','mechanics'):
                check(f'possessed[{i}].{field}',left[field],right[field])
        check('support_count',len(cached['support_skills']),len(actual['support_skills']))
        for i,(left,right) in enumerate(zip(cached['support_skills'],actual['support_skills'])):
            for field in ('name','effect_private'):
                check(f'support[{i}].{field}',left[field],right[field])
            projection=lambda entries:[{k:p[k] for k in ('support_level','skill_level')} for p in entries]
            check(f'support[{i}].progression',projection(left['progression']),projection(right['progression']))
    return {'card_id':actual['card_id'],'checked_fields':checked,
            'differences_private':differences,'cache_inheritance_gaps':gaps,
            'comparison_status':'matching_with_inheritance_gaps' if not differences else 'needs_review'}


def build(manifest_path, cached_path):
    manifest=read(manifest_path)
    by_id={c['card_id']:c for c in load_cards(ROOT,manifest['base_dataset_version'])}
    runs=manifest['runs']
    if len(runs)!=4 or len({r['card_id'] for r in runs})!=4:
        raise ValueError('Expected four distinct registered cards')
    cards=[]
    fetch_times=[]
    for run in runs:
        directory=(ROOT/'private/raw'/run['directory']).resolve()
        if not directory.is_relative_to((ROOT/'private/raw').resolve()):
            raise ValueError('Input outside private/raw')
        card=by_id[run['card_id']]
        if card['card_kind']!=run['card_kind']:
            raise ValueError('Input P/S mismatch')
        record=transform_run(directory,card,manifest['base_dataset_version'])['cards'][0]
        if record['source_sha256']!=run['sha256']:
            raise ValueError('Input manifest hash mismatch')
        cards.append(record)
        fetch_times.append(datetime.fromisoformat(record['fetched_at']))
    if Counter(c['card_kind'] for c in cards)!=Counter({'P':2,'S':2}):
        raise ValueError('Expected P2/S2')
    times=sorted(fetch_times)
    gaps=[(right-left).total_seconds() for left,right in zip(times,times[1:])]
    if min(gaps)<60:
        raise ValueError('Actual acquisition interval below 60 seconds')
    cached=read(cached_path)
    cached_by_id={c['card_id']:c for c in cached['cards']}
    comparisons=[compare_card(cached_by_id[card['card_id']],card) for card in cards]
    result={'pilot_schema':'0.3','base_dataset_version':manifest['base_dataset_version'],
            'input_kind':'saved_wiki_html','input_manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            'cards':cards,'coverage':{'scope':'P2/S2 real-HTML pilot','complete':False,'total':4,'P':2,'S':2,
                                    'unverified':['all-card structures','structured public effects','master adoption','detail Web release']},
            'audit':{'acquisition_intervals_seconds':gaps,'cache_content_hash':cached['content_hash'],
                     'comparisons':comparisons,'status':'extracted_not_adopted'}}
    stable=json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':'))
    result['content_hash']=hashlib.sha256(stable.encode()).hexdigest()
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest',type=Path,default=ROOT/'private/raw/detail-pilot-20261009/manifest.json')
    parser.add_argument('--cached',type=Path,default=ROOT/'private/audits/detail-sample-20261009-v2.json')
    parser.add_argument('--output',type=Path,default=ROOT/'private/audits/detail-pilot-html-20261009-v2.json')
    args=parser.parse_args()
    document=build(args.manifest,args.cached)
    save_candidate(document,args.output)
    print(json.dumps({'cards':len(document['cards']),'content_hash':document['content_hash'],
                      'checked_fields':sum(c['checked_fields'] for c in document['audit']['comparisons']),
                      'differences':sum(len(c['differences_private']) for c in document['audit']['comparisons']),
                      'cache_inheritance_gaps':sum(len(c['cache_inheritance_gaps']) for c in document['audit']['comparisons']),
                      'intervals_seconds':document['audit']['acquisition_intervals_seconds']},ensure_ascii=False))


if __name__=='__main__':
    main()
