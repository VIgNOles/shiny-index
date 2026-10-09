import copy,os,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from openpyxl import load_workbook
from tests import test_sheet_import as sheet_import
from tests.test_detail_master import candidate,rehash
from src.indexer import load_master,save_master
from src.detail_master import adopt,empty,table_rows,from_workbook
from scripts.import_sheet_export import review

class DetailSheetSyncTests(unittest.TestCase):
 def setUp(self):
  sheet_import.SheetExportTests.setUp(self)
  cid=load_master(self.master)['registry'][0]['card_id'];c=candidate();c['cards'][0]['card_id']=cid;c['card_coverage'][0]['card_id']=cid;rehash(c)
  detail=adopt(empty(c['base_dataset_version']),c)
  wb=load_workbook(self.master)
  for name,rows in table_rows(detail).items():
   ws=wb.create_sheet(name)
   for row in rows:ws.append(row)
  wb.save(self.master);wb.close();shutil.copy2(self.master,self.export)
 def test_detail_only_edit_review_and_combined_sync(self):
  wb=load_workbook(self.export);ws=wb['詳細項目'];ws['G2']='変更名称';ws['K2']='訂正';ws['L2']='source';ws['M2']='2026-10-09T04:00:00Z';wb.save(self.export);wb.close()
  report=review(self.master,self.export)
  self.assertTrue(report['detail_changed']);self.assertEqual(report['edit_changes'],[])
  expected=from_workbook(self.export)
  with patch.dict(os.environ,{'XLSX_BACKEND':'stdlib'}):save_master(load_master(self.export),self.master,detail_source=self.export)
  self.assertEqual(from_workbook(self.master),expected)
  self.assertEqual(expected['registry'][0]['override']['name'],'変更名称')
 def test_missing_detail_tabs_are_rejected(self):
  wb=load_workbook(self.export)
  from src.detail_master import DETAIL_TABS
  for name in DETAIL_TABS:wb.remove(wb[name])
  wb.save(self.export);wb.close()
  with self.assertRaisesRegex(ValueError,'Detail tabs removed'):review(self.master,self.export)
if __name__=='__main__':unittest.main()
