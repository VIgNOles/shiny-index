"""Exercise XLSX edits and rebuild using real research records, in a private copy."""
import copy
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.indexer import *
batch=read('private/sample-batch.json')
initial=copy.deepcopy(batch);initial['cards']=initial['cards'][:-1];initial['run_id']='drill-eight'
m=accept(empty(),initial);save_master(m,'private/drill/master.xlsx')
v1=prepare(load_master('private/drill/master.xlsx'),'private/drill/site')
cid=m['registry'][0]['card_id'];newid=str(uuid.uuid4());c=batch['cards'][-1]
m['registry'].append({'card_id':newid,'family_id':newid,'aliases':[],'updated_at':now()})
m['overrides']=[{'card_id':newid,'values':{f:c[f] for f in FIELDS if c.get(f) is not None},'clear_fields':[],'reason':'実カードC09を手入力で追加','source_ref':'design-C09','updated_at':now()}, {'card_id':cid,'values':{'review_status':'needs_review'},'clear_fields':[],'reason':'公式未照合のため確認待ちへ変更','source_ref':'design-C01','updated_at':now()}]
save_master(m,'private/drill/master.xlsx');loaded=load_master('private/drill/master.xlsx')
v2=prepare(loaded,'private/drill/site')
assert v1!=v2 and len(resolve(loaded))==9
assert next(x for x in resolve(loaded) if x['card_id']==cid)['review_status']=='needs_review'
later=copy.deepcopy(batch);later['run_id']='drill-later'
matched=accept(loaded,later,{key(c):newid});assert len(resolve(matched))==9
assert next(x for x in resolve(matched) if x['card_id']==newid)['card_title']==c['card_title']
# Old immutable bundle is still intact; rollback changes the selected HTML and pointer only.
rollback('private/drill/site',v1)
assert read('private/drill/site/data/latest.json')['dataset_version']==v1
rollback('private/drill/site',v2)
assert (Path('private/drill/site/data')/v1/'cards.json').exists()
assert verify_bundle(Path('private/drill/site/data')/v1)['count']==8
assert verify_bundle(Path('private/drill/site/data')/v2)['count']==9
write('private/drill/report.json',{'before':v1,'after':v2,'added_id':newid,'edited_id':cid,'xlsx_edit_roundtrip':True,'manual_later_match':True,'old_bundle_preserved':True,'scope':'private real-data drill; no public deployment'})
print('Update drill passed:',v1,'->',v2)
