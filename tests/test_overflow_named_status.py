import copy
import unittest
from src.skill_effects import effect_details,validate_effect_details
from src.skill_conditions_v2 import context

class OverflowNamedStatusTests(unittest.TestCase):
 def setUp(self):
  self.ctx=context([{'idol_name':'鈴木羽那','unit_name':'コメティック'},{'idol_name':'郁田はるき','unit_name':'コメティック'}])
 def parse(self,text,kind='panel_live',**kw):
  d=effect_details({'kind':kind,'effect_private':text,**kw},self.ctx['idols'],self.ctx)
  validate_effect_details(d,self.ctx['idols'],self.ctx)
  return d['effects']
 def test_overflow_modifies_only_adjacent_heal_without_fixed_memory_gain(self):
  es=self.parse('メンタル20%回復[超過分は思い出ゲージに変換]/メンタル5%回復/思い出ゲージ10%UP(Link)メンタル30%回復')
  self.assertEqual([e['metric'] for e in es],['mental_recovery','mental_recovery','memory_gauge_gain','mental_recovery'])
  self.assertTrue(es[0]['overflow_to_memory'])
  for e in es[1:]:self.assertNotIn('overflow_to_memory',e)
  self.assertEqual(es[2]['value'],10);self.assertEqual(es[3]['scope'],'link')
 def test_short_me_and_full_mental_recovery_are_equivalent(self):
  self.assertEqual(self.parse('Me15%回復[超過思い出変換]'),self.parse('メンタル15%回復[超過分は思い出ゲージに変換]'))
 def test_overflow_not_inherited_across_unknown_suffix_slash_or_condition(self):
  for text in ['メンタル5%回復/[超過思い出変換]','メンタル5%回復[不明][超過思い出変換]','メンタル5%回復/メンタル10%回復[超過思い出変換]']:
   self.assertNotIn('overflow_to_memory',self.parse(text)[0])
  for text in ['説明Me15%回復[超過思い出変換]','[条件:Me15%回復[超過思い出変換]]']:
   self.assertEqual(self.parse(text),[])
 def test_memory_link_and_base_overflow_stay_separate(self):
  es=self.parse('思い出アピール[Lv5]/メンタル25%回復[超過分は思い出ゲージに変換]','memory_appeal',link_appeal_private='思い出ゲージ20%UP')
  self.assertEqual([(e['scope'],e['metric']) for e in es],[('base','mental_recovery'),('memory_link','memory_gauge_gain')])
 def test_named_status_duration_is_not_a_rate_buff(self):
  es=self.parse('瞳の輝き[2ターン]/注目度50%UP[4ターン]/フレキシブル[1ターン]')
  self.assertEqual([(e['metric'],e['targets'],e['value'],e['turns']) for e in es],[('sparkle_eyes',['瞳の輝き'],1,2),('rate_up',['注目度'],50,4),('flexible',['フレキシブル'],1,1)])
  for e in (es[0],es[2]):self.assertNotIn('trigger',e);self.assertNotIn('recipient',e)
 def test_plus_and_link_conditions_attach_only_to_their_status(self):
  es=self.parse('Vocal4倍アピール(Plus)[2ターン以前]フレキシブル[1ターン](Link)[羽那・はるき]気力+2')
  self.assertEqual([e['scope'] for e in es],['base','plus','link'])
  self.assertNotIn('activation_condition',es[0]);self.assertEqual(es[1]['activation_condition']['expression']['field'],'turn')
  self.assertEqual(es[2]['activation_condition']['expression']['terms'][0]['field'],'history_participant')
 def test_missing_durations_and_unknown_names_rejected(self):
  for text in ['フレキシブル','瞳の輝き','瞳の輝き/Dance50%UP[3ターン]','[条件:フレキシブル[2ターン]]','説明瞳の輝き[2ターン]','気力+1.5','気力+1%','思い出ゲージ30%DOWN[3ターン]']:
   self.assertFalse(any(e['metric'] in {'flexible','sparkle_eyes','vigor_gain','memory_gauge_loss'} for e in self.parse(text)),text)
 def test_immediate_resources_do_not_borrow_duration(self):
  es=self.parse('気力+2/思い出ゲージ30%DOWN/Dance50%UP[4ターン]')
  self.assertEqual([e['metric'] for e in es],['vigor_gain','memory_gauge_loss','rate_up'])
  self.assertEqual((es[0]['value'],es[1]['value']),(2,30));self.assertNotIn('turns',es[0]);self.assertNotIn('turns',es[1])
 def test_saved_missing_separator_after_vigor_does_not_swallow_exchange(self):
  es=self.parse('気力+2 交換数UP[1回]');self.assertEqual([e['metric'] for e in es],['vigor_gain','exchange_count_up'])
 def test_validator_rejects_cross_metric_fields_and_borrowed_duration(self):
  bad=[]
  heal=self.parse('メンタル5%回復')[0];bad.append({**heal,'overflow_to_memory':False})
  buff=self.parse('Dance50%UP[3ターン]')[0];bad.append({**buff,'overflow_to_memory':True})
  flexible=self.parse('フレキシブル[2ターン]')[0]
  for update in [{'value':50},{'turns':0},{'targets':['注目度']},{'recipient':'self'}]:bad.append({**flexible,**update})
  missing=copy.deepcopy(flexible);missing.pop('turns');bad.append(missing)
  vigor=self.parse('気力+1')[0]
  for update in [{'value':1.5},{'value':0},{'value':True},{'turns':2}]:bad.append({**vigor,**update})
  bad.append({**self.parse('思い出ゲージ30%DOWN')[0],'turns':4})
  for e in bad:
   with self.subTest(e=e),self.assertRaises(ValueError):validate_effect_details({'status':'partial','effects':[e]},self.ctx['idols'],self.ctx)

 def test_conversion_does_not_grant_unconditional_rate_up_or_take_link_duration(self):
  es=self.parse('Visual4倍アピール/自身のステータス効果全てをVisual40%UP[3ターン]に変換(Link)Visual60%UP[5ターン]')
  self.assertEqual([e['metric'] for e in es],['appeal','status_conversion','rate_up'])
  self.assertEqual((es[1]['targets'],es[1]['value'],es[1]['turns'],es[1]['recipient']),(['Visual'],40,3,'self'))
  self.assertEqual((es[2]['value'],es[2]['turns'],es[2]['scope']),(60,5,'link'))
 def test_perfect_multiplier_is_an_adjacent_alternative_not_an_extra_appeal(self):
  es=self.parse('Dance0.6倍アピール[PERFECTなら3倍アピール]/Dance2倍アピール(Link)Vocal4倍アピール')
  self.assertEqual(len(es),3);self.assertEqual(es[0]['value'],.6);self.assertEqual(es[0]['perfect_value'],3)
  for e in es[1:]:self.assertNotIn('perfect_value',e)
  self.assertNotIn('perfect_value',self.parse('Dance0.6倍アピール/[PERFECTなら3倍アピール]')[0])
 def test_rare_satisfaction_retains_qualitative_chance_and_no_guessed_percent(self):
  es=self.parse('Vocal2倍アピール/ごく稀に現在の興味値に関わらず一気に満足させる(Link)ごくごく稀に現在の興味値に関わらず一気に満足させる')
  self.assertEqual([e['metric'] for e in es],['appeal','instant_satisfaction','instant_satisfaction'])
  self.assertEqual([e['chance_tier'] for e in es[1:]],['rare','very_rare'])
  for e in es[1:]:self.assertEqual(e['probability'],{'unknown':True});self.assertNotIn('turns',e);self.assertNotIn('audience',e)
  self.assertFalse(any(e['metric']=='instant_satisfaction' for e in self.parse('必ず現在の興味値に関わらず一気に満足させる')))
 def test_charm_variable_duration_preserves_both_bounds(self):
  es=self.parse('魅了[2ターン](Grow)[注目度UPを付与]全観客に魅了[2～3ターン]/Visual最大150%UP[4ターン]')
  self.assertEqual(es[0]['turns'],2);self.assertEqual(es[1]['turn_range'],{'minimum':2,'maximum':3});self.assertEqual(es[1]['scope'],'grow');self.assertEqual(es[1]['audience'],'all')
  self.assertNotIn('turns',es[1]);self.assertEqual(es[2]['turns'],4)
 def test_conversion_perfect_chance_and_ranges_reject_invalid_fields(self):
  conversion=self.parse('自身のステータス効果全てをVisual40%UP[3ターン]に変換')[0]
  rare=self.parse('ごく稀に現在の興味値に関わらず一気に満足させる')[0]
  appeal=self.parse('Visual0.7倍アピール[PERFECTなら3.5倍アピール]')[0]
  charm=self.parse('魅了[2～3ターン]')[0]
  bad=[{**conversion,'targets':['注目度']},{**conversion,'recipient':'rivals'},{**rare,'probability':{'value':3}},{**rare,'chance_tier':'often'},{**rare,'turns':2},{**conversion,'perfect_value':3},{**appeal,'perfect_value':float('nan')},{**charm,'turn_range':{'minimum':3,'maximum':2}}]
  for e in bad:
   with self.subTest(e=e),self.assertRaises(ValueError):validate_effect_details({'status':'partial','effects':[e]},self.ctx['idols'],self.ctx)

 def test_owner_keyword_binds_only_adjacent_buff_not_entire_skill(self):
  es=self.parse('Dance3.5倍アピール/思い出ゲージ10%UP/Dance40%UP[3ターン][キーワード:リーダーシップ](Plus)[4ターン以降]Dance30%UP[5ターン]')
  self.assertEqual(es[2]['restrictions']['owner_keywords'],['リーダーシップ'])
  for e in [*es[:2],es[3]]:self.assertNotIn('owner_keywords',e.get('restrictions',{}))
  for clause in ['キーワード:未知','キーワード:歌姫、歌姫','キーワード:歌姫又はカリスマ']:
   self.assertNotIn('owner_keywords',self.parse('Vocal50%UP[3ターン]['+clause+']')[0].get('restrictions',{}))
  bad={**es[2],'restrictions':{'owner_keywords':['未知']}}
  with self.assertRaises(ValueError):validate_effect_details({'status':'partial','effects':[bad]},self.ctx['idols'],self.ctx)
