import copy
import unittest
from src.skill_effects import effect_details,validate_effect_details
from src.skill_conditions_v2 import context

class ReactionEffectTests(unittest.TestCase):
 def setUp(self):
  self.ctx=context([{'idol_name':'浅倉透','unit_name':'ノクチル'},{'idol_name':'樋口円香','unit_name':'ノクチル'}])
 def doc(self,text,**kw):
  d=effect_details({'kind':'panel_live','effect_private':text,**kw},self.ctx['idols'],self.ctx)
  validate_effect_details(d,self.ctx['idols'],self.ctx)
  return d
 def test_watch_window_and_granted_duration_are_independent(self):
  es=self.doc('Vocal3倍アピール/2ターンの間回避時Vo100%UP[4ターン][3回]/注目度10%UP[5ターン]')['effects']
  e=es[1]
  self.assertEqual((e['trigger'],e['trigger_turns'],e['turns'],e['uses']),('reaction_evaded',2,4,3))
  self.assertNotIn('trigger_turns',es[0]);self.assertNotIn('trigger',es[2]);self.assertEqual(e['targets'],['Vocal'])
 def test_damage_grant_keeps_link_history_condition(self):
  es=self.doc('Dance5倍アピール(Link)[透]3ターンの間ダメージ時Dance50%UP[4ターン][3回]')['effects']
  e=es[1];self.assertEqual(e['scope'],'link');self.assertEqual(e['trigger'],'reaction_damage')
  self.assertEqual(e['activation_condition']['expression'],{'field':'history_participant','operator':'eq','value':'浅倉透'})
 def test_compound_grants_keep_shared_limit_and_do_not_create_immediate_buff(self):
  es=self.doc('3ターンの間ダメージ時Da60%UP[3ターン]、Vi60%UP[3ターン][6回]')['effects']
  self.assertEqual(len(es),2);self.assertEqual([e['targets'] for e in es],[['Dance'],['Visual']])
  self.assertTrue(all(e['shared_uses'] and e['uses']==6 and e['trigger']=='reaction_damage' for e in es))
 def test_missing_attribute_is_not_inferred_from_appeal(self):
  es=self.doc('Visual4倍アピール/2ターンの間回避時100%UP[4ターン][3回]')['effects']
  self.assertEqual(len(es),1);self.assertEqual(es[0]['metric'],'appeal')
 def test_unknown_reaction_tail_blocks_incorrect_suffix_extraction(self):
  for text in ['3ターンの間ダメージ時未知効果、Vi60%UP[3ターン][6回]','3ターンの間回避時Vocal60%UP[3ターン]','3ターンの間回避時Vocal60%UP[3ターン][0回]','[3ターンの間回避時Vocal60%UP[3ターン][2回]]']:
   self.assertEqual(self.doc(text)['effects'],[],text)
 def test_interest_statuses_are_not_fixed_interest_multipliers(self):
  es=self.doc('全観客にVocal4倍アピール/興味反転[2ターン]/全観客に興味限定[1ターン]')['effects']
  self.assertEqual([e['metric'] for e in es],['appeal','interest_reverse','interest_limit'])
  self.assertEqual(es[1]['unit'],'boolean');self.assertNotIn('audience',es[1]);self.assertEqual(es[2]['audience'],'all')
 def test_melancholy_keeps_recipient_and_delayed_reduction(self):
  for prefix,recipient in [('自身に','self'),('ライバルに','rivals'),('全ユニットに','all_units')]:
   e=self.doc(prefix+'メランコリー効果10%付与[3ターン]')['effects'][0]
   self.assertEqual((e['metric'],e['recipient'],e['trigger'],e['value']),('melancholy',recipient,'appeal_phase_start',10))
   self.assertEqual(e['turns'],3);self.assertNotIn('audience',e)
 def test_new_fields_and_trigger_semantics_are_strict(self):
  cases=[
   ('2ターンの間回避時Vo100%UP[4ターン][3回]',lambda e:e.pop('trigger_turns')),
   ('2ターンの間回避時Vo100%UP[4ターン][3回]',lambda e:e.update(trigger_turns=True)),
   ('2ターンの間回避時Vo100%UP[4ターン][3回]',lambda e:e.update(uses=101)),
   ('2ターンの間回避時Vo100%UP[4ターン][3回]',lambda e:e.update(shared_uses=True)),
   ('興味反転[2ターン]',lambda e:e.update(recipient='rivals')),
   ('自身にメランコリー効果10%付与[3ターン]',lambda e:e.update(recipient='unknown')),
   ('自身にメランコリー効果10%付与[3ターン]',lambda e:e.update(trigger='always')),
   ('Vocal100%UP[3ターン]',lambda e:e.update(trigger_turns=3)),
  ]
  for text,mutate in cases:
   d=copy.deepcopy(self.doc(text));mutate(d['effects'][0])
   with self.assertRaises(ValueError,msg=text):validate_effect_details(d,self.ctx['idols'],self.ctx)
if __name__=='__main__':unittest.main()
