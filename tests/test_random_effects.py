import copy
import unittest
from src.random_effects import candidate, note_pool, resolve_pools, unavailable_pool, validate_pool
from src.skill_effects import effect_details, validate_effect_details

IDS = {'小宮果穂', '七草にちか'}
POS = lambda t: [dict(table=t, row=1, column=1, section_anchor='template_3')]
def note(t, text, name='ランダム効果付与'):
    return dict(name=name, effect_private=text, source_positions=POS(t))
def item(t, kind='panel_live', did='normal'):
    return dict(detail_id=did, kind=kind, effect_private='Vocal3倍アピール/ランダム効果2個付与', source_positions=POS(t))

class RandomEffectsTests(unittest.TestCase):
    def test_whole_candidates_separate_kinds_values_and_durations(self):
        p=note_pool(note(3,'以下の中からランダムで効果が付与される ・Vocal40%UP[4ターン] ・パッシブスキル10%強化[3ターン] ・交換数UP[1回]'),IDS)
        self.assertEqual([o['kind'] for o in p['options']],['rate_up','passive_boost','exchange_count_up'])
        self.assertNotIn('turns',p['options'][2]);self.assertEqual(p['selection_probability'],'unknown')
        for s in ['Vocal40%UP[4ターン]謎条件','最大Vocal40%UP[4ターン]','Vocal40%UP[4～5ターン]']:
            self.assertIsNone(candidate(s,IDS))
    def test_person_bonus_accepts_confirmed_ratio_alias_and_requires_known_name(self):
        o=candidate('小宮 果穂のアピール倍率0.1倍UP[5ターン]',IDS)
        self.assertEqual((o['value'],o['unit'],o['idols']),(0.1,'multiplier',['小宮果穂']))
        self.assertEqual(candidate('七草 にちかのアピール倍率0.2UP[4ターン]',IDS),candidate('七草 にちかのアピール倍率0.2倍UP[4ターン]',IDS))
        self.assertIsNone(candidate('七草にちかのアピール値0.2UP[4ターン]',IDS))
        self.assertIsNone(candidate('七草にちかのアピール倍率0.2%UP[4ターン]',IDS))
        self.assertIsNone(candidate('七草にちかのアピール倍率0.2UP',IDS))
        self.assertIsNone(candidate('架空人物のアピール倍率0.1倍UP[5ターン]',IDS))
    def test_unknown_candidate_count_preserves_partial_without_prose(self):
        p=note_pool(note(3,'・七草にちかのアピール値0.2UP[4ターン]'),IDS)
        self.assertEqual((p['status'],p['unstructured_count'],p['options']),('partial',1,[]))
    def test_roots_three_confirmed_alternatives_preserve_duration_and_unknown_odds(self):
        ids={'七草にちか','緋田美琴','斑鳩ルカ'}
        text='・七草 にちかのアピール倍率0.2UP[4ターン] ・緋田 美琴のアピール倍率0.2UP[4ターン] ・斑鳩 ルカのアピール倍率0.2UP[4ターン] 同一の効果が付与される場合もあり'
        p=note_pool(note(3,text),ids)
        self.assertEqual((p['status'],p['unstructured_count']),('structured',0))
        self.assertEqual({o['idols'][0] for o in p['options']},ids)
        self.assertTrue(all(o['value']==0.2 and o['unit']=='multiplier' and o['turns']==4 for o in p['options']))
        self.assertEqual(p['selection_probability'],'unknown');self.assertTrue(p['same_option_can_repeat'])

    def test_optional_intro_and_exact_explanatory_trailer(self):
        p=note_pool(note(3,'・Dance40%UP[4ターン] ・フレキシブル[1ターン] 白・架・祝・幻+の場合、同一の効果が付与される場合もあり'),IDS)
        self.assertEqual(p['unstructured_count'],0);self.assertEqual(len(p['options']),2)
    def test_resurrection_keeps_mental_zero_turns_and_uses(self):
        o=candidate('リザレクション効果30%付与[3ターン][1回]',IDS)
        self.assertEqual((o['trigger'],o['turns'],o['uses']),('mental_zero',3,1))
    def test_normal_and_mb_tables_stay_separate_even_heading_omits_mb(self):
        card=dict(items=[item(2),item(4,'mb_live','mb')],skill_notes_private=[
            note(3,'・Vocal40%UP[4ターン]'),note(5,'・Vocal80%UP[4ターン]','ランダム効果付与*1')])
        p=resolve_pools(card,IDS)
        self.assertEqual(p['normal']['options'][0]['value'],40);self.assertEqual(p['mb']['options'][0]['value'],80)
        card['skill_notes_private'][0]['name']='[MB]ランダム効果付与'
        with self.assertRaises(ValueError):resolve_pools(card,IDS)
    def test_duplicate_or_ambiguous_pool_fails_closed(self):
        card=dict(items=[item(2)],skill_notes_private=[note(3,'・Vocal40%UP[4ターン]')]*2)
        with self.assertRaises(ValueError):resolve_pools(card,IDS)
        card['skill_notes_private']=card['skill_notes_private'][:1];card['items'].append(item(2,'mb_live','mb'))
        with self.assertRaises(ValueError):resolve_pools(card,IDS)
    def test_candidate_is_nested_not_an_additional_guaranteed_rate(self):
        p=note_pool(note(3,'・Vocal40%UP[4ターン]'),IDS)
        d=effect_details(dict(kind='panel_live',effect_private='Vocal3倍アピール/ランダム効果2個付与(Link)Dance20%UP[3ターン]'),IDS,random_pool=p)
        validate_effect_details(d,IDS)
        self.assertEqual([e['metric'] for e in d['effects']],['appeal','random_grant','rate_up'])
        self.assertEqual(d['effects'][1]['scope'],'base');self.assertNotIn('random_pool',d['effects'][2])
        self.assertEqual(d['effects'][2]['targets'],['Dance'])
    def test_missing_pool_does_not_invent_options(self):
        d=effect_details(dict(kind='panel_live',effect_private='ランダム効果2個付与'),IDS)
        self.assertEqual(d['effects'][0]['random_pool'],unavailable_pool());validate_effect_details(d,IDS)
    def test_strict_public_allowlist_and_no_invented_probability(self):
        p=note_pool(note(3,'・Vocal40%UP[4ターン]'),IDS)
        for change in [lambda v:v.update(raw_text='原文'),lambda v:v.update(selection_probability=0.5),
                       lambda v:v['options'][0].update(raw_text='原文'),
                       lambda v:v['options'][0].update(turns=0),
                       lambda v:v['options'][0].update(idols=['小宮果穂']),
                       lambda v:v['options'].append(copy.deepcopy(v['options'][0])),
                       lambda v:v['source_positions'][0].update(row=-1)]:
            bad=copy.deepcopy(p);change(bad)
            with self.assertRaises(ValueError):validate_pool(bad,IDS)
    def test_grant_bounds_and_pool_on_other_metric_rejected(self):
        for text in ['ランダム効果0個付与','ランダム効果101個付与']:
            with self.assertRaises(ValueError):validate_effect_details(effect_details(dict(kind='panel_live',effect_private=text),IDS),IDS)
        d=effect_details(dict(kind='panel_live',effect_private='Vocal3倍アピール'),IDS)
        d['effects'][0]['random_pool']=unavailable_pool()
        with self.assertRaises(ValueError):validate_effect_details(d,IDS)

if __name__=='__main__':unittest.main()

