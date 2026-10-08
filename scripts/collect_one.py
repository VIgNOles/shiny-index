"""One allowlisted Wiki page per cooldown period; never adopts or publishes."""
import argparse
import os
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import sys
from urllib.error import HTTPError

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.indexer import ROOT, collect, read, write
from src.card_details import wiki_key
from scripts.transform_detail_html import load_cards

STATE=ROOT/'private/raw/acquisition-state.json'


def as_utc(value):
    return datetime.fromisoformat(value.replace('Z','+00:00')).astimezone(timezone.utc)


def status(manifest, state, current):
    cooldown=manifest['single_page_cooldown_seconds']
    if not isinstance(cooldown,int) or cooldown<86400:
        raise ValueError('single-page cooldown must be at least 24 hours')
    if state is None or not state.get('last_attempt_at'):
        return {'initialized':False,'single_page_enabled':manifest.get('single_page_collection_enabled') is True,
                'full_collection_enabled':manifest.get('full_collection_enabled') is True,
                'next_allowed_at':None,'can_fetch':False}
    times=[as_utc(state[key])+timedelta(seconds=cooldown)
           for key in ('last_attempt_at','last_rate_limit_at') if state.get(key)]
    if state.get('server_not_before_at'):
        times.append(as_utc(state['server_not_before_at']))
    next_allowed=max(times) if times else current
    return {'initialized':True,'single_page_enabled':manifest.get('single_page_collection_enabled') is True,
            'full_collection_enabled':manifest.get('full_collection_enabled') is True,
            'next_allowed_at':next_allowed.isoformat(timespec='seconds'),
            'can_fetch':manifest.get('single_page_collection_enabled') is True and current>=next_allowed}


def retry_after_deadline(value, current):
    if not value: return None
    if value.isdecimal():
        return current+timedelta(seconds=int(value))
    try:
        parsed=parsedate_to_datetime(value)
    except (ValueError, TypeError):
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else None


def registered_pages(manifest):
    items=manifest['pages']+manifest['audit_pages']+manifest.get('detail_pages',[])
    if len({item['id'] for item in items})!=len(items):
        raise ValueError('duplicate source page ID')
    details=manifest.get('detail_pages',[])
    if details:
        cards=load_cards(ROOT,manifest['detail_base_dataset_version'])
        by_id={card['card_id']:card for card in cards}
        if len({item['card_id'] for item in details})!=len(details):
            raise ValueError('duplicate detail card ID')
        for item in details:
            card=by_id.get(item['card_id'])
            if not card or card['card_kind']!=item['kind'] or not card.get('wiki_url') or (
                    wiki_key(card['wiki_url'])!=wiki_key(item['url'])):
                raise ValueError('detail source card ID/kind/URL mismatch')
    return {item['id']:item for item in items}


def _fetch_one_unlocked(page_id, directory, *, current=None, state_path=STATE, fetcher=collect, authorized_early=False):
    manifest=read(ROOT/'source_manifest.json')
    current=current or datetime.now(timezone.utc)
    state=read(state_path) if Path(state_path).exists() else None
    availability=status(manifest,state,current)
    early_allowed=(authorized_early and availability['initialized'] and
                   availability['single_page_enabled'] and not state.get('last_early_authorized_at') and
                   current>=as_utc(state['last_attempt_at'])+timedelta(hours=1) and
                   (not state.get('server_not_before_at') or
                    current>=as_utc(state['server_not_before_at'])))
    if not availability['can_fetch'] and not early_allowed:
        raise RuntimeError('Wiki single-page fetch unavailable until '+str(availability['next_allowed_at']))
    pages=registered_pages(manifest)
    if page_id not in pages: raise ValueError('page ID outside source manifest')
    target=Path(directory)
    if pages[page_id].get('card_id') and not target.resolve().is_relative_to((ROOT/'private/raw').resolve()):
        raise ValueError('Detail raw inputs must stay under private/raw/')
    if target.exists(): raise FileExistsError('Use a fresh directory; saved inputs are immutable')
    stamp=current.isoformat(timespec='seconds')
    state['last_attempt_at']=stamp
    state['last_page_id']=page_id
    if early_allowed and not availability['can_fetch']:
        state['last_early_authorized_at']=stamp
    write(state_path,state)
    try:
        fetcher(pages[page_id]['url'],target,allow_limited=True)
    except HTTPError as error:
        if error.code in (429,503):
            if error.code==429: state['last_rate_limit_at']=stamp
            deadline=retry_after_deadline(error.headers.get('Retry-After') if error.headers else None,current)
            if deadline: state['server_not_before_at']=deadline.isoformat(timespec='seconds')
            write(state_path,state)
        if target.is_dir():
            write(target/'limited-run.json',{'page_id':page_id,'status':'failed','full_run':False,'authorized_early':bool(early_allowed and not availability['can_fetch'])})
        raise
    except Exception:
        if target.is_dir():
            write(target/'limited-run.json',{'page_id':page_id,'status':'failed','full_run':False,'authorized_early':bool(early_allowed and not availability['can_fetch'])})
        raise
    result=read(target/'fetch.json')
    write(target/'limited-run.json',{'page_id':page_id,'status':result['status'],'full_run':False,'authorized_early':bool(early_allowed and not availability['can_fetch'])})
    return result



def fetch_one(page_id, directory, *, current=None, state_path=STATE, fetcher=collect, authorized_early=False):
    lock_path=Path(state_path).with_suffix('.lock')
    lock_path.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(lock_path,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    try:
        return _fetch_one_unlocked(page_id,directory,current=current,state_path=state_path,fetcher=fetcher,authorized_early=authorized_early)
    finally:
        os.close(fd)
        lock_path.unlink()



def main():
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('status')
    sub.add_parser('init')
    command=sub.add_parser('fetch')
    command.add_argument('page_id')
    command.add_argument('directory')
    command.add_argument('--user-authorized-early-fetch',action='store_true')
    args=parser.parse_args()
    manifest=read(ROOT/'source_manifest.json')
    state=read(STATE) if STATE.exists() else None
    if args.command=='init':
        if STATE.exists(): raise FileExistsError('Acquisition state already exists')
        stamp=datetime.now(timezone.utc).isoformat(timespec='seconds')
        write(STATE,{'last_attempt_at':stamp,'initialized_at':stamp,'note':'Fresh environment starts with a 24-hour cooldown'})
        state=read(STATE)
    if args.command in ('status','init'):
        import json
        print(json.dumps(status(manifest,state,datetime.now(timezone.utc)),ensure_ascii=False))
    else:
        print(fetch_one(args.page_id,args.directory,authorized_early=args.user_authorized_early_fetch))


if __name__=='__main__':
    main()
