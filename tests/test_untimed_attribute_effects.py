import unittest
from src.skill_effects import live,validate_effect_details

class UntimedAttributeEffectsTests(unittest.TestCase):
 def test_known_memory_amount_keeps_three_targets_without_duration(self):
  facts=live('思い出アピール[Lv3]/Vo&Da&Vi5%UP')
  self.assertEqual(len(facts),1)
  self.assertEqual(facts[0]['targets'],['Vocal','Dance','Visual'])
  self.assertEqual(facts[0]['value'],5)
  self.assertNotIn('turns',facts[0]);self.assertEqual(facts[0]['restriction_status'],'partial')
  validate_effect_details({'status':'partial','effects':facts},set())
 def test_link_does_not_inherit_person_bonus_turns(self):
  facts=live('Dance2.5倍アピール/緋田美琴のアピール倍率0.5倍UP[3ターン](Link)Dance50%UP')
  f=next(x for x in facts if x['metric']=='rate_up')
  self.assertEqual((f['scope'],f['targets'],f['value']),('link',['Dance'],50))
  self.assertNotIn('turns',f)
 def test_adjacent_duration_is_parsed_once_and_preserved(self):
  f=live('Vocal20%UP[2ターン]/Dance50%UP')
  self.assertEqual(len(f),2);self.assertEqual(f[0]['turns'],2);self.assertNotIn('turns',f[1])
 def test_unknown_tail_nested_condition_or_unfinished_clause_is_not_guessed(self):
  for s in ['Vocal20%UP謎条件','[Vocal20%UP]','条件:Vocal20%UP','Vocal20%UP[不明]','Vocal20%UP[2ターン以降]','[条件:不明/Vocal20%UP/追加]']:
   self.assertFalse(live(s),s)
