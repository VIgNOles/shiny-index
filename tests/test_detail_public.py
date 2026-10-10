import copy,unittest
from src.detail_master import adopt,empty
from src.detail_public import public_document,validate_public
from tests.test_detail_master import candidate,CID,rehash

class DetailPublicTests(unittest.TestCase):
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

if __name__=='__main__':unittest.main()
