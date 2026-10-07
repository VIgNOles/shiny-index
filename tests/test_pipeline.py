import copy
import os
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch
from src.indexer import accept,empty,load_master,read,resolve,key,save_master,validate
from scripts.review_batch import review

class PipelineTests(unittest.TestCase):
 def setUp(self):
  cards=[]
  for i in range(9):
   cards.append(dict(card_title=f'【テスト{i}】',idol_id=f'idol_{i}',idol_name=f'人物{i}',card_kind='P' if i<4 else 'S',rarity='SSR',unit_id=None,unit_name=None,first_implemented_on='2020-01-01',acquisition_category='unknown',series_ids=[],series_status='unknown',collab_work=None,wiki_url=f'https://wikiwiki.jp/shinycolors/テスト{i}',wiki_link_status='observed',variant_kind='base',review_status='needs_review',source_ref='synthetic-test'))
  self.batch={'cards':cards,'status':'validated','run_id':'test','observed_at':'2020-01-01','scope':'sample'};self.m=accept(empty(),self.batch)
 def test_idempotent(self):
  self.assertEqual(self.m,accept(self.m,self.batch))
  b=copy.deepcopy(self.batch);b['run_id']='second';m=accept(self.m,b)
  self.assertEqual(resolve(self.m),resolve(m))
 def test_override_clear_release(self):
  cid=self.m['registry'][0]['card_id']
  self.m['overrides']=[{'card_id':cid,'values':{'card_title':'手修正'},'clear_fields':['first_implemented_on'],'updated_at':'2026-10-07T00:00:00Z'}]
  b=copy.deepcopy(self.batch);b['run_id']='changed';b['cards'][0]['card_title']='取得変更'
  m=accept(self.m,b);c=next(c for c in resolve(m) if c['card_id']==cid)
  self.assertEqual(c['card_title'],'手修正');self.assertIsNone(c['first_implemented_on'])
  m['overrides']=[];self.assertEqual(next(c for c in resolve(m) if c['card_id']==cid)['card_title'],'取得変更')
 def test_manual_requires_mapping(self):
  reg=self.m['registry'][0];reg['aliases']=[]
  b=copy.deepcopy(self.batch);b['run_id']='manual-match'
  with self.assertRaisesRegex(ValueError,'manual duplicate'):accept(self.m,b)
  m=accept(self.m,b,{key(b['cards'][0]):reg['card_id']})
  self.assertEqual(len(resolve(m)),9);self.assertEqual(m['registry'][0]['card_id'],reg['card_id'])
 def test_missing_full_blocks(self):
  b=copy.deepcopy(self.batch);b.update(scope='full',run_id='missing');b['cards'].pop()
  before=copy.deepcopy(self.m)
  with self.assertRaises(ValueError):accept(self.m,b)
  self.assertEqual(self.m,before)
 def test_invalid_and_duplicate(self):
  for mutate in [lambda c:c.update(game='shinycolors_song'),lambda c:c.update(first_implemented_on='2026-02-30'),lambda c:c.update(wiki_url='javascript:alert(1)'),lambda c:c.update(rarity='XX')]:
   cards=resolve(self.m);mutate(cards[0])
   with self.assertRaises(ValueError):validate(cards)
  cards=resolve(self.m)
  with self.assertRaises(ValueError):validate(cards+[cards[0]])
 def test_road_same_url(self):
  cards=resolve(self.m);c=copy.deepcopy(cards[0]);c.update(card_id=str(uuid.uuid4()),family_id=cards[0]['card_id'],variant_kind='idol_road_sr',rarity='SR',first_implemented_on=None);cards.append(c);validate(cards)
 def test_field_specific_evidence(self):
  b=copy.deepcopy(self.batch);b['run_id']='field-evidence'
  b['cards'][0].update(acquisition_category='limited_gacha',series_ids=['axe8'],series_status='known')
  b['cards'][0]['field_sources']={'acquisition_category':{'source_ref':'W09','url':'https://wikiwiki.jp/shinycolors/ガシャ','response_hash':'testhash','locator':'AXE8'}}
  m=accept(self.m,b)
  cid=self.m['registry'][0]['card_id']
  evidence=next(e for e in m['evidence'] if e['card_id']==cid and e['field_name']=='acquisition_category')
  self.assertEqual((evidence['source_ref'],evidence['response_hash']),('W09','testhash'))
 def test_master_roundtrip_keeps_candidates_and_overrides(self):
  m=copy.deepcopy(self.m);cid=m['registry'][0]['card_id']
  m['candidates']=[{'run_id':'held-run','status':'held','parser_version':'test-1','changes':[{'card_id':cid,'old':'A','new':'B'}]}]
  m['overrides']=[{'card_id':cid,'values':{'review_status':'needs_review'},'clear_fields':[],'reason':'候補を確認中','source_ref':'manual-test','updated_at':'2026-10-07T12:00:00+09:00'}]
  with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{'XLSX_BACKEND':'stdlib'}):
   path=Path(directory)/'master.xlsx';save_master(m,path)
   self.assertEqual(load_master(path),m)
   from openpyxl import load_workbook
   wb=load_workbook(path);wb['取得候補']['B2']='accepted';wb.save(path)
   with self.assertRaisesRegex(ValueError,'candidate row mismatch'):load_master(path)
 def test_review_reports_changed_missing_new_and_override(self):
  m=copy.deepcopy(self.m);cid=m['registry'][0]['card_id']
  m['overrides']=[{'card_id':cid,'values':{'card_title':'手修正'},'clear_fields':[]}]
  b=copy.deepcopy(self.batch);b.update(scope='full',run_id='review-test')
  b['cards'][0]['card_title']='取得変更';b['cards'].pop(1)
  new=copy.deepcopy(b['cards'][0]);new.update(wiki_url='https://wikiwiki.jp/shinycolors/新規',idol_id='idol_new',idol_name='新規',card_title='【新規】')
  b['cards'].append(new)
  report=review(m,b)
  self.assertEqual({k:report['counts'][k] for k in ['new','changed','missing']},{'new':1,'changed':1,'missing':1})
  self.assertTrue(report['changed_rows'][0]['fields'][0]['manual_override'])
  self.assertTrue(report['warnings']['missing_existing_keys'])
  self.assertEqual(m['revision'],1)
 def test_failed_batch(self):
  b=copy.deepcopy(self.batch);b['status']='failed'
  with self.assertRaises(ValueError):accept(self.m,b)

if __name__=='__main__':unittest.main()
