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
    def test_explanation_table_is_private_and_does_not_add_live_tags(self):
        note='<table><tr><th>付与効果甲</th></tr><tr><td>合成の説明 (Plus)</td></tr></table>'
        card=extract_html(fixture(extra=note),CARD)
        self.assertEqual(len(card['panel_nodes']),2)
        self.assertEqual(card['skill_notes_private'][0]['name'],'付与効果甲')
        self.assertEqual(card['panel_nodes'][0]['mechanics'],['link'])
        self.assertEqual(len(card['skill_notes_private'][0]['source_positions']),2)

    def test_dedicated_only_ability_has_unknown_sp_and_own_source(self):
        from src.card_details import match_abilities
        table=BeautifulSoup('<table><tr><th>能力甲</th><td>合成の効果</td></tr></table>','html.parser').table
        nodes=[];match_abilities(nodes,[(4,table,'ability')])
        self.assertEqual(nodes[0]['kind'],'unique_ability');self.assertIsNone(nodes[0]['sp'])
        self.assertEqual(nodes[0]['source_positions'][0]['section_anchor'],'ability')
        self.assertEqual(len(nodes),1)

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
