"""Shared-page identities, explicit labels and reordered table boundaries."""
import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from src.card_details import extract_html
from src.detail_variants import validate_variants,transform_shared_run
from src.detail_master import empty,adopt
from src.detail_public import public_document
from src.indexer import digest,write
from tests.test_detail_html import PANEL,MEMORY

URL='https://wikiwiki.jp/shinycolors/【白いツバサ】試験アイドル'
CARDS=[dict(card_id='00000000-0000-4000-8000-00000000000'+str(i+1),card_kind='P',card_title=title,idol_name='試験アイドル',wiki_url=URL,rarity=rarity,variant_kind=kind)
       for i,(kind,rarity,title) in enumerate([('base','R','【白いツバサ】'),('idol_road_sr','SR','【白いツバサ】'),('idol_road_ssr','SSR','【アイドルロード】')])]

def fold(card,body):
    label=card['rarity']+card['card_title']+card['idol_name']
    return '<div class="fold-container"><div class="fold-summary">'+label+'</div><div class="fold-content"><p>'+label+'</p><div class="h-scrollable">'+body+'</div></div></div>'

def fixture(order=(0,1,2)):
    panels=''.join(fold(CARDS[i],PANEL.replace('Vocal2倍','Vocal'+str(i+1)+'倍')) for i in order)
    memories=''.join(fold(CARDS[i],MEMORY.replace('合成Link効果','派生'+str(i))) for i in reversed(order))
    return ('<html><head><meta charset="utf-8"><title>【白いツバサ】試験アイドル - Wiki</title><link rel="canonical" href="'+URL+'"></head><body><div id="content"><h2>スキルパネル</h2>'+panels+'<h2>思い出アピール</h2>'+memories+'</div></body></html>').encode()

class VariantTests(unittest.TestCase):
    def test_explicit_labels_separate_three_ids_even_when_tables_reorder(self):
        for order in [(0,1,2),(2,0,1)]:
            for i,card in enumerate(CARDS):
                result=extract_html(fixture(order),card,variant_cards=CARDS)
                self.assertEqual(result['card_id'],card['card_id'])
                self.assertTrue(result['panel_nodes'][0]['effect_private'].startswith('Vocal'+str(i+1)+'倍'))
                self.assertEqual(result['memory_appeals'][0]['link_appeal_private'],'派生'+str(i))
                self.assertEqual(result['variant_mapping']['basis'],'explicit_fold_labels')
                self.assertEqual(result['coverage']['stage_skill'],'not_collected')

    def test_missing_unknown_or_mismatched_labels_cannot_mix_variants(self):
        label='SR【白いツバサ】試験アイドル'
        for bad in [fixture().replace(label.encode(),b'UNKNOWN'),fixture().replace(b'fold-summary',b'no-summary',1),fixture().replace(b'fold-container',b'no-container',1)]:
            with self.assertRaises(ValueError):extract_html(bad,CARDS[0],variant_cards=CARDS)
        bad=fixture().replace(('<p>'+label+'</p>').encode(),b'<p>wrong identity</p>',1)
        with self.assertRaisesRegex(ValueError,'label/identity'):extract_html(bad,CARDS[0],variant_cards=CARDS)

    def test_incomplete_or_wrong_identity_group_is_rejected(self):
        for bad in [CARDS[:2],CARDS+[CARDS[0]]]:
            with self.assertRaises(ValueError):validate_variants(bad)
        for field,value in [('rarity','R'),('card_kind','S'),('idol_name','他人'),('wiki_url',URL+'別')]:
            bad=copy.deepcopy(CARDS);bad[1][field]=value
            with self.assertRaises(ValueError):validate_variants(bad)

    def test_replay_keeps_ids_and_public_joins_variant_card_ids(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            def replay(raw):
                (p/'response.html').write_bytes(raw);write(p/'fetch.json',{'url':URL,'http_status':200,'status':'fetched','sha256':hashlib.sha256(raw).hexdigest(),'fetched_at':'2026-10-09T00:00:00+00:00'})
                doc=transform_shared_run(p,CARDS,'v1-0000000000000000')
                doc['card_coverage']=[{'card_id':c['card_id'],'card_kind':'P','status':'candidate_needs_review'} for c in CARDS]
                doc['coverage']={};doc['content_hash']=digest({k:v for k,v in doc.items() if k!='content_hash'})
                return doc
            master=adopt(empty('v1-0000000000000000'),replay(fixture()),base_cards=CARDS)
            updated=adopt(master,replay(fixture((2,0,1))),base_cards=CARDS)
            self.assertEqual({r['detail_id'] for r in master['registry']},{r['detail_id'] for r in updated['registry']})
            public=public_document(updated,CARDS)
            self.assertEqual(len(public['cards']),3)
            self.assertEqual(public['coverage']['status_counts'],{'available_partial':3})
            self.assertNotIn('effect_private',json.dumps(public))

if __name__=='__main__':unittest.main()
