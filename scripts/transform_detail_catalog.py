"""Replay a frozen full/partial detail acquisition snapshot without network or master writes."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.card_details import transform_run
from src.detail_catalog import load_catalog, verify_saved_fetch
from src.indexer import ROOT, read
from scripts.collect_detail_catalog import SUCCESS, config, private_run, validate_state
from scripts.transform_detail_html import load_cards, save_candidate


def transform_catalog(path, *, root=ROOT, transformer=transform_run):
    run = private_run(path, root)
    catalog = load_catalog(root, run/'catalog.json', config(root))
    # state.json is atomically replaced by the worker: this is one consistent snapshot.
    state = read(run/'state.json')
    validate_state(catalog, state)
    by_id = {card['card_id']: card for card in load_cards(root, catalog['base_dataset_version'])}
    candidates = []
    rows = []
    for card in catalog['unlinked_cards']:
        rows.append({'card_id': card['card_id'], 'card_kind': card['card_kind'],
                     'status': 'missing_page_on_hold'})
    for target in catalog['targets']:
        page = state['pages'][target['id']]
        entry = {'page_id': target['id'], 'input_status': page['status'],
                 'wiki_url': target['url'], 'input_directory': page.get('directory'),
                 'source_sha256': page.get('sha256'), 'fetched_at': page.get('fetched_at')}
        if page['status'] not in SUCCESS:
            rows.extend(dict(entry, card_id=cid, card_kind=target['kind'], status='input_'+page['status'])
                        for cid in target['card_ids'])
            continue
        try:
            report = verify_saved_fetch(root, root/page['directory'], target['url'])
            if report['sha256'] != page['sha256'] or report['fetched_at'] != page['fetched_at']:
                raise ValueError('Checkpoint/input hash or timestamp mismatch')
        except (OSError, ValueError, KeyError) as error:
            rows.extend(dict(entry, card_id=cid, card_kind=target['kind'], status='input_invalid', error=str(error))
                        for cid in target['card_ids'])
            continue
        if target['variant_mapping_required']:
            rows.extend(dict(entry, card_id=cid, card_kind=target['kind'], status='needs_variant_mapping',
                             reason='Shared URL: base and idol-road variants must map to separate sections')
                        for cid in target['card_ids'])
            continue
        cid = target['card_ids'][0]
        try:
            document = transformer(root/page['directory'], by_id[cid], catalog['base_dataset_version'])
            if len(document['cards']) != 1 or document['cards'][0]['card_id'] != cid or (
                    document['cards'][0]['card_kind'] != target['kind']):
                raise ValueError('Transformed identity/kind mismatch')
            candidates.append(document['cards'][0])
            rows.append(dict(entry, card_id=cid, card_kind=target['kind'], status='candidate_needs_review'))
        except (OSError, ValueError, KeyError, IndexError, TypeError) as error:
            rows.append(dict(entry, card_id=cid, card_kind=target['kind'], status='needs_structure_review',
                             error=type(error).__name__+': '+str(error)))
    rows.sort(key=lambda row: row['card_id'])
    candidates.sort(key=lambda card: card['card_id'])
    if len(rows) != catalog['card_count'] or len({row['card_id'] for row in rows}) != len(rows):
        raise ValueError('Coverage cardinality mismatch')
    counts = Counter(row['status'] for row in rows)
    kinds = {kind: dict(Counter(row['status'] for row in rows if row['card_kind'] == kind)) for kind in ('P', 'S')}
    result = {'catalog_candidate_schema': '0.1', 'pilot_schema': '0.3',
              'base_dataset_version': catalog['base_dataset_version'],
              'base_cards_sha256': catalog['base_cards_sha256'],
              'checkpoint_revision': state['revision'], 'checkpoint_updated_at': state['updated_at'],
              'acquisition_status': state['status'], 'input_kind': 'saved_wiki_html',
              'coverage': {'card_count': catalog['card_count'], 'unique_pages': catalog['unique_pages'],
                           'card_status_counts': dict(counts), 'card_status_counts_by_kind': kinds,
                           'known_implemented_on_min': catalog['known_implemented_on_min'],
                           'known_implemented_on_max': catalog['known_implemented_on_max'],
                           'unknown_implemented_on_count': catalog['unknown_implemented_on_count'],
                           'all_target_pages_saved': all(page['status'] in SUCCESS for page in state['pages'].values()),
                           'all_details_validated': False, 'adopted_or_published': False,
                           'unverified': ['Independent game-wide completeness', 'Unlinked pages on hold',
                                          'Shared URL variant mapping', 'Structural exceptions',
                                          'Public effect structure and stable detail IDs', 'Canonical adoption']},
              'cards': candidates, 'card_coverage': rows}
    stable = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    result['content_hash'] = hashlib.sha256(stable.encode('utf-8')).hexdigest()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run_dir', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = transform_catalog(args.run_dir)
    save_candidate(result, args.output)
    print(json.dumps({'output': str(args.output), 'content_hash': result['content_hash'],
                      'checkpoint_revision': result['checkpoint_revision'], **result['coverage']},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
