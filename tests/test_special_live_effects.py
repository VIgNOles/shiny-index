import copy
import unittest
from src.skill_effects import effect_details,validate_effect_details
from src.skill_conditions_v2 import context

class SpecialLiveEffectTests(unittest.TestCase):
 def setUp(self):
  self.ctx=context([{'idol_name':n,'unit_name':u} for n,u in [('小宮果穂','放課後クライマックスガールズ'),('西城樹里','放課後クライマックスガールズ'),('斑鳩ルカ','コメティック')]])
 def doc(self,text,kind='panel_live',**kw):
  d=effect_details({'kind':kind,'effect_private':text,**kw},self.ctx['idols'],self.ctx)
  validate_effect_details(d,self.ctx['idols'],self.ctx)
  return d
 def test_resurrection_is_delayed_recovery_with_own_duration_and_uses(self):
  es=self.doc('Dance3倍アピール/リザレクション効果20%付与[3ターン][1回]/注目度30%UP[5ターン]')['effects']
  self.assertEqual([e['metric'] for e in es],['appeal','resurrection','rate_up'])
  self.assertEqual((es[1]['value'],es[1]['turns'],es[1]['uses'],es[1]['trigger']),(20,3,1,'mental_zero'))
  self.assertNotIn('turns',es[0]);self.assertEqual(es[2]['turns'],5)
 def test_change_condition_and_memory_link_stay_in_their_slots(self):
  es=self.doc('リザレクション効果33%付与[3ターン][1回](Change)[斑鳩ルカがライブに参加している場合]リザレクション効果33%付与[3ターン][1回]')['effects']
  self.assertEqual([e['scope'] for e in es],['base','change']);self.assertNotIn('activation_condition',es[0])
  self.assertEqual(es[1]['activation_condition']['expression']['field'],'participant')
  e=self.doc('思い出アピール[Lv1]','memory_appeal',link_appeal_private='リザレクション効果10%付与[3ターン][1回]')['effects'][0]
  self.assertEqual(e['scope'],'memory_link')
 def test_clear_keeps_excluded_status_and_never_acquires_cost_as_duration(self):
  e=self.doc('全観客の興味変動無効以外のステータス効果を解除[コスト:4]','quick_skill')['effects'][0]
  self.assertEqual(e['excludes'],['興味変動無効']);self.assertEqual(e['audience'],'all');self.assertNotIn('turns',e)
  self.assertEqual(self.doc('全観客の全ステータス効果を解除')['effects'],[])
 def test_duet_addition_is_current_appeal_not_persistent_buff(self):
  e=self.doc('このターンのアピールにデュエット[編成アイドル]を追加[コスト:2]','quick_skill')['effects'][0]
  self.assertEqual((e['metric'],e['duet_target'],e['timing']),('duet_add',{'kind':'formation'},'current_turn'))
  self.assertNotIn('turns',e)
 def test_duet_preserves_duplicate_calls_canonical_unit_and_named_target(self):
  es=self.doc('デュエット[放クラ]/デュエット[放クラ](Plus)[2ターン以前]デュエット[小宮 果穂]')['effects']
  self.assertEqual(len(es),3);self.assertEqual(es[0],es[1])
  self.assertEqual(es[0]['duet_target'],{'kind':'unit','name':'放課後クライマックスガールズ'})
  self.assertEqual(es[2]['duet_target'],{'kind':'idol','name':'小宮果穂'});self.assertEqual(es[2]['scope'],'plus')
  self.assertEqual(self.doc('デュエット[未知名]')['effects'],[])
 def test_grow_minimum_interest_is_not_fixed_multiplier_or_appeal_range(self):
  es=self.doc('Vocal3倍アピール(Grow)[注目度UPを付与]全観客に興味最小0.1倍[2ターン]/魅了[2ターン]')['effects']
  self.assertEqual(es[1]['metric'],'interest_minimum');self.assertNotIn('minimum',es[1]);self.assertEqual(es[1]['value'],0.1)
  self.assertEqual(es[1]['mechanic_condition']['role'],'growth');self.assertEqual(es[2]['mechanic_condition'],es[1]['mechanic_condition'])
  self.assertNotIn('audience',es[2]);self.assertEqual(es[1]['audience'],'all')
  self.assertEqual(self.doc('興味最小0.1倍[2ターン]')['effects'],[])
 def test_variable_and_maximum_duration_do_not_invent_fixed_turns(self):
  es=self.doc('熱狂[2-3ターン]/全観客に熱狂最大3つ付与[2～4ターン]/熱狂[最大3ターン]')['effects']
  self.assertEqual(es[0]['turn_range'],{'minimum':2,'maximum':3})
  self.assertEqual(es[1]['grant_count_maximum'],3);self.assertEqual(es[1]['turn_range'],{'minimum':2,'maximum':4})
  self.assertEqual(es[2]['turns_maximum'],3);self.assertTrue(all('turns' not in e for e in es))
  self.assertEqual(self.doc('熱狂[4～2ターン]')['effects'],[])
 def test_condition_and_unknown_prefix_are_not_status_grants(self):
  for s in ['[条件:魅了[3ターン]]','未知魅了[3ターン]','未知リザレクション効果10%付与[3ターン][1回]','魅了強化[3ターン]']:
   self.assertEqual(self.doc(s)['effects'],[])
 def test_strict_new_fields_reject_wrong_semantics_and_private_content(self):
  cases=[
   ('熱狂[2～4ターン]',lambda e:e.update(turns=4)),
   ('デュエット[放クラ]',lambda e:e['duet_target'].update(name='架空ユニット')),
   ('全観客の興味変動無効以外のステータス効果を解除',lambda e:e.update(excludes=[])),
   ('リザレクション効果10%付与[3ターン][1回]',lambda e:e.update(trigger='always')),
   ('魅了[3ターン]',lambda e:e.update(duet_target={'kind':'formation'})),
   ('熱狂[最大3ターン]',lambda e:e.update(private_text='原文')),
  ]
  for text,mutate in cases:
   d=copy.deepcopy(self.doc(text));mutate(d['effects'][0])
   with self.assertRaises(ValueError):validate_effect_details(d,self.ctx['idols'],self.ctx)
if __name__=='__main__':unittest.main()
