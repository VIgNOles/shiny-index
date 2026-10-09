"""Synthetic S fixtures for provenance, maximum level, and origin separation."""
import unittest
from tests.test_detail_html import CARD, URL, PANEL
from src.card_details import extract_html


def s_fixture(max_level=80, last_column='最大', bad_value=None):
    # Fictitious names/effects; no Wiki text in committed tests.
    basic='''<table><tr><th>アイドル</th><td colspan="2">試験アイドル</td></tr>
    <tr><th>アイデア</th><td colspan="2">トーク</td></tr>
    <tr><th>ひらめき</th><td colspan="2">Me.</td></tr>
    <tr><th>楽曲熟練度</th><th>歌唱力</th><th>集中力</th></tr></table>'''
    status=f'''<table><tr><th>Lv</th><th>Vo</th><th>Da</th><th>Vi</th><th>メンタル</th></tr>
    <tr><th>1</th><td>1</td><td>2</td><td>3</td><td>4</td></tr>
    <tr><th>{max_level}（☆4）</th><td>101</td><td>102</td><td>103</td><td>104</td></tr></table>'''
    possessed='''<table><tr><th>スキル名</th><th>効果</th><th>取得Lv</th></tr>
    <tr><th>技能甲</th><td>合成効果</td><td>初期</td></tr>
    <tr><th>技能乙</th><td>合成効果(Change)</td><td>80</td></tr></table>'''
    support=f'''<table><tr><th rowspan="2">スキル名</th><th rowspan="2">スキル効果</th><th colspan="3">取得Lv/スキルLv</th></tr>
    <tr><th>1</th><th>80</th><th>{last_column}</th></tr>
    <tr><th>支援甲</th><td>合成式&lt;Lv*5&gt;</td><td>1</td><td></td><td>{bad_value or '5'}</td></tr></table>'''
    return f'''<html><head><title>【試験】試験アイドル - Wiki</title><link rel="canonical" href="{URL}"></head>
    <body><div id="content">{basic}<h2>ステータス</h2>{status}<h2>スキルパネル</h2>{PANEL}
    <h2>所持スキル</h2><h3>ライブスキル</h3>{possessed}<h3>サポートスキル</h3>{support}
    <h3>ファイトスキル</h3><table><tr><th>excluded-fight</th><td>(Grow)</td></tr></table>
    <h2>特徴</h2><p>(Refrain)は収録しない説明</p></div></body></html>'''.encode()


