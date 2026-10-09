"""Bounded sequential detail acquisition; private checkpoints, no adoption/publication."""
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.indexer import ROOT, read, write
from src.detail_catalog import build_catalog, load_catalog, verify_saved_fetch
from src.card_details import wiki_key
from scripts.collect_one import STATE, as_utc, fetch_one, status as availability
from scripts.transform_detail_html import save_candidate

SUCCESS = {'fetched', 'reused'}
STATUSES = SUCCESS | {'pending', 'failed', 'needs_inspection'}


def utcnow():
    return datetime.now(timezone.utc)


def stamp(current=None):
    return (current or utcnow()).isoformat(timespec='seconds')


def private_run(path, root=ROOT):
    path = Path(path).resolve()
    if not path.is_relative_to((root/'private/raw').resolve()):
        raise ValueError('Acquisition runs must stay under private/raw/')
    return path


def config(root):
    return read(root/'source_manifest.json')


def validate_state(catalog, state):
    ids = {target['id'] for target in catalog['targets']}
    if set(state['pages']) != ids or state['base_dataset_version'] != catalog['base_dataset_version']:
        raise ValueError('Checkpoint/catalogue mismatch')
    if any(page['status'] not in STATUSES for page in state['pages'].values()):
        raise ValueError('Invalid checkpoint status')
    if state.get('active_attempt') and state['active_attempt']['page_id'] not in ids:
        raise ValueError('Unregistered active attempt')


def checkpoint(run, state):
    state['revision'] += 1
    state['updated_at'] = stamp()
    write(run/'state.json', state)


def completed_page(report, directory, root, status):
    return {'status': status, 'directory': directory.resolve().relative_to(root.resolve()).as_posix(),
            'sha256': report['sha256'], 'fetched_at': report['fetched_at']}


def initialize(path, *, root=ROOT):
    run = private_run(path, root)
    if run.exists():
        raise FileExistsError('Use a fresh run directory; initialization is immutable')
    manifest = config(root)
    if manifest.get('detail_catalog_enabled') is not True:
        raise RuntimeError('Detail catalogue acquisition is disabled')
    catalog = build_catalog(root, manifest['detail_base_dataset_version'])
    if catalog['card_count'] != manifest['detail_catalog_expected_cards'] or (
            catalog['unique_pages'] != manifest['detail_catalog_expected_pages']):
        raise ValueError('Unexpected card/page count; inspect before acquisition')
    pages = {target['id']: {'status': 'pending'} for target in catalog['targets']}
    targets = {wiki_key(target['url']): target for target in catalog['targets']}
    saved = {}
    ignored = []
    for report_path in sorted((root/'private/raw').rglob('fetch.json')):
        try:
            report = read(report_path)
            key = wiki_key(report['url'])
        except (ValueError, KeyError):
            continue
        if key not in targets or report.get('status') != 'fetched':
            continue
        try:
            report = verify_saved_fetch(root, report_path.parent, targets[key]['url'])
        except (OSError, ValueError, KeyError) as error:
            ignored.append({'directory': str(report_path.parent.relative_to(root)), 'error': str(error)})
            continue
        if key not in saved or as_utc(report['fetched_at']) > as_utc(saved[key][0]['fetched_at']):
            saved[key] = (report, report_path.parent)
    for key, (report, directory) in saved.items():
        pages[targets[key]['id']] = completed_page(report, directory, root, 'reused')
    save_candidate(catalog, run/'catalog.json', root)
    state = {'state_schema': '1.0', 'base_dataset_version': catalog['base_dataset_version'],
             'created_at': stamp(), 'updated_at': stamp(), 'revision': 0,
             'status': 'ready', 'pages': pages, 'active_attempt': None,
             'ignored_saved_inputs': ignored, 'history': []}
    write(run/'state.json', state)
    return report_status(run, root=root)


