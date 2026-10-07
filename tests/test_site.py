import copy
import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.check_site import check
from scripts.stage_release import stage
from src.indexer import accept, empty, prepare, read, write


class SiteValidationTests(unittest.TestCase):
 def test_exact_tree_pointer_and_export_content(self):
  card=dict(card_title='【検証】',idol_id='idol_test',idol_name='検証',card_kind='P',rarity='R',unit_id=None,unit_name=None,first_implemented_on='2020-01-01',acquisition_category='initial',series_ids=[],series_status='none',collab_work=None,wiki_url='https://wikiwiki.jp/shinycolors/検証',wiki_link_status='observed',variant_kind='base',review_status='wiki_only',source_ref='synthetic-test')
  batch={'cards':[card],'status':'validated','run_id':'site-test','observed_at':'2020-01-01','scope':'sample'}
  with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{'XLSX_BACKEND':'stdlib'}):
   site=Path(directory)/'site';version=prepare(accept(empty(),batch),site)
   self.assertEqual(check(site)[0]['version'],version)
   leak=site/'data'/'private.txt';leak.write_text('must not publish',encoding='utf-8')
   with self.assertRaisesRegex(ValueError,'unexpected data entry'):check(site)
   leak.unlink()
   latest=site/'data'/'latest.json';pointer=read(latest)
   write(latest,{'dataset_version':'v1-'+'0'*16,'manifest':'v1-'+'0'*16+'/manifest.json'})
   with self.assertRaisesRegex(ValueError,'invalid latest pointer'):check(site)
   write(latest,pointer)
   bundle=site/'data'/version;sources=bundle/'sources.json';manifest=bundle/'manifest.json'
   write(sources,[])
   metadata=read(manifest);metadata['files']['sources.json']=hashlib.sha256(sources.read_bytes()).hexdigest();write(manifest,metadata)
   with self.assertRaisesRegex(ValueError,'bundle content mismatch sources'):check(site)

 def test_stage_latest_only_then_keep_previous_release(self):
  card=dict(card_title='【検証】',idol_id='idol_test',idol_name='検証',card_kind='P',rarity='R',unit_id=None,unit_name=None,first_implemented_on='2020-01-01',acquisition_category='initial',series_ids=[],series_status='none',collab_work=None,wiki_url='https://wikiwiki.jp/shinycolors/検証',wiki_link_status='observed',variant_kind='base',review_status='wiki_only',source_ref='synthetic-test')
  batch={'cards':[card],'status':'validated','run_id':'stage-test','observed_at':'2020-01-01','scope':'sample'}
  with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{'XLSX_BACKEND':'stdlib'}):
   source=Path(directory)/'source';m=accept(empty(),batch);first=prepare(m,source)
   prior=Path(directory)/'prior';self.assertEqual(stage(source,prior)['versions'],[first])
   cid=m['registry'][0]['card_id']
   m['overrides']=[{'card_id':cid,'values':{'review_status':'needs_review'},'clear_fields':[],'reason':'確認待ち','source_ref':'manual-test','updated_at':'2026-10-07T12:00:00+09:00'}]
   second=prepare(m,source);self.assertNotEqual(first,second)
   staged=Path(directory)/'next';result=stage(source,staged,prior)
   self.assertEqual(result['latest'],second)
   self.assertEqual(set(result['versions']),{first,second})
   self.assertEqual(len(check(staged)),2)
   with self.assertRaises(FileExistsError):stage(source,staged,prior)
   with self.assertRaisesRegex(ValueError,'previous release must be separate'):stage(source,Path(directory)/'unsafe',source)


if __name__=='__main__':unittest.main()
