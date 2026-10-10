"""Offline effect audit: compare derived facts without mutating the canonical master."""
import argparse, collections, hashlib, json, re, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.detail_master import resolve
from src.detail_public import public_document
from src.indexer import ROOT, read, write

def audit(master_path, site_path, output, root=ROOT, baseline_version=None):
 root=Path(root);site=Path(site_path);output=Path(output)
 if not output.resolve().is_relative_to((root/'private').resolve()):
  raise ValueError('Audit evidence with source text must remain private')
 master=read(master_path);pointer=read(site/'details/latest.json')
 if baseline_version:
  if not re.fullmatch(r'd1-[0-9a-f]{16}',baseline_version):raise ValueError('Invalid baseline detail version')
  pointer={**pointer,'detail_version':baseline_version}
 old=read(site/'details'/pointer['detail_version']/'details.json')
 base=read(site/'data/latest.json')['dataset_version']
 new=public_document(master,read(site/'data'/base/'cards.json')['cards'],base)
 def without_effects(doc):
  return [{**{k:v for k,v in c.items() if k!='items'},
           'items':[{k:v for k,v in i.items() if k!='effect_details'} for i in c['items']]} for c in doc['cards']]
 if without_effects(old)!=without_effects(new):raise ValueError('Existing card, ID, manual value or field changed')
 if {k:v for k,v in old['coverage'].items() if k!='effect_detail_counts'}!={k:v for k,v in new['coverage'].items() if k!='effect_detail_counts'}:
  raise ValueError('Existing coverage changed')
 source={i['detail_id']:(c,i) for c in resolve(master) for i in c['items']}
 old_items={i['detail_id']:i for c in old['cards'] for i in c['items']}
 facts=collections.Counter();conditions=collections.Counter();scaling=collections.Counter();changed=[];lost=[];scope_corrections=[];condition_updates=[]
 current_conditions=collections.Counter();mechanic_rules=collections.Counter();standalone_rules=collections.Counter()
 for c in new['cards']:
  for i in c['items']:
   es=i.get('effect_details',{}).get('effects',[])
   facts.update(e['metric'] for e in es)
   conditions.update(e['activation_condition']['status'] for e in es if 'activation_condition' in e)
   current_conditions.update((e.get('mechanic_condition') or e['activation_condition'])['status'] for e in es if 'activation_condition' in e or 'mechanic_condition' in e)
   mechanic_rules.update(e['mechanic_condition']['role'] for e in es if 'mechanic_condition' in e)
   standalone_rules.update(r['condition']['role'] for r in i.get('effect_details',{}).get('mechanic_conditions',[]))
   scaling.update(e['restrictions']['scaling'] for e in es if 'scaling' in e.get('restrictions',{}))
   prior=old_items[i['detail_id']].get('effect_details',{})
   if prior!=i.get('effect_details',{}):
    sc,si=source[i['detail_id']]
    changed.append({'card_id':c['card_id'],'detail_id':i['detail_id'],'kind':i['kind'],
      'wiki_url':c['wiki_url'],'source_sha256':c['source_sha256'],'source_positions':i['source_positions'],
      'private_text':{k:si[k] for k in ('effect_private','link_appeal_private','charge_appeal_private') if si.get(k)},
      'before':prior,'after':i.get('effect_details')})
   for e in prior.get('effects',[]):
    if not any(all(other.get(k)==v for k,v in e.items()) for other in es):
     moved=[other for other in es if all(other.get(k)==v for k,v in e.items() if k!='scope')]
     if moved and e['scope']=='base':
      scope_corrections.append({'detail_id':i['detail_id'],'old_scope':e['scope'],'new_scopes':[other['scope'] for other in moved],'old_effect':e})
     else:
      revised=[other for other in es if all(other.get(k)==v for k,v in e.items() if k!='activation_condition')]
      before=e.get('activation_condition',{})
      compatible=[]
      for other in revised:
       after=other.get('activation_condition',{})
       a,b=before.get('expression',{}),after.get('expression',{})
       if before=={'status':'unsupported'} and after.get('status')=='structured':
        compatible.append(other)
       elif e['scope'] in {'link','memory_link'} and a.get('field')=='participant' and b=={**a,'field':'history_participant'}:
        compatible.append(other)
      if compatible:condition_updates.append({'detail_id':i['detail_id'],'scope':e['scope'],'before':before,'after':[other.get('activation_condition') for other in compatible]})
      else:lost.append({'detail_id':i['detail_id'],'old_effect':e})
 report={'base':base,'before':old['meta']['detail_version'],'after':new['meta']['detail_version'],
  'canonical_revision':master['revision'],'cards':len(new['cards']),'items':new['coverage']['detail_item_count'],
  'existing_cards_ids_values_and_coverage_equal':True,
  'master_file_sha256':hashlib.sha256(Path(master_path).read_bytes()).hexdigest(),
  'override_count':sum(bool(r.get('override')) for r in master['registry']),
  'effect_fact_counts':dict(facts),'effect_condition_counts':dict(conditions),'effect_condition_current_counts':dict(current_conditions),'effect_mechanic_rule_counts':dict(mechanic_rules),'standalone_mechanic_rule_counts':dict(standalone_rules),'scaling_counts':dict(scaling),
  'effect_item_status_counts':new['coverage']['effect_detail_counts'],
  'changed_items':len(changed),'old_effect_scope_corrections':scope_corrections,'condition_updates':condition_updates,'old_effects_not_preserved':lost,'changed':changed,'wiki_requests':0}
 if lost:raise ValueError('Previously derived effect lost; review before publication')
 write(output,report)
 return {k:v for k,v in report.items() if k not in {'changed','old_effect_scope_corrections','condition_updates'}}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('master');p.add_argument('site');p.add_argument('output');p.add_argument('--baseline-version');a=p.parse_args()
 print(json.dumps(audit(a.master,a.site,a.output,baseline_version=a.baseline_version),ensure_ascii=False,indent=2))
