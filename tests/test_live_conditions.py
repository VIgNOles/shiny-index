import copy
import unittest
from src.live_conditions import mechanic_rule, validate_rule
from src.skill_conditions_v2 import context
from src.skill_effects import effect_details, validate_effect_details

class LiveConditionTests(unittest.TestCase):
 def setUp(self):
  self.ctx=context([{'idol_name':n,'unit_name':u} for n,u in [
   ('小宮果穂','放課後クライマックスガールズ'),('園田智代子','放課後クライマックスガールズ'),
   ('有栖川夏葉','放課後クライマックスガールズ'),('西城樹里','放課後クライマックスガールズ'),
   ('八宮めぐる','イルミネーションスターズ'),('鈴木羽那','コメティック'),
   ('七草にちか','シーズ'),('緋田美琴','シーズ'),('斑鳩ルカ','コメティック')]])
 def rule(self,text,scope):
  rule=mechanic_rule('['+text+']',self.ctx,scope)
  self.assertIsNotNone(rule);validate_rule(rule,self.ctx,scope);return rule
 def test_plus_counts_current_passives_and_requires_all_unit_members(self):
  rule=self.rule('パッシブスキル6個以上発動イルミネ全員がライブに参加','plus')
  a,b=rule['expression']['terms']
  self.assertEqual((a['field'],a['value']),('active_passive_count',6))
  self.assertEqual(b,{'field':'unit_all_participants','operator':'eq','value':'イルミネーションスターズ'})
  self.assertEqual(rule['role'],'activation')
 def test_plus_shorthand_status_and_shared_history_or(self):
  p=self.rule('注目度UPが3個以上付与放クラ全員がライブに参加している場合','plus')['expression']
  self.assertEqual(p['operator'],'all');self.assertEqual(p['terms'][0]['status'],'注目度UP')
  p=self.rule('履歴にコメティックのアイドル3人以上又は西城樹里がある場合','plus')['expression']
  self.assertEqual(p['operator'],'any');self.assertEqual([p['field'] for p in p['terms']],['history_unit_count','history_participant'])
 def test_refrain_named_boost_count_resolves_only_known_unique_names(self):
  p=self.rule('夏葉のアピール倍率UPが2個以上付与されている場合','refrain')['expression']
  self.assertEqual(p,{'field':'idol_appeal_boost_count','operator':'gte','value':2,'idol':'有栖川夏葉'})
  self.assertIsNone(mechanic_rule('[未知のアピール倍率UPが2個以上付与されている場合]',self.ctx,'refrain'))
 def test_grow_counts_grants_not_current_states_and_preserves_rollover(self):
  rule=self.rule('VocalUPを2個付与毎','grow')
  self.assertEqual(rule['expression'],{'field':'status_granted','operator':'eq','value':'VocalUP'})
  self.assertEqual(rule['events_per_level'],2)
  self.assertEqual((rule['level_up_timing'],rule['carry_over'],rule['reset_on_use']),('next_turn',True,True))
  self.assertIsNone(mechanic_rule('[VocalUPが2個以上付与されている場合]',self.ctx,'grow'))
 def test_grow_shared_three_idol_suffix_and_mixed_or(self):
  p=self.rule('七草にちか又は緋田美琴又は斑鳩ルカのアピール倍率UPを付与','grow')['expression']
  self.assertEqual(p['operator'],'any');self.assertEqual([x['value'] for x in p['terms']],['七草にちか','緋田美琴','斑鳩ルカ'])
  p=self.rule('注目度DOWN又は西城樹里のアピール倍率UPを付与','grow')['expression']
  self.assertEqual([x['field'] for x in p['terms']],['status_granted','idol_appeal_boost_granted'])
 def test_grow_history_additions_and_targeted_reactions_are_events(self):
  p=self.rule('履歴に放クラアイドルを追加','grow')['expression']
  self.assertEqual(p['field'],'history_unit_added');self.assertEqual(p['value'],'放課後クライマックスガールズ')
  p=self.rule('観客からリアクションの対象になる毎','grow')['expression']
  self.assertEqual(p['field'],'audience_reaction_targeted')
  self.assertNotEqual(p['field'],'damage_received')  # targeting is not actual damage
 def test_unknown_tail_duplicate_or_multiple_brackets_never_partially_parse(self):
  for text,scope in [('DanceUPを付与ただし未知','grow'),('DanceUP又は未知を付与','grow'),('DanceUP又はDanceUPを付与','grow'),('DanceUPを0個付与毎','grow'),('DanceUPを付与','plus')]:
   self.assertIsNone(mechanic_rule('['+text+']',self.ctx,scope))
  self.assertIsNone(mechanic_rule('[DanceUPを付与][未知]',self.ctx,'grow'))
 def test_rule_binding_preserves_legacy_fallback_and_never_leaks(self):
  d=effect_details({'kind':'panel_live','effect_private':'Vocal4倍アピール(Grow)[DanceUPを付与]Dance最大3倍アピール(Refrain)[未知]リフレイン[1ターン前]'},self.ctx['idols'],self.ctx)
  validate_effect_details(d,self.ctx['idols'],self.ctx)
  a,b,c=d['effects'];self.assertNotIn('mechanic_condition',a)
  self.assertEqual(b['activation_condition'],{'status':'unsupported'});self.assertEqual(b['mechanic_condition']['role'],'growth')
  self.assertNotIn('mechanic_condition',c)
 def test_standalone_growth_rule_survives_without_inventing_an_effect(self):
  d=effect_details({'kind':'panel_live','effect_private':'Vocal4倍アピール(Grow)[DanceUP又はパッシブスキル強化を付与]未知効果'},self.ctx['idols'],self.ctx)
  validate_effect_details(d,self.ctx['idols'],self.ctx)
  self.assertEqual(len(d['effects']),1);self.assertEqual(d['mechanic_conditions'][0]['segment'],1)
  self.assertEqual(d['mechanic_conditions'][0]['scope'],'grow')
  self.assertNotIn('未知効果',str(d))
  only=effect_details({'kind':'panel_live','effect_private':'(Grow)[DanceUPを付与]未知効果'},self.ctx['idols'],self.ctx)
  self.assertEqual(only['status'],'partial');self.assertEqual(only['effects'],[])
  validate_effect_details(only,self.ctx['idols'],self.ctx)
 def test_grow_maximum_buff_is_an_upper_bound_and_keeps_its_own_duration(self):
  d=effect_details({'kind':'panel_live','effect_private':'Vocal100%UP[3ターン](Grow)[VocalUPを2個付与毎]Vocal最大300%UP[4ターン]'},self.ctx['idols'],self.ctx)
  validate_effect_details(d,self.ctx['idols'],self.ctx)
  normal,grow=d['effects']
  self.assertNotIn('maximum',normal);self.assertEqual(normal['turns'],3)
  self.assertEqual((grow['metric'],grow['value'],grow['maximum'],grow['turns'],grow['scope']),('rate_up',300,True,4,'grow'))
  self.assertEqual(grow['mechanic_condition']['events_per_level'],2)
  self.assertNotIn('mechanic_conditions',d)
  # No interpretation is invented for maximum buffs in other contexts.
  for text in ['Vocal最大300%UP[4ターン]','(Plus)[2ターン以前]Vocal最大300%UP[4ターン]']:
   self.assertEqual(effect_details({'kind':'panel_live','effect_private':text},self.ctx['idols'],self.ctx)['effects'],[])

 def test_validator_rejects_prose_events_in_state_rule_and_invalid_counts(self):
  good=self.rule('DanceUPを付与','grow')
  for patch in [{'raw_text':'私有本文'},{'events_per_level':True},{'carry_over':False},{'expression':{'field':'status_granted','operator':'eq','value':'未知本文'}}]:
   bad={**copy.deepcopy(good),**patch}
   with self.assertRaises(ValueError):validate_rule(bad,self.ctx,'grow')
  with self.assertRaises(ValueError):validate_rule(good,self.ctx,'plus')
  bad=self.rule('夏葉のアピール倍率UPが2個以上付与されている場合','refrain')
  bad['expression']['value']=-1
  with self.assertRaises(ValueError):validate_rule(bad,self.ctx,'refrain')
  d=effect_details({'kind':'panel_live','effect_private':'(Grow)[DanceUPを付与]未知'},self.ctx['idols'],self.ctx)
  d['mechanic_conditions']*=2
  with self.assertRaises(ValueError):validate_effect_details(d,self.ctx['idols'],self.ctx)

if __name__=='__main__':unittest.main()
