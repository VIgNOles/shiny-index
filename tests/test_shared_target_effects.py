import unittest
from src.skill_effects import effect_details,validate_effect_details
from src.skill_conditions_v2 import context
from scripts.audit_effect_structure import source_proven_shared_target_update

class SharedTargetTests(unittest.TestCase):
 def setUp(self):self.ctx=context([{'idol_name':'小宮果穂','unit_name':'放課後クライマックスガールズ'}])
 def doc(self,text):
  d=effect_details({'kind':'panel_live','effect_private':text},self.ctx['idols'],self.ctx)
  validate_effect_details(d,self.ctx['idols'],self.ctx);return d
 def test_shared_value_and_duration_are_one_fact_without_duplicate_suffix(self):
  es=self.doc('Vocal3.5倍アピール/注目度＆メンタルダメージ 50％UP［1ターン］(Link)Vocal3倍アピール')['effects']
  self.assertEqual(len(es),3);shared=es[1]
  self.assertEqual(shared['targets'],['注目度','メンタルダメージ'])
  self.assertEqual((shared['metric'],shared['value'],shared['turns'],shared['scope']),('rate_up',50,1,'base'))
  self.assertNotIn('turns',es[0]);self.assertEqual(es[2]['scope'],'link');self.assertNotIn('turns',es[2])
 def test_separate_values_and_turns_do_not_merge(self):
  es=self.doc('注目度20%UP[2ターン]/メンタルダメージ50%UP[1ターン]')['effects']
  self.assertEqual([(e['targets'],e['value'],e['turns']) for e in es],[(['注目度'],20,2),(['メンタルダメージ'],50,1)])
 def test_direction_recipient_scope_and_order_stay_on_their_own_effect(self):
  es=self.doc('必ず最初にアピールを行いVocal3倍アピール(Link)ライバルの注目度&メンタルダメージ30%DOWN[2ターン]')['effects']
  e=es[1];self.assertEqual((e['metric'],e['scope'],e['recipient']),('rate_down','link','rivals'))
  self.assertEqual(e['targets'],['注目度','メンタルダメージ']);self.assertNotIn('appeal_order',e)
 def test_shared_target_does_not_open_unknown_or_bracketed_prefix(self):
  for text in ['未知注目度&メンタルダメージ50%UP[1ターン]','[注目度&メンタルダメージ50%UP[1ターン]]']:
   self.assertEqual(self.doc(text)['effects'],[])
 def test_audit_requires_exact_source_and_identical_remaining_fields(self):
  source={'kind':'panel_live','effect_private':'Vocal3倍アピール/注目度&メンタルダメージ50%UP[1ターン](Link)Dance3倍アピール'}
  after=self.doc(source['effect_private'])['effects'][1];before={**after,'targets':['メンタルダメージ']}
  self.assertTrue(source_proven_shared_target_update(before,after,source))
  for extra in [{'value':70},{'turns':2},{'scope':'link'},{'metric':'rate_down'},{'targets':['注目度','メンタルダメージ','Dance']},{'recipient':'self'}]:
   candidate={**after,**extra}
   self.assertFalse(source_proven_shared_target_update(before,candidate,source))
  for text in ['注目度50%UP[1ターン]/メンタルダメージ50%UP[1ターン]','未知注目度&メンタルダメージ50%UP[1ターン]','(Link)注目度&メンタルダメージ50%UP[1ターン]','注目度&メンタルダメージ70%UP[1ターン]','注目度&メンタルダメージ50%UP[2ターン]']:
   self.assertFalse(source_proven_shared_target_update(before,after,{**source,'effect_private':text}))
 def test_audit_accepts_only_matching_memory_link_slot(self):
  after={'metric':'rate_up','targets':['注目度','メンタルダメージ'],'unit':'percent','scope':'memory_link','value':50.0,'turns':1,'restriction_status':'partial'}
  before={**after,'targets':['メンタルダメージ']}
  source={'kind':'memory_appeal','effect_private':'注目度&メンタルダメージ50%UP[1ターン]'}
  self.assertFalse(source_proven_shared_target_update(before,after,source))
  source['link_appeal_private']=source['effect_private']
  self.assertTrue(source_proven_shared_target_update(before,after,source))

if __name__=='__main__':unittest.main()
