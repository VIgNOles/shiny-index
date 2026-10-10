import unittest
from src.skill_effects import effect_details,validate_effect_details
class SkillEffectTests(unittest.TestCase):
 def get(self,kind,text,**kw):
  d=effect_details(dict(kind=kind,effect_private=text,**kw),{'櫻木真乃','風野灯織'})
  validate_effect_details(d,{'櫻木真乃','風野灯織'});return d
 def test_support_probability_and_effect_have_separate_level_values(self):
  e=self.get('support_skill','「休む」を選択時に<Lv*3>%の確率で体力回復量+15')['effects'][0]
  self.assertEqual(e['value'],15);self.assertEqual(e['probability']['formula']['coefficient'],3)
  self.assertEqual(e['trigger'],'rest')
 def test_support_whole_cell_and_member_constraint(self):
  e=self.get('support_skill','行動した場所に自分以外のユニットメンバーがいると1人につきSP+<Lv*1>')['effects'][0]
  self.assertTrue(e['per_member']);self.assertEqual(e['formula']['coefficient'],1)
  self.assertEqual(self.get('support_skill','一緒にダンスレッスンをするとSP+<Lv*1>/条件不明')['status'],'unsupported')
 def test_support_unknown_probability_is_never_invented(self):
  e=self.get('support_skill','テンション最高時に一緒に行動すると確率でSP+<Lv*1>')['effects'][0]
  self.assertEqual(e['probability'],{'unknown':True})
 def test_qualitative_stay_and_event_formula(self):
  e=self.get('support_skill','ボーカルレッスン滞在率がUP')['effects'][0]
  self.assertTrue(e['amount_unknown']);self.assertNotIn('value',e)
  e=self.get('support_skill','アイドルイベントとサポートイベントの発生率1+<Lv*0.1>倍')['effects'][0]
  self.assertEqual(e['formula']['offset'],1)
 def test_individual_durations_and_mechanic_scopes(self):
  es=self.get('panel_live','Vocal4.5倍アピール/ Vocal20%UP[5ターン]/ Vocal10%UP[7ターン] (Plus)[条件] Vocal40%UP[3ターン]')['effects']
  self.assertEqual([(e['value'],e.get('turns'),e['scope']) for e in es],[(4.5,None,'base'),(20,5,'base'),(10,7,'base'),(40,3,'plus')])
  self.assertTrue(all(e['restriction_status']=='partial' for e in es))
 def test_unknown_or_range_duration_and_status_prefix_are_rejected(self):
  for s in ['Vocal20%UP[3～5ターン]','Vocal最大300%UP[4ターン]']:
   self.assertEqual(self.get('panel_live',s)['effects'],[])
 def test_appeal_range_audience_and_conditional_maximum(self):
  es=self.get('panel_live','全観客にDance0.5～4.5倍アピール/(Link)Vocal最大5倍アピール[条件]')['effects']
  self.assertEqual((es[0]['minimum'],es[0]['value'],es[0]['audience']),(0.5,4.5,'all'));self.assertEqual(es[0]['targets'],['Dance']);self.assertEqual(es[1]['targets'],['Vocal'])
  self.assertTrue(es[1]['maximum']);self.assertEqual(es[1]['restriction_status'],'partial')
 def test_random_alternatives_are_not_claimed_as_simultaneous_effects(self):
  d=self.get('panel_live','Vocal20%UP[3ターン]/Dance20%UP[3ターン]',random_effect_options=[{'target':'Vocal'},{'target':'Dance'}])
  self.assertEqual(d['effects'],[])
 def test_memory_extra_slots_do_not_merge_into_normal_effects(self):
  es=self.get('memory_appeal','Vocal20%UP[3ターン]',link_appeal_private='Dance30%UP[5ターン]',charge_appeal_private='Visual40%UP[7ターン]')['effects']
  self.assertEqual([e['scope'] for e in es],['base','memory_link','memory_charge'])
 def test_ability_target_and_group_remain_attached(self):
  e=self.get('unique_ability','(アビリティ) 櫻木 真乃と風野 灯織のアピール値を+30%UP[グループ:相アイ]')['effects'][0]
  self.assertEqual(e['restrictions'],{'group':'相アイ','idols':['櫻木真乃','風野灯織']})
  self.assertEqual(self.get('unique_ability','架空名のアピール値を+30%UP')['status'],'unsupported')
 def test_group_identifier_preserves_internal_spaces(self):
  e=self.get('unique_ability','アピール値を+30%UP [グループ:Present Present]')['effects'][0]
  self.assertEqual(e['restrictions']['group'],'Present Present')
  e=self.get('memory_appeal','',link_appeal_private='(Link)Vocal20%UP[3ターン]')['effects'][0]
  self.assertEqual(e['scope'],'memory_link')
 def test_ability_scaling_and_unit_constraint_are_not_unconditional(self):
  e=self.get('unique_ability','アピール値最大21％UP[履歴が多いほど効果UP][条件:履歴に1ジャンルのみ]')['effects'][0]
  self.assertTrue(e['maximum']);self.assertEqual(e['restrictions'],{'scaling':'history','history_genres':1})
  e=self.get('unique_ability','アピール値を+13%UP[条件:編成アイドルの所属ユニットが１種類以下の場合]')['effects'][0]
  self.assertEqual(e['restrictions']['unit_types_max'],1)
 def test_ability_unknown_condition_stays_partial(self):
  d=self.get('unique_ability','アピール値を+13%UP[条件:不明な条件]')
  self.assertEqual(d['status'],'partial');self.assertEqual(d['effects'][0]['restriction_status'],'partial')
 def test_phase_probability_does_not_become_appeal_multiplier(self):
  e=self.get('unique_ability','アピールフェイズ開始毎に5％の確率でVo&Da&Vi10%UP[3ターン]付与')['effects'][0]
  self.assertEqual(e['targets'],['Vocal','Dance','Visual']);self.assertEqual(e['probability'],{'value':5});self.assertEqual(e['turns'],3)
 def test_extra_particle_is_only_accepted_for_exact_known_skill_pair(self):
  d=self.get('support_skill','テンション最高時に一緒に行動するとでVocal上限+<Lv*1>',name='テンションマスタリーVo上限＋')
  self.assertEqual(d['status'],'structured');self.assertEqual(d['effects'][0]['source_notation'],'extra_particle_de')
  self.assertEqual(self.get('support_skill','テンション最高時に一緒に行動するとでVocal上限+<Lv*1>',name='別のスキル')['status'],'unsupported')
 def test_private_prose_and_nonfinite_values_rejected(self):
  d=self.get('support_skill','プロデュース開始時に絆+<Lv*5>')
  d['effects'][0]['raw_text']='private'
  with self.assertRaises(ValueError):validate_effect_details(d,set())
  del d['effects'][0]['raw_text'];d['effects'][0]['formula']['coefficient']=float('nan')
  with self.assertRaises(ValueError):validate_effect_details(d,set())

