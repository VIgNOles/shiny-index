import copy
import unittest
from src.skill_effects import effect_details,validate_effect_details

class ConsumptionEffectTests(unittest.TestCase):
 def doc(self,text,kind='panel_live',**kw):
  d=effect_details({'kind':kind,'effect_private':text,**kw})
  validate_effect_details(d,())
  return d
 def test_target_is_distinct_from_appeal_attribute_and_grants(self):
  es=self.doc('Dance1.2～6倍アピール[消去:VisualUP]/Dance&Visual15%UP[6ターン](Link)Dance0.6～3倍アピール[消去:VocalUP]')['effects']
  self.assertEqual([e['scope'] for e in es],['base','base','link'])
  self.assertEqual(es[0]['targets'],['Dance'])
  self.assertEqual(es[0]['status_consumption']['statuses'],[{'target':'Visual','direction':'UP'}])
  self.assertNotIn('status_consumption',es[1]);self.assertEqual(es[1]['turns'],6)
  self.assertEqual(es[2]['status_consumption']['statuses'],[{'target':'Vocal','direction':'UP'}])
 def test_multiple_appeals_keep_own_suffix_and_order(self):
  es=self.doc('全観客にVocal最大2.5倍アピール[消去:VocalUP]&Dance最大2.5倍アピール[消去:DanceUP]')['effects']
  self.assertEqual(len(es),2)
  self.assertEqual([e['status_consumption']['statuses'][0]['target'] for e in es],['Vocal','Dance'])
  self.assertEqual(es[0]['audience'],'all');self.assertNotIn('audience',es[1])
 def test_shared_direction_aliases_and_multi_status_sum(self):
  e=self.doc('Vo最大3倍アピール[消去:Da & ViUP]')['effects'][0]
  self.assertEqual(e['status_consumption']['statuses'],[{'target':'Dance','direction':'UP'},{'target':'Visual','direction':'UP'}])
  self.assertEqual(e['status_consumption']['quantity'],'all');self.assertFalse(e['status_consumption']['passive_included'])
 def test_down_is_not_up_and_does_not_become_a_grant(self):
  e=self.doc('Da最大1倍アピール[消去:DanceDOWN]')['effects'][0]
  self.assertEqual(e['status_consumption']['statuses'][0]['direction'],'DOWN')
  self.assertNotIn('turns',e);self.assertNotIn('uses',e)
 def test_explicit_range_is_preserved_without_filling_a_formula(self):
  e=self.doc('Dance0.5～2倍アピール[消去:VisualDOWN]')['effects'][0]
  self.assertEqual((e['minimum'],e['value']),(0.5,2));self.assertNotIn('formula',e)
  e=self.doc('Visual最大7倍アピール[消去:VisualUP]')['effects'][0]
  self.assertTrue(e['maximum']);self.assertNotIn('minimum',e)
 def test_memory_base_and_link_are_independent(self):
  es=self.doc('思い出アピール[Lv5]/Dance0.6～3倍アピール[消去:DanceUP]','memory_appeal',link_appeal_private='全観客にVisual0.6～3倍アピール[消去:VisualUP]')['effects']
  self.assertEqual([e['scope'] for e in es],['base','memory_link'])
  self.assertEqual([e['status_consumption']['statuses'][0]['target'] for e in es],['Dance','Visual'])
 def test_no_suffix_propagation_through_other_brackets_or_text(self):
  for text in ['Vocal3倍アピール/ [消去:VocalUP]','Vocal3倍アピール[3ターン][消去:VocalUP]','Vocal3倍アピール何か[消去:VocalUP]']:
   self.assertTrue(all('status_consumption' not in e for e in self.doc(text)['effects']))
 def test_unknown_and_incomplete_statuses_stay_unstructured(self):
  for body in ['不明UP','Vocal','VocalUP&Dance','VoUP&VocalUP','VocalUP、DanceUP','VocalUP[3ターン]','VocalUP以外']:
   self.assertNotIn('status_consumption',self.doc('Vocal3倍アピール[消去:'+body+']')['effects'][0])
 def test_nested_condition_and_unknown_prefix_are_not_effects(self):
  for text in ['[条件:Vocal3倍アピール[消去:VocalUP]]','未知Vocal3倍アピール[消去:VocalUP]','[消去:VocalUP]']:
   self.assertEqual(self.doc(text)['effects'],[])
 def test_validator_rejects_semantic_drift_and_private_fields(self):
  original=self.doc('Vocal3倍アピール[消去:VocalUP]')
  mutations=[
   lambda e:e.update(metric='rate_up'),lambda e:e.update(turns=3),
   lambda e:e['status_consumption'].update(quantity=4),
   lambda e:e['status_consumption'].update(passive_included=True),
   lambda e:e['status_consumption'].update(timing='after_skill'),
   lambda e:e['status_consumption'].update(private_text='原文'),
   lambda e:e['status_consumption']['statuses'][0].update(target='メンタル'),
   lambda e:e['status_consumption']['statuses'][0].update(direction='CUT'),
   lambda e:e['status_consumption']['statuses'].append(e['status_consumption']['statuses'][0].copy()),
  ]
  for mutate in mutations:
   d=copy.deepcopy(original);mutate(d['effects'][0])
   with self.assertRaises(ValueError):validate_effect_details(d,())

if __name__=='__main__':unittest.main()
