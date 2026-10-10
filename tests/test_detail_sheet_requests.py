import copy,json,unittest
from unittest.mock import patch
from scripts.prepare_detail_sheet_requests import build_requests,value_cell
from src.detail_master import DETAIL_TABS,empty,adopt
from tests.test_detail_master import candidate

class RequestTests(unittest.TestCase):
    def test_byte_limit_includes_row_wrappers_without_losing_rows(self):
        old={title:[['header']*5] for title in DETAIL_TABS}
        new=copy.deepcopy(old)
        new['詳細属性'].extend([[str(i)]*5 for i in range(650)])
        with patch('scripts.prepare_detail_sheet_requests.table_rows',side_effect=[old,new]):
            batches,_=build_requests({}, {},self.metadata(rows=10000),max_batch_bytes=85000)
        self.assertTrue(all(len(json.dumps(b,ensure_ascii=False).encode('utf-8'))<=85000 for b in batches))
        blocks=[r['updateCells'] for b in batches for r in b if 'updateCells' in r]
        self.assertEqual([r['values'][0]['userEnteredValue']['stringValue'] for b in blocks for r in b['rows']],[str(i) for i in range(650)])
        self.assertEqual([b['start']['rowIndex'] for b in blocks],[1]+[1+sum(len(x['rows']) for x in blocks[:i]) for i in range(1,len(blocks))])
        oversized=copy.deepcopy(old);oversized['詳細属性'].append(['x'*90000]*5)
        with patch('scripts.prepare_detail_sheet_requests.table_rows',side_effect=[old,oversized]),self.assertRaisesRegex(ValueError,'exceeds bounded size'):
            build_requests({}, {},self.metadata(rows=10000),max_batch_bytes=85000)

    def metadata(self,rows=2):return {'sheets':[{'properties':{'title':title,'sheetId':i,'gridProperties':{'rowCount':rows,'columnCount':16}}} for i,title in enumerate(DETAIL_TABS,1)]+[{'properties':{'title':'追加・手修正','sheetId':99,'gridProperties':{'rowCount':10,'columnCount':26}}}]}
    def test_requests_target_only_six_tabs_and_grow_before_writes(self):
        c=candidate();before=empty(c['base_dataset_version']);after=adopt(before,c)
        batches,changed=build_requests(before,after,self.metadata())
        touched=set()
        for batch in batches:
            for request in batch:
                body=next(iter(request.values()))
                for key in ['properties','start','range','filter','source','destination']:
                    value=body.get(key,{})
                    if 'range' in value:value=value['range']
                    if 'sheetId' in value:touched.add(value['sheetId'])
        self.assertTrue(touched<={1,2,3,4,5,6});self.assertNotIn(99,touched)
        self.assertGreater(changed['詳細項目'],0)
        for title,count in changed.items():self.assertIsInstance(count,int)
    def test_removed_rows_and_wrong_metadata_are_rejected(self):
        c=candidate();after=adopt(empty(c['base_dataset_version']),c)
        with self.assertRaisesRegex(ValueError,'row removal'):build_requests(after,empty(c['base_dataset_version']),self.metadata())
        with self.assertRaisesRegex(ValueError,'six detail'):build_requests(empty(c['base_dataset_version']),after,{'sheets':[]})
    def test_new_logical_rows_receive_formats_inside_existing_grid(self):
        c=candidate();before=empty(c['base_dataset_version']);after=adopt(before,c)
        batches,_=build_requests(before,after,self.metadata(rows=10000))
        formats=[r['copyPaste'] for batch in batches for r in batch if 'copyPaste' in r]
        self.assertTrue(formats)
        self.assertTrue(all(r['pasteType']=='PASTE_FORMAT' for r in formats))
        self.assertTrue(all(r['destination']['startRowIndex']==1 for r in formats))
        self.assertFalse(any('updateSheetProperties' in r for batch in batches for r in batch))

    def test_values_use_literal_strings_not_formulas(self):
        self.assertEqual(value_cell('=formula'),{'userEnteredValue':{'stringValue':'=formula'}})
        self.assertEqual(value_cell(None),{})
        self.assertEqual(value_cell(40),{'userEnteredValue':{'numberValue':40}})

if __name__=='__main__':unittest.main()
