import copy,unittest
from src.detail_master import adopt,add_manual,empty,from_rows,table_rows,resolve
from src.indexer import digest

CID='00000000-0000-4000-8000-000000000001'

def candidate(kind='P'):
    c={'base_dataset_version':'v1-0000000000000000','card_coverage':[{'card_id':CID,'card_kind':kind,'status':'candidate_needs_review'}],
       'cards':[{'card_id':CID,'card_kind':kind,'card_title':'【実カード】','wiki_url':'https://wikiwiki.jp/shinycolors/【実カード】人物',
                'coverage':{'skill_panel':'extracted'},'fetched_at':'2026-10-09T04:00:00+00:00','source_sha256':'a'*64,'panel_nodes':[
                {'kind':'panel_live','name':'スキル','sp':20,'effect_private':'Vocal2倍アピール','mechanics':['link'],
                 'source_positions':[{'table':2,'row':2,'column':1,'section_anchor':'skills'}]}]}]}
    c['content_hash']=digest(c);return c

def rehash(c):c['content_hash']=digest({k:v for k,v in c.items() if k!='content_hash'});return c

class DetailMasterTests(unittest.TestCase):
    def test_replay_and_reorder_preserve_ids(self):
        c=candidate();m=adopt(empty(c['base_dataset_version']),c)
        c['cards'][0]['panel_nodes'][0].update(effect_private='Vocal3倍アピール',source_positions=[{'table':2,'row':9,'column':1}]);rehash(c)
        updated=adopt(m,c)
        self.assertEqual(updated['registry'][0]['detail_id'],m['registry'][0]['detail_id'])
        self.assertEqual(updated['registry'][0]['source']['effect_private'],'Vocal3倍アピール')
        self.assertEqual(adopt(updated,c),updated)

    def test_manual_override_survives(self):
        c=candidate();m=adopt(empty(c['base_dataset_version']),c)
        r=m['registry'][0];r.update(override={'name':'修正した名称'},reason='表示訂正',source_ref=c['cards'][0]['wiki_url'],updated_at='2026-10-09T04:00:00Z')
        self.assertEqual(resolve(adopt(m,c))[0]['items'][0]['name'],'修正した名称')
        self.assertEqual(from_rows(table_rows(m)),m)

    def test_manual_then_fetched_same_skill_merges(self):
        c=candidate();first=copy.deepcopy(c);first['cards'][0]['panel_nodes']=[];rehash(first)
        m=adopt(empty(c['base_dataset_version']),first)
        m=add_manual(m,CID,c['cards'][0]['panel_nodes'][0],'実データを先行登録',c['cards'][0]['wiki_url'],'2026-10-09T04:00:00Z')
        updated=adopt(m,c)
        self.assertEqual(len(updated['registry']),1)
        self.assertEqual(updated['registry'][0]['detail_id'],m['registry'][0]['detail_id'])

    def test_missing_old_skill_rejected(self):
        c=candidate();m=adopt(empty(c['base_dataset_version']),c)
        c['cards'][0]['panel_nodes']=[];rehash(c)
        with self.assertRaisesRegex(ValueError,'disappeared'):adopt(m,c)

    def test_source_columns_cannot_be_edited(self):
        c=candidate();m=adopt(empty(c['base_dataset_version']),c);t=table_rows(m)
        t['詳細項目'][1][3]='取得列を書換'
        with self.assertRaisesRegex(ValueError,'fetched columns'):from_rows(t)

    def test_manual_requires_evidence(self):
        c=candidate();m=adopt(empty(c['base_dataset_version']),c);t=table_rows(m);t['詳細項目'][1][6]='修正'
        with self.assertRaisesRegex(ValueError,'requires reason'):from_rows(t)

    def test_support_unique_ability_is_valid(self):
        c=candidate('S');c['cards'][0]['panel_nodes'][0]['kind']='unique_ability';rehash(c)
        self.assertEqual(adopt(empty(c['base_dataset_version']),c)['registry'][0]['source']['kind'],'unique_ability')

    def test_p_does_not_accept_s_possessed_skill(self):
        c=candidate();c['cards'][0]['panel_nodes'][0]['kind']='possessed_live';rehash(c)
        with self.assertRaisesRegex(ValueError,'P/S'):adopt(empty(c['base_dataset_version']),c)

    def test_ambiguous_duplicates_have_separate_cell_ids(self):
        c=candidate();node=copy.deepcopy(c['cards'][0]['panel_nodes'][0]);node['source_positions'][0]['row']=4
        c['cards'][0]['panel_nodes'].append(node);rehash(c)
        m=adopt(empty(c['base_dataset_version']),c)
        self.assertEqual(len({r['detail_id'] for r in m['registry']}),2)
        self.assertEqual(adopt(m,c),m)

    def test_manual_cap_effect_updates_structured_value(self):
        c=candidate();n=c['cards'][0]['panel_nodes'][0];n.update(kind='cap_increase',name='上限UP',effect_private='Visual 上限+50',cap_targets=['Visual'],cap_delta=50);rehash(c)
        m=adopt(empty(c['base_dataset_version']),c);row=m['registry'][0]
        row.update(override={'effect_private':'Vocal & Visual 上限+100'},reason='訂正',source_ref='Wiki',updated_at='2026-10-09T04:00:00Z')
        item=resolve(m)[0]['items'][0];self.assertEqual(item['cap_delta'],100);self.assertEqual(item['cap_targets'],['Vocal','Visual'])

    def test_manual_live_effect_updates_tags_without_erasing_explicit_override(self):
        c=candidate();m=adopt(empty(c['base_dataset_version']),c);row=m['registry'][0]
        row.update(override={'effect_private':'Vocal3倍アピール (Plus)'},reason='訂正',source_ref='Wiki',updated_at='2026-10-09T04:00:00Z')
        self.assertEqual(resolve(m)[0]['items'][0]['mechanics'],['plus'])
        row['override']['mechanics']=['change']
        self.assertEqual(resolve(m)[0]['items'][0]['mechanics'],['change'])

    def test_hash_tampering_rejected(self):
        c=candidate();c['cards'][0]['panel_nodes'][0]['sp']=999
        with self.assertRaisesRegex(ValueError,'hash'):adopt(empty(c['base_dataset_version']),c)

if __name__=='__main__':unittest.main()
