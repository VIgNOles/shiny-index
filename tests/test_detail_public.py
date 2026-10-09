import copy,unittest
from src.detail_master import adopt,empty
from src.detail_public import public_document,validate_public
from tests.test_detail_master import candidate,CID,rehash

class DetailPublicTests(unittest.TestCase):
 def build(self):
  c=candidate();m=adopt(empty(c['base_dataset_version']),c)
  return public_document(m,[{'card_id':CID,'card_kind':'P'}])
 def test_private_prose_removed_and_provenance_kept(self):
  d=self.build();item=d['cards'][0]['items'][0]
  self.assertNotIn('effect_private',item)
  self.assertEqual(item['numeric_facts'][0]['value'],2)
  self.assertEqual(d['cards'][0]['source_sha256'],'a'*64)
  self.assertFalse(d['coverage']['complete'])
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
