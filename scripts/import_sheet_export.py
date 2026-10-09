"""Review and apply a native Google Sheet's XLSX export without changing acquisition data."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

from openpyxl import load_workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.indexer import TABS, load_master, now, read, resolve, save_master, write


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sheet_rows(path, name):
    workbook = load_workbook(path, read_only=True, data_only=False)
    try:
        from src.detail_master import DETAIL_TABS
        names=set(workbook.sheetnames)
        if not set(TABS)<=names or names-set(TABS) not in (set(),set(DETAIL_TABS)):
            raise ValueError('unexpected master tabs')
        rows = []
        for row in workbook[name].iter_rows(values_only=True):
            trimmed = list(row)
            while trimmed and trimmed[-1] is None:
                trimmed.pop()
            if trimmed:
                rows.append(trimmed)
        return rows
    finally:
        workbook.close()


def review(master_path, export_path):
    master_path, export_path = Path(master_path), Path(export_path)
    if master_path.resolve() == export_path.resolve():
        raise ValueError('export must be separate from the active master')
    for name in TABS:
        if name != '追加・手修正' and sheet_rows(master_path, name) != sheet_rows(export_path, name):
            raise ValueError(f'protected tab changed: {name}')
    original, imported = load_master(master_path), load_master(export_path)
    for field in ['revision', 'coverage', 'source', 'evidence', 'runs', 'dictionaries', 'candidates']:
        if original[field] != imported[field]:
            raise ValueError(f'protected master state changed: {field}')
    old_registry = {r['card_id']: r for r in original['registry']}
    new_registry = {r['card_id']: r for r in imported['registry']}
    for card_id, record in old_registry.items():
        if new_registry.get(card_id) != record:
            raise ValueError(f'fixed ID or source aliases changed: {card_id}')
    added = sorted(set(new_registry) - set(old_registry))
    if any(new_registry[c]['aliases'] or new_registry[c]['family_id'] != c for c in added):
        raise ValueError('new manual card has an unexpected source alias or family')
    from src.detail_master import DETAIL_TABS,from_workbook
    detail_changed=False
    book=load_workbook(export_path,read_only=True);has_details=set(DETAIL_TABS)<=set(book.sheetnames);book.close()
    oldbook=load_workbook(master_path,read_only=True);had_details=set(DETAIL_TABS)<=set(oldbook.sheetnames);oldbook.close()
    if had_details and not has_details:raise ValueError('Detail tabs removed from export')
    if has_details:
        incoming_detail=from_workbook(export_path)
        detail_changed=not had_details or from_workbook(master_path)!=incoming_detail
    before, after = resolve(original), resolve(imported)
    def identity(card):
        return (card['idol_id'], card['card_kind'], card['variant_kind'], card['card_title'])
    existing = {identity(c) for c in before}
    if any(identity(c) in existing for c in after if c['card_id'] in added):
        raise ValueError('possible manual duplicate; use the existing card ID')
    old_edits = {x['card_id']: x for x in original['overrides']}
    new_edits = {x['card_id']: x for x in imported['overrides']}
    return {
        'master_sha256': file_hash(master_path),
        'export_sha256': file_hash(export_path),
        'master_revision': original['revision'],
        'before_count': len(before),
        'after_count': len(after),
        'added_ids': added,
        'changed_edit_ids': sorted(c for c in new_edits.keys() & old_edits.keys() if new_edits[c] != old_edits[c]),
        'removed_edit_ids': sorted(old_edits.keys() - new_edits.keys()),
        'new_edit_ids': sorted(new_edits.keys() - old_edits.keys()),
        'edit_changes': [
            {'card_id': c, 'before': old_edits.get(c), 'after': new_edits.get(c)}
            for c in sorted(old_edits.keys() | new_edits.keys())
            if old_edits.get(c) != new_edits.get(c)
        ],
        'added_cards': [
            {k: c[k] for k in ['card_id', 'card_title', 'idol_id', 'idol_name', 'card_kind', 'variant_kind', 'wiki_url']}
            for c in after if c['card_id'] in added
        ],
        'protected_tabs_unchanged': True,
        'detail_changed': detail_changed,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['review', 'apply'])
    parser.add_argument('master')
    parser.add_argument('export')
    parser.add_argument('report')
    args = parser.parse_args()
    report_path = Path(args.report)
    if args.mode == 'review':
        if report_path.exists():
            raise FileExistsError('review report already exists; choose a new path')
        result = review(args.master, args.export)
        write(report_path, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    approved = read(report_path)
    current = review(args.master, args.export)
    if current != approved:
        raise ValueError('master or export changed since review; make a new review')
    if not current['detail_changed'] and not any(current[k] for k in ['added_ids', 'changed_edit_ids', 'removed_edit_ids', 'new_edit_ids']):
        print('No manual changes; active master was not rewritten.')
        return
    imported = load_master(args.export)
    save_master(imported, args.master, detail_source=args.export)
    if load_master(args.master) != imported:
        raise ValueError('applied master read-back mismatch')
    print(json.dumps({'applied_at': now(), 'result': current}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
