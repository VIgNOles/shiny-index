import json
import copy,unittest
from src.detail_master import adopt,empty
from src.detail_public import public_document,validate_public
from tests.test_detail_master import candidate,CID,rehash

class DetailPublicTests(unittest.TestCase):
 def test_confirmed_status_and_override_survives_reacquisition_without_rewriting_source(self):
  c=candidate();raw='[条件:パッシブスキル発動率UP強化が付与されている場合] [確率:30%] [最大:1回]'
  c['cards'][0]['panel_nodes'][0].update(kind='panel_passive',effect_private=raw);rehash(c)
  m=adopt(empty(c['base_dataset_version']),c);base=[{'card_id':CID,'card_kind':'P'}]
  initial=public_document(m,base)['cards'][0]['items'][0]
  self.assertEqual(initial['activation_condition'],{'status':'unsupported'});self.assertNotIn('activation_condition_v2',initial)
  row=m['registry'][0];original=copy.deepcopy(row['source']);did=row['detail_id']
  row.update(override={'effect_private':raw.replace('パッシブスキル発動率UP強化が付与されている場合','パッシブスキル発動率UPが付与されている場合かつパッシブスキル強化が付与されている場合')},reason='ユーザーによるゲーム内確認: 両方必須',source_ref='test:game-confirmation',updated_at='2026-10-11T00:00:00+09:00')
  refreshed=adopt(m,c);self.assertEqual(refreshed['registry'][0],row)
  doc=public_document(refreshed,base);item=doc['cards'][0]['items'][0];p=item['activation_condition_v2']['expression']
  self.assertEqual(p,{'operator':'all','terms':[{'field':'status_count','operator':'gte','value':1,'status':'パッシブスキル発動率UP'},{'field':'status_count','operator':'gte','value':1,'status':'パッシブスキル強化'}]})
  self.assertEqual(item['detail_id'],did);self.assertEqual(row['source'],original)
  self.assertEqual(item['manual_source_ref'],'test:game-confirmation');self.assertNotIn('effect_private',item)
  self.assertEqual(doc['coverage']['activation_condition_current_counts'].get('unsupported',0),0)
  row['override']['effect_private']='[条件:パッシブスキル発動率UP又は強化が付与されている場合]'
  self.assertEqual(public_document(m,base)['cards'][0]['items'][0]['activation_condition_v2']['expression']['operator'],'any')

 def test_keyword_export_keeps_old_ui_unsupported_and_uses_resolved_override(self):
  c=candidate();c['cards'][0]['panel_nodes'][0].update(kind='panel_passive',effect_private='[条件:キーワードアイドル]');rehash(c)
  m=adopt(empty(c['base_dataset_version']),c);base=[{'card_id':CID,'card_kind':'P'}];d=public_document(m,base);i=d['cards'][0]['items'][0]
  self.assertEqual(i['activation_condition'],{'status':'unsupported'});self.assertNotIn('activation_condition_v2',i)
  self.assertEqual(i['activation_condition_v3']['expression']['value'],'アイドル')
  self.assertEqual(d['coverage']['activation_condition_search_counts'],{'unsupported':1});self.assertEqual(d['coverage']['activation_condition_current_counts'],{'structured':1})
  for mutate in [lambda x:x['coverage'].pop('activation_condition_current_counts'),lambda x:x['coverage']['activation_condition_current_counts'].update(structured=4),lambda x:x['cards'][0]['items'][0]['activation_condition_v3']['expression'].update(raw_private='本文'),lambda x:x['cards'][0]['items'][0].update(kind='panel_live'),lambda x:x['cards'][0]['items'][0].update(activation_condition_v2={'status':'structured','expression':{'field':'turn','operator':'gte','value':3}})]:
   bad=copy.deepcopy(d);mutate(bad)
   with self.assertRaises(ValueError):validate_public(bad,base)
  source=copy.deepcopy(m['registry'][0]['source'])
  m['registry'][0].update(override={'effect_private':'[条件:キーワードリーダーシップ、カリスマ]'},reason='条件訂正',source_ref='test:source',updated_at='2026-10-11T00:00:00+00:00')
  p=public_document(m,base)['cards'][0]['items'][0]['activation_condition_v3']['expression']
  self.assertEqual(p['operator'],'all');self.assertEqual(source,m['registry'][0]['source'])

 def test_passive_activation_conditions_use_resolved_overrides_and_keep_prose_private(self):
  c=candidate();c['cards'][0]['panel_nodes'][0].update(kind='panel_passive',effect_private='[条件:メンタル75%以上] [確率:20%]')
  rehash(c);m=adopt(empty(c['base_dataset_version']),c);base=[{'card_id':CID,'card_kind':'P'}]
  d=public_document(m,base);item=d['cards'][0]['items'][0]
  self.assertEqual(item['activation_condition']['expression']['value'],75)
  self.assertEqual(d['coverage']['activation_condition_counts'],{'structured':1})
  self.assertTrue(item['conditions_not_structured'])
  self.assertNotIn('effect_private',item)
  row=m['registry'][0];original=copy.deepcopy(row['source'])
  row.update(override={'effect_private':'[条件:3ターン以前]'},reason='条件訂正',source_ref='test:source',updated_at='2026-10-10T00:00:00+00:00')
  corrected=public_document(m,base)['cards'][0]['items'][0]
  self.assertEqual(corrected['activation_condition']['expression'],{'field':'turn','operator':'lte','value':3})
  self.assertEqual(row['source'],original)
  row['override']['effect_private']='[条件:未知条件]'
  d=public_document(m,base)
  self.assertEqual(d['cards'][0]['items'][0]['activation_condition'],{'status':'unsupported'})
  self.assertEqual(d['coverage']['activation_condition_counts'],{'unsupported':1})
 def test_activation_condition_tampering_and_cross_kind_are_rejected(self):
  c=candidate();c['cards'][0]['panel_nodes'][0].update(kind='panel_passive',effect_private='[条件:メンタル75%以上]')
  rehash(c);m=adopt(empty(c['base_dataset_version']),c);base=[{'card_id':CID,'card_kind':'P'}]
  d=public_document(m,base)
  for mutate,message in [(lambda x:x['cards'][0]['items'][0]['activation_condition'].update(raw_private='全文'),'activation condition'),
                         (lambda x:x['cards'][0]['items'][0].update(kind='panel_live'),'non-passive'),
                         (lambda x:x['coverage']['activation_condition_counts'].update(structured=99),'condition count')]:
   bad=copy.deepcopy(d);mutate(bad)
   with self.assertRaisesRegex(ValueError,message):validate_public(bad,base)


 def test_extended_conditions_preserve_legacy_export_and_resolved_override(self):
  c=candidate();c['cards'][0]['panel_nodes'][0].update(kind='panel_passive',effect_private='[条件:メンタル35%以上64%以下]');rehash(c)
  m=adopt(empty(c['base_dataset_version']),c);base=[{'card_id':CID,'card_kind':'P'}]
  d=public_document(m,base);i=d['cards'][0]['items'][0]
  self.assertEqual(i['activation_condition'],{'status':'unsupported'})
  self.assertEqual(i['activation_condition_v2']['expression']['operator'],'all')
  self.assertEqual(d['coverage']['activation_condition_counts'],{'unsupported':1})
  self.assertEqual(d['coverage']['activation_condition_search_counts'],{'structured':1})
  row=m['registry'][0];source=copy.deepcopy(row['source'])
  row.update(override={'effect_private':'[条件:メンタル75%以上又は3ターン以前]'},reason='条件訂正',source_ref='test:source',updated_at='2026-10-11T00:00:00+00:00')
  changed=public_document(m,base)['cards'][0]['items'][0]
  self.assertEqual(changed['activation_condition_v2']['expression']['operator'],'any')
  self.assertEqual(source,row['source'])
 def test_condition_extension_tampering_and_effective_count_are_rejected(self):
  c=candidate();c['cards'][0]['panel_nodes'][0].update(kind='panel_passive',effect_private='[条件:メンタル35%以上64%以下]');rehash(c)
  m=adopt(empty(c['base_dataset_version']),c);base=[{'card_id':CID,'card_kind':'P'}];d=public_document(m,base)
  for mutate in [
   lambda x:x['cards'][0]['items'][0]['activation_condition_v2']['expression'].update(raw_private='全文'),
   lambda x:x['cards'][0]['items'][0].update(kind='panel_live'),
   lambda x:x['coverage']['activation_condition_search_counts'].update(structured=9),
   lambda x:x['coverage'].pop('activation_condition_search_counts'),
   lambda x:x['cards'][0]['items'][0].update(activation_condition={'status':'structured','expression':{'field':'turn','operator':'gte','value':3}}),
  ]:
   bad=copy.deepcopy(d);mutate(bad)
   with self.assertRaises(ValueError):validate_public(bad,base)

 def test_acquisition_and_held_gaps_are_not_conflated_with_effect_structure(self):
  c=candidate();m=adopt(empty(c['base_dataset_version']),c);bases=[{'card_id':CID,'card_kind':'P'}]
  d=public_document(m,bases)
  self.assertNotIn('Full detail acquisition',d['coverage']['unverified'])
  self.assertIn('Complete effect/condition structure',d['coverage']['unverified'])
  self.assertFalse(d['coverage']['complete'])
  held='00000000-0000-4000-8000-000000000002';bases.append({'card_id':held,'card_kind':'S'})
  m['coverage'].append({'card_id':held,'card_kind':'S','status':'missing_page_on_hold'})
  d=public_document(m,bases)
  self.assertNotIn('Full detail acquisition',d['coverage']['unverified'])
  self.assertIn('Unlinked pages on hold',d['coverage']['unverified'])
  m['coverage'][-1]['status']='input_pending';d=public_document(m,bases)
  self.assertIn('Full detail acquisition',d['coverage']['unverified'])
  self.assertNotIn('Unlinked pages on hold',d['coverage']['unverified'])

 def test_shared_normal_mb_origin_kinds_are_public_and_validated(self):
  c=candidate();c['cards'][0]['generated_live']=[{'kind':'generated_live','name':'child','sp':None,'generation_stage':1,
    'generated_from_name':'スキル','generated_from_names':['スキル','[MB]スキル(2/5)'],
    'generation_origin_kind':'panel_live','generation_origin_kinds':['panel_live','mb_live'],
    'effect_private':'Vocal5倍(Plus)','mechanics':['plus'],'mb_shared_target_private':True}];rehash(c)
  m=adopt(empty(c['base_dataset_version']),c);d=public_document(m,[{'card_id':CID,'card_kind':'P'}]);child=d['cards'][0]['items'][1]
  self.assertEqual(child['generation_origin_kinds'],['panel_live','mb_live'])
  self.assertNotIn('mb_shared_target_private',child)
  for bad in [[],['panel_live'],['mb_live','panel_live'],['panel_live','possessed_live'],'panel_live']:
   broken=copy.deepcopy(d);broken['cards'][0]['items'][1]['generation_origin_kinds']=bad
   with self.subTest(bad=bad),self.assertRaisesRegex(ValueError,'origin kinds'):validate_public(broken,[{'card_id':CID,'card_kind':'P'}])

 def test_new_bundle_hash_and_existing_pretty_bundle_bytes_are_preserved(self):
  import json,hashlib,tempfile
  from pathlib import Path
  from src.detail_public import prepare
  from unittest.mock import patch
  c=candidate();m=adopt(empty(c['base_dataset_version']),c);base=[{'card_id':CID,'card_kind':'P'}]
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);first=prepare(m,base,root);bundle=root/'details'/first['meta']['detail_version']
   path=bundle/'details.json';manifest=bundle/'manifest.json'
   self.assertEqual(json.loads(path.read_bytes()),first)
   self.assertEqual(json.loads(manifest.read_bytes())['files']['details.json'],hashlib.sha256(path.read_bytes()).hexdigest())
   # Simulate a valid immutable bundle emitted by the previous pretty writer.
   path.write_bytes((json.dumps(first,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
   meta=json.loads(manifest.read_bytes());meta['files']['details.json']=hashlib.sha256(path.read_bytes()).hexdigest()
   manifest.write_bytes(json.dumps(meta,ensure_ascii=False,indent=2).encode('utf-8'))
   saved={p.name:p.read_bytes() for p in bundle.iterdir()}
   with patch('src.detail_public.now',return_value='2026-10-10T20:00:00+00:00'):
    self.assertEqual(prepare(m,base,root),first)
   c['cards'][0]['panel_nodes'][0]['effect_private']='Vocal3倍アピール';rehash(c)
   second=prepare(adopt(m,c),base,root)
   self.assertNotEqual(first['meta']['detail_version'],second['meta']['detail_version'])
   self.assertEqual(saved,{p.name:p.read_bytes() for p in bundle.iterdir()})
   self.assertEqual(json.loads((root/'details'/second['meta']['detail_version']/'details.json').read_bytes()),second)

 def build(self):
  c=candidate();m=adopt(empty(c['base_dataset_version']),c)
  return public_document(m,[{'card_id':CID,'card_kind':'P'}])
 def test_private_prose_removed_and_provenance_kept(self):
  d=self.build();item=d['cards'][0]['items'][0]
  self.assertNotIn('effect_private',item)
  self.assertEqual(item['numeric_facts'][0]['value'],2)
  self.assertEqual(d['cards'][0]['source_sha256'],'a'*64)
  self.assertFalse(d['coverage']['complete'])
 def test_generated_live_relation_is_public_without_effect_prose(self):
  c=candidate();c['cards'][0]['generated_live']=[{'kind':'generated_live','name':'生成甲','sp':None,
   'generation_stage':1,'generated_from_name':'スキル','effect_private':'非公開説明 Vocal7倍(change)','mechanics':['change']}];rehash(c)
  m=adopt(empty(c['base_dataset_version']),c);d=public_document(m,[{'card_id':CID,'card_kind':'P'}]);item=d['cards'][0]['items'][1]
  self.assertEqual(item['kind'],'generated_live');self.assertEqual(item['generated_from_name'],'スキル')
  self.assertEqual(item['generation_stage'],1);self.assertNotIn('effect_private',item)
  c['cards'][0]['generated_live'][0]['sp']=40;rehash(c)
  with self.assertRaisesRegex(ValueError,'generated-live'):adopt(empty(c['base_dataset_version']),c)
 def test_shared_generated_parents_are_public_and_invalid_shapes_rejected(self):
  c=candidate();c['cards'][0]['generated_live']=[{'kind':'generated_live','name':'child','sp':None,'generation_stage':1,
    'generated_from_name':'スキル','generated_from_names':['スキル','スキル+'],'effect_private':'非公開本文','mechanics':[]}];rehash(c)
  d=public_document(adopt(empty(c['base_dataset_version']),c),[{'card_id':CID,'card_kind':'P'}])
  item=d['cards'][0]['items'][1];self.assertEqual(item['generated_from_names'],['スキル','スキル+'])
  self.assertNotIn('effect_private',item)
  for bad in [[],['スキル'],['wrong','スキル+'],['スキル','ス キ ル'],['スキル',{}],'スキル']:
   broken=copy.deepcopy(d);broken['cards'][0]['items'][1]['generated_from_names']=bad
   with self.subTest(bad=bad),self.assertRaisesRegex(ValueError,'parent names'):
    validate_public(broken,[{'card_id':CID,'card_kind':'P'}])
  broken=copy.deepcopy(d);broken['cards'][0]['items'][1]['kind']='panel_live'
  with self.assertRaisesRegex(ValueError,'parent names'):validate_public(broken,[{'card_id':CID,'card_kind':'P'}])
 def test_random_options_allow_only_structured_facts(self):
  c=candidate();item=c['cards'][0]['panel_nodes'][0]
  item['random_effect_options']=[{'metric':'rate','target':'Vocal','value':50,'unit':'percent','direction':'UP','turns':3}];rehash(c)
  m=adopt(empty(c['base_dataset_version']),c);d=public_document(m,[{'card_id':CID,'card_kind':'P'}])
  self.assertEqual(d['cards'][0]['items'][0]['random_effect_options'][0]['turns'],3)
  d['cards'][0]['items'][0]['random_effect_options'][0]['prose']='非公開全文'
  with self.assertRaisesRegex(ValueError,'random-effect option'):validate_public(d,[{'card_id':CID,'card_kind':'P'}])
 def memory_document(self,link='Dance3倍アピール',charge='Visual4倍アピール'):
  c=candidate();c['cards'][0]['memory_appeals']=[{'kind':'memory_appeal','name':'思い出','level':1,'effect_private':'思い出アピール[Lv1] / Vocal2倍アピール','link_appeal_private':link,'charge_appeal_private':charge}];rehash(c)
  return public_document(adopt(empty(c['base_dataset_version']),c),[{'card_id':CID,'card_kind':'P'}])
 def test_memory_link_and_charge_are_separate_without_prose(self):
  d=self.memory_document();item=next(i for i in d['cards'][0]['items'] if i['kind']=='memory_appeal')
  self.assertEqual(item['numeric_facts'][0]['targets'],['Vocal'])
  self.assertEqual(item['memory_link_facts'][0]['targets'],['Dance'])
  self.assertEqual(item['memory_charge_facts'][0]['targets'],['Visual'])
  self.assertTrue(item['memory_link_present']);self.assertTrue(item['memory_charge_present'])
  self.assertNotIn('link_appeal_private',item);self.assertNotIn('charge_appeal_private',item)
 def test_maximum_memory_appeal_is_not_a_fixed_multiplier(self):
  d=self.memory_document(link='全観客にDance最大3.5倍アピール [回復回数増加で効果UP]')
  item=next(i for i in d['cards'][0]['items'] if i['kind']=='memory_appeal')
  self.assertEqual(item['memory_link_facts'][0]['metric'],'appeal_maximum')
  self.assertEqual(item['memory_link_facts'][0]['value'],3.5)
  self.assertTrue(item['conditions_not_structured'])
 def test_memory_range_remains_a_range_and_rejects_invalid_bounds(self):
  d=self.memory_document(link='全観客にVocal0.4～2倍アピール[消去:VocalUP]');item=next(i for i in d['cards'][0]['items'] if i['kind']=='memory_appeal')
  self.assertEqual(item['memory_link_facts'],[{'metric':'appeal_range','targets':['Vocal'],'minimum':0.4,'maximum':2.0,'unit':'multiplier'}])
  item['memory_link_facts'][0]['minimum']=3
  with self.assertRaisesRegex(ValueError,'memory numeric range'):validate_public(d,[{'card_id':CID,'card_kind':'P'}])
 def test_memory_absent_and_unstructured_effects_are_distinct(self):
  d=self.memory_document(link='任意の未対応説明',charge=None);item=next(i for i in d['cards'][0]['items'] if i['kind']=='memory_appeal')
  self.assertTrue(item['memory_link_present']);self.assertEqual(item['memory_link_facts'],[])
  self.assertFalse(item['memory_charge_present']);self.assertEqual(item['memory_charge_facts'],[])
  d=self.memory_document(link='メンタルダメージ50%CUT[1ターン]');item=next(i for i in d['cards'][0]['items'] if i['kind']=='memory_appeal')
  self.assertEqual(item['memory_link_facts'][0]['target'],'メンタルダメージ')
 def test_memory_slot_rejects_nested_prose_and_wrong_kind(self):
  d=self.memory_document();item=next(i for i in d['cards'][0]['items'] if i['kind']=='memory_appeal')
  item['memory_link_facts'][0]['prose']='非公開全文'
  with self.assertRaisesRegex(ValueError,'memory numeric fact'):validate_public(d,[{'card_id':CID,'card_kind':'P'}])
  d=self.memory_document();item=next(i for i in d['cards'][0]['items'] if i['kind']=='memory_appeal');item['kind']='panel_live'
  with self.assertRaisesRegex(ValueError,'memory effect slots'):validate_public(d,[{'card_id':CID,'card_kind':'P'}])
 def test_count_anomaly_rejected(self):
  d=self.build();d['coverage']['detail_item_count']=999
  with self.assertRaisesRegex(ValueError,'Count anomaly'):validate_public(d,[{'card_id':CID,'card_kind':'P'}])
 def test_private_field_injected_rejected(self):
  d=self.build();d['cards'][0]['items'][0]['effect_private']='秘密の全文'
  with self.assertRaisesRegex(ValueError,'Non-public'):validate_public(d,[{'card_id':CID,'card_kind':'P'}])
 def test_nested_private_field_rejected(self):
  d=self.build();d['cards'][0]['coverage']['effect_private']='非公開本文'
  with self.assertRaisesRegex(ValueError,'Non-public coverage'):validate_public(d,[{'card_id':CID,'card_kind':'P'}])
 def test_public_content_tamper_rejected(self):
  d=self.build();d['cards'][0]['items'][0]['name']='変更'
  with self.assertRaisesRegex(ValueError,'version mismatch'):validate_public(d,[{'card_id':CID,'card_kind':'P'}])
 def test_coverage_cannot_silently_drop_missing_card(self):
  c=candidate();m=adopt(empty(c['base_dataset_version']),c)
  with self.assertRaisesRegex(ValueError,'Missing base coverage'):public_document(m,[{'card_id':CID,'card_kind':'P'},{'card_id':'00000000-0000-4000-8000-000000000002','card_kind':'S'}])
 def test_new_base_card_gets_explicit_uncollected_coverage(self):
  c=candidate();m=adopt(empty(c['base_dataset_version']),c)
  bases=[{'card_id':CID,'card_kind':'P'},{'card_id':'00000000-0000-4000-8000-000000000002','card_kind':'S'}]
  d=public_document(m,bases,'v1-ffffffffffffffff')
  self.assertEqual(d['coverage']['base_card_count'],2)
  self.assertEqual(d['coverage']['status_counts']['not_in_acquisition_catalog'],1)
  self.assertEqual(d['meta']['source_base_dataset_version'],c['base_dataset_version'])
 def test_ps_mismatch_rejected(self):
  c=candidate();m=adopt(empty(c['base_dataset_version']),c)
  with self.assertRaisesRegex(ValueError,'mixed P/S'):public_document(m,[{'card_id':CID,'card_kind':'S'}])

 def test_effect_facts_use_manual_values_without_rewriting_source(self):
  c=candidate();c['cards'][0]['panel_nodes'][0].update(kind='panel_live',effect_private='Vocal20%UP[3ターン]')
  rehash(c);m=adopt(empty(c['base_dataset_version']),c);base=[{'card_id':CID,'card_kind':'P'}]
  row=m['registry'][0];before=copy.deepcopy(row['source']);row.update(override={'effect_private':'Dance30%UP[5ターン]'},reason='確認済み',source_ref='test:manual',updated_at='2026-10-11T00:00:00+09:00')
  d=public_document(m,base);e=d['cards'][0]['items'][0]['effect_details']['effects'][0]
  self.assertEqual((e['targets'],e['value'],e['turns']),(['Dance'],30,5));self.assertEqual(row['source'],before)
  self.assertNotIn('effect_private',json.dumps(d,ensure_ascii=False));self.assertEqual(d['coverage']['effect_detail_counts'],{'panel_live':{'partial':1}})
  for mutation in [lambda x:x['coverage'].pop('effect_detail_counts'),lambda x:x['coverage']['effect_detail_counts']['panel_live'].update(partial=2),lambda x:x['cards'][0]['items'][0]['effect_details']['effects'][0].update(raw_private='本文')]:
   bad=copy.deepcopy(d);mutation(bad)
   with self.assertRaises(ValueError):validate_public(bad,base)


 def test_live_rule_export_preserves_legacy_fields_and_rejects_private_rule_text(self):
  c=candidate();c['cards'][0]['panel_nodes'][0].update(kind='panel_live',effect_private='Vocal4倍アピール(Grow)[DanceUPを付与]Dance最大3倍アピール')
  rehash(c);m=adopt(empty(c['base_dataset_version']),c);base=[{'card_id':CID,'card_kind':'P'}]
  source=copy.deepcopy(m['registry'][0]['source']);d=public_document(m,base)
  es=d['cards'][0]['items'][0]['effect_details']['effects']
  self.assertNotIn('mechanic_condition',es[0]);self.assertEqual(es[1]['activation_condition'],{'status':'unsupported'})
  self.assertEqual(es[1]['mechanic_condition']['expression']['field'],'status_granted')
  self.assertEqual(m['registry'][0]['source'],source);self.assertNotIn('effect_private',json.dumps(d))
  for patch in [{'raw_text':'本文'},{'carry_over':False},{'role':'activation'}]:
   bad=copy.deepcopy(d);bad['cards'][0]['items'][0]['effect_details']['effects'][1]['mechanic_condition'].update(patch)
   with self.assertRaises(ValueError):validate_public(bad,base)

if __name__=='__main__':unittest.main()
