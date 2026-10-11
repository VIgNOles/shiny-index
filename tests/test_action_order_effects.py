import copy
import unittest
from src.skill_effects import effect_details,validate_effect_details
from src.skill_conditions_v2 import context

class ActionOrderTests(unittest.TestCase):
 def setUp(self):self.ctx=context([{'idol_name':'浅倉透','unit_name':'ノクチル'}])
 def doc(self,text,**kw):
  d=effect_details({'kind':'panel_live','effect_private':text,**kw},self.ctx['idols'],self.ctx)
  validate_effect_details(d,self.ctx['idols'],self.ctx);return d
 def test_short_and_long_appeals_have_same_order_without_duplicate_facts(self):
  for word,order in [('最初','first'),('最後','last')]:
   for middle in ['', 'アピールを行い']:
    es=self.doc('必ず'+word+'に'+middle+'全観客にVisual4.5倍アピール')['effects']
    self.assertEqual(len(es),1);e=es[0]
    self.assertEqual((e['metric'],e['value'],e['appeal_order'],e['audience']),('appeal',4.5,order,'all'))
    self.assertEqual(e['order_excludes'],['collaboration_fes'])
 def test_order_is_separate_from_buffs_when_no_numeric_appeal_is_given(self):
  es=self.doc('必ず最初にアピールを行いメンタルダメージ50%UP[1ターン]/Dance100%UP[3ターン](Link)メンタル20%回復')['effects']
  self.assertEqual([e['metric'] for e in es],['action_order','rate_up','rate_up','mental_recovery'])
  self.assertEqual(es[0]['targets'],['行動順']);self.assertEqual(es[0]['unit'],'boolean')
  self.assertEqual(es[0]['appeal_order'],'first');self.assertNotIn('turns',es[0])
  self.assertEqual(es[1]['targets'],['メンタルダメージ']);self.assertEqual(es[1]['turns'],1)
  self.assertEqual(es[2]['targets'],['Dance']);self.assertEqual(es[2]['turns'],3)
  self.assertEqual(es[3]['scope'],'link');self.assertTrue(all('appeal_order' not in e for e in es[1:]))
 def test_order_does_not_leak_to_following_appeals_or_mechanic_scope(self):
  es=self.doc('必ず最後にアピールを行いVocal3倍アピール/Visual2倍アピール(Link)Dance4倍アピール')['effects']
  self.assertEqual([e.get('appeal_order') for e in es],['last',None,None]);self.assertEqual(es[2]['scope'],'link')
 def test_link_condition_stays_attached_to_order_and_its_own_effect(self):
  es=self.doc('Vocal2倍アピール(Link)[透]必ず最初にアピールを行いメンタル10%回復')['effects']
  self.assertEqual([e['metric'] for e in es],['appeal','action_order','mental_recovery'])
  self.assertNotIn('activation_condition',es[0])
  for e in es[1:]:
   self.assertEqual(e['scope'],'link');self.assertEqual(e['activation_condition']['expression']['field'],'history_participant')
 def test_unknown_prefix_and_nested_conditions_do_not_open_effect_boundaries(self):
  for text in ['未知必ず最初にアピールを行いVocal3倍アピール','[必ず最後にアピールを行いVocal3倍アピール]','未知必ず最初にアピールを行いメンタルダメージ50%UP[1ターン]','必ず最初にメンタルダメージ50%UP[1ターン]','必ず最初にアピールを行い未知Vocal3倍アピール']:
   self.assertEqual(self.doc(text)['effects'],[],text)
 def test_existing_appeal_range_consumption_and_restrictions_remain_local(self):
  e=self.doc('必ず最後にアピールを行いDance最大5.5倍アピール[注目度が低いほど効果UP]')['effects'][0]
  self.assertTrue(e['maximum']);self.assertEqual(e['restrictions'],{'scaling':'attention_descending'})
  self.assertNotIn('minimum',e)
 def test_order_fields_and_standalone_semantics_are_strict(self):
  cases=[('必ず最初にVocal3倍アピール',{'order_excludes':['unknown']}),('必ず最初にVocal3倍アピール',{'appeal_order':'middle'}),('Vocal3倍アピール',{'order_excludes':['collaboration_fes']}),('必ず最初にアピールを行いメンタル10%回復',{'turns':1}),('必ず最初にアピールを行いメンタル10%回復',{'targets':['Visual']}),('必ず最初にアピールを行いメンタル10%回復',{'unit':'multiplier'}),('必ず最初にアピールを行いメンタル10%回復',{'recipient':'self'})]
  for text,extra in cases:
   d=copy.deepcopy(self.doc(text));d['effects'][0].update(extra)
   with self.assertRaises(ValueError,msg=text):validate_effect_details(d,self.ctx['idols'],self.ctx)
 def test_legacy_appeal_order_without_new_optional_field_remains_valid(self):
  d=self.doc('必ず最後にVocal3倍アピール');d['effects'][0].pop('order_excludes');validate_effect_details(d,self.ctx['idols'],self.ctx)
if __name__=='__main__':unittest.main()
