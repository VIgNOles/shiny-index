"""Compose seven already-saved Wiki pages into a fresh offline transform input.

This never fetches, adopts, or publishes. The original responses stay immutable.
"""
import argparse
import hashlib
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.compare_saved_page import load_saved
from src.indexer import ROOT, read, write

PAGE_DIRS = {
    'W02': 'p-list',
    'W03': 's-list',
    'W04': 's-volume',
    'W07': 'collab',
    'W08': 'road',
    'W05': 'chronology',
    'W09': 'gacha',
}
JST = timezone(timedelta(hours=9))


def compose(destination, sources, *, manifest_path=ROOT / 'source_manifest.json', allowed_root=ROOT / 'private/raw'):
    if set(sources) != set(PAGE_DIRS):
        raise ValueError(f'Exactly these page IDs are required: {sorted(PAGE_DIRS)}')
    manifest = read(manifest_path)
    urls = {page['id']: page['url'] for page in manifest['pages'] + manifest['audit_pages']}
    target = Path(destination).resolve()
    allowed = Path(allowed_root).resolve()
    if target == allowed or not target.is_relative_to(allowed):
        raise ValueError('Composition destination must be inside private/raw')
    if target.exists():
        raise FileExistsError('Use a fresh destination; saved inputs are immutable')
    validated = []
    for page_id, folder_name in PAGE_DIRS.items():
        source = Path(sources[page_id]).resolve()
        if not source.is_dir() or not source.is_relative_to(allowed) or source == target or target.is_relative_to(source) or source.is_relative_to(target):
            raise ValueError(f'Unsafe source/destination for {page_id}')
        saved = load_saved(source)
        if saved['url'] != urls[page_id]:
            raise ValueError(f'Wrong saved page for {page_id}: {saved["url"]}')
        metadata = read(source / 'fetch.json')
        if metadata['sha256'] != saved['sha256']:
            raise ValueError(f'Saved hash mismatch for {page_id}')
        fetched = datetime.fromisoformat(saved['fetched_at'].replace('Z', '+00:00'))
        if fetched.tzinfo is None:
            raise ValueError(f'Unzoned fetched_at for {page_id}')
        validated.append({
            'id': page_id, 'directory': folder_name, 'source': str(source),
            'url': saved['url'], 'sha256': saved['sha256'],
            'fetched_at': saved['fetched_at'],
            'observed_on_jst': fetched.astimezone(JST).date().isoformat(),
        })
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f'.{target.name}-building-', dir=target.parent))
    try:
        for page in validated:
            source = Path(page['source'])
            out = staging / page['directory']
            out.mkdir()
            for name in ('response.html', 'fetch.json', 'limited-run.json'):
                item = source / name
                if item.is_file():
                    shutil.copy2(item, out / name)
            if hashlib.sha256((out / 'response.html').read_bytes()).hexdigest() != page['sha256']:
                raise ValueError(f'Copied hash mismatch for {page["id"]}')
        report = {
            'status': 'validated-saved-pages',
            'full_run': False,
            'pages': validated,
            'confirmed_through_jst': min(page['observed_on_jst'] for page in validated),
            'note': 'Offline composition only; each source response remains immutable.',
        }
        write(staging / 'composition.json', report)
        os.replace(staging, target)
        return report
    except Exception:
        # A partial staging directory is kept for inspection; the final target stays absent.
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination')
    parser.add_argument('--page', action='append', required=True, metavar='ID=SAVED_DIRECTORY')
    args = parser.parse_args()
    sources = {}
    for item in args.page:
        if '=' not in item:
            parser.error('--page must be ID=SAVED_DIRECTORY')
        page_id, directory = item.split('=', 1)
        if page_id in sources:
            parser.error(f'duplicate page ID: {page_id}')
        sources[page_id] = directory
    report = compose(args.destination, sources)
    print(f"Composed {len(report['pages'])} saved pages through {report['confirmed_through_jst']}; no network or master changes.")


if __name__ == '__main__':
    main()