def report_status(path, *, root=ROOT):
    run = private_run(path, root)
    catalog = load_catalog(root, run/'catalog.json', config(root))
    state = read(run/'state.json')
    validate_state(catalog, state)
    counts = Counter(page['status'] for page in state['pages'].values())
    cards = Counter()
    times = []
    for target in catalog['targets']:
        page = state['pages'][target['id']]
        cards[page['status']] += len(target['card_ids'])
        if page['status'] in SUCCESS:
            times.append(page['fetched_at'])
    acquired = counts['fetched'] + counts['reused']
    worker = read(run/'worker.lock') if (run/'worker.lock').exists() else None
    return {'run': str(run.relative_to(root)), 'status': state['status'], 'revision': state['revision'],
            'updated_at': state['updated_at'], 'base_dataset_version': catalog['base_dataset_version'],
            'card_count': catalog['card_count'], 'card_kind_counts': catalog['card_kind_counts'],
            'unique_pages': catalog['unique_pages'], 'page_status_counts': dict(counts),
            'cards_by_input_status': dict(cards), 'unlinked_cards_on_hold': len(catalog['unlinked_cards']),
            'shared_url_pages_needing_variant_mapping': catalog['shared_url_pages'],
            'acquired_pages': acquired, 'page_acquisition_complete': acquired == catalog['unique_pages'],
            'details_adopted_or_published': False,
            'input_fetched_at_min': min(times, key=as_utc) if times else None,
            'input_fetched_at_max': max(times, key=as_utc) if times else None,
            'known_implemented_on_min': catalog['known_implemented_on_min'],
            'known_implemented_on_max': catalog['known_implemented_on_max'],
            'unknown_implemented_on_count': catalog['unknown_implemented_on_count'],
            'active_attempt': state.get('active_attempt'), 'next_allowed_at': state.get('next_allowed_at'),
            'stop_reason': state.get('stop_reason'), 'worker': worker,
            'worker_is_alive': process_alive(worker['pid']) if worker else False,
            'stop_requested': (run/'STOP').exists()}


def recover_attempt(run, catalog, state, root, current):
    active = state.get('active_attempt')
    if not active:
        return
    target = next(t for t in catalog['targets'] if t['id'] == active['page_id'])
    directory = root/active['directory']
    try:
        report = verify_saved_fetch(root, directory, target['url'])
        state['pages'][target['id']] = completed_page(report, directory, root, 'fetched')
        state['history'].append({'event': 'recovered_completed_attempt', **active})
        state['last_completed_at'] = stamp(current)
    except (OSError, ValueError, KeyError) as error:
        # Absence is not proof the request was never sent. Never silently refetch.
        state['pages'][target['id']] = {'status': 'needs_inspection', **active, 'error': str(error)}
        state['status'] = 'needs_inspection'
        state['stop_reason'] = 'Interrupted attempt has no verified complete response'
    state['active_attempt'] = None
    checkpoint(run, state)



def verify_completed_inputs(run, catalog, state, root):
    for target in catalog['targets']:
        page = state['pages'][target['id']]
        if page['status'] not in SUCCESS:
            continue
        try:
            report = verify_saved_fetch(root, root/page['directory'], target['url'])
            if report['sha256'] != page['sha256'] or report['fetched_at'] != page['fetched_at']:
                raise ValueError('Saved input/checkpoint mismatch')
        except (OSError, ValueError, KeyError) as error:
            state['history'].append({'event': 'saved_input_integrity_failure', 'page_id': target['id'],
                                     'previous': page})
            state['pages'][target['id']] = dict(page, status='needs_inspection', error=str(error))
            state['status'] = 'needs_inspection'
            state['stop_reason'] = 'Saved response integrity failed; no automatic replacement'
            checkpoint(run, state)
            return False
    return True


def failure_is_cooling(manifest, shared, current):
    backoff = manifest.get('single_page_failure_backoff_seconds', 86400)
    return any(shared.get(key) and current < as_utc(shared[key])+timedelta(seconds=backoff)
               for key in ('last_failure_at', 'last_rate_limit_at')) or (
        bool(shared.get('server_not_before_at')) and current < as_utc(shared['server_not_before_at']))


