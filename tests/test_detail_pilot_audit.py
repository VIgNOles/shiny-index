"""Regression for complete panel comparisons across the two coordinate systems."""
import unittest
from copy import deepcopy
from scripts.verify_detail_pilot import compare_card


class DetailPilotAuditTests(unittest.TestCase):
    def test_end_of_span_cache_coordinates_do_not_skip_skill_checks(self):
        cached={'card_id':'test','card_kind':'P','panel_nodes':[
            {'sp':20,'panel_column':5,'kind':'panel_live','name':'技能甲','effect_private':'合成効果',
             'mechanics':['link'],'unlock_star':None}], 'mb_live':[], 'memory_appeals':[]}
        actual={'card_id':'test','card_kind':'P','panel_nodes':[
            {'sp':20,'source_positions':[{'column':5}], 'kind':'panel_live','name':'技能甲',
             'effect_private':'合成 効果','mechanics':['link'],'unlock_star':None}],
            'mb_live':[],'memory_appeals':[]}
        report=compare_card(cached,actual)
        self.assertEqual(report['differences_private'],[])
        self.assertGreaterEqual(report['checked_fields'],10)
        changed=deepcopy(actual)
        changed['panel_nodes'][0]['mechanics']=['plus']
        self.assertEqual([d['field'] for d in compare_card(cached,changed)['differences_private']],['panel[0].mechanics'])

    def test_shared_memory_cell_gap_requires_html_inheritance_proof(self):
        cached={'card_id':'test','card_kind':'P','panel_nodes':[],'mb_live':[],'memory_appeals':[
            {'level':2,'name':'記憶','effect_private':'効果','link_appeal_private':None,'charge_appeal_private':None}]}
        actual={'card_id':'test','card_kind':'P','panel_nodes':[],'mb_live':[],'memory_appeals':[
            {'level':2,'name':'記憶','effect_private':'効果','link_appeal_private':'共有Link','charge_appeal_private':None,
             'source_positions':[{'row':3},{'row':3},{'row':2}]}]}
        report=compare_card(cached,actual)
        self.assertEqual(report['differences_private'],[])
        self.assertEqual(len(report['cache_inheritance_gaps']),1)
        changed=deepcopy(actual)
        changed['memory_appeals'][0]['source_positions'][2]['row']=3
        self.assertEqual(len(compare_card(cached,changed)['differences_private']),1)


if __name__=='__main__':
    unittest.main()
