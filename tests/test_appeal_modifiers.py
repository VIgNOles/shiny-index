import copy,unittest
from src.skill_effects import effect_details,validate_effect_details
from src.skill_conditions_v2 import context

class AppealModifierTests(unittest.TestCase):
 def setUp(self):self.ctx=context([{'idol_name':n,'unit_name':'シーズ'} for n in ['緋田美琴','七草にちか']])
 def doc(self,text,**kw):
  d=effect_details(dict(kind='panel_live',effect_private=text,**kw),self.ctx['idols'],self.ctx);validate_effect_details(d,self.ctx['idols'],self.ctx);return d
 def test_enhancement_belongs_to_adjacent_appeal_only(self):
  es=self.doc('全観客にDance4倍アピール[Dance強化]/Dance2倍アピール(Link)Visual3倍アピール')['effects']
  self.assertEqual(es[0]['appeal_enhancement'],{'target':'Dance','factor':2,'this_appeal_only':True})
  self.assertEqual(es[0]['value'],4);self.assertNotIn('turns',es[0]);self.assertTrue(all('appeal_enhancement' not in e for e in es[1:]))
 def test_attributes_and_charm_have_distinct_factors(self):
  for target in ['Vocal','Dance','Visual','魅了']:
   e=self.doc('Vocal3倍アピール['+target+'強化]')['effects'][0]
   self.assertEqual(e['appeal_enhancement']['factor'],1.5 if target=='魅了' else 2)
 def test_unknown_nonadjacent_or_duplicate_modifiers_not_adopted(self):
  for text in ['Vocal3倍アピール/ [Vocal強化]','Vocal3倍アピール[Vocal強化][Visual強化]','Vocal3倍アピール[未知強化]']:
   self.assertTrue(all('appeal_enhancement' not in e for e in self.doc(text)['effects']))
 def test_known_adjacent_restrictions_are_preserved(self):
  e=self.doc('Vocal最大3倍アピール[Vocal強化][メンタルが多い程効果UP]')['effects'][0]
  self.assertTrue(e['maximum']);self.assertEqual(e['restrictions'],{'scaling':'mental'});self.assertIn('appeal_enhancement',e)
 def test_personal_bonus_is_additive_and_not_an_appeal(self):
  es=self.doc('緋田美琴のアピール倍率0.5倍UP[4ターン]/Visual2倍アピール')['effects']
  self.assertEqual((es[0]['metric'],es[0]['value'],es[0]['unit'],es[0]['turns']),('idol_appeal_bonus',.5,'multiplier',4));self.assertEqual(es[0]['restrictions'],{'idols':['緋田美琴']})
  self.assertEqual(es[1]['metric'],'appeal');self.assertNotIn('restrictions',es[1])
 def test_shared_persons_scope_and_grow_maximum(self):
  es=self.doc('Vocal2倍アピール(Link)七草にちか&緋田美琴のライブスキル倍率0.2倍UP[3ターン](Grow)緋田美琴のアピール倍率最大0.5倍UP[4ターン]')['effects']
  self.assertEqual((es[1]['scope'],es[1]['restrictions']['idols']),('link',['七草にちか','緋田美琴']));self.assertTrue(es[2]['maximum']);self.assertEqual(es[2]['scope'],'grow')
 def test_unknown_names_units_duplicates_and_missing_duration_rejected(self):
  for text in ['未知&緋田美琴のアピール倍率0.5倍UP[4ターン]','緋田美琴&緋田美琴のアピール倍率0.5倍UP[4ターン]','緋田美琴のアピール倍率0.5UP[4ターン]','緋田美琴のアピール倍率0.5倍UP','緋田美琴のアピール倍率最大0.5倍UP[4ターン]','[緋田美琴のアピール倍率0.5倍UP[4ターン]]Vocal2倍アピール']:
   self.assertFalse(any(e['metric']=='idol_appeal_bonus' for e in self.doc(text)['effects']),text)
 def test_validator_rejects_invalid_enhancement_and_bonus(self):
  d=self.doc('Vocal2倍アピール[Vocal強化]');d['effects'][0]['appeal_enhancement']['factor']=3
  with self.assertRaises(ValueError):validate_effect_details(d,self.ctx['idols'],self.ctx)
  d=self.doc('緋田美琴のアピール倍率0.5倍UP[4ターン]');d['effects'][0]['unit']='percent'
  with self.assertRaises(ValueError):validate_effect_details(d,self.ctx['idols'],self.ctx)
 def test_scaling_notation_alias(self):
  e=self.doc('Vocal最大3倍アピール[注目度が高い程効果UP]')['effects'][0];self.assertEqual(e['restrictions']['scaling'],'attention')
