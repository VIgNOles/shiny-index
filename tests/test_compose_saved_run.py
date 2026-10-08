"""Offline composition must reject wrong, corrupt, and incomplete saved inputs."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.compose_saved_run import PAGE_DIRS, compose
from src.indexer import read, write


class ComposeSavedRunTests(unittest.TestCase):
    def fixture(self, root):
        pages = []
        sources = {}
        for n, page_id in enumerate(PAGE_DIRS):
            url = f'https://wikiwiki.jp/shinycolors/test-{page_id}'
            pages.append({'id': page_id, 'url': url})
            source = root / f'source-{page_id}'
            source.mkdir()
            raw = f'<html><head><link rel="canonical" href="{url}"></head><body><div id="content">Card {page_id}</div></body></html>'.encode()
            (source / 'response.html').write_bytes(raw)
            write(source / 'fetch.json', {
                'status': 'fetched', 'url': url,
                'sha256': hashlib.sha256(raw).hexdigest(),
                'fetched_at': '2026-10-08T00:00:00+00:00' if n else '2026-10-07T14:00:00+00:00',
            })
            sources[page_id] = source
        manifest = root / 'manifest.json'
        write(manifest, {'pages': pages, 'audit_pages': []})
        return sources, manifest

    def test_verified_composition_keeps_sources_and_uses_oldest_jst_date(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sources, manifest = self.fixture(root)
            before = {page_id: (path / 'response.html').read_bytes() for page_id, path in sources.items()}
            out = root / 'composed'
            result = compose(out, sources, manifest_path=manifest, allowed_root=root)
            self.assertEqual(result['confirmed_through_jst'], '2026-10-07')
            self.assertFalse(result['full_run'])
            self.assertEqual(len(result['pages']), 7)
            for page_id, folder in PAGE_DIRS.items():
                self.assertEqual((out / folder / 'response.html').read_bytes(), before[page_id])
                self.assertEqual((sources[page_id] / 'response.html').read_bytes(), before[page_id])
            self.assertEqual(read(out / 'composition.json'), result)
            with self.assertRaises(FileExistsError):
                compose(out, sources, manifest_path=manifest, allowed_root=root)

    def test_wrong_page_or_corrupt_hash_stops_before_final_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sources, manifest = self.fixture(root)
            wrong = root / 'wrong'
            info = read(sources['W09'] / 'fetch.json')
            info['url'] = 'https://wikiwiki.jp/shinycolors/another-page'
            write(sources['W09'] / 'fetch.json', info)
            with self.assertRaises(ValueError):
                compose(wrong, sources, manifest_path=manifest, allowed_root=root)
            self.assertFalse(wrong.exists())
            info['url'] = 'https://wikiwiki.jp/shinycolors/test-W09'
            info['sha256'] = '0' * 64
            write(sources['W09'] / 'fetch.json', info)
            with self.assertRaises(ValueError):
                compose(wrong, sources, manifest_path=manifest, allowed_root=root)
            self.assertFalse(wrong.exists())

    def test_public_destination_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            private = root / 'private'
            private.mkdir()
            sources, manifest = self.fixture(private)
            outside = root / 'site' / 'raw'
            with self.assertRaisesRegex(ValueError, 'inside private/raw'):
                compose(outside, sources, manifest_path=manifest, allowed_root=private)
            self.assertFalse(outside.exists())

    def test_missing_page_stops_before_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sources, manifest = self.fixture(root)
            sources.pop('W09')
            with self.assertRaisesRegex(ValueError, 'Exactly these page IDs'):
                compose(root / 'composed', sources, manifest_path=manifest, allowed_root=root)
            self.assertFalse((root / 'composed').exists())


if __name__ == '__main__':
    unittest.main()
