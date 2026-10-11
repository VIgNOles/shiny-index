import unittest
from src.skill_effects import effect_details, validate_effect_details
from src.skill_conditions_v2 import context


class MentalSpentEffectTests(unittest.TestCase):
    def setUp(self):
        self.ctx=context([{'idol_name':'白瀬咲耶','unit_name':'アンティーカ'}])
    def doc(self,text,kind='panel_live',**extra):
        d=effect_details(dict(kind=kind,effect_private=text,**extra),self.ctx['idols'],self.ctx)
        validate_effect_details(d,self.ctx['idols'],self.ctx)
        return d
    def scaled(self,text):
        return [e for e in self.doc(text)['effects'] if e.get('restrictions',{}).get('scaling')=='mental_spent']
    def test_adjacent_cost_maximum_buff_and_bracket_order(self):
        for suffix in ('[減少値が多いほど効果UP][4ターン]','[4ターン][減少値が多いほど効果UP]'):
            es=self.doc('Vi4倍アピール/自身のメンタルを20%減らし、Vi最大120%UP'+suffix)['effects']
            self.assertEqual([e['metric'] for e in es],['appeal','mental_cost','rate_up'])
            self.assertEqual((es[1]['value'],es[1]['recipient']),(20,'self'))
            self.assertEqual((es[2]['targets'],es[2]['value'],es[2]['turns'],es[2]['maximum']),(['Visual'],120,4,True))
            self.assertEqual(es[2]['restrictions'],{'scaling':'mental_spent'})
            self.assertNotIn('recipient',es[2]);self.assertTrue(all(e['restriction_status']=='partial' for e in es))
    def test_known_attribute_aliases_are_normalized(self):
        for alias,target in [('Vo','Vocal'),('Da','Dance'),('Vi','Visual'),('ボーカル','Vocal'),('ダンス','Dance'),('ビジュアル','Visual')]:
            e=self.scaled('自身のメンタルを30%減らし、'+alias+'最大80%UP[減少値が多いほど効果UP][3ターン]')[0]
            self.assertEqual(e['targets'],[target])
    def test_scope_and_other_durations_are_not_inherited(self):
        es=self.doc('自身のメンタルを30%減らし、Da最大120%UP[減少値が多いほど効果UP][3ターン](Link)Vocal30%UP[5ターン]')['effects']
        self.assertEqual((es[1]['scope'],es[1]['turns']),('base',3))
        self.assertEqual((es[2]['scope'],es[2]['turns']),('link',5))
        self.assertNotIn('restrictions',es[2]);self.assertNotIn('maximum',es[2])
    def test_mb_and_memory_link_keep_own_slots(self):
        text='自身のメンタルを35%減らし、Dance最大240%UP[減少値が多いほど効果UP][5ターン]'
        es=self.doc(text,kind='mb_live')['effects'];self.assertEqual(es[1]['turns'],5)
        es=self.doc('Visual3倍アピール',kind='memory_appeal',link_appeal_private=text)['effects']
        self.assertEqual([e['scope'] for e in es],['base','memory_link','memory_link'])
        self.assertNotIn('restrictions',es[0])
    def test_explicit_grow_scaling_is_not_duplicated(self):
        es=self.doc('(Grow)[3ターン以前]自身のメンタルを30%減らし、Vocal最大80%UP[3ターン][減少値が多いほど効果UP]')['effects']
        self.assertEqual([e['metric'] for e in es],['mental_cost','rate_up'])
        self.assertEqual(es[1]['scope'],'grow')
        self.assertEqual(es[1]['activation_condition']['status'],'structured')
    def test_existing_grow_adjacent_restrictions_are_preserved(self):
        es=self.doc('(Grow)[3ターン以前]自身のメンタルを30%減らし、Vocal最大80%UP[3ターン][減少値が多いほど効果UP][興味無視]')['effects']
        self.assertEqual(es[1]['restrictions'],{'scaling':'mental_spent','ignore_interest':True})
        self.assertEqual(len(es),2)
    def test_unknown_missing_or_distant_context_never_opens_maximum(self):
        for text in [
            'Vocal最大120%UP[3ターン]',
            '自身のメンタルを30%減らし/Vocal最大120%UP[減少値が多いほど効果UP][3ターン]',
            '自身のメンタルを30%減らし、Vocal最大120%UP[3ターン]',
            '自身のメンタルを30%減らし、Vocal最大120%UP[メンタルが多いほど効果UP][3ターン]',
            '未知自身のメンタルを30%減らし、Vocal最大120%UP[減少値が多いほど効果UP][3ターン]',
            '[条件:自身のメンタルを30%減らし、Vocal最大120%UP[減少値が多いほど効果UP][3ターン]]',
            '自身のメンタルを101%減らし、Vocal最大120%UP[減少値が多いほど効果UP][3ターン]',
            '自身のメンタルを0%減らし、Vocal最大120%UP[減少値が多いほど効果UP][3ターン]',
            '自身のメンタルを30%減らし、Vocal最大120%UP[減少値が多いほど効果UP][3～5ターン]',
        ]:
            self.assertEqual(self.scaled(text),[],text)
    def test_duration_bounds_are_validated_before_publication(self):
        for turns in (0,101):
            with self.assertRaises(ValueError):
                self.doc('自身のメンタルを30%減らし、Dance最大80%UP[減少値が多いほど効果UP]['+str(turns)+'ターン]')

if __name__=='__main__':unittest.main()

