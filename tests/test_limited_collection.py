import io
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

import scripts.collect_one as limited
import src.indexer as indexer


class LimitedCollectionTests(unittest.TestCase):
    def test_reference_pages_are_allowlisted_separately_and_ids_cannot_collide(self):
        manifest={'pages':[], 'audit_pages':[], 'reference_pages':[{'id':'R01','url':'https://wikiwiki.jp/shinycolors/スキル効果の解説'}]}
        self.assertEqual(set(limited.registered_pages(manifest)),{'R01'})
        manifest['audit_pages']=[dict(manifest['reference_pages'][0])]
        with self.assertRaisesRegex(ValueError,'duplicate source page ID'):
            limited.registered_pages(manifest)

    def test_cooldown_starts_after_slow_request_completion(self):
        start=datetime(2026,10,11,0,0,tzinfo=timezone.utc)
        manifest={'single_page_cooldown_seconds':60,'single_page_collection_enabled':True}
        state={'last_attempt_at':start.isoformat(),'last_completed_at':(start+timedelta(seconds=25)).isoformat()}
        self.assertFalse(limited.status(manifest,state,start+timedelta(seconds=84))['can_fetch'])
        self.assertTrue(limited.status(manifest,state,start+timedelta(seconds=85))['can_fetch'])

    def test_cooldown_blocks_before_network_or_directory_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            indexer.write(root/'source_manifest.json',{
                'single_page_collection_enabled':True,
                'single_page_cooldown_seconds':86400,
                'full_collection_enabled':False,
                'pages':[{'id':'W09','url':'https://wikiwiki.jp/shinycolors/ガシャ'}],
                'audit_pages':[]
            })
            state=root/'state.json'
            start=datetime(2026,10,7,15,30,tzinfo=timezone.utc)
            indexer.write(state,{'last_attempt_at':start.isoformat(),'last_rate_limit_at':start.isoformat()})
            target=root/'raw'
            def forbidden(*args,**kwargs):
                raise AssertionError('network attempted')
            with patch.object(limited,'ROOT',root):
                with self.assertRaisesRegex(RuntimeError,'unavailable until'):
                    limited.fetch_one('W09',target,current=start+timedelta(hours=23),state_path=state,fetcher=forbidden)
            self.assertFalse(target.exists())
            self.assertEqual(indexer.read(state)['last_attempt_at'],start.isoformat())

    def test_missing_state_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            indexer.write(root/'source_manifest.json',{
                'single_page_collection_enabled':True,
                'single_page_cooldown_seconds':86400,
                'full_collection_enabled':False,
                'pages':[{'id':'W09','url':'https://wikiwiki.jp/shinycolors/ガシャ'}],
                'audit_pages':[]
            })
            with patch.object(limited,'ROOT',root):
                with self.assertRaisesRegex(RuntimeError,'unavailable until None'):
                    limited.fetch_one('W09',root/'raw',state_path=root/'state.json',fetcher=lambda *a,**k: self.fail('network attempted'))
            self.assertFalse((root/'raw').exists())

    def test_existing_lock_blocks_parallel_fetch(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            indexer.write(root/'source_manifest.json',{
                'single_page_collection_enabled':True,
                'single_page_cooldown_seconds':86400,
                'full_collection_enabled':False,
                'pages':[{'id':'W09','url':'https://wikiwiki.jp/shinycolors/ガシャ'}],
                'audit_pages':[]
            })
            state=root/'state.json'
            state.with_suffix('.lock').write_text('in progress',encoding='utf-8')
            with patch.object(limited,'ROOT',root):
                with self.assertRaises(FileExistsError):
                    limited.fetch_one('W09',root/'raw',state_path=state,fetcher=lambda *a,**k: self.fail('network attempted'))
            self.assertFalse((root/'raw').exists())

    def test_exactly_one_allowed_page_is_saved_for_audit_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            url='https://wikiwiki.jp/shinycolors/ガシャ'
            indexer.write(root/'source_manifest.json',{
                'single_page_collection_enabled':True,
                'single_page_cooldown_seconds':86400,
                'full_collection_enabled':False,
                'pages':[{'id':'W09','url':url}],
                'audit_pages':[]
            })
            state=root/'state.json'
            current=datetime(2026,10,8,16,0,tzinfo=timezone.utc)
            indexer.write(state,{'last_attempt_at':(current-timedelta(days=2)).isoformat()})
            target=root/'raw'
            calls=[]
            def fake_fetch(received_url,directory,*,allow_limited):
                calls.append((received_url,allow_limited))
                directory.mkdir()
                indexer.write(directory/'fetch.json',{'status':'fetched','sha256':'test'})
            with patch.object(limited,'ROOT',root),patch.object(limited,'monotonic',side_effect=[10,35]):
                self.assertEqual(limited.fetch_one('W09',target,current=current,state_path=state,fetcher=fake_fetch)['status'],'fetched')
            self.assertEqual(indexer.read(state)['last_completed_at'],(current+timedelta(seconds=25)).isoformat(timespec='seconds'))
            self.assertEqual(calls,[(url,True)])
            self.assertEqual(indexer.read(target/'limited-run.json'),{'page_id':'W09','status':'fetched','full_run':False,'authorized_early':False})
            self.assertEqual(indexer.read(state)['last_attempt_at'],current.isoformat(timespec='seconds'))

    def test_explicit_early_fetch_is_single_page_and_keeps_retry_after(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            url='https://wikiwiki.jp/shinycolors/ガシャ'
            indexer.write(root/'source_manifest.json',{
                'single_page_collection_enabled':True,
                'single_page_cooldown_seconds':86400,
                'full_collection_enabled':False,
                'pages':[],
                'audit_pages':[{'id':'W09','url':url}]
            })
            start=datetime(2026,10,7,15,30,tzinfo=timezone.utc)
            current=start+timedelta(hours=11)
            state=root/'state.json'
            indexer.write(state,{'last_attempt_at':start.isoformat(),'last_rate_limit_at':start.isoformat()})
            calls=[]
            def fake_fetch(received_url,directory,*,allow_limited):
                calls.append((received_url,allow_limited))
                directory.mkdir()
                indexer.write(directory/'fetch.json',{'status':'fetched','sha256':'test'})
            with patch.object(limited,'ROOT',root):
                result=limited.fetch_one('W09',root/'raw',current=current,state_path=state,
                                         fetcher=fake_fetch,authorized_early=True)
            self.assertEqual(result['status'],'fetched')
            self.assertEqual(calls,[(url,True)])
            self.assertEqual(indexer.read(root/'raw'/'limited-run.json')['authorized_early'],True)
            self.assertEqual(indexer.read(state)['last_early_authorized_at'],current.isoformat(timespec='seconds'))
            self.assertFalse(limited.status(indexer.read(root/'source_manifest.json'),
                                            indexer.read(state),current+timedelta(hours=1))['can_fetch'])
            with patch.object(limited,'ROOT',root):
                with self.assertRaisesRegex(RuntimeError,'unavailable until'):
                    limited.fetch_one('W09',root/'second',current=current+timedelta(hours=2),
                                      state_path=state,fetcher=fake_fetch,authorized_early=True)
            self.assertEqual(len(calls),1)
            blocked=root/'blocked'
            indexer.write(state,{'last_attempt_at':start.isoformat(),
                                 'server_not_before_at':(current+timedelta(hours=2)).isoformat()})
            with patch.object(limited,'ROOT',root):
                with self.assertRaisesRegex(RuntimeError,'unavailable until'):
                    limited.fetch_one('W09',blocked,current=current,state_path=state,
                                      fetcher=fake_fetch,authorized_early=True)
            self.assertFalse(blocked.exists())
            self.assertEqual(len(calls),1)
    def test_429_extends_cooldown_to_server_retry_after(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            url='https://wikiwiki.jp/shinycolors/ガシャ'
            indexer.write(root/'source_manifest.json',{
                'single_page_collection_enabled':True,
                'single_page_cooldown_seconds':86400,
                'full_collection_enabled':False,
                'pages':[{'id':'W09','url':url}],
                'audit_pages':[]
            })
            state=root/'state.json'
            current=datetime(2026,10,8,16,0,tzinfo=timezone.utc)
            indexer.write(state,{'last_attempt_at':(current-timedelta(days=2)).isoformat()})
            target=root/'raw'
            calls=[]
            def fail_once(received_url,directory,*,allow_limited):
                calls.append(received_url)
                directory.mkdir()
                raise HTTPError(url,429,'Too Many Requests',{'Retry-After':'172800'},None)
            with patch.object(limited,'ROOT',root):
                with self.assertRaises(HTTPError):
                    limited.fetch_one('W09',target,current=current,state_path=state,fetcher=fail_once)
                availability=limited.status(indexer.read(root/'source_manifest.json'),indexer.read(state),current+timedelta(hours=25))
            self.assertEqual(calls,[url])
            self.assertFalse(availability['can_fetch'])
            self.assertEqual(availability['next_allowed_at'],(current+timedelta(days=2)).isoformat(timespec='seconds'))
            self.assertEqual(indexer.read(target/'limited-run.json')['status'],'failed')

    def test_released_local_wait_keeps_spacing_and_server_deadline(self):
        current=datetime(2026,10,9,0,0,tzinfo=timezone.utc)
        manifest={'single_page_cooldown_seconds':60,'single_page_failure_backoff_seconds':86400,
                  'single_page_collection_enabled':True,'full_collection_enabled':False}
        state={'last_attempt_at':(current-timedelta(hours=2)).isoformat(),
               'last_rate_limit_at':(current-timedelta(days=2)).isoformat()}
        self.assertTrue(limited.status(manifest,state,current)['can_fetch'])
        state['last_attempt_at']=current.isoformat()
        self.assertFalse(limited.status(manifest,state,current+timedelta(seconds=59))['can_fetch'])
        self.assertTrue(limited.status(manifest,state,current+timedelta(seconds=60))['can_fetch'])
        state['server_not_before_at']=(current+timedelta(hours=3)).isoformat()
        self.assertFalse(limited.status(manifest,state,current+timedelta(hours=1))['can_fetch'])
        state.pop('server_not_before_at')
        state['last_failure_at']=current.isoformat()
        self.assertFalse(limited.status(manifest,state,current+timedelta(hours=23))['can_fetch'])

    def test_failure_with_short_spacing_stops_following_page(self):
        for failure in (HTTPError('test',503,'Unavailable',None,None),ValueError('security interstitial')):
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as temp:
                root=Path(temp)
                manifest={'pages':[{'id':'W09','url':'https://wikiwiki.jp/shinycolors/ガシャ'}],
                          'audit_pages':[],'single_page_cooldown_seconds':60,
                          'single_page_failure_backoff_seconds':86400,'single_page_collection_enabled':True}
                indexer.write(root/'source_manifest.json',manifest)
                state=root/'state.json'
                current=datetime(2026,10,9,0,0,tzinfo=timezone.utc)
                indexer.write(state,{'last_attempt_at':(current-timedelta(days=2)).isoformat()})
                calls=[]
                def fail_once(*args,**kwargs):
                    calls.append(args[0])
                    raise failure
                with patch.object(limited,'ROOT',root):
                    with self.assertRaises(type(failure)):
                        limited.fetch_one('W09',root/'failed',current=current,state_path=state,fetcher=fail_once)
                    with self.assertRaisesRegex(RuntimeError,'unavailable until'):
                        limited.fetch_one('W09',root/'next',current=current+timedelta(minutes=2),state_path=state,fetcher=fail_once,authorized_early=True)
                self.assertEqual(len(calls),1)
                self.assertEqual(indexer.read(state)['last_failure_at'],current.isoformat(timespec='seconds'))

    def test_security_page_is_not_accepted_as_card_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            indexer.write(root/'source_manifest.json',{'single_page_collection_enabled':True})
            url='https://wikiwiki.jp/shinycolors/ガシャ'
            response=b'<html><head><link rel="canonical" href="https://wikiwiki.jp/pp/security-check-guide"></head><body>'+b'challenge'*200+b'</body></html>'
            class Page:
                status=200
                headers={'Content-Type':'text/html'}
                def __enter__(self): return self
                def __exit__(self,*args): return False
                def read(self): return response
            calls=[]
            def fake_urlopen(request,timeout):
                calls.append(request)
                return io.BytesIO(b'User-agent: *\nDisallow:\n') if len(calls)==1 else Page()
            with patch.object(indexer,'ROOT',root),patch.object(indexer,'urlopen',side_effect=fake_urlopen):
                with self.assertRaisesRegex(ValueError,'security interstitial'):
                    indexer.collect(url,root/'raw',allow_limited=True)
            self.assertEqual(len(calls),2)
            self.assertFalse((root/'raw/response.html').exists())
            self.assertEqual(indexer.read(root/'raw/fetch.json')['status'],'failed')

    def test_matching_canonical_without_wiki_content_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            indexer.write(root/'source_manifest.json',{'single_page_collection_enabled':True})
            url='https://wikiwiki.jp/shinycolors/ガシャ'
            response=('<html><head><link rel="canonical" href="'+url+'"></head><body>'+('確認画面'*500)+'</body></html>').encode('utf-8')
            class Page:
                status=200
                headers={'Content-Type':'text/html'}
                def __enter__(self): return self
                def __exit__(self,*args): return False
                def read(self): return response
            calls=[]
            def fake_urlopen(request,timeout):
                calls.append(request)
                return io.BytesIO(b'User-agent: *\nDisallow:\n') if len(calls)==1 else Page()
            with patch.object(indexer,'ROOT',root),patch.object(indexer,'urlopen',side_effect=fake_urlopen):
                with self.assertRaisesRegex(ValueError,'unexpected Wiki content'):
                    indexer.collect(url,root/'raw',allow_limited=True)
            self.assertEqual(len(calls),2)
            self.assertFalse((root/'raw/response.html').exists())

    def test_http_429_is_recorded_without_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            indexer.write(root/'source_manifest.json',{'single_page_collection_enabled':True})
            url='https://wikiwiki.jp/shinycolors/ガシャ'
            calls=[]
            def fake_urlopen(request,timeout):
                calls.append(request)
                if len(calls)==1: return io.BytesIO(b'User-agent: *\nDisallow:\n')
                raise HTTPError(url,429,'Too Many Requests',{'Retry-After':'3600'},None)
            with patch.object(indexer,'ROOT',root),patch.object(indexer,'urlopen',side_effect=fake_urlopen):
                with self.assertRaises(HTTPError):
                    indexer.collect(url,root/'raw',allow_limited=True)
            report=indexer.read(root/'raw/fetch.json')
            self.assertEqual(len(calls),2)
            self.assertEqual(report['http_status'],429)
            self.assertEqual(report['retry_after'],'3600')
            self.assertEqual(report['status'],'failed')


    def test_short_card_uses_title_and_panel_instead_of_commentary_length(self):
        from src.wiki_response import validate_response
        url='https://wikiwiki.jp/shinycolors/【合成】試験'
        raw=('<html><head><title>【合成】試験 - Wiki</title><link rel="canonical" href="'+url+'"></head><body><div id="content"><h2>スキルパネル</h2><table><tr><td>SP</td></tr></table></div><!--'+('padding '*200)+'--></body></html>').encode()
        validate_response(raw,url)
        with self.assertRaisesRegex(ValueError,'skill-panel'):
            validate_response(raw.replace('スキルパネル'.encode(),'別の節'.encode()),url)

    def test_registered_title_may_differ_from_url_but_wrong_card_is_rejected(self):
        from src.wiki_response import validate_response
        url='https://wikiwiki.jp/shinycolors/【AKQJ10】試験'
        raw=('<html><head><title>【♡AKQJ10】試験 - Wiki</title><link rel="canonical" href="'+url+'"></head><body><div id="content"><h2>スキルパネル</h2><table><tr><td>SP</td></tr></table></div><!--'+('padding '*200)+'--></body></html>').encode()
        with self.assertRaisesRegex(ValueError,'title'):validate_response(raw,url)
        validate_response(raw,url,['【♡AKQJ10】試験'])
        with self.assertRaisesRegex(ValueError,'title'):
            validate_response(raw.replace('♡AKQJ10'.encode(),'別カード'.encode()),url,['【♡AKQJ10】試験'])

    def test_false_positive_review_does_not_cancel_http_backoff(self):
        now=datetime(2026,10,9,3,0,tzinfo=timezone.utc)
        manifest={'single_page_collection_enabled':True,'single_page_cooldown_seconds':60,
                  'single_page_failure_backoff_seconds':86400}
        failed=(now-timedelta(hours=2)).isoformat()
        state={'last_attempt_at':failed,'last_failure_at':failed,'last_failure_reason':'HTTP 429',
               'failure_reviews':[{'classification':'local_validator_false_positive','failed_at':failed}]}
        self.assertFalse(limited.status(manifest,state,now)['can_fetch'])
        state['last_failure_reason']='ValueError: unexpected Wiki content or security interstitial'
        self.assertTrue(limited.status(manifest,state,now)['can_fetch'])
        state['last_rate_limit_at']=failed
        self.assertFalse(limited.status(manifest,state,now)['can_fetch'])

    def test_diagnostic_is_one_same_page_and_keeps_server_deadline(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);current=datetime(2026,10,9,3,0,tzinfo=timezone.utc)
            manifest={'single_page_collection_enabled':True,'single_page_cooldown_seconds':60,
                      'single_page_failure_backoff_seconds':86400,'pages':[{'id':'W09','url':'https://wikiwiki.jp/shinycolors/ガシャ'}], 'audit_pages':[]}
            indexer.write(root/'source_manifest.json',manifest)
            state=root/'state.json';failed=(current-timedelta(hours=2)).isoformat()
            indexer.write(state,{'last_attempt_at':failed,'last_failure_at':failed,'last_page_id':'W09',
                                'last_failure_reason':'ValueError: unexpected Wiki content or security interstitial'})
            calls=[]
            def fake_fetch(url,directory,**kwargs):
                calls.append(url);directory.mkdir()
                indexer.write(directory/'fetch.json',{'status':'fetched'})
            with patch.object(limited,'ROOT',root):
                limited.fetch_one('W09',root/'first',current=current,state_path=state,fetcher=fake_fetch,diagnose_content_failure=True)
                with self.assertRaises(RuntimeError):
                    limited.fetch_one('W09',root/'second',current=current+timedelta(hours=2),state_path=state,fetcher=fake_fetch,diagnose_content_failure=True)
            self.assertEqual(len(calls),1)


if __name__=='__main__':
    unittest.main()
