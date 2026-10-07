"""Review a validated acquisition batch against a master without adopting it."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.indexer import FIELDS, digest, key, load_master, read, write


def review(master, batch):
    if batch.get('status')!='validated' or not batch.get('cards'):
        raise ValueError('invalid/empty batch')
    aliases={alias:reg['card_id'] for reg in master['registry'] for alias in reg['aliases']}
    source={record['card_id']:record['values'] for record in master['source']}
    overrides={record['card_id']:record for record in master['overrides']}
    incoming={}
    for card in batch['cards']:
        source_key=key(card)
        if source_key in incoming: raise ValueError('duplicate incoming source')
        incoming[source_key]=card
    added=[];changed=[];unchanged=0;manual_matches=[]
    for source_key,card in incoming.items():
        card_id=aliases.get(source_key)
        if card_id is None:
            added.append(source_key)
            for reg in master['registry']:
                values=source.get(reg['card_id'],{})
                override=overrides.get(reg['card_id'],{}).get('values',{})
                if all((override.get(f) or values.get(f))==card.get(f) for f in ['idol_id','card_kind','variant_kind','card_title']):
                    manual_matches.append({'source_key':source_key,'possible_card_id':reg['card_id']})
            continue
        old=source.get(card_id,{})
        fields=[]
        for field in FIELDS:
            before=old.get(field);after=card.get(field)
            if before==after: continue
            override=overrides.get(card_id,{})
            fields.append({'field':field,'before':before,'after':after,'manual_override':field in override.get('values',{}) or field in override.get('clear_fields',[])})
        if fields:changed.append({'source_key':source_key,'card_id':card_id,'fields':fields})
        else:unchanged+=1
    missing=sorted(set(aliases)-set(incoming)) if batch.get('scope')=='full' else []
    count_delta=len(incoming)-len(aliases) if batch.get('scope')=='full' else None
    count_anomaly=bool(batch.get('scope')=='full' and aliases and (abs(count_delta)>=20 or abs(count_delta)/len(aliases)>=.05))
    return {'run_id':batch['run_id'],'batch_hash':digest(batch),'base_revision':master['revision'],'scope':batch.get('scope'),'observed_at':batch.get('observed_at'),'parser_version':batch.get('parser_version'),'counts':{'incoming':len(incoming),'existing_aliases':len(aliases),'new':len(added),'changed':len(changed),'unchanged':unchanged,'missing':len(missing)},'new_keys':sorted(added),'missing_keys':missing,'changed_rows':sorted(changed,key=lambda x:x['source_key']),'possible_manual_matches':manual_matches,'warnings':{'count_anomaly':count_anomaly,'missing_existing_keys':bool(missing),'manual_identity_matches':bool(manual_matches),'unknown_classifications':sum(c.get('acquisition_category')=='unknown' for c in batch['cards'])},'adopted':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('master');parser.add_argument('batch');parser.add_argument('output')
    args=parser.parse_args()
    report=review(load_master(args.master),read(args.batch))
    path=Path(args.output)
    if path.exists() and read(path)!=report: raise FileExistsError('review output exists with different content')
    if not path.exists():write(path,report)
    print(report['counts'],report['warnings'])