class SupportDetailHtmlTests(unittest.TestCase):
    def test_explicit_maximum_label_does_not_imply_limit_break(self):
        from bs4 import BeautifulSoup
        from src.card_details import parse_s_status
        html='<table><tr><th>Lv</th><th>Vo</th><th>Da</th><th>Vi</th><th>メンタル</th></tr><tr><th>1</th><td>1</td><td>2</td><td>3</td><td>4</td></tr><tr><th>10(MAX)</th><td>50</td><td>60</td><td>70</td><td>80</td></tr></table>'
        parse=lambda raw:parse_s_status([(1,BeautifulSoup(raw,'html.parser').table,'status')])
        status=parse(html)
        self.assertEqual(status['level'],10)
        self.assertIsNone(status['limit_break'])
        self.assertEqual(status['vocal'],50)
        self.assertEqual(status['source_positions'][0]['row'],3)
        self.assertEqual(parse(html.replace('10(MAX)','10（MAX）'))['level'],10)
        for raw in (html.replace('<th>1</th>','<th>1(MAX)</th>'),
                    html.replace('10(MAX)','10').replace('<th>1</th>','<th>1(MAX)</th>'),
                    html.replace('10(MAX)','10(MIX)'),
                    html.replace('10(MAX)','MAX')):
            with self.subTest(raw=raw),self.assertRaises(ValueError):parse(raw)


    def test_traits_spans_maximum_level_and_excluded_sections(self):
        card=extract_html(s_fixture(),dict(CARD,card_kind='S'))
        self.assertEqual(card['traits']['music_proficiencies'],['歌唱力','集中力'])
        self.assertEqual(card['traits']['idea'],'トーク')
        self.assertEqual(len(card['traits']['source_positions']['アイデア']),1)
        self.assertEqual(card['max_status']['level'],80)
        self.assertEqual(card['max_status']['limit_break'],4)
        self.assertEqual(card['max_status']['vocal'],101)
        self.assertEqual(extract_html(s_fixture(max_level=90),dict(CARD,card_kind='S'))['max_status']['level'],90)
        self.assertEqual(card['coverage']['fight_skill'],'not_collected')
        self.assertNotIn('excluded-fight',str(card))
        self.assertNotIn('refrain',str(card))

    def test_panel_and_possessed_mechanics_are_independent(self):
        card=extract_html(s_fixture(),dict(CARD,card_kind='S'))
        self.assertEqual(card['panel_nodes'][0]['name'],card['possessed_live'][0]['name'])
        self.assertEqual(card['panel_nodes'][0]['mechanics'],['link'])
        self.assertEqual(card['possessed_live'][0]['mechanics'],[])
        self.assertEqual(card['possessed_live'][1]['mechanics'],['change'])
        self.assertEqual(card['possessed_live'][0]['kind'],'possessed_live')

    def test_support_special_max_column_and_formula_are_preserved(self):
        skill=extract_html(s_fixture(),dict(CARD,card_kind='S'))['support_skills'][0]
        self.assertEqual(skill['effect_private'],'合成式<Lv*5>')
        self.assertEqual([(p['support_level'],p['skill_level']) for p in skill['progression']],[('1',1),('最大',5)])
        self.assertEqual(len(skill['progression'][1]['source_positions']),2)
        numeric=extract_html(s_fixture(last_column='90'),dict(CARD,card_kind='S'))['support_skills'][0]
        self.assertEqual(numeric['progression'][-1]['support_level'],'90')

    def test_bad_support_values_or_unknown_header_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'progression'):
            extract_html(s_fixture(bad_value='?'),dict(CARD,card_kind='S'))
        with self.assertRaisesRegex(ValueError,'level columns'):
            extract_html(s_fixture(last_column='不明'),dict(CARD,card_kind='S'))
        with self.assertRaisesRegex(ValueError,'level columns'):
            extract_html(s_fixture(last_column='80'),dict(CARD,card_kind='S'))

    def test_p_s_mismatch_and_missing_trait_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'P/S section mismatch'):
            extract_html(s_fixture(),CARD)
        with self.assertRaisesRegex(ValueError,'S traits'):
            extract_html(s_fixture().replace('楽曲熟練度'.encode(),'未確認'.encode()),dict(CARD,card_kind='S'))

    def test_non_numeric_status_is_rejected_without_guessing(self):
        with self.assertRaisesRegex(ValueError,'Unrecognized S status value'):
            extract_html(s_fixture().replace(b'<td>101</td>',b'<td>bad-number</td>'),dict(CARD,card_kind='S'))


    def test_maximum_status_missing_values_keep_other_sections(self):
        raw = s_fixture().replace(b'<td>101</td>',b'<td></td>')
        card = extract_html(raw,dict(CARD,card_kind='S'))
        self.assertIsNone(card['max_status']['vocal'])
        self.assertEqual(card['max_status']['missing_fields'],['vocal'])
        self.assertEqual(card['max_status']['level'],80)
        self.assertEqual(card['coverage']['max_status'],'partial_missing_values')
        self.assertTrue(card['panel_nodes'])

    def test_non_maximum_status_blank_does_not_block_maximum(self):
        raw=s_fixture().replace(b'<td>1</td><td>2</td><td>3</td><td>4</td>',b'<td></td><td></td><td></td><td></td>')
        card=extract_html(raw,dict(CARD,card_kind='S'))
        self.assertEqual(card['max_status']['vocal'],101)


if __name__=='__main__':
    unittest.main()
