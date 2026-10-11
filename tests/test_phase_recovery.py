import copy
import unittest
from src.skill_effects import live, validate_effect_details


class PhaseRecoveryTests(unittest.TestCase):
 def parse(self,text):
  facts=live(text)
  validate_effect_details({'status':'partial' if facts else 'unsupported','effects':facts},())
  return facts

 def test_phase_start_own_duration_and_instant_recovery_are_distinct(self):
  es=self.parse('Dance2.5倍アピール/アピールフェイズ開始時メンタル5%回復[3ターン]/メンタル10%回復')
  self.assertEqual([e['metric'] for e in es],['appeal','mental_recovery','mental_recovery'])
  self.assertEqual((es[1]['value'],es[1]['turns'],es[1]['trigger']),(5,3,'appeal_phase_start'))
  self.assertNotIn('trigger',es[2]);self.assertNotIn('turns',es[2])
  self.assertNotIn('starts_next_turn',es[1]);self.assertNotIn('recipient',es[1])

 def test_known_particle_spelling(self):
  e=self.parse('Visual2.5倍アピール/アピールフェイズ開始時に メンタル4%回復[5ターン]')[1]
  self.assertEqual((e['value'],e['turns'],e['trigger']),(4,5,'appeal_phase_start'))

 def test_explicit_recipient_and_marker_do_not_leak(self):
  es=self.parse('アピールフェイズ開始時自身のメンタル4%回復[5ターン](Link)アピールフェイズ開始時ライバルのメンタル2%回復[2ターン]/メンタル3%回復')
  self.assertEqual([(e['scope'],e.get('recipient'),e.get('turns')) for e in es],[('base','self',5),('link','rivals',2),('link',None,None)])

 def test_short_relax_has_existing_named_status_timing(self):
  e=self.parse('Dance2.3倍アピール/リラックス2%付与[3ターン]')[1]
  full=self.parse('リラックス効果2%付与[3ターン]')[0]
  self.assertEqual(e,full)
  self.assertEqual((e['metric'],e['value'],e['turns'],e['trigger'],e['starts_next_turn']),('relax',2,3,'appeal_phase_start',True))

 def test_missing_duration_unknown_prefix_and_bracketed_prose_rejected(self):
  for text in ['アピールフェイズ開始時メンタル5%回復','アピールフェイズ終了時メンタル5%回復[3ターン]','説明アピールフェイズ開始時メンタル5%回復[3ターン]','[説明:アピールフェイズ開始時メンタル5%回復[3ターン]]','リラックス2%付与']:
   with self.subTest(text=text):self.assertEqual(self.parse(text),[])

 def test_duration_cannot_be_borrowed_from_next_effect(self):
  es=self.parse('アピールフェイズ開始時メンタル5%回復/Dance50%UP[4ターン]')
  self.assertEqual([e['metric'] for e in es],['rate_up'])
  bad=copy.deepcopy(self.parse('アピールフェイズ開始時メンタル5%回復[3ターン]')[0]);bad.pop('turns')
  with self.assertRaises(ValueError):validate_effect_details({'status':'partial','effects':[bad]},())