class LiveEffectExtensionTests(unittest.TestCase):
 def setUp(self):
  from src.skill_conditions_v2 import context
  self.ctx=context([{'idol_name':'小宮果穂','unit_name':'放課後クライマックスガールズ'},{'idol_name':'園田智代子','unit_name':'放課後クライマックスガールズ'}])
 def parse(self,text,**extras):
  doc=effect_details(dict(kind='panel_live',effect_private=text,**extras),self.ctx['idols'],self.ctx)
  validate_effect_details(doc,self.ctx['idols'],self.ctx);return doc['effects']
 def test_mechanic_conditions_never_leak_backwards_or_into_next_scope(self):
  es=self.parse('Vocal4倍アピール(Plus)[2ターン以前放クラ全員がライブに参加している場合]Vocal40%UP[3ターン]/Dance20%UP[5ターン](Refrain)[注目度DOWNが3個以上付与されている場合]リフレイン[2ターン前]')
  self.assertNotIn('activation_condition',es[0])
  self.assertEqual(es[1]['activation_condition'],es[2]['activation_condition'])
  self.assertEqual(es[1]['activation_condition']['expression']['operator'],'all')
  self.assertEqual(es[3]['activation_condition']['expression']['status'],'注目度DOWN')
  self.assertEqual((es[3]['metric'],es[3]['value'],es[3]['unit']),('refrain',2,'points'))
  self.assertNotIn('turns',es[3])
 def test_unknown_condition_is_explicit_and_no_raw_prose_is_exported(self):
  es=self.parse('Vocal4倍アピール(Plus)[未知の条件]Dance40%UP[3ターン]')
  self.assertEqual(es[1]['activation_condition'],{'status':'unsupported'})
  self.assertNotIn('未知',str(es))
 def test_adjacent_scaling_and_audience_and_order_are_individual(self):
  es=self.parse('必ず最後に全観客にDance最大5.5倍アピール[注目度が低いほど効果UP]/Vocal3倍アピール[興味無視]/Dance120%UP[4ターン]')
  self.assertEqual(es[0]['restrictions'],{'scaling':'attention_descending'})
  self.assertEqual(es[0]['appeal_order'],'last')
  self.assertEqual(es[1]['restrictions'],{'ignore_interest':True})
  self.assertNotIn('restrictions',es[2])
 def test_instant_recovery_and_gauge_never_borrow_duration(self):
  es=self.parse('メンタル20%回復/思い出ゲージ15%UP/パッシブスキル発動率30%UP[3ターン]/回避率30%UP[4ターン]/交換数UP[2回]')
  self.assertEqual([e['metric'] for e in es],['mental_recovery','memory_gauge_gain','rate_up','rate_up','exchange_count_up'])
  self.assertNotIn('turns',es[0]);self.assertNotIn('turns',es[1]);self.assertNotIn('turns',es[4])
  self.assertEqual(es[3]['targets'],['リアクション回避率'])
  self.assertEqual([e['turns'] for e in es[2:4]],[3,4])
 def test_cost_relax_and_passive_boost_have_distinct_semantics(self):
  es=self.parse('自身のメンタルを30%減らし/リラックス効果1%付与[4ターン]/パッシブスキル10%強化[3ターン]')
  self.assertEqual([e['metric'] for e in es],['mental_cost','relax','passive_boost'])
  self.assertEqual([e['targets'] for e in es],[['メンタル'],['リラックス'],['パッシブスキル']])
 def test_bracketed_unknown_text_does_not_become_an_effect(self):
  self.assertEqual(self.parse('[説明:メンタル20%回復]/(Plus)[未知Vocal3倍アピール]'),[])
 def test_memory_link_condition_stays_in_its_slot(self):
  doc=effect_details({'kind':'memory_appeal','effect_private':'Vocal3倍アピール','link_appeal_private':'(Link)[小宮果穂がライブに参加している場合]Dance5倍アピール'},self.ctx['idols'],self.ctx)
  es=doc['effects'];self.assertEqual(es[1]['scope'],'memory_link')
  self.assertNotIn('activation_condition',es[0]);self.assertEqual(es[1]['activation_condition']['expression']['value'],'小宮果穂')
 def test_mechanic_case_and_known_typo_follow_acquisition_parser(self):
  es=self.parse('Vocal4倍アピール(link)Dance20%UP[2ターン](gRoWuP)[2ターン以前]Vocal40%UP[3ターン](Reflain)リフレイン[1ターン前]')
  self.assertEqual([e['scope'] for e in es],['base','link','grow','refrain'])
 def test_invalid_condition_and_private_fields_fail_validation(self):
  import copy
  doc={'status':'partial','effects':self.parse('(Plus)[2ターン以前]Vocal40%UP[3ターン]')}
  for mutate in [lambda e:e['activation_condition'].update(private_text='全文'),lambda e:e.update(appeal_order='last'),lambda e:e['activation_condition']['expression'].update(value=-1)]:
   bad=copy.deepcopy(doc);mutate(bad['effects'][0])
   with self.assertRaises(ValueError):validate_effect_details(bad,self.ctx['idols'],self.ctx)

if __name__=='__main__':unittest.main()
