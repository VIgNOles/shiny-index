"""Validate real Wiki structures without using commentary length as a card-data test."""
from bs4 import BeautifulSoup
from unicodedata import normalize
from urllib.parse import unquote, urlsplit
from src.card_details import text, wiki_key


def registered_titles(root,url):
    """The card title can differ from the observed Wiki URL (e.g. omitted heart)."""
    import json
    from pathlib import Path
    root=Path(root);manifest=root/'source_manifest.json'
    if not manifest.exists():return []
    config=json.loads(manifest.read_text(encoding='utf-8'));version=config.get('detail_base_dataset_version')
    path=root/'site/data'/str(version)/'cards.json'
    if not path.exists():return []
    key=wiki_key(url)
    return [card['card_title']+card['idol_name'] for card in json.loads(path.read_text(encoding='utf-8'))['cards']
            if card.get('wiki_url') and wiki_key(card['wiki_url'])==key]


def validate_response(raw, url, expected_titles=()):
    if b'<html' not in raw.lower() or len(raw) < 1000:
        raise ValueError('unexpected response')
    document = BeautifulSoup(raw, 'html.parser')
    canonical = document.select('link[rel="canonical"]')
    try:
        valid_canonical = len(canonical)==1 and wiki_key(canonical[0].get('href',''))==wiki_key(url)
    except ValueError:
        valid_canonical = False
    if not valid_canonical:
        raise ValueError('unexpected Wiki page or security interstitial')
    content = document.select_one('#content')
    if content is None or not content.find('table'):
        raise ValueError('unexpected Wiki content or security interstitial')
    path = unquote(urlsplit(url).path)
    if path.startswith('/shinycolors/【'):
        titles=[path.removeprefix('/shinycolors/'),*expected_titles]
        headings = [text(h).removesuffix('▲').removesuffix('▼').strip()
                    for h in content.find_all(['h2','h3','h4','h5','h6'])]
        if (not document.title or not any(normalize('NFKC',text(document.title)).startswith(normalize('NFKC',title)) for title in titles) or
                not any(h.startswith('スキルパネル') for h in headings)):
            raise ValueError('unexpected individual-card title or skill-panel structure')
    elif len(content.get_text(' ', strip=True)) < 1000:
        raise ValueError('unexpected Wiki content or security interstitial')
    return document
