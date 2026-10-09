"""Synthetic fixtures for HTML integrity, spans, and skill-category boundaries."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from bs4 import BeautifulSoup
from src.card_details import extract_html, table_grid, transform_run
from scripts.transform_detail_html import save_candidate
import scripts.collect_one as limited
from src.indexer import write, read

URL = 'https://wikiwiki.jp/shinycolors/【試験】試験アイドル'
CARD = {'card_id': 'test-id', 'card_kind': 'P', 'card_title': '【試験】',
        'idol_name': '試験アイドル', 'wiki_url': URL}
PANEL = '''<table><tr><th>SP</th><th colspan="4">凡例</th></tr>
<tr><th rowspan="2">30</th><th colspan="2">技能<span>甲</span></th><th colspan="2">Vocal上限UP (☆3)</th></tr>
<tr><td colspan="2" style="background-color:gainsboro">Vocal2倍<br>(Link)追撃</td><td colspan="2">Vocal上限+100</td></tr></table>'''
MEMORY = '''<table><tr><th>スキル名</th><th>効果</th><th>リンクアピール</th></tr>
<tr><th>記憶甲</th><td>思い出アピール[Lv1]</td><td rowspan="2">合成Link効果</td></tr>
<tr><th>記憶乙</th><td>思い出アピール[Lv2]</td></tr></table>'''


def fixture(panel=PANEL, memory=MEMORY, extra=''):
    return f'''<html><head><title>【試験】試験アイドル - Wiki</title>
    <link rel="canonical" href="{URL}"></head><body><div id="content">
    <h2>スキルパネル<a name="panel"></a></h2>{panel}{extra}
    <h2>思い出アピール<a name="memory"></a></h2>{memory}
    <h2>特徴</h2><p>(Plus)(Grow)は無関係な説明</p></div></body></html>'''.encode()


class DetailHtmlTests(unittest.TestCase):

    def test_legacy_cap_up_plus_requires_matching_heading(self):
        panel=PANEL.replace('Vocal上限+100','Vocal上限UP+100')
        node=extract_html(fixture(panel=panel),CARD)['panel_nodes'][1]
        self.assertEqual((node['kind'],node['cap_targets'],node['cap_delta']),('cap_increase',['Vocal'],100))
        self.assertEqual(node['effect_private'],'Vocal上限UP+100')
        for invalid in ('Dance上限UP+100','Vocal上限UP++100','Vocal上限UP+100 extra'):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                extract_html(fixture(panel=PANEL.replace('Vocal上限+100',invalid)),CARD)

    def test_mb_random_options_attach_only_to_matching_mb_skills(self):
        mb='<table><tr><th>メモリーブースト</th></tr><tr><th>[MB]技能甲(2/5)</th></tr><tr><td style="background-color:gainsboro">Vocal3倍/ランダム効果3個付与(Plus)</td></tr></table>'
        supplement='<table><tr><th>[MB]ランダム効果付与</th></tr><tr><td>以下の中からランダムで効果が付与される<br>複数付与する場合、同一の効果が付与される場合もあり</td></tr><tr><th>技能甲</th></tr><tr><td>・Vocal20%UP[5ターン]<br>・Vocal40%UP[5ターン]</td></tr></table>'
        card=extract_html(fixture(extra=mb+supplement),CARD)
        self.assertNotIn('random_effect_options',card['panel_nodes'][0])
        self.assertEqual(card['panel_nodes'][0]['mechanics'],['link'])
        node=card['mb_live'][0]
        self.assertEqual(node['mechanics'],['plus'])
        self.assertEqual([v['value'] for v in node['random_effect_options']],[20,40])
        self.assertEqual(node['random_effect_options'][0]['turns'],5)
        self.assertEqual(len(node['source_positions']),4)
        for altered in (supplement.replace('<th>技能甲</th>','<th>別技能</th>'),
                        supplement.replace('同一の効果が付与される場合もあり','未知の条件'),
                        supplement.replace('・Vocal40%UP[5ターン]','・未知効果'),
                        supplement.replace('・Vocal40%UP[5ターン]','・Vocal20%UP[5ターン]')):
            with self.subTest(altered=altered),self.assertRaises(ValueError):
                extract_html(fixture(extra=mb+altered),CARD)
        with self.assertRaisesRegex(ValueError,'ambiguous'):
            extract_html(fixture(extra=mb+mb+supplement),CARD)

    def test_cap_line_break_requires_independent_heading_agreement(self):
        panel = PANEL.replace('Vocal上限UP (☆3)', 'Vocal & Dance & Visual上限UP (☆3)').replace('Vocal上限+100', 'Vocal & Dance<br>Visual 上限+25')
        cap = extract_html(fixture(panel=panel), CARD)['panel_nodes'][1]
        self.assertEqual(cap['cap_targets'], ['Vocal', 'Dance', 'Visual'])
        self.assertEqual(cap['cap_delta'], 25)
        self.assertEqual(cap['effect_private'], 'Vocal & Dance Visual 上限+25')
        self.assertIn('original cell preserved', cap['cap_parse_note_private'])
        for old, new in [('Dance<br>Visual', 'Dance Visual'),
                         ('Dance & Visual上限UP', 'Dance上限UP'),
                         ('Dance<br>Visual', 'Dance<br>Dance'),
                         ('Dance<br>Visual', 'Dance<br>unknown')]:
            with self.subTest(new=new), self.assertRaises(ValueError):
                extract_html(fixture(panel=panel.replace(old, new)), CARD)

    def test_generated_diagram_keeps_children_separate_and_checks_parent_names(self):
        from src.card_details import parse_generated_live
        diagram = '<table><tr><th colspan="3">ライブスキル生成(連係図)</th></tr>'
        diagram += '<tr><th>root A</th><th rowspan="2">初 手</th><th>root B</th></tr>'
        diagram += '<tr><td style="background-color:gainsboro">ライブスキル生成[child A](Plus)</td><td style="background-color:gainsboro">ライブスキル生成[child B](Link)</td></tr>'
        diagram += '<tr><td>↓</td><td>↓</td><td>↓</td></tr>'
        diagram += '<tr><th>child A</th><th rowspan="2">1 連</th><th>child B</th></tr>'
        diagram += '<tr><td style="background-color:gainsboro">Vocal7倍(change)</td><td style="background-color:gainsboro">Vocal6倍</td></tr></table>'
        roots = [{'kind':'panel_live','name':'root A','effect_private':'ライブスキル生成[child A](Plus)'},
                 {'kind':'panel_live','name':'root B','effect_private':'ライブスキル生成[child B](Link)'}]
        parse = lambda markup: parse_generated_live(3,BeautifulSoup(markup,'html.parser').table,'panel',roots)
        generated = parse(diagram)
        self.assertEqual(len(generated),2)
        self.assertEqual(generated[0]['generated_from_name'],'root A')
        self.assertEqual(generated[0]['mechanics'],['change'])
        self.assertEqual(generated[1]['mechanics'],[])
        self.assertIsNone(generated[0]['sp'])
        self.assertEqual(generated[0]['source_positions'][0],{'table':3,'row':5,'column':1,'section_anchor':'panel'})
        for old,new,message in [('child B</th>','child A</th>','Duplicate'),('初 手','2連','stage label'),
                                ('↓','→','connector'),('child A</th>','unrelated</th>','parent/target'),
                                ('Vocal7倍(change)','ライブスキル生成[next]','unresolved final')]:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError,message):
                parse(diagram.replace(old,new))

    def test_compact_generated_mb_context_and_target_coverage(self):
        from src.card_details import parse_compact_generated
        html='<table><tr><th colspan="2">[MB]生成されるライブスキル</th></tr><tr><th>[MB]child A</th><th>[MB]child B</th></tr><tr><td style="background-color:gainsboro">Dance5倍(change)</td><td style="background-color:gainsboro">Dance6倍</td></tr></table>'
        parents=[{'kind':'mb_live','name':'[MB]root(2/5)','effect_private':'ライブスキル生成[child A]'},
                 {'kind':'mb_live','name':'[MB]root+(4/5)','effect_private':'ライブスキル生成[child B]'}]
        parse=lambda value:parse_compact_generated(4,BeautifulSoup(value,'html.parser').table,'panel',parents,memory_boost=True)
        items=parse(html);self.assertEqual(len(items),2);self.assertEqual(items[0]['generation_origin_kind'],'mb_live')
        self.assertEqual(items[0]['mechanics'],['change']);self.assertIsNone(items[0]['sp'])
        for old,new,error in [('[MB]child A','child A','MB context'),('child B','unknown','parent ambiguous'),('Dance6倍','ライブスキル生成[next]','unresolved')]:
            with self.subTest(error=error),self.assertRaisesRegex(ValueError,error):parse(html.replace(old,new))

    def test_compact_generated_shared_target_keeps_both_explicit_parents_once(self):
        from src.card_details import parse_compact_generated
        html='<table><tr><th>生成されるライブスキル</th></tr><tr><th>child</th></tr><tr><td style="background-color:gainsboro">Visual5倍(change)</td></tr></table>'
        parents=[{'kind':'panel_live','name':'root','effect_private':'ライブスキル生成[child]'},
                 {'kind':'panel_live','name':'root+(☆4)','effect_private':'ライブスキル生成[child]'}]
        parse=lambda value:parse_compact_generated(5,BeautifulSoup(html,'html.parser').table,'panel',value)
        records=parse(parents)
        self.assertEqual(len(records),1)
        self.assertEqual(records[0]['generated_from_names'],['root','root+(☆4)'])
        self.assertEqual(records[0]['generated_from_name'],'root')
        self.assertEqual(records[0]['mechanics'],['change'])
        for invalid in [[],[parents[0],dict(parents[0])],[dict(parents[0],kind='mb_live')]]:
            with self.subTest(invalid=invalid),self.assertRaisesRegex(ValueError,'parent ambiguous'):
                parse(invalid)

    def test_generated_skill_footnote_is_evidence_not_part_of_target_name(self):
        from src.card_details import parse_compact_generated
        note='<a class="note_super tooltip" id="notetext_1">*1</a>'
        html='<table><tr><th>[MB]生成されるライブスキル</th></tr><tr><th>[MB]child'+note+'</th></tr><tr><td style="background-color:gainsboro">Dance5倍(Plus)</td></tr></table>'
        parent=[{'kind':'mb_live','name':'[MB]root(4/5)','effect_private':'ライブスキル生成[child]'}]
        parse=lambda value:parse_compact_generated(7,BeautifulSoup(value,'html.parser').table,'panel',parent,memory_boost=True)
        child=parse(html)[0]
        self.assertEqual(child['name'],'[MB]child')
        self.assertEqual(child['generated_from_name'],'[MB]root(4/5)')
        self.assertEqual(child['mechanics'],['plus'])
        self.assertEqual(child['source_positions'][0],{'table':7,'row':2,'column':1,'section_anchor':'panel'})
        for old,new in [('note_super','ordinary'),('notetext_1','other_1'),('*1','literal')]:
            with self.subTest(old=old),self.assertRaisesRegex(ValueError,'parent ambiguous'):
                parse(html.replace(old,new))

    def test_mb_random_explanation_does_not_become_a_skill_or_hide_unknown_tables(self):
        mb='<table><tr><th>メモリーブースト</th></tr><tr><th>[MB]root(2/5)</th></tr><tr><td style="background-color:gainsboro">Visual5倍(Plus)</td></tr></table>'
        note='<table><tr><th>[MB]ランダム効果付与</th></tr><tr><td>未構造化の選択肢 (Refrain)</td></tr></table>'
        card=extract_html(fixture(extra=mb+note),CARD)
        self.assertEqual(len(card['mb_live']),1)
        self.assertEqual(card['mb_live'][0]['mb_stage'],2)
        self.assertEqual(card['mb_live'][0]['mechanics'],['plus'])
        self.assertNotIn('random_effect_options',card['mb_live'][0])
        self.assertEqual(card['skill_notes_private'][0]['name'],'[MB]ランダム効果付与')
        self.assertEqual(len(card['skill_notes_private'][0]['source_positions']),2)
        with self.assertRaisesRegex(ValueError,'MB stage/effect missing'):
            extract_html(fixture(extra=mb+note.replace('[MB]ランダム効果付与','[MB]未知の表')),CARD)
        with self.assertRaisesRegex(ValueError,'Unknown MB random-effect explanation'):
            extract_html(fixture(extra=mb+note.replace('未構造化の選択肢 (Refrain)','')),CARD)

    def test_mb_explanation_header_footnote_is_not_a_stage_or_effect(self):
        mb='<table><tr><th>メモリーブースト</th></tr><tr><th>[MB]root(2/5)</th></tr><tr><td style="background-color:gainsboro">Dance4倍(Refrain)</td></tr></table>'
        marker='<a class="note_super tooltip" id="notetext_1">*1</a>'
        note='<table><tr><th>[MB]ランダム効果付与'+marker+'</th></tr><tr><td>未構造化の説明</td></tr></table>'
        card=extract_html(fixture(extra=mb+note),CARD)
        self.assertEqual(len(card['mb_live']),1)
        self.assertEqual(card['mb_live'][0]['mechanics'],['refrain'])
        self.assertEqual(card['skill_notes_private'][0]['name'],'[MB]ランダム効果付与')
        self.assertEqual(card['skill_notes_private'][0]['effect_private'],'未構造化の説明')
        for old,new in [('note_super','ordinary'),('notetext_1','other'),('*1','literal')]:
            with self.subTest(new=new),self.assertRaisesRegex(ValueError,'MB stage/effect missing'):
                extract_html(fixture(extra=mb+note.replace(old,new)),CARD)

    def test_random_options_attach_to_exact_parent_and_preserve_evidence(self):
        from src.card_details import attach_random_options
        html='<table><tr><th colspan="2">ランダム効果付与</th></tr><tr><td colspan="2">以下の中からランダムで効果が付与される</td></tr><tr><th>root A</th><th>root B</th></tr><tr><td>・Vocal5%UP[3ターン] ・Vocal50%UP[3ターン]</td><td>・Dance100%UP[4ターン]</td></tr></table>'
        make=lambda:[{'kind':'panel_live','name':'root A (☆4)','effect_private':'ランダム効果1個付与','source_positions':[]},
                     {'kind':'panel_live','name':'root B','effect_private':'ランダム効果1個付与','source_positions':[]}]
        nodes=make();attach_random_options(8,BeautifulSoup(html,'html.parser').table,'panel',nodes)
        self.assertEqual([x['value'] for x in nodes[0]['random_effect_options']],[5,50])
        repeated=html.replace('以下の中からランダムで効果が付与される','以下の中からランダムで効果が付与される<br>複数付与する場合、同一の効果が付与される場合もあり')
        repeated_nodes=make();attach_random_options(8,BeautifulSoup(repeated,'html.parser').table,'panel',repeated_nodes)
        self.assertEqual(repeated_nodes[0]['random_effect_options'],nodes[0]['random_effect_options'])
        self.assertEqual(nodes[1]['random_effect_options'][0]['turns'],4)
        self.assertEqual(nodes[0]['source_positions'][0]['row'],3)
        for old,new,error in [('root B','unknown','parent ambiguous'),('Dance100%UP','未対応効果','Unknown random-effect option')]:
            with self.subTest(error=error),self.assertRaisesRegex(ValueError,error):attach_random_options(8,BeautifulSoup(html.replace(old,new),'html.parser').table,'panel',make())

    def test_explanation_table_is_private_and_does_not_add_live_tags(self):
        note='<table><tr><th>付与効果甲</th></tr><tr><td>合成の説明 (Plus)</td></tr></table>'
        card=extract_html(fixture(extra=note),CARD)
        self.assertEqual(len(card['panel_nodes']),2)
        self.assertEqual(card['skill_notes_private'][0]['name'],'付与効果甲')
        self.assertEqual(card['panel_nodes'][0]['mechanics'],['link'])
        self.assertEqual(len(card['skill_notes_private'][0]['source_positions']),2)
        random_note=extract_html(fixture(extra=note.replace('付与効果甲','ランダム効果付与')),CARD)
        self.assertEqual(random_note['skill_notes_private'][0]['name'],'ランダム効果付与')
        self.assertNotIn('random_effect_options',random_note['panel_nodes'][0])

    def test_dedicated_only_ability_has_unknown_sp_and_own_source(self):
        from src.card_details import match_abilities
        table=BeautifulSoup('<table><tr><th>能力甲</th><td>合成の効果</td></tr></table>','html.parser').table
        nodes=[];match_abilities(nodes,[(4,table,'ability')])
        self.assertEqual(nodes[0]['kind'],'unique_ability');self.assertIsNone(nodes[0]['sp'])
        self.assertEqual(nodes[0]['source_positions'][0]['section_anchor'],'ability')
        self.assertEqual(len(nodes),1)

    def test_separate_memory_link_condition_keeps_image_evidence_private(self):
        condition='<table><tr><th>思い出アピールリンク条件</th><td><img alt="Link_test.png" src="https://cdn.example.test/test.png"></td><td>相手甲</td></tr></table>'
        card=extract_html(fixture(memory=MEMORY+condition),CARD)
        self.assertEqual(len(card['memory_appeals']),2)
        info=card['memory_appeals'][0]['link_condition_private']
        self.assertEqual(info['image_refs_private'][0]['alt'],'Link_test.png')
        self.assertEqual(info['text_private'],['','相手甲'])
        self.assertEqual(len(info['source_positions']),3)
        self.assertEqual(info,card['memory_appeals'][1]['link_condition_private'])
        with self.assertRaisesRegex(ValueError,'Duplicate memory-link'):
            extract_html(fixture(memory=MEMORY+condition+condition),CARD)
        with self.assertRaisesRegex(ValueError,'Unknown extra memory'):
            extract_html(fixture(memory=MEMORY+condition.replace('思い出アピールリンク条件','未知の表')),CARD)

    def test_combined_cells_and_inline_spans_keep_names_and_evidence(self):
        card = extract_html(fixture(), CARD)
        nodes = card['panel_nodes']
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0]['name'], '技能甲')
        self.assertEqual(nodes[0]['mechanics'], ['link'])
        self.assertEqual(nodes[1]['cap_delta'], 100)
        self.assertEqual(nodes[1]['unlock_star'], 3)
        memory = card['memory_appeals']
        self.assertEqual(memory[0]['link_appeal_private'], memory[1]['link_appeal_private'])
        self.assertEqual(memory[0]['source_positions'][-1], memory[1]['source_positions'][-1])
        self.assertEqual(memory[1]['source_positions'][-1]['row'], 2)
        self.assertEqual(card['coverage']['stage_skill'], 'not_collected')
        self.assertEqual(card['coverage']['review'], 'needs_review')

    def test_multi_cap_keeps_every_target_on_one_node(self):
        panel=PANEL.replace('Vocal上限+100','Dance & メンタル 上限+150')
        node=extract_html(fixture(panel=panel),CARD)['panel_nodes'][1]
        self.assertEqual(node['cap_targets'],['Dance','メンタル'])
        self.assertEqual(node['cap_delta'],150)
        with self.assertRaisesRegex(ValueError,'Duplicate cap target'):
            extract_html(fixture(panel=PANEL.replace('Vocal上限+100','Vocal & Vocal 上限+100')),CARD)

    def test_mb_has_own_mechanics_and_stage_not_star(self):
        mb = '''<table><tr><th colspan="2">メモリーブースト</th></tr>
        <tr><th colspan="2">技能甲[MB] (2/5)</th></tr>
        <tr><td colspan="2" style="background-color:gainsboro">Vocal3倍(Plus)追撃</td></tr></table>'''
        card = extract_html(fixture(extra=mb), CARD)
        self.assertEqual(card['panel_nodes'][0]['mechanics'], ['link'])
        self.assertEqual(card['mb_live'][0]['mechanics'], ['plus'])
        self.assertEqual(card['mb_live'][0]['mb_stage'], 2)
        self.assertNotIn('unlock_star', card['mb_live'][0])

    def test_quick_and_passive_are_distinct(self):
        panel = '''<table><tr><th>SP</th><th>凡例</th><th>凡例</th></tr>
        <tr><th rowspan="2">40</th><th>技能甲</th><th>Vocal10%UP (E4)</th></tr>
        <tr><td>[コスト:3]</td><td>[条件:2ターン以前][確率:10%]</td></tr></table>'''
        nodes = extract_html(fixture(panel=panel), CARD)['panel_nodes']
        self.assertEqual([n['kind'] for n in nodes], ['quick_skill', 'panel_passive'])
        self.assertEqual(nodes[0]['energy_cost'], 3)
        self.assertEqual(nodes[1]['unlock_event'], '4')

    def test_ability_two_sections_are_one_node_with_both_sources(self):
        panel = '''<table><tr><th>SP</th><th>凡例</th></tr>
        <tr><th rowspan="2">40</th><th>能力甲</th></tr>
        <tr><td>(アビリティ)合成効果</td></tr></table>'''
        extra = '<h2>アビリティ</h2><table><tr><th>能力甲</th><td>合成効果</td></tr></table>'
        nodes = extract_html(fixture(panel=panel, extra=extra), CARD)['panel_nodes']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(len(nodes[0]['source_positions']), 4)
        with self.assertRaisesRegex(ValueError, 'content differs'):
            extract_html(fixture(panel=panel, extra=extra.replace('合成効果', '異なる効果')), CARD)

    def test_unknown_effect_and_ragged_table_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unclassified'):
            extract_html(fixture(panel=PANEL.replace('Vocal上限+100', '未対応の構造')), CARD)
        with self.assertRaisesRegex(ValueError, 'Unparsed cap increase'):
            extract_html(fixture(panel=PANEL.replace('Vocal上限+100', '未対応上限+100')), CARD)
        for markup in ('<table><tr><td>A</td><td>B</td></tr><tr><td>C</td></tr></table>',
                       '<table><tr><td rowspan="3">A</td></tr></table>'):
            with self.assertRaises(ValueError):
                table_grid(BeautifulSoup(markup, 'html.parser').table)

    def test_wrong_card_and_wrong_p_s_sections_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Wiki URL|canonical'):
            extract_html(fixture().replace(URL.encode(), b'https://wikiwiki.jp/pp/security-check-guide'), CARD)
        with self.assertRaisesRegex(ValueError, 'wrong card title'):
            extract_html(fixture().replace('【試験】試験アイドル - Wiki'.encode(), '【別人】 - Wiki'.encode()), CARD)
        with self.assertRaisesRegex(ValueError, 'P/S section mismatch'):
            extract_html(fixture(), dict(CARD, card_kind='S'))

    def test_missing_or_duplicate_memory_level_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'memory levels'):
            extract_html(fixture(memory=MEMORY.replace('Lv2', 'Lv3')), CARD)
        with self.assertRaisesRegex(ValueError, 'memory levels'):
            extract_html(fixture(memory=MEMORY.replace('Lv2', 'Lv1')), CARD)

    def test_replay_is_stable_and_rejects_tampered_or_failed_input(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw = fixture()
            (root / 'response.html').write_bytes(raw)
            report = {'url': URL, 'status': 'fetched', 'http_status': 200,
                      'sha256': hashlib.sha256(raw).hexdigest(), 'fetched_at': '2026-10-06T00:00:00+00:00'}
            write(root / 'fetch.json', report)
            first = transform_run(root, CARD, 'test-version')
            self.assertEqual(first, transform_run(root, CARD, 'test-version'))
            (root / 'response.html').write_bytes(raw + b' ')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                transform_run(root, CARD, 'test-version')
            write(root / 'fetch.json', dict(report, status='failed'))
            with self.assertRaisesRegex(ValueError, 'not successful'):
                transform_run(root, CARD, 'test-version')

    def test_candidates_cannot_publish_or_overwrite_different_content(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / 'private/candidate.json'
            save_candidate({'value': 1}, output, root)
            save_candidate({'value': 1}, output, root)
            with self.assertRaises(FileExistsError):
                save_candidate({'value': 2}, output, root)
            self.assertEqual(read(output), {'value': 1})
            with self.assertRaisesRegex(ValueError, 'private'):
                save_candidate({'value': 1}, root / 'site/data/details.json', root)
            self.assertFalse((root / 'site').exists())

    def test_interrupted_candidate_save_does_not_leave_partial_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / 'private/candidate.json'
            with patch('scripts.transform_detail_html.os.link', side_effect=OSError('simulated failure')):
                with self.assertRaises(OSError):
                    save_candidate({'value': 1}, output, root)
            self.assertFalse(output.exists())
            self.assertEqual(list(output.parent.glob('*.tmp')), [])

    def test_detail_allowlist_uses_shared_gate_and_rejects_mismatched_kind(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = {'pages': [], 'audit_pages': [], 'detail_pages': [
                {'id': 'D01', 'card_id': CARD['card_id'], 'kind': 'P', 'url': URL}],
                'detail_base_dataset_version': 'test-version', 'single_page_collection_enabled': True,
                'single_page_cooldown_seconds': 86400, 'full_collection_enabled': False}
            write(root / 'source_manifest.json', manifest)
            state = root / 'state.json'
            current = datetime(2026, 10, 9, 4, 0, tzinfo=timezone.utc)
            write(state, {'last_attempt_at': (current-timedelta(days=2)).isoformat()})
            calls = []
            def fake_fetch(url, target, *, allow_limited):
                calls.append(url)
                write(target / 'fetch.json', {'status': 'fetched'})
            with patch.object(limited, 'ROOT', root), patch.object(limited, 'load_cards', return_value=[CARD]):
                with self.assertRaisesRegex(ValueError, 'private/raw'):
                    limited.fetch_one('D01', root / 'site/raw', current=current, state_path=state, fetcher=fake_fetch)
                manifest['detail_pages'][0]['kind'] = 'S'
                write(root / 'source_manifest.json', manifest)
                with self.assertRaisesRegex(ValueError, 'ID/kind/URL mismatch'):
                    limited.fetch_one('D01', root / 'private/raw/failed', current=current, state_path=state, fetcher=fake_fetch)
                manifest['detail_pages'][0]['kind'] = 'P'
                write(root / 'source_manifest.json', manifest)
                limited.fetch_one('D01', root / 'private/raw/first', current=current, state_path=state, fetcher=fake_fetch)
                with self.assertRaisesRegex(RuntimeError, 'unavailable until'):
                    limited.fetch_one('D01', root / 'private/raw/second', current=current+timedelta(hours=1), state_path=state, fetcher=fake_fetch)
            self.assertEqual(calls, [URL])
            self.assertFalse((root / 'private/raw/second').exists())


if __name__ == '__main__':
    unittest.main()
