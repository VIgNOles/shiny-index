import copy
import unittest
import uuid
from src.indexer import accept,empty,read,resolve,key,validate

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
 def test_failed_batch(self):
  b=copy.deepcopy(self.batch);b['status']='failed'
  with self.assertRaises(ValueError):accept(self.m,b)

if __name__=='__main__':unittest.main()
