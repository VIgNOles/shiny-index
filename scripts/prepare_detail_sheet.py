"""Prepare resumable native Sheets writes for six detail tabs only."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.detail_master import DETAIL_TABS,table_rows
from src.indexer import read,write

def prepare(master,output):
    output=Path(output)
    if output.exists():raise FileExistsError('Choose a new request directory')
    output.mkdir(parents=True)
    tables=table_rows(master);requests=[]
    for i,(name,rows) in enumerate(tables.items()):
        sid=700000001+i;width=len(rows[0]);height=max(len(rows)+20,200)
        requests.append({'addSheet':{'properties':{'sheetId':sid,'title':name,'gridProperties':{'rowCount':height,'columnCount':width,'frozenRowCount':1,'hideGridlines':True}}}})
        requests.append({'repeatCell':{'range':{'sheetId':sid},'cell':{'userEnteredFormat':{'textFormat':{'fontFamily':'Arial','fontSize':11},'verticalAlignment':'TOP','wrapStrategy':'CLIP'}},'fields':'userEnteredFormat'}})
        requests.append({'repeatCell':{'range':{'sheetId':sid,'startRowIndex':0,'endRowIndex':1},'cell':{'userEnteredFormat':{'backgroundColor':{'red':.9,'green':.9,'blue':.9},'textFormat':{'bold':True}}},'fields':'userEnteredFormat.backgroundColor,userEnteredFormat.textFormat.bold'}})
        requests.append({'updateDimensionProperties':{'range':{'sheetId':sid,'dimension':'COLUMNS','startIndex':0,'endIndex':width},'properties':{'pixelSize':150},'fields':'pixelSize'}})
        if name!='_detail_meta':requests.append({'setBasicFilter':{'filter':{'range':{'sheetId':sid,'startRowIndex':0,'endRowIndex':len(rows),'startColumnIndex':0,'endColumnIndex':width}}}})
        if name=='詳細項目':
            requests.append({'repeatCell':{'range':{'sheetId':sid,'startRowIndex':1,'startColumnIndex':6,'endColumnIndex':13},'cell':{'userEnteredFormat':{'backgroundColor':{'red':.95,'green':.98,'blue':1}}},'fields':'userEnteredFormat.backgroundColor'}})
    batches=[requests]
    for i,(name,rows) in enumerate(tables.items()):
        sid=700000001+i;start=0;chunk=[];size=0
        for row in rows:
            cells={'values':[{} if v is None else {'userEnteredValue':{'numberValue':v} if type(v) in (int,float) else {'boolValue':v} if type(v) is bool else {'stringValue':str(v)}} for v in row]}
            n=len(json.dumps(cells,ensure_ascii=False))
            if chunk and size+n>35000:
                batches.append([{'updateCells':{'start':{'sheetId':sid,'rowIndex':start,'columnIndex':0},'rows':chunk,'fields':'userEnteredValue'}}]);start+=len(chunk);chunk=[];size=0
            chunk.append(cells);size+=n
        if chunk:batches.append([{'updateCells':{'start':{'sheetId':sid,'rowIndex':start,'columnIndex':0},'rows':chunk,'fields':'userEnteredValue'}}])
    for n,batch in enumerate(batches):write(output/f'{n:03}.json',batch)
    plan={'batches':len(batches),'master_hash':__import__('src.indexer',fromlist=['digest']).digest(master),'tabs':{name:{'sheet_id':700000001+i,'rows':len(rows),'columns':len(rows[0])} for i,(name,rows) in enumerate(tables.items())}}
    write(output/'plan.json',plan);return plan

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('master');p.add_argument('output');a=p.parse_args();print(json.dumps(prepare(read(a.master),a.output),ensure_ascii=False))
