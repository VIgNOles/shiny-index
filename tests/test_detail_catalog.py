"""Network-free checks of full detail boundaries, pause/recovery and failure stop."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import scripts.collect_detail_catalog as bulk
import scripts.collect_one as single
from src.detail_catalog import build_catalog, load_catalog, verify_saved_fetch
from src.indexer import read, write
from scripts.transform_detail_catalog import transform_catalog
from scripts.run_detail_workflow import run_workflow

VERSION = 'v1-0000000000000000'


class BulkDetailTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.current = datetime(2026, 10, 9, tzinfo=timezone.utc)
        self.cards = [self.card('p1', 'P', '【A】人物'), self.card('s1', 'S', '【B】人物')]
        self.manifest = {'detail_catalog_enabled': True, 'detail_catalog_expected_cards': 2,
                         'detail_catalog_expected_pages': 2, 'detail_base_dataset_version': VERSION,
                         'single_page_collection_enabled': True, 'single_page_cooldown_seconds': 60,
                         'single_page_failure_backoff_seconds': 86400, 'full_collection_enabled': False,
                         'pages': [], 'audit_pages': [], 'detail_pages': []}
        self.state_path = self.root/'private/raw/acquisition-state.json'
        self.run = self.root/'private/raw/full'
        self.write_base()
        write(self.state_path, {'last_attempt_at': (self.current-timedelta(days=2)).isoformat()})
        self.clock_value = self.current

    def card(self, cid, kind, title, variant='base'):
        return {'card_id': cid, 'game': 'shinycolors_enza', 'card_kind': kind,
                'card_title': title, 'idol_name': '人物', 'rarity': 'SSR', 'variant_kind': variant,
                'wiki_url': 'https://wikiwiki.jp/shinycolors/'+title,
                'first_implemented_on': '2020-01-01'}

    def write_base(self):
        write(self.root/'site/data'/VERSION/'cards.json', {'cards': self.cards})
        write(self.root/'source_manifest.json', self.manifest)

    def saved(self, directory, url, fetched_at=None):
        directory.mkdir(parents=True)
        html = ('<html><head><meta charset="utf-8"><link rel="canonical" href="'+url+
                '"></head><body><div id="content"><table><tr><td>'+('実データ '*300)+
                '</td></tr></table></div></body></html>').encode('utf-8')
        (directory/'response.html').write_bytes(html)
        write(directory/'fetch.json', {'url': url, 'status': 'fetched', 'http_status': 200,
                                      'fetched_at': (fetched_at or self.current).isoformat(),
                                      'sha256': hashlib.sha256(html).hexdigest()})

    def clock(self):
        return self.clock_value

    def sleep(self, seconds):
        self.clock_value += timedelta(seconds=seconds)

    def fetch_adapter(self, failing=None, calls=None):
        def raw_fetch(url, directory, *, allow_limited):
            if calls is not None:
                calls.append((url, self.clock()))
            if failing is not None and len(calls) == 2:
                directory.mkdir(parents=True)
                raise failing
            self.saved(directory, url, self.clock())
        def fetch(page, directory, **kwargs):
            with patch.object(single, 'ROOT', self.root):
                return single.fetch_one(page, directory, fetcher=raw_fetch, **kwargs)
        return fetch

    def initialize(self):
        return bulk.initialize(self.run, root=self.root)

    def run_worker(self, budget=2, **kwargs):
        return bulk.run_worker(self.run, budget, root=self.root, state_path=self.state_path,
                               clock=self.clock, sleep=self.sleep, **kwargs)

    def test_shared_url_dedup_preserves_ids_and_missing_hold(self):
        self.cards += [self.card('p2', 'P', '【A】人物', 'idol_road_sr'),
                       self.card('p3', 'P', '【A】人物', 'idol_road_ssr')]
        missing = self.card('m1', 'S', '【未作成】人物')
        missing['wiki_url'] = None
        self.cards.append(missing)
        self.write_base()
        catalog = build_catalog(self.root, VERSION)
        self.assertEqual((catalog['card_count'], catalog['unique_pages'], catalog['linked_cards']), (5, 2, 4))
        self.assertEqual(catalog['targets'][0]['card_ids'], ['p1', 'p2', 'p3'])
        self.assertTrue(catalog['targets'][0]['variant_mapping_required'])
        self.assertEqual(catalog['unlinked_cards'][0]['status'], 'missing_page')

    def test_invalid_kind_url_and_duplicate_ids_fail(self):
        for field, value in [('card_kind', 'other'), ('game', 'other'),
                             ('wiki_url', 'https://example.com/shinycolors/【A】人物'),
                             ('card_id', 's1')]:
            with self.subTest(field=field):
                previous = self.cards[0][field]
                self.cards[0][field] = value
                self.write_base()
                with self.assertRaises(ValueError):
                    build_catalog(self.root, VERSION)
                self.cards[0][field] = previous

    def test_changed_catalog_or_base_count_is_rejected_before_fetch(self):
        self.initialize()
        catalog = read(self.run/'catalog.json')
        catalog['targets'][0]['url'] = self.cards[1]['wiki_url']
        write(self.run/'catalog.json', catalog)
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            self.run_worker(fetch=lambda *a, **k: self.fail('network'))
        self.assertFalse((self.run/'worker.lock').exists())

    def test_saved_response_is_reused_and_not_refetched(self):
        self.saved(self.root/'private/raw/old', self.cards[0]['wiki_url'])
        result = self.initialize()
        self.assertEqual(result['page_status_counts'], {'reused': 1, 'pending': 1})
        calls = []
        result = self.run_worker(fetch=self.fetch_adapter(calls=calls))
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], self.cards[1]['wiki_url'])
        self.assertTrue(result['page_acquisition_complete'])
        self.assertFalse(result['details_adopted_or_published'])

    def test_saved_hash_corruption_is_not_reused(self):
        directory = self.root/'private/raw/old'
        self.saved(directory, self.cards[0]['wiki_url'])
        (directory/'response.html').write_text('corrupt', encoding='utf-8')
        result = self.initialize()
        self.assertEqual(result['page_status_counts'], {'pending': 2})
        self.assertEqual(len(read(self.run/'state.json')['ignored_saved_inputs']), 1)

    def test_429_stops_batch_and_retains_success_with_server_backoff(self):
        self.initialize()
        calls = []
        error = HTTPError('test', 429, 'Too Many Requests', {'Retry-After': '172800'}, None)
        result = self.run_worker(fetch=self.fetch_adapter(error, calls))
        self.assertEqual(len(calls), 2)
        self.assertGreaterEqual((calls[1][1]-calls[0][1]).total_seconds(), 60)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['page_status_counts'], {'fetched': 1, 'failed': 1})
        self.assertIn('server_not_before_at', read(self.state_path))
        self.run_worker(fetch=lambda *a, **k: self.fail('automatic retry'))
        self.assertFalse((self.run/'worker.lock').exists())
        self.assertEqual(read(self.root/'site/data'/VERSION/'cards.json')['cards'], self.cards)

    def test_budget_resume_retains_success_and_spacing(self):
        self.initialize()
        calls = []
        result = self.run_worker(1, fetch=self.fetch_adapter(calls=calls))
        self.assertEqual(result['status'], 'budget_finished')
        result = self.run_worker(1, fetch=self.fetch_adapter(calls=calls))
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(len(calls), 2)
        self.assertGreaterEqual((calls[1][1]-calls[0][1]).total_seconds(), 60)

    def test_stop_and_second_worker_make_no_network_call(self):
        self.initialize()
        (self.run/'STOP').touch()
        result = self.run_worker(fetch=lambda *a, **k: self.fail('network'))
        self.assertEqual(result['status'], 'stopped')
        (self.run/'worker.lock').write_text('{}')
        with self.assertRaises(FileExistsError):
            self.run_worker(fetch=lambda *a, **k: self.fail('network'))

    def test_valid_interrupted_response_recovers_without_new_request(self):
        self.initialize()
        state = read(self.run/'state.json')
        target = read(self.run/'catalog.json')['targets'][0]
        directory = self.run/'pages'/target['id']/'interrupted'
        self.saved(directory, target['url'])
        state['active_attempt'] = {'page_id': target['id'], 'directory': directory.relative_to(self.root).as_posix(),
                                   'started_at': self.current.isoformat()}
        write(self.run/'state.json', state)
        calls = []
        result = self.run_worker(fetch=self.fetch_adapter(calls=calls))
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], self.cards[1]['wiki_url'])
        self.assertTrue(result['page_acquisition_complete'])
        self.assertEqual(read(self.run/'state.json')['history'][0]['event'], 'recovered_completed_attempt')

    def test_ambiguous_interruption_requires_inspection_and_never_refetches(self):
        self.initialize()
        state = read(self.run/'state.json')
        target = read(self.run/'catalog.json')['targets'][0]
        state['active_attempt'] = {'page_id': target['id'], 'directory': 'private/raw/full/partial',
                                   'started_at': self.current.isoformat()}
        write(self.run/'state.json', state)
        result = self.run_worker(fetch=lambda *a, **k: self.fail('unknown request repeated'))
        self.assertEqual(result['status'], 'needs_inspection')
        self.assertEqual(result['page_status_counts']['needs_inspection'], 1)

    def test_invalid_budget_and_public_directory_are_rejected(self):
        self.initialize()
        for budget in (0, 3, True):
            with self.assertRaises(ValueError):
                self.run_worker(budget, fetch=lambda *a, **k: self.fail('network'))
        with self.assertRaises(ValueError):
            bulk.initialize(self.root/'site/unsafe', root=self.root)


    def test_partial_transform_is_repeatable_and_network_free(self):
        self.saved(self.root/'private/raw/old', self.cards[0]['wiki_url'])
        self.initialize()
        def fake_transform(directory, card, version):
            return {'cards': [{'card_id': card['card_id'], 'card_kind': card['card_kind']} ]}
        first = transform_catalog(self.run, root=self.root, transformer=fake_transform)
        second = transform_catalog(self.run, root=self.root, transformer=fake_transform)
        self.assertEqual(first, second)
        self.assertEqual(first['coverage']['card_status_counts'], {'candidate_needs_review': 1, 'input_pending': 1})
        self.assertFalse(first['coverage']['all_target_pages_saved'])
        self.assertFalse(first['coverage']['adopted_or_published'])

    def test_structural_error_does_not_drop_coverage_or_other_cards(self):
        for n, card in enumerate(self.cards):
            self.saved(self.root/'private/raw'/str(n), card['wiki_url'])
        self.initialize()
        def fake_transform(directory, card, version):
            if card['card_kind'] == 'P':
                raise ValueError('unknown panel')
            return {'cards': [{'card_id': card['card_id'], 'card_kind': card['card_kind']}]}
        result = transform_catalog(self.run, root=self.root, transformer=fake_transform)
        self.assertEqual(len(result['card_coverage']), 2)
        self.assertEqual(result['coverage']['card_status_counts'], {'needs_structure_review': 1, 'candidate_needs_review': 1})
        self.assertEqual(result['cards'][0]['card_id'], 's1')
        self.assertTrue(result['coverage']['all_target_pages_saved'])
        self.assertFalse(result['coverage']['all_details_validated'])

    def test_shared_url_inputs_never_mix_road_variants(self):
        self.cards += [self.card('p2', 'P', '【A】人物', 'idol_road_sr'),
                       self.card('p3', 'P', '【A】人物', 'idol_road_ssr')]
        self.manifest['detail_catalog_expected_cards'] = 4
        self.write_base()
        self.saved(self.root/'private/raw/old', self.cards[0]['wiki_url'])
        self.initialize()
        result = transform_catalog(self.run, root=self.root, transformer=lambda *a: self.fail('ambiguous mapping'))
        self.assertEqual(result['coverage']['card_status_counts'], {'needs_variant_mapping': 3, 'input_pending': 1})
        self.assertEqual(result['cards'], [])

    def test_checkpoint_input_mismatch_is_reported_without_candidate(self):
        self.saved(self.root/'private/raw/old', self.cards[0]['wiki_url'])
        self.initialize()
        state = read(self.run/'state.json')
        target = read(self.run/'catalog.json')['targets'][0]
        state['pages'][target['id']]['sha256'] = 'wrong'
        write(self.run/'state.json', state)
        result = transform_catalog(self.run, root=self.root, transformer=lambda *a: self.fail('invalid input accepted'))
        self.assertEqual(result['coverage']['card_status_counts']['input_invalid'], 1)
        self.assertEqual(result['cards'], [])

    def test_unknown_resolution_preserves_history_and_failure_backoff(self):
        self.initialize()
        state = read(self.run/'state.json')
        target = read(self.run/'catalog.json')['targets'][0]
        state['pages'][target['id']] = {'status': 'needs_inspection', 'directory': 'private/raw/full/unknown',
                                        'started_at': self.current.isoformat()}
        write(self.run/'state.json', state)
        result = bulk.resolve_unknown(self.run, target['id'], 'Checked no complete response; retain partial directory',
                                      root=self.root, state_path=self.state_path, current=self.current)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(read(self.run/'state.json')['history'][0]['previous']['status'], 'needs_inspection')
        self.assertEqual(read(self.state_path)['last_failure_at'], self.current.isoformat(timespec='seconds'))
        self.assertFalse((self.run/'worker.lock').exists())
        self.assertFalse(self.state_path.with_suffix('.lock').exists())
        self.run_worker(fetch=lambda *a, **k: self.fail('automatic retry'))
        with self.assertRaises(RuntimeError):
            self.run_worker(retry_page=target['id'], fetch=lambda *a, **k: self.fail('backoff bypass'))

    def test_corrupt_completed_input_blocks_resume_without_replacement(self):
        directory = self.root/'private/raw/old'
        self.saved(directory, self.cards[0]['wiki_url'])
        self.initialize()
        (directory/'response.html').write_text('corrupt', encoding='utf-8')
        result = self.run_worker(fetch=lambda *a, **k: self.fail('raw silently replaced'))
        self.assertEqual(result['status'], 'needs_inspection')
        self.assertEqual(result['page_status_counts']['needs_inspection'], 1)
        self.assertEqual((directory/'response.html').read_text(encoding='utf-8'), 'corrupt')
        self.assertEqual(read(self.run/'state.json')['history'][0]['event'], 'saved_input_integrity_failure')

    def test_local_verification_failure_also_requires_backoff_for_retry(self):
        self.initialize()
        def incomplete_fetch(page, directory, **kwargs):
            directory.mkdir(parents=True)
            write(directory/'fetch.json', {'status': 'failed'})
        result = self.run_worker(fetch=incomplete_fetch)
        self.assertEqual(result['status'], 'failed')
        page_id = next(key for key, value in read(self.run/'state.json')['pages'].items() if value['status'] == 'failed')
        with self.assertRaisesRegex(RuntimeError, 'Local acquisition failure backoff'):
            self.run_worker(retry_page=page_id, fetch=lambda *a, **k: self.fail('backoff bypass'))

    def test_workflow_produces_partial_audit_on_acquisition_stop(self):
        self.initialize()
        (self.run/'STOP').touch()
        def worker(*args, **kwargs):
            return bulk.run_worker(*args, **kwargs, clock=self.clock, sleep=self.sleep,
                                   fetch=lambda *a, **k: self.fail('stop ignored'))
        result = run_workflow(self.run, 2, root=self.root, state_path=self.state_path, worker=worker)
        self.assertEqual(result['phase'], 'finished')
        self.assertEqual(result['acquisition']['status'], 'stopped')
        self.assertEqual(result['coverage']['card_status_counts'], {'input_pending': 2})
        self.assertFalse(result['coverage']['adopted_or_published'])
        self.assertTrue((self.root/result['candidate_file']).exists())
        self.assertFalse((self.run/'workflow.lock').exists())

    def test_workflow_audits_saved_success_and_failure_without_retry(self):
        self.initialize()
        calls = []
        error = HTTPError('test', 429, 'Too Many Requests', None, None)
        def worker(*args, **kwargs):
            return bulk.run_worker(*args, **kwargs, clock=self.clock, sleep=self.sleep,
                                   fetch=self.fetch_adapter(error, calls))
        result = run_workflow(self.run, 2, root=self.root, state_path=self.state_path, worker=worker)
        self.assertEqual(len(calls), 2)
        self.assertEqual(result['acquisition']['status'], 'failed')
        self.assertEqual(result['coverage']['card_status_counts'], {'needs_structure_review': 1, 'input_failed': 1})
        self.assertFalse(result['coverage']['all_target_pages_saved'])
        self.assertEqual(read(self.root/'site/data'/VERSION/'cards.json')['cards'], self.cards)

    def test_workflow_audit_error_is_recorded_without_public_write(self):
        self.initialize()
        (self.run/'STOP').touch()
        def worker(*args, **kwargs):
            return bulk.run_worker(*args, **kwargs, clock=self.clock, sleep=self.sleep)
        def broken_transform(*args, **kwargs):
            raise ValueError('offline disk error')
        with self.assertRaises(ValueError):
            run_workflow(self.run, 2, root=self.root, state_path=self.state_path,
                         worker=worker, transformer=broken_transform)
        self.assertEqual(read(self.run/'workflow-report.json')['phase'], 'audit_failed')
        self.assertFalse((self.run/'workflow.lock').exists())
        self.assertEqual(read(self.root/'site/data'/VERSION/'cards.json')['cards'], self.cards)

    def test_worker_alive_status_uses_actual_process(self):
        self.initialize()
        write(self.run/'worker.lock', {'pid': 1234})
        with patch.object(bulk, 'process_alive', return_value=False):
            self.assertFalse(bulk.report_status(self.run, root=self.root)['worker_is_alive'])

    def test_stale_lock_release_requires_dead_expected_owner(self):
        self.initialize()
        write(self.run/'worker.lock', {'pid': 1234})
        with patch.object(bulk, 'process_alive', return_value=True):
            with self.assertRaises(RuntimeError):
                bulk.release_stale_lock(self.run, 1234, root=self.root)
        with patch.object(bulk, 'process_alive', return_value=False):
            with self.assertRaises(RuntimeError):
                bulk.release_stale_lock(self.run, 4321, root=self.root)
            bulk.release_stale_lock(self.run, 1234, root=self.root)
        self.assertFalse((self.run/'worker.lock').exists())


if __name__ == '__main__':
    unittest.main()
