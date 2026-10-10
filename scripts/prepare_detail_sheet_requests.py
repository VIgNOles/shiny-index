"""Prepare bounded detail-only requests for a native whole-workbook copy; never sends them."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.detail_master import from_workbook,table_rows,DETAIL_TABS
from src.indexer import ROOT,read,write,digest


def value_cell(value):
    if value is None or value=='':return {}
    if type(value) is int or type(value) is float:return {'userEnteredValue':{'numberValue':value}}
    if type(value) is bool:return {'userEnteredValue':{'boolValue':value}}
    return {'userEnteredValue':{'stringValue':str(value)}}


def build_requests(before,after,metadata,max_batch_bytes=24000):
    if not 12000<=max_batch_bytes<=100000:raise ValueError('Invalid bounded request size')
    properties={s['properties']['title']:s['properties'] for s in metadata['sheets']}
    if set(DETAIL_TABS)-set(properties):raise ValueError('Read metadata must contain all six detail tabs')
    old=table_rows(before);new=table_rows(after);requests=[];changed={}
    for title in DETAIL_TABS:
        props=properties[title];sid=props['sheetId'];rows=new[title];width=len(rows[0]);old_rows=old[title]
        if len(rows)<len(old_rows):raise ValueError('Detail row removal requires separate review')
        grid=props['gridProperties'];grow=len(rows)>grid['rowCount']
        if grow:
            requests.append({'updateSheetProperties':{'properties':{'sheetId':sid,'gridProperties':{'rowCount':len(rows)+20}},'fields':'gridProperties.rowCount'}})
        if width>grid['columnCount']:raise ValueError('Unexpected detail column change')
        positions=[i for i,row in enumerate(rows) if i>=len(old_rows) or row!=old_rows[i]]
        changed[title]=len(positions)
        start=None;values=[]
        def flush():
            nonlocal start,values
            if values:requests.append({'updateCells':{'start':{'sheetId':sid,'rowIndex':start,'columnIndex':0},'rows':[{'values':v} for v in values],'fields':'userEnteredValue'}})
            start=None;values=[]
        for i in positions:
            cells=[value_cell(v) for v in rows[i]]
            prospective={'updateCells':{'start':{'sheetId':sid,'rowIndex':start if start is not None else i,'columnIndex':0},
                                        'rows':[{'values':row} for row in values+[cells]],'fields':'userEnteredValue'}}
            if values and (i!=start+len(values) or len(json.dumps([prospective],ensure_ascii=False).encode('utf-8'))>max_batch_bytes):flush()
            if start is None:start=i
            values.append(cells)
        flush()
        if len(rows)>len(old_rows):
            requests.append({'copyPaste':{'source':{'sheetId':sid,'startRowIndex':1,'endRowIndex':2,'startColumnIndex':0,'endColumnIndex':width},
                                         'destination':{'sheetId':sid,'startRowIndex':len(old_rows),'endRowIndex':len(rows),'startColumnIndex':0,'endColumnIndex':width},'pasteType':'PASTE_FORMAT'}})
        if title!='_detail_meta':requests.append({'setBasicFilter':{'filter':{'range':{'sheetId':sid,'startRowIndex':0,'endRowIndex':len(rows),'startColumnIndex':0,'endColumnIndex':width}}}})
    batches=[];current=[]
    for request in requests:
        if len(json.dumps([request],ensure_ascii=False).encode('utf-8'))>max_batch_bytes:raise ValueError('One request exceeds bounded size; inspect unusually long cell')
        if current and len(json.dumps(current+[request],ensure_ascii=False).encode('utf-8'))>max_batch_bytes:
            batches.append(current);current=[]
        current.append(request)
    if current:batches.append(current)
    return batches,changed


def prepare(export,plan,metadata_path,output):
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'private').resolve()) or output.exists():raise ValueError('Choose a fresh private request directory')
    before=from_workbook(export);after=read(Path(plan)/'master.json');metadata=read(metadata_path)
    old_ids={r['detail_id'] for r in before['registry']};new_ids={r['detail_id'] for r in after['registry']}
    if not old_ids<=new_ids:raise ValueError('Fixed detail IDs disappeared')
    old_overrides={r['detail_id']:r['override'] for r in before['registry']};new_overrides={r['detail_id']:r['override'] for r in after['registry']}
    if any(new_overrides[k]!=v for k,v in old_overrides.items()):raise ValueError('Manual override changed')
    batches,changed=build_requests(before,after,metadata);output.mkdir(parents=True)
    for i,batch in enumerate(batches):write(output/f'{i:03}.json',batch)
    report={'batches':len(batches),'before_master_hash':digest(before),'after_master_hash':digest(after),'source_spreadsheet_id':metadata['spreadsheetId'],
            'changed_rows_by_tab':changed,'existing_fixed_ids_and_overrides_preserved':True,'writes_performed':False,'requires_native_full_workbook_copy':True}
    write(output/'plan.json',report);return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('fresh_export');p.add_argument('adoption_plan');p.add_argument('native_metadata');p.add_argument('output');a=p.parse_args()
    print(json.dumps(prepare(a.fresh_export,a.adoption_plan,a.native_metadata,a.output),ensure_ascii=False))
