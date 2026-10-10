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
  for s in ['Vocal20%UP[3～5ターン]','Vocal最大300%UP[4ターン]','パッシブスキル発動率10%UP[3ターン]']:
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
if __name__=='__main__':unittest.main()
