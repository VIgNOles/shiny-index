import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from scripts.recovery_drill import check_pair
from src.indexer import digest

class RecoveryPairTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.site=self.root/'site';self.master=self.root/'master.xlsx';self.connection=self.root/'connection.json'
  self.master.write_bytes(b'verified native snapshot')
  self.doc={'meta':{'canonical_detail_revision':19,'base_dataset_version':'v1-1111111111111111','source_base_dataset_version':'v1-1111111111111111'},
   'cards':[{'card_id':'id','items':[{'detail_id':'stable','name':'manual correction'}]}],'coverage':{'detail_item_count':1}}
  self.native=self.version(self.doc);self.put(self.native,self.doc)
  self.derived=copy.deepcopy(self.doc);self.derived['cards'][0]['items'][0]['effect_details']={'status':'partial','effects':[]}
  self.derived['coverage']['effect_detail_counts']={'panel_live':{'partial':1}}
  self.current=self.version(self.derived);self.put(self.current,self.derived)
  (self.site/'details/latest.json').write_text(json.dumps({'detail_version':self.current}),encoding='utf-8')
  self.conn={'baseline_sha256':hashlib.sha256(self.master.read_bytes()).hexdigest(),'detail_dataset_version':self.native,'canonical_detail_revision':19}
  self.save()
 def version(self,doc):
  return 'd1-'+digest({'base_dataset_version':doc['meta']['base_dataset_version'],'cards':doc['cards'],'coverage':doc['coverage']})[:16]
 def put(self,version,doc):
  p=self.site/'details'/version/'details.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(doc),encoding='utf-8')
 def save(self):self.connection.write_text(json.dumps(self.conn),encoding='utf-8')
 def check(self):return check_pair(self.site,self.master,self.connection)
 def test_derived_version_can_change_while_native_snapshot_and_values_stay_fixed(self):
  result=self.check();self.assertTrue(result['non_effect_fields_equal'])
  self.assertEqual(result['native_detail_version'],self.native);self.assertEqual(result['derived_public_version'],self.current)
 def test_source_and_derived_same_version_still_validate(self):
  (self.site/'details/latest.json').write_text(json.dumps({'detail_version':self.native}),encoding='utf-8')
  self.assertTrue(self.check()['non_effect_fields_equal'])
 def test_same_version_changed_manual_value_is_rejected(self):
  (self.site/'details/latest.json').write_text(json.dumps({'detail_version':self.native}),encoding='utf-8')
  bad=copy.deepcopy(self.doc);bad['cards'][0]['items'][0]['name']='lost correction';self.put(self.native,bad)
  with self.assertRaisesRegex(ValueError,'content hash'):self.check()
 def test_matching_tampering_in_native_and_derived_is_rejected(self):
  for version,doc in [(self.native,self.doc),(self.current,self.derived)]:
   bad=copy.deepcopy(doc);bad['cards'][0]['items'][0]['detail_id']='changed-id';self.put(version,bad)
  with self.assertRaisesRegex(ValueError,'content hash'):self.check()
 def test_master_hash_and_revision_mismatches_rejected(self):
  self.master.write_bytes(b'interrupted')
  with self.assertRaisesRegex(ValueError,'workbook hash'):self.check()
  self.master.write_bytes(b'verified native snapshot');self.conn['canonical_detail_revision']=18;self.save()
  with self.assertRaisesRegex(ValueError,'canonical revision'):self.check()
 def test_derived_id_manual_value_coverage_and_base_changes_rejected(self):
  for change in [lambda d:d['cards'][0]['items'][0].update(name='lost correction'),
                 lambda d:d['cards'][0]['items'][0].update(detail_id='new-id'),
                 lambda d:d['coverage'].update(detail_item_count=0),
                 lambda d:d['meta'].update(base_dataset_version='v1-2222222222222222')]:
   d=copy.deepcopy(self.derived);change(d);self.put(self.current,d)
   with self.assertRaises(ValueError):self.check()
 def test_invalid_pointer_cannot_escape_snapshot_root(self):
  self.conn['detail_dataset_version']='../../outside';self.save()
  with self.assertRaisesRegex(ValueError,'Invalid original/public'):self.check()

if __name__=='__main__':unittest.main()