def run_worker(path, max_attempts, *, root=ROOT, state_path=STATE, fetch=fetch_one,
               clock=utcnow, sleep=time.sleep, clear_stop=False, retry_page=None):
    run = private_run(path, root)
    manifest = config(root)
    catalog = load_catalog(root, run/'catalog.json', manifest)
    cap = manifest['detail_catalog_expected_pages']
    if (not isinstance(max_attempts, int) or isinstance(max_attempts, bool) or
            not 1 <= max_attempts <= cap or catalog['unique_pages'] != cap):
        raise ValueError('Invalid bounded page budget or abnormal catalogue count')
    lock = run/'worker.lock'
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump({'pid': os.getpid(), 'started_at': stamp(clock()), 'max_attempts': max_attempts}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        state = read(run/'state.json')
        validate_state(catalog, state)
        recover_attempt(run, catalog, state, root, clock())
        if not verify_completed_inputs(run, catalog, state, root):
            return report_status(run, root=root)
        if any(page['status'] == 'needs_inspection' for page in state['pages'].values()):
            return report_status(run, root=root)
        if retry_page:
            if retry_page not in state['pages'] or state['pages'][retry_page]['status'] != 'failed':
                raise ValueError('Explicit retry requires one reviewed failed page ID')
            shared = read(state_path)
            previous_failure = state['pages'][retry_page]
            local_failure_at = previous_failure.get('failed_at') or previous_failure.get('started_at')
            if local_failure_at and clock() < as_utc(local_failure_at)+timedelta(seconds=manifest.get('single_page_failure_backoff_seconds',86400)):
                raise RuntimeError('Local acquisition failure backoff has not elapsed')
            if not availability(config(root), shared, clock())['can_fetch']:
                raise RuntimeError('Failure backoff/server deadline has not elapsed')
            state['history'].append({'event': 'explicit_retry', 'at': stamp(clock()),
                                     'page_id': retry_page, 'previous': state['pages'][retry_page]})
            state['pages'][retry_page] = {'status': 'pending'}
        if any(page['status'] == 'failed' for page in state['pages'].values()):
            state['status'] = 'failed'
            state['stop_reason'] = 'Review failure and explicitly retry one page after backoff'
            checkpoint(run, state)
            return report_status(run, root=root)
        if clear_stop and (run/'STOP').exists():
            (run/'STOP').unlink()
        state['status'] = 'running'
        state.pop('stop_reason', None)
        state['worker_pid'] = os.getpid()
        checkpoint(run, state)
        attempts = 0
        for target in catalog['targets']:
            if state['pages'][target['id']]['status'] in SUCCESS:
                continue
            if attempts >= max_attempts:
                break
            while True:
                if (run/'STOP').exists():
                    state['status'] = 'stopped'
                    state['stop_reason'] = 'Operator requested a safe stop'
                    checkpoint(run, state)
                    return report_status(run, root=root)
                manifest = config(root)
                if manifest.get('detail_catalog_enabled') is not True:
                    raise RuntimeError('Detail acquisition disabled during execution')
                shared = read(state_path)
                current = clock()
                allowed = availability(manifest, shared, current)
                if not allowed['initialized'] or not allowed['single_page_enabled']:
                    raise RuntimeError('Shared acquisition control unavailable')
                if failure_is_cooling(manifest, shared, current):
                    state['status'] = 'blocked_backoff'
                    state['stop_reason'] = 'Shared acquisition failure/server backoff; no automatic retry'
                    state['next_allowed_at'] = allowed['next_allowed_at']
                    checkpoint(run, state)
                    return report_status(run, root=root)
                deadline = as_utc(allowed['next_allowed_at'])
                if state.get('last_completed_at'):
                    deadline = max(deadline, as_utc(state['last_completed_at']) +
                                   timedelta(seconds=manifest['single_page_cooldown_seconds']))
                if current >= deadline:
                    break
                if state.get('next_allowed_at') != stamp(deadline):
                    state['next_allowed_at'] = stamp(deadline)
                    checkpoint(run, state)
                sleep(min(2, max(0.05, (deadline-current).total_seconds())))
            directory = run/'pages'/target['id']/('attempt-'+uuid.uuid4().hex)
            active = {'page_id': target['id'], 'directory': directory.relative_to(root).as_posix(),
                      'started_at': stamp(clock())}
            state['active_attempt'] = active
            state['next_allowed_at'] = None
            checkpoint(run, state)
            attempts += 1
            try:
                fetch(target['id'], directory, current=clock(), state_path=state_path,
                      catalog_path=run/'catalog.json')
                report = verify_saved_fetch(root, directory, target['url'])
                state['pages'][target['id']] = completed_page(report, directory, root, 'fetched')
                state['last_completed_at'] = stamp(clock())
                state['active_attempt'] = None
                checkpoint(run, state)
                print(json.dumps({'page_id': target['id'], 'status': 'fetched', 'at': stamp(clock()),
                                  'cards': target['card_ids'], 'attempts_this_worker': attempts}, ensure_ascii=False), flush=True)
            except Exception as error:
                state['pages'][target['id']] = {'status': 'failed', **active, 'failed_at': stamp(clock()),
                                              'error': type(error).__name__+': '+str(error)}
                state['status'] = 'failed'
                state['stop_reason'] = 'Acquisition failed; all following pages stopped'
                state['active_attempt'] = None
                checkpoint(run, state)
                print(json.dumps({'page_id': target['id'], 'status': 'failed', 'error': str(error)}, ensure_ascii=False), flush=True)
                return report_status(run, root=root)
        if all(page['status'] in SUCCESS for page in state['pages'].values()):
            state['status'] = 'verifying_inputs'
            checkpoint(run, state)
            if not verify_completed_inputs(run, catalog, state, root):
                return report_status(run, root=root)
        state['status'] = ('complete' if all(page['status'] in SUCCESS for page in state['pages'].values())
                           else 'budget_finished')
        checkpoint(run, state)
        return report_status(run, root=root)
    except Exception as error:
        if 'state' in locals():
            state['status'] = 'stopped_error'
            state['stop_reason'] = type(error).__name__+': '+str(error)
            checkpoint(run, state)
        raise
    except KeyboardInterrupt:
        if 'state' in locals():
            state['status'] = 'interrupted'
            state['stop_reason'] = 'Keyboard interrupt; verify active attempt before resume'
            checkpoint(run, state)
        raise
    finally:
        lock.unlink(missing_ok=True)


def process_alive(pid):
    if os.name == 'nt':
        import ctypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            if ctypes.get_last_error() == 87:
                return False
            raise OSError('Cannot establish whether worker is still running')
        try:
            code = ctypes.c_ulong()
            if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
                raise OSError('Cannot read worker exit status')
            return code.value == 259
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def release_stale_lock(path, expected_pid, *, root=ROOT, lock_kind='worker'):
    run = private_run(path, root)
    lock = run/'worker.lock'
    if lock_kind not in ('worker', 'workflow'):
        raise ValueError('Unknown lock kind')
    lock = run/(lock_kind+'.lock')
    owner = read(lock)
    if owner['pid'] != expected_pid or process_alive(expected_pid):
        raise RuntimeError('Lock owner mismatch or worker is still running')
    # The shared request lock may describe an in-flight/unknown request. Never remove it here.
    lock.unlink()
    return {'released_pid': expected_pid, 'lock_kind': lock_kind, 'shared_request_lock_untouched': True}



def resolve_unknown(path, page_id, reason, *, root=ROOT, state_path=STATE, current=None):
    """Operator-reviewed unknown attempt: recover saved success or mark failure, never fetch."""
    if not reason.strip():
        raise ValueError('Inspection reason is required')
    run = private_run(path, root)
    current = current or utcnow()
    worker_lock = run/'worker.lock'
    request_lock = Path(state_path).with_suffix('.lock')
    worker_fd = os.open(worker_lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    request_fd = None
    try:
        os.write(worker_fd, json.dumps({'pid': os.getpid(), 'started_at': stamp(current),
                                       'operation': 'resolve_unknown'}).encode('utf-8'))
        request_fd = os.open(request_lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        catalog = load_catalog(root, run/'catalog.json', config(root))
        state = read(run/'state.json')
        validate_state(catalog, state)
        previous = state['pages'].get(page_id)
        if not previous or previous['status'] != 'needs_inspection':
            raise ValueError('Only an inspected ambiguous page may be resolved')
        target = next(target for target in catalog['targets'] if target['id'] == page_id)
        try:
            report = verify_saved_fetch(root, root/previous['directory'], target['url'])
            state['pages'][page_id] = completed_page(report, root/previous['directory'], root, 'fetched')
            state['last_completed_at'] = stamp(current)
        except (OSError, ValueError, KeyError):
            state['pages'][page_id] = dict(previous, status='failed', inspection_reason=reason)
            shared = read(state_path)
            # Conservative local recovery backoff from review time; preserve attempt/server history.
            shared['last_failure_at'] = stamp(current)
            shared['last_failure_reason'] = 'Unknown interrupted request: '+reason
            write(state_path, shared)
        state['history'].append({'event': 'resolved_unknown_attempt', 'at': stamp(current),
                                 'page_id': page_id, 'reason': reason, 'previous': previous})
        state['status'] = 'ready' if state['pages'][page_id]['status'] == 'fetched' else 'failed'
        checkpoint(run, state)
        return report_status(run, root=root)
    finally:
        if request_fd is not None:
            os.close(request_fd)
            request_lock.unlink()
        os.close(worker_fd)
        worker_lock.unlink()


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('init', 'status', 'stop', 'run', 'release-stale-lock', 'resolve-unknown'):
        command = sub.add_parser(name)
        command.add_argument('run_dir', type=Path)
        if name == 'run':
            command.add_argument('--max-attempts', type=int, required=True)
            command.add_argument('--clear-stop', action='store_true')
            command.add_argument('--retry-page')
        if name == 'resolve-unknown':
            command.add_argument('--page-id', required=True)
            command.add_argument('--reason', required=True)
        if name == 'release-stale-lock':
            command.add_argument('--expected-pid', type=int, required=True)
            command.add_argument('--lock-kind', choices=('worker','workflow'), default='worker')
    args = parser.parse_args()
    if args.command == 'init':
        result = initialize(args.run_dir)
    elif args.command == 'run':
        result = run_worker(args.run_dir, args.max_attempts, clear_stop=args.clear_stop, retry_page=args.retry_page)
    elif args.command == 'stop':
        run = private_run(args.run_dir)
        if not (run/'state.json').exists():
            raise ValueError('Run is not initialized')
        (run/'STOP').touch(exist_ok=True)
        result = report_status(run)
    elif args.command == 'resolve-unknown':
        result = resolve_unknown(args.run_dir, args.page_id, args.reason)
    elif args.command == 'release-stale-lock':
        result = release_stale_lock(args.run_dir, args.expected_pid, lock_kind=args.lock_kind)
    else:
        result = report_status(args.run_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
