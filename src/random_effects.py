
"""Source-bound random alternatives; no implied simultaneous or uniform grants."""
import copy
import json
import math
import re
import unicodedata


def normalized(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', text or ''))


def unavailable_pool():
    return dict(status='unavailable', options=[], unstructured_count=0,
                source_positions=[], same_option_can_repeat=True,
                selection_probability='unknown')


def candidate(text, known_idols=()):
    n = normalized(text)
    m = re.fullmatch(r'(Vocal|Dance|Visual|リアクション回避率|パッシブスキル発動率)(\d+(?:\.\d+)?)%UP\[(\d+)ターン\]', n)
    if m:
        return dict(kind='rate_up', targets=[m[1]], value=float(m[2]), unit='percent', turns=int(m[3]))
    m = re.fullmatch(r'パッシブスキル(\d+(?:\.\d+)?)%強化\[(\d+)ターン\]', n)
    if m:
        return dict(kind='passive_boost', targets=['パッシブスキル'], value=float(m[1]), unit='percent', turns=int(m[2]))
    m = re.fullmatch(r'交換数UP\[(\d+)回\]', n)
    if m:
        return dict(kind='exchange_count_up', targets=['交換数'], value=int(m[1]), unit='points')
    m = re.fullmatch(r'(.+?)のアピール(?:倍率|値)(\d+(?:\.\d+)?)倍UP\[(\d+)ターン\]', n)
    if m:
        ids = [name for name in known_idols if normalized(name) == m[1]]
        if len(ids) == 1:
            return dict(kind='idol_appeal_bonus', targets=['アピール値'], idols=ids,
                        value=float(m[2]), unit='multiplier', turns=int(m[3]))
    m = re.fullmatch(r'フレキシブル\[(\d+)ターン\]', n)
    if m:
        return dict(kind='flexible', targets=['フレキシブル'], value=1, unit='boolean', turns=int(m[1]))
    m = re.fullmatch(r'リザレクション効果(\d+(?:\.\d+)?)%付与\[(\d+)ターン\]\[(\d+)回\]', n)
    if m:
        return dict(kind='resurrection', targets=['メンタル'], value=float(m[1]), unit='percent',
                    turns=int(m[2]), uses=int(m[3]), trigger='mental_zero')
    return None


def note_pool(note, known_idols):
    text = normalized(note['effect_private'])
    # Strip exact observed explanatory tails before splitting bullet marks.
    for tail in ('白・架・祝・幻+の場合、同一の効果が付与される場合もあり',
                 '複数付与する場合、同一の効果が付与される場合もあり',
                 '同一の効果が付与される場合もあり'):
        if text.endswith(tail):
            text = text[:-len(tail)]
            break
    text = text.removeprefix('以下の中からランダムで効果が付与される')
    if not text.startswith('・'):
        raise ValueError('Unrecognised random candidate table layout')
    parts = text[1:].split('・')
    if not parts or any(not part for part in parts):
        raise ValueError('Empty random candidate')
    options = [candidate(part, known_idols) for part in parts]
    unknown = sum(o is None for o in options)
    pool = dict(status='partial' if unknown else 'structured',
                options=[o for o in options if o is not None], unstructured_count=unknown,
                source_positions=copy.deepcopy(note['source_positions']),
                same_option_can_repeat=True, selection_probability='unknown')
    validate_pool(pool, known_idols)
    return pool


def resolve_pools(card, known_idols):
    live = [i for i in card['items'] if i['kind'] in {'panel_live', 'mb_live'}]
    pools = {}
    for item in live:
        if item.get('random_effect_options') and re.search(r'ランダム効果\d+個付与', normalized(item.get('effect_private'))):
            options = [dict(kind='rate_up', targets=[o['target']], value=o['value'],
                            unit=o['unit'], turns=o['turns']) for o in item['random_effect_options']]
            pool = dict(status='structured', options=options, unstructured_count=0,
                        source_positions=copy.deepcopy(item['source_positions']),
                        same_option_can_repeat=True, selection_probability='unknown')
            validate_pool(pool, known_idols)
            pools[item['detail_id']] = pool
    for note in card.get('skill_notes_private', []):
        name = normalized(note.get('name'))
        if not re.fullmatch(r'(?:\[MB\])?ランダム効果付与(?:\*1)?', name):
            continue
        table = note['source_positions'][0]['table']
        preceding = [i for i in live if i.get('source_positions') and i['source_positions'][0]['table'] < table]
        if not preceding:
            raise ValueError('Random candidate table has no preceding live table')
        primary = max(i['source_positions'][0]['table'] for i in preceding)
        owners = [i for i in preceding if i['source_positions'][0]['table'] == primary]
        kinds = {i['kind'] for i in owners}
        if len(kinds) != 1 or ('[MB]' in name and kinds != {'mb_live'}):
            raise ValueError('Ambiguous or mismatched random candidate owner')
        owners = [i for i in owners if re.search(r'ランダム効果\d+個付与', normalized(i.get('effect_private')))]
        if not owners:
            raise ValueError('Random candidate table has no explicit grant')
        if any(i['source_positions'][0].get('section_anchor') != note['source_positions'][0].get('section_anchor') for i in owners):
            raise ValueError('Random candidate owner crosses source sections')
        pool = note_pool(note, known_idols)
        for item in owners:
            if item['detail_id'] in pools:
                raise ValueError('Duplicate random candidate table association')
            pools[item['detail_id']] = copy.deepcopy(pool)
    return pools


def validate_pool(pool, known_idols):
    keys = {'status', 'options', 'unstructured_count', 'source_positions', 'same_option_can_repeat', 'selection_probability'}
    if not isinstance(pool, dict) or set(pool) != keys:
        raise ValueError('Non-public random pool field')
    options = pool['options']; unknown = pool['unstructured_count']
    if not isinstance(options, list) or type(unknown) is not int or unknown < 0:
        raise ValueError('Invalid random candidate counts')
    expected = 'partial' if unknown else 'structured' if options else 'unavailable'
    if pool['status'] != expected or pool['same_option_can_repeat'] is not True or pool['selection_probability'] != 'unknown':
        raise ValueError('Invalid random selection semantics')
    if not isinstance(pool['source_positions'], list) or (expected != 'unavailable' and not pool['source_positions']):
        raise ValueError('Missing random source positions')
    for p in pool['source_positions']:
        if not isinstance(p, dict) or not {'table', 'row', 'column'} <= set(p) or set(p) - {'table', 'row', 'column', 'section_anchor', 'field'}:
            raise ValueError('Invalid random source position')
        if any(type(p[k]) is not int or p[k] < 1 for k in ('table', 'row', 'column')):
            raise ValueError('Invalid random source coordinate')
        if 'section_anchor' in p and (not isinstance(p['section_anchor'], str) or not re.fullmatch(r'[A-Za-z0-9_-]+', p['section_anchor'])):
            raise ValueError('Invalid random source anchor')
        if 'field' in p and p['field'] not in {'effect_private', 'name'}:
            raise ValueError('Invalid random source field')
    seen = set()
    for o in options:
        if not isinstance(o, dict) or not {'kind', 'targets', 'unit', 'value'} <= set(o):
            raise ValueError('Invalid random candidate')
        kind = o['kind']; extra = {'turns'}
        if kind == 'rate_up':
            targets = {'Vocal', 'Dance', 'Visual', 'リアクション回避率', 'パッシブスキル発動率'}; unit = 'percent'
        else:
            allowed = {'passive_boost': (['パッシブスキル'], 'percent'), 'exchange_count_up': (['交換数'], 'points'),
                       'idol_appeal_bonus': (['アピール値'], 'multiplier'), 'flexible': (['フレキシブル'], 'boolean'),
                       'resurrection': (['メンタル'], 'percent')}
            if kind not in allowed:
                raise ValueError('Unknown random candidate kind')
            target, unit = allowed[kind]; targets = set(target)
        if kind == 'idol_appeal_bonus': extra.add('idols')
        if kind == 'resurrection': extra.update({'uses', 'trigger'})
        if set(o) - {'kind', 'targets', 'unit', 'value'} - extra or not isinstance(o['targets'], list) or len(o['targets']) != 1 or set(o['targets']) - targets or o['unit'] != unit:
            raise ValueError('Invalid random candidate fields')
        if type(o['value']) not in (int, float) or not math.isfinite(o['value']) or not 0 < o['value'] <= 10000:
            raise ValueError('Invalid random candidate amount')
        if kind == 'exchange_count_up':
            if type(o['value']) is not int or 'turns' in o: raise ValueError('Invalid exchange candidate')
        elif type(o.get('turns')) is not int or not 1 <= o['turns'] <= 100:
            raise ValueError('Missing random candidate duration')
        if kind == 'idol_appeal_bonus' and (not isinstance(o.get('idols'), list) or len(o['idols']) != 1 or o['idols'][0] not in known_idols):
            raise ValueError('Unknown random candidate idol')
        if kind == 'flexible' and o['value'] != 1: raise ValueError('Invalid flexible candidate')
        if kind == 'resurrection' and (o.get('trigger') != 'mental_zero' or type(o.get('uses')) is not int or not 1 <= o['uses'] <= 100):
            raise ValueError('Invalid resurrection candidate')
        key = json.dumps(o, sort_keys=True)
        if key in seen: raise ValueError('Duplicate random candidate')
        seen.add(key)

