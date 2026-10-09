"""Immutable base-index catalogue and integrity checks for detail HTML acquisition."""
from collections import Counter, defaultdict
import hashlib
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from src.card_details import wiki_key
from src.indexer import read
from scripts.transform_detail_html import load_cards


def build_catalog(root: Path, version: str) -> dict:
    cards = load_cards(root, version)
    if not cards or any(not isinstance(c.get('card_id'), str) or not c['card_id'] for c in cards) or (
            len({c['card_id'] for c in cards}) != len(cards)):
        raise ValueError('Empty base index or duplicate card ID')
    groups = defaultdict(list)
    unlinked = []
    for card in cards:
        if card.get('game') != 'shinycolors_enza' or card['card_kind'] not in ('P', 'S'):
            raise ValueError('Wrong base game/kind')
        metadata = {key: card.get(key) for key in ('card_id','card_kind','card_title','idol_name','rarity','variant_kind')}
        if not card.get('wiki_url'):
            unlinked.append(dict(metadata, status='missing_page', reason='Existing unlinked cards remain on hold'))
            continue
        key = wiki_key(card['wiki_url'])
        if not key.startswith('/shinycolors/【'):
            raise ValueError('Base URL is not an individual card page')
        groups[key].append(card)
    targets = []
    for key, group in sorted(groups.items()):
        if len({card['card_kind'] for card in group}) != 1:
            raise ValueError('Shared URL with different P/S kinds needs explicit mapping')
        group = sorted(group, key=lambda card: card['card_id'])
        targets.append({'id': 'DC-' + hashlib.sha256(key.encode()).hexdigest()[:16],
                        'url': group[0]['wiki_url'], 'kind': group[0]['card_kind'],
                        'cards': [{field: card.get(field) for field in ('card_id','card_kind','card_title','idol_name','rarity','variant_kind')}
                                  for card in group], 'card_ids': [card['card_id'] for card in group],
                        'variant_mapping_required': len(group) > 1})
    if len({target['id'] for target in targets}) != len(targets):
        raise ValueError('Page-ID collision')
    dates = sorted(card['first_implemented_on'] for card in cards if card.get('first_implemented_on'))
    return {'catalog_schema': '1.0', 'base_dataset_version': version,
            'base_cards_sha256': hashlib.sha256((root/'site/data'/version/'cards.json').read_bytes()).hexdigest(),
            'card_count': len(cards), 'card_kind_counts': dict(Counter(card['card_kind'] for card in cards)),
            'unique_pages': len(targets), 'linked_cards': sum(len(target['cards']) for target in targets),
            'unlinked_cards': sorted(unlinked, key=lambda card: card['card_id']),
            'shared_url_pages': sum(target['variant_mapping_required'] for target in targets),
            'known_implemented_on_min': dates[0] if dates else None,
            'known_implemented_on_max': dates[-1] if dates else None,
            'unknown_implemented_on_count': sum(not card.get('first_implemented_on') for card in cards),
            'targets': targets}


def load_catalog(root: Path, path: Path, manifest: dict) -> dict:
    if manifest.get('detail_catalog_enabled') is not True:
        raise RuntimeError('Full detail catalogue acquisition is not enabled')
    if not path.resolve().is_relative_to((root/'private').resolve()):
        raise ValueError('Catalogue must stay under private/')
    catalog = read(path)
    expected = build_catalog(root, manifest['detail_base_dataset_version'])
    if catalog != expected or catalog['card_count'] != manifest['detail_catalog_expected_cards']:
        raise ValueError('Catalogue/base index mismatch or abnormal card count')
    return catalog


def verify_saved_fetch(root: Path, directory: Path, url: str) -> dict:
    if not directory.resolve().is_relative_to((root/'private/raw').resolve()):
        raise ValueError('Saved HTML outside private/raw/')
    report = read(directory/'fetch.json')
    raw = (directory/'response.html').read_bytes()
    if report.get('status') != 'fetched' or report.get('http_status') != 200 or (
            report.get('sha256') != hashlib.sha256(raw).hexdigest()):
        raise ValueError('Saved fetch failed, incomplete, or has a hash mismatch')
    if wiki_key(report['url']) != wiki_key(url):
        raise ValueError('Saved URL mismatch')
    document = BeautifulSoup(raw, 'html.parser')
    links = document.select('link[rel="canonical"]')
    content = document.select_one('#content')
    if len(links) != 1 or wiki_key(links[0].get('href','')) != wiki_key(url) or (
            content is None or not content.find('table') or len(content.get_text(' ', strip=True)) < 1000):
        raise ValueError('Saved response is not the requested Wiki content')
    if not report.get('fetched_at'):
        raise ValueError('Saved fetch lacks timestamp')
    timestamp = datetime.fromisoformat(report['fetched_at'].replace('Z', '+00:00'))
    if timestamp.tzinfo is None:
        raise ValueError('Saved fetch timestamp lacks timezone')
    return report
