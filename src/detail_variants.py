"""Map shared idol-road pages by explicit R/SR/SSR fold labels, never table order."""
from unicodedata import normalize
from src.card_details import text,wiki_key,transform_run
from src.indexer import digest

VARIANTS={'base':('R','【白いツバサ】'),'idol_road_sr':('SR','【白いツバサ】'),'idol_road_ssr':('SSR','【アイドルロード】')}

def validate_variants(cards):
    if len(cards)!=3 or len({c['card_id'] for c in cards})!=3 or {c.get('variant_kind') for c in cards}!=set(VARIANTS):
        raise ValueError('Expected explicit base R, road SR and road SSR identities')
    if len({c['idol_name'] for c in cards})!=1 or len({wiki_key(c['wiki_url']) for c in cards})!=1:
        raise ValueError('Shared variant idol/URL mismatch')
    for card in cards:
        rarity,title=VARIANTS[card['variant_kind']]
        if card['card_kind']!='P' or (card['rarity'],card['card_title'])!=(rarity,title):
            raise ValueError('Shared variant kind/rarity/title mismatch')
    return next(c for c in cards if c['variant_kind']=='base')

def select_variant_tables(tables,cards,card_id,*,required=True):
    validate_variants(cards)
    labels={normalize('NFKC',c['rarity']+c['card_title']+c['idol_name']):c['card_id'] for c in cards}
    groups={c['card_id']:[] for c in cards};containers={c['card_id']:set() for c in cards}
    for number,table,anchor in tables:
        container=table.find_parent('div',class_='fold-container')
        if container is None:raise ValueError('Shared table missing explicit variant fold')
        summaries=container.find_all('div',class_='fold-summary',recursive=False)
        contents=container.find_all('div',class_='fold-content',recursive=False)
        if len(summaries)!=1 or len(contents)!=1 or table not in contents[0].descendants:
            raise ValueError('Ambiguous shared variant fold')
        label=normalize('NFKC',text(summaries[0]));paragraph=contents[0].find('p',recursive=False)
        if label not in labels or paragraph is None or normalize('NFKC',text(paragraph))!=label:
            raise ValueError('Shared variant label/identity mismatch')
        cid=labels[label];groups[cid].append((number,table,anchor));containers[cid].add(id(container))
    if any(len(values)>1 for values in containers.values()) or (required and any(not groups[cid] for cid in groups)):
        raise ValueError('Missing or duplicate shared variant section')
    if card_id not in groups:raise ValueError('Requested card is not a shared variant')
    return groups[card_id]

def transform_shared_run(directory,cards,base_version):
    validate_variants(cards)
    records=[transform_run(directory,card,base_version,variant_cards=cards)['cards'][0] for card in cards]
    result={'pilot_schema':'0.3','base_dataset_version':base_version,'input_kind':'saved_wiki_html','cards':records}
    result['content_hash']=digest(result)
    return result
