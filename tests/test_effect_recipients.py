import copy
import unittest
from src.skill_effects import effect_details,validate_effect_details

class EffectRecipientTests(unittest.TestCase):
 def doc(self,text):
  d=effect_details({'kind':'panel_live','effect_private':text})
  validate_effect_details(d,[])
  return d
 def test_recipient_binds_only_to_its_own_attribute_effect(self):
  es=self.doc('全ユニットのVisual10%UP[4ターン]/Vocal50%UP[3ターン](Link)Dance80%UP[2ターン]')['effects']
  self.assertEqual([e.get('recipient') for e in es],['all_units',None,None])
  self.assertEqual([e['scope'] for e in es],['base','base','link'])
  self.assertEqual(es[0]['targets'],['Visual'])
 def test_rival_down_is_separate_from_own_cost(self):
  es=self.doc('ライバルのVisual10%DOWN[1ターン]/自身のメンタルを10%減らす(Link)Vocal50%UP[2ターン]')['effects']
  self.assertEqual([(e['metric'],e.get('recipient')) for e in es],[('rate_down','rivals'),('mental_cost','self'),('rate_up',None)])
 def test_recovery_and_relax_have_different_timing(self):
  es=self.doc('全ユニットのメンタル10%回復/全ユニットにリラックス効果5%付与[3ターン]')['effects']
  self.assertEqual([e['recipient'] for e in es],['all_units','all_units'])
  self.assertEqual(es[0]['metric'],'mental_recovery');self.assertNotIn('trigger',es[0]);self.assertNotIn('turns',es[0])
  self.assertEqual((es[1]['metric'],es[1]['trigger'],es[1]['starts_next_turn'],es[1]['turns']),('relax','appeal_phase_start',True,3))
 def test_unprefixed_effects_do_not_imply_self(self):
  for text in ['Vocal50%UP[3ターン]','メンタル10%回復','リラックス効果5%付与[3ターン]']:
   e=self.doc(text)['effects'][0];self.assertNotIn('recipient',e)
 def test_unknown_prefix_and_bracketed_conditions_are_not_effects(self):
  for text in ['未知の全ユニットのVocal50%UP[3ターン]','未知の全ユニットのメンタル10%回復','未知の全ユニットにリラックス効果5%付与[3ターン]','[全ユニットのVisual50%UP[3ターン]]','全観客のVisual50%UP[3ターン]']:
   self.assertEqual(self.doc(text)['effects'],[],text)
 def test_explicit_self_and_compound_attributes_are_preserved(self):
  e=self.doc('自身のVocal&Dance50%UP[3ターン]')['effects'][0]
  self.assertEqual(e['recipient'],'self');self.assertEqual(e['targets'],['Vocal','Dance'])
 def test_validator_rejects_incompatible_scope_and_timing(self):
  cases=[('Vocal50%UP[3ターン]',{'recipient':'unknown'}),('Vocal3倍アピール',{'recipient':'all_units'}),('自身のメンタルを10%減らす',{'recipient':'rivals'}),('メンタル10%回復',{'starts_next_turn':True}),('リラックス効果5%付与[3ターン]',{'starts_next_turn':1}),('リラックス効果5%付与[3ターン]',{'trigger':'always'}),('リラックス効果5%付与[3ターン]',{'recipient':'all_audience'})]
  for text,extra in cases:
   d=copy.deepcopy(self.doc(text));d['effects'][0].update(extra)
   with self.assertRaises(ValueError,msg=text):validate_effect_details(d,[])
 def test_legacy_relax_facts_remain_valid(self):
  d=self.doc('リラックス効果5%付与[3ターン]');e=d['effects'][0];e.pop('trigger');e.pop('starts_next_turn');validate_effect_details(d,[])
if __name__=='__main__':unittest.main()
