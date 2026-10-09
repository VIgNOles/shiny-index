"""Prepare a reviewed private adoption plan from a fresh native master export and saved catalogue."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.detail_master import from_workbook,adopt,table_rows
from src.indexer import load_master,resolve,read,write,ROOT,digest

def prepare(sheet_export,candidate_path,output):
    out=Path(output).resolve()
    if not out.is_relative_to((ROOT/'private').resolve()):raise ValueError('Adoption plan must remain private')
    if out.exists():raise FileExistsError('Choose a fresh plan directory')
    master=from_workbook(sheet_export);candidate=read(candidate_path);base=resolve(load_master(sheet_export))
    proposed=adopt(master,candidate,base_cards=base)
    old_ids={row['detail_id'] for row in master['registry']};new_ids={row['detail_id'] for row in proposed['registry']}
    if not old_ids<=new_ids:raise ValueError('Existing fixed detail IDs disappeared')
    before_overrides={row['detail_id']:row.get('override',{}) for row in master['registry']}
    after_overrides={row['detail_id']:row.get('override',{}) for row in proposed['registry']}
    if any(after_overrides[key]!=value for key,value in before_overrides.items()):raise ValueError('Manual override changed during adoption')
    out.mkdir(parents=True)
    write(out/'master.json',proposed);write(out/'tables.json',table_rows(proposed))
    report={'active_master_changed':False,'sheet_writes_performed':False,'published':False,
            'input_candidate_hash':candidate['content_hash'],'input_master_hash':digest(master),'output_master_hash':digest(proposed),
            'before_cards':len(master['cards']),'after_cards':len(proposed['cards']),
            'before_items':len(master['registry']),'after_items':len(proposed['registry']),
            'added_card_ids':sorted(set(proposed['cards'])-set(master['cards'])),
            'new_detail_ids':sorted(new_ids-old_ids),'fixed_ids_preserved':True,'manual_overrides_preserved':True,
            'coverage':candidate['coverage']}
    write(out/'review.json',report);return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('sheet_export');p.add_argument('candidate');p.add_argument('output');a=p.parse_args()
    r=prepare(a.sheet_export,a.candidate,a.output)
    print(json.dumps({key:r[key] for key in ['before_cards','after_cards','before_items','after_items','fixed_ids_preserved','manual_overrides_preserved','published']},ensure_ascii=False))
