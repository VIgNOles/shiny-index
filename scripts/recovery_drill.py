"""Exercise snapshot recovery in a new private directory; no network or production writes."""
import argparse
from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import json
import re
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.check_site import check
from src.detail_master import from_workbook


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def hashes(directory):
    return {p.relative_to(directory).as_posix(): sha(p)
            for p in sorted(Path(directory).rglob('*')) if p.is_file()}


def checked_site(site):
    with redirect_stdout(io.StringIO()):
        return check(site)


def check_pair(site, master, connection):
    conn = json.loads(Path(connection).read_text(encoding='utf-8'))
    latest = json.loads((Path(site) / 'details/latest.json').read_text(encoding='utf-8'))
    if sha(master) != conn['baseline_sha256']:
        raise ValueError('Original workbook hash mismatch')
    # The connection stores the last native Sheet publication. Later derived
    # effect releases intentionally change only the public content version.
    native_version=conn['detail_dataset_version'];public_version=latest['detail_version']
    if not all(isinstance(v,str) and re.fullmatch(r'd1-[0-9a-f]{16}',v) for v in (native_version,public_version)):
        raise ValueError('Invalid original/public detail version')
    docs=[json.loads((Path(site)/'details'/version/'details.json').read_text(encoding='utf-8'))
          for version in (native_version,public_version)]
    native,current=docs
    revision=conn.get('canonical_detail_revision',conn.get('detail_revision'))
    if type(revision) is not int or any(d['meta']['canonical_detail_revision']!=revision for d in docs):
        raise ValueError('Original/public canonical revision mismatch')
    for key in ('base_dataset_version','source_base_dataset_version'):
        if native['meta'][key]!=current['meta'][key]:
            raise ValueError('Original/public base version mismatch')
    def canonical_fields(doc):
        return {'cards':[{**{k:v for k,v in card.items() if k!='items'},
                         'items':[{k:v for k,v in item.items() if k!='effect_details'} for item in card['items']]}
                        for card in doc['cards']],
                'coverage':{k:v for k,v in doc['coverage'].items() if k!='effect_detail_counts'}}
    if canonical_fields(native)!=canonical_fields(current):
        raise ValueError('Original/public non-effect fields mismatch')
    return {'native_detail_version':native_version,'derived_public_version':public_version,
            'canonical_detail_revision':revision,'non_effect_fields_equal':True}


def run(site, master, connection, output):
    site, master, connection, output = [Path(p).resolve() for p in (site, master, connection, output)]
    private = (ROOT / 'private').resolve()
    if (not all(p.is_relative_to(ROOT) for p in (site, master, connection))
            or output == private or not output.is_relative_to(private)
            or any(output.is_relative_to(p) or p.is_relative_to(output) for p in (site, master, connection))
            or output.exists()):
        raise ValueError('Use a new, separate private output directory and project snapshots')
    association=check_pair(site, master, connection)
    checked_site(site)
    baseline = {'site': hashes(site), 'master': sha(master), 'connection': sha(connection)}
    output.mkdir(parents=True)
    restored = output / 'restored'
    shutil.copytree(site, restored / 'site')
    shutil.copy2(master, restored / 'master.xlsx')
    shutil.copy2(connection, restored / 'connection.json')
    target = restored / 'site'
    pair = lambda: check_pair(target, restored / 'master.xlsx', restored / 'connection.json')
    cases = []

    def rejected(name, validate):
        try:
            validate()
        except (ValueError, KeyError, FileNotFoundError, json.JSONDecodeError) as error:
            cases.append({'case': name, 'detected': True, 'error': str(error)})
        else:
            raise AssertionError('Corruption was not detected: ' + name)

    latest = json.loads((target / 'details/latest.json').read_text(encoding='utf-8'))
    relative = Path('details') / latest['detail_version'] / 'details.json'
    damaged = target / relative
    damaged.write_bytes(b'{"broken":true}\n')
    rejected('detail_payload_corrupted', lambda: checked_site(target))
    shutil.copy2(site / relative, damaged)

    doc=json.loads(damaged.read_text(encoding='utf-8'))
    doc['cards'][0]['items'][0]['name'] += ' interrupted value'
    damaged.write_text(json.dumps(doc),encoding='utf-8')
    rejected('derived_non_effect_value_changed',pair)
    shutil.copy2(site/relative,damaged)

    (restored / 'master.xlsx').write_bytes(b'interrupted workbook replacement\n')
    rejected('original_workbook_corrupted', pair)
    shutil.copy2(master, restored / 'master.xlsx')

    conn = json.loads((restored / 'connection.json').read_text(encoding='utf-8'))
    conn['detail_dataset_version'] = 'd1-0000000000000000'
    (restored / 'connection.json').write_text(json.dumps(conn), encoding='utf-8')
    rejected('original_public_version_mismatch', pair)

    # Reapply the complete saved snapshot, without deleting anything or touching sources.
    shutil.copytree(site, target, dirs_exist_ok=True)
    shutil.copy2(master, restored / 'master.xlsx')
    shutil.copy2(connection, restored / 'connection.json')
    pair()
    checked_site(target)
    assert hashes(target) == baseline['site']
    assert sha(restored / 'master.xlsx') == baseline['master']
    assert sha(restored / 'connection.json') == baseline['connection']
    canonical = from_workbook(restored / 'master.xlsx')
    assert hashes(site) == baseline['site'] and sha(master) == baseline['master'] and sha(connection) == baseline['connection']
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'isolated_only': True,
              'network_requests': 0, 'source_files_unchanged': True, 'cases': cases,
              'full_site_files_restored': len(baseline['site']), 'full_site_bytes_match': True,
              'master_sha256': baseline['master'], 'canonical_detail_revision': canonical['revision'],
              'canonical_detail_cards': len(canonical['cards']),
              'canonical_detail_items': len(canonical['registry']),
              'connection_bytes_restored': True, 'detail_version': latest['detail_version'],
              'live_production_failure_rehearsed': False, 'original_public_association':association}
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', default='site')
    parser.add_argument('--master', default='private/master.xlsx')
    parser.add_argument('--connection', default='private/sheets-connection.json')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.site, args.master, args.connection, args.output), ensure_ascii=False))
