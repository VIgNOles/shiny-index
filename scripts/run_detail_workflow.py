"""One bounded acquisition, then an independent offline audit; never retries/publishes."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.indexer import ROOT, write
from scripts.collect_detail_catalog import STATE, private_run, run_worker, report_status, stamp
from scripts.transform_detail_catalog import transform_catalog
from scripts.transform_detail_html import save_candidate


def run_workflow(path, max_attempts, *, root=ROOT, state_path=STATE,
                 worker=run_worker, transformer=transform_catalog, **worker_options):
    run = private_run(path, root)
    # An exclusive workflow lock also covers the final offline transform.
    import os
    lock = run/'workflow.lock'
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    report_path = run/'workflow-report.json'
    try:
        owner = {'pid': os.getpid(), 'started_at': stamp()}
        os.write(fd, json.dumps(owner).encode('utf-8'))
        report = dict(owner, phase='acquisition', adopted_or_published=False)
        write(report_path, report)
        try:
            worker(path, max_attempts, root=root, state_path=state_path, **worker_options)
        except Exception as error:
            report['acquisition_error'] = type(error).__name__+': '+str(error)
        report['phase'] = 'offline_audit'
        write(report_path, report)
        # Parse a snapshot even when acquisition stops/fails: report every card's actual state.
        candidate = transformer(path, root=root)
        output = root/'private/audits'/('detail-catalog-'+candidate['content_hash']+'.json')
        save_candidate(candidate, output, root)
        report.update(phase='finished', finished_at=stamp(),
                      candidate_file=output.relative_to(root).as_posix(),
                      candidate_content_hash=candidate['content_hash'],
                      coverage=candidate['coverage'], acquisition=report_status(run, root=root))
        write(report_path, report)
        return report
    except BaseException as error:
        if 'report' in locals():
            report.update(phase='interrupted' if isinstance(error, KeyboardInterrupt) else 'audit_failed',
                          error=type(error).__name__+': '+str(error), ended_at=stamp())
            write(report_path, report)
        raise
    finally:
        os.close(fd)
        lock.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run_dir', type=Path)
    parser.add_argument('--max-attempts', type=int, required=True)
    parser.add_argument('--clear-stop', action='store_true')
    parser.add_argument('--retry-page')
    args = parser.parse_args()
    result = run_workflow(args.run_dir, args.max_attempts,
                          clear_stop=args.clear_stop, retry_page=args.retry_page)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    if result.get('acquisition_error') or result['acquisition']['status'] in ('failed','needs_inspection','stopped_error','blocked_backoff'):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
