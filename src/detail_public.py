"""Allowlisted factual detail distribution; Wiki prose remains in the private master."""
from collections import Counter
from datetime import datetime
import hashlib,json,re,uuid,math
from pathlib import Path
from urllib.parse import urlsplit,unquote
from src.detail_master import resolve,validate,KINDS,validate_generation_parents
from src.indexer import digest,read,write,now
from src.skill_effects import effect_details,validate_effect_details
from src.skill_conditions import activation_condition,validate_condition
from src.skill_conditions_v3 import keyword_extension,validate_keyword_condition
from src.skill_conditions_v2 import context as condition_context,activation_extension,validate_extension

MECHANICS={'link','plus','change','grow','refrain'}
COVERAGE_FIELDS={'skill_panel','review','memory_appeal','memory_boost','generated_live','unique_ability','stage_skill','aptitude','fight_skill','max_status','possessed_live','quick_skill','support_skills','traits'}
ITEM_FIELDS=['detail_id','kind','name','sp','unlock_star','unlock_event','mb_stage','mb_total_stages','level','acquired_at_level','mechanics','cap_targets','cap_delta','energy_cost','generation_stage','generated_from_name','generated_from_names','generation_origin_kind','generation_origin_kinds','random_effect_options','memory_link_facts','memory_charge_facts','memory_link_present','memory_charge_present']

def numeric_facts(item):
    # Individual numeric facts do not imply unconditional or complete skill effects.
    value=item.get('name','')+' / '+item.get('effect_private','')
    facts=[]
    for match in re.finditer(r'(Vocal|Dance|Visual)((?:\s*&\s*(?:Vocal|Dance|Visual))*)\s*(\d+(?:\.\d+)?)\s*[～〜~]\s*(\d+(?:\.\d+)?)倍(?:アピール)?',value):
        facts.append({'metric':'appeal_range','targets':re.findall(r'Vocal|Dance|Visual',match[1]+match[2]),'minimum':float(match[3]),'maximum':float(match[4]),'unit':'multiplier'})
    for match in re.finditer(r'(Vocal|Dance|Visual)((?:\s*&\s*(?:Vocal|Dance|Visual))*)\s*(最大)?\s*(\d+(?:\.\d+)?)倍(?:アピール)?',value):
        facts.append({'metric':'appeal_maximum' if match[3] else 'appeal','targets':re.findall(r'Vocal|Dance|Visual',match[1]+match[2]),'value':float(match[4]),'unit':'multiplier'})
    for match in re.finditer(r'(Vocal|Dance|Visual|注目度|思い出ゲージ|リアクション回避率|メンタルダメージ|メンタル)\s*(\d+(?:\.\d+)?)%\s*(UP|DOWN|CUT)',value):
        facts.append({'metric':'rate','target':match[1],'value':float(match[2]),'unit':'percent','direction':match[3]})
    for label,metric,unit in [('確率','activation_probability','percent'),('最大','activation_limit','times')]:
        match=re.search(r'\['+label+r':\s*(\d+)(?:%|回)\]',value)
        if match:facts.append({'metric':metric,'value':int(match[1]),'unit':unit})
    return [dict(row) for row in {json.dumps(f,sort_keys=True):f for f in facts}.values()]


def public_document(master,base_cards,base_version=None):
    base_version=base_version or master['base_dataset_version']
    validate(master);bases={c['card_id']:c for c in base_cards}
    if len(bases)!=len(base_cards):raise ValueError('Duplicate base card')
    known_idols={c['idol_name'] for c in base_cards if c.get('idol_name')}
    conditions=condition_context(base_cards)
    cards=[]
    for source in resolve(master):
        cid=source['card_id']
        if cid not in bases or bases[cid]['card_kind']!=source['card_kind']:raise ValueError('Orphan or mixed P/S detail')
        card={key:source[key] for key in ['card_id','card_kind','wiki_url','fetched_at','source_sha256','coverage']}
        card['items']=[]
        if source['card_kind']=='S':
            card['traits']={key:source['traits'][key] for key in ['idea','inspiration','music_proficiencies']}
            card['max_status']={key:source['max_status'].get(key) for key in ['level','limit_break','vocal','dance','visual','mental','missing_fields']}
        for item in source['items']:
            public={key:item[key] for key in ITEM_FIELDS if key in item}
            public.update(numeric_facts=numeric_facts(item),effect_structure='partial',conditions_not_structured=True,
                          source_positions=item.get('source_positions',[]))
            effects=effect_details(item,known_idols)
            if effects is not None:public['effect_details']=effects
            condition=activation_condition(item,known_idols)
            if condition is not None:
                public['activation_condition']=condition
                if condition['status']=='unsupported':
                    extension=activation_extension(item,conditions)
                    if extension is not None:public['activation_condition_v2']=extension
                    else:
                        keyword=keyword_extension(item)
                        if keyword is not None:public['activation_condition_v3']=keyword
            if item['kind']=='memory_appeal':
                for slot,source_field in [('link','link_appeal_private'),('charge','charge_appeal_private')]:
                    text=(item.get(source_field) or '').strip()
                    public['memory_'+slot+'_present']=text not in {'','-','－','―'}
                    public['memory_'+slot+'_facts']=numeric_facts({'effect_private':text}) if public['memory_'+slot+'_present'] else []
            if item.get('progression'):
                public['progression']=[{key:step[key] for key in ['support_level','skill_level']} for step in item['progression']]
            if item.get('manual_source_ref'):public['manual_source_ref']=item['manual_source_ref']
            card['items'].append(public)
        cards.append(card)
    adopted={c['card_id']:c for c in cards};coverage=[]
    for row in master['coverage']:
        cid=row['card_id']
        if cid not in bases or row['card_kind']!=bases[cid]['card_kind']:raise ValueError('Unknown coverage card')
        state='available_partial' if cid in adopted else row['status']
        coverage.append({'card_id':cid,'card_kind':row['card_kind'],'status':state})
    if {r['card_id'] for r in coverage}!=set(bases):
        if base_version==master['base_dataset_version']:raise ValueError('Missing base coverage')
        represented={r['card_id'] for r in coverage}
        coverage.extend({'card_id':cid,'card_kind':bases[cid]['card_kind'],'status':'not_in_acquisition_catalog'} for cid in sorted(set(bases)-represented))
    condition_counts=Counter(i['activation_condition']['status'] for c in cards for i in c['items'] if 'activation_condition' in i)
    search_condition_counts=Counter(i.get('activation_condition_v2',i['activation_condition'])['status'] for c in cards for i in c['items'] if i['kind']=='panel_passive')
    current_condition_counts=Counter(i.get('activation_condition_v3',i.get('activation_condition_v2',i['activation_condition']))['status'] for c in cards for i in c['items'] if i['kind']=='panel_passive')
    effect_counts={kind:dict(Counter(i['effect_details']['status'] for c in cards for i in c['items'] if i['kind']==kind)) for kind in sorted({i['kind'] for c in cards for i in c['items'] if 'effect_details' in i})}
    counts=Counter(row['status'] for row in coverage)
    unverified=['Complete effect/condition structure','Independent official verification']
    if any(state not in {'available_partial','missing_page_on_hold'} for state in counts):
        unverified.insert(0,'Full detail acquisition')
    if counts.get('missing_page_on_hold'):
        unverified.append('Unlinked pages on hold')
    body={'cards':cards,'coverage':{'complete':False,'base_card_count':len(bases),'detail_card_count':len(cards),
          'detail_item_count':sum(len(c['items']) for c in cards),'by_kind':dict(Counter(c['card_kind'] for c in cards)),
          'status_counts':dict(counts),'card_status':coverage,
          'activation_condition_counts':dict(condition_counts),
          'activation_condition_search_counts':dict(search_condition_counts),
          'activation_condition_current_counts':dict(current_condition_counts),
          'effect_detail_counts':effect_counts,
          'not_collected':['P.stage_skill','P.aptitude','S.fight_skill'],
          'unverified':unverified}}
    version='d1-'+digest({'base_dataset_version':base_version,**body})[:16]
    doc={'meta':{'detail_schema':'1.0','detail_version':version,'base_dataset_version':base_version,'source_base_dataset_version':master['base_dataset_version'],
                 'canonical_detail_revision':master['revision'],'published_at':now(),'source_fetched_from':min(c['fetched_at'] for c in cards),
                 'source_fetched_to':max(c['fetched_at'] for c in cards)},**body}
    validate_public(doc,base_cards);return doc



def validate_memory_facts(item):
    fields={'memory_link_facts','memory_charge_facts','memory_link_present','memory_charge_present'}
    if not fields.intersection(item):return
    if item['kind']!='memory_appeal' or not fields.issubset(item):raise ValueError('Invalid memory effect slots')
    for slot in ('link','charge'):
        present=item['memory_'+slot+'_present'];facts=item['memory_'+slot+'_facts']
        if type(present) is not bool or not isinstance(facts,list) or (not present and facts):raise ValueError('Invalid memory effect presence')
        for fact in facts:
            if not isinstance(fact,dict):raise ValueError('Invalid memory numeric fact')
            if fact.get('metric')=='appeal_range':
                if (set(fact)!={'metric','targets','minimum','maximum','unit'} or not isinstance(fact['targets'],list) or not fact['targets'] or set(fact['targets'])-{'Vocal','Dance','Visual'} or fact['unit']!='multiplier'
                        or any(type(fact[k]) not in (int,float) or not math.isfinite(fact[k]) for k in ('minimum','maximum')) or not 0<=fact['minimum']<=fact['maximum']):raise ValueError('Invalid memory numeric range')
                continue
            if not isinstance(fact,dict) or type(fact.get('value')) not in (int,float) or not math.isfinite(fact['value']) or fact['value']<0:raise ValueError('Invalid memory numeric fact')
            metric=fact.get('metric')
            if metric in {'appeal','appeal_maximum'}:
                if set(fact)!={'metric','targets','value','unit'} or not isinstance(fact['targets'],list) or not fact['targets'] or set(fact['targets'])-{'Vocal','Dance','Visual'} or fact['unit']!='multiplier':raise ValueError('Invalid memory numeric fact')
            elif metric=='rate':
                if set(fact)!={'metric','target','value','unit','direction'} or fact['target'] not in {'Vocal','Dance','Visual','注目度','思い出ゲージ','リアクション回避率','メンタルダメージ','メンタル'} or fact['unit']!='percent' or fact['direction'] not in {'UP','DOWN','CUT'}:raise ValueError('Invalid memory numeric fact')
            elif metric in {'activation_probability','activation_limit'}:
                if set(fact)!={'metric','value','unit'} or type(fact['value']) is not int or fact['unit']!=('percent' if metric=='activation_probability' else 'times'):raise ValueError('Invalid memory numeric fact')
            else:raise ValueError('Invalid memory numeric fact')

def validate_public(doc,base_cards):
    if set(doc)!={'meta','cards','coverage'}:raise ValueError('Non-public document field')
    bases={c['card_id']:c for c in base_cards};ids=set();items=set()
    known_idols={c['idol_name'] for c in base_cards if c.get('idol_name')}
    conditions=condition_context(base_cards)
    if doc['meta']['detail_schema']!='1.0':raise ValueError('Unknown detail schema')
    for card in doc['cards']:
        if set(card)-{'card_id','card_kind','wiki_url','fetched_at','source_sha256','coverage','items','traits','max_status'}:raise ValueError('Non-public card field')
        cid=card['card_id'];uuid.UUID(cid)
        if cid in ids or cid not in bases or card['card_kind']!=bases[cid]['card_kind']:raise ValueError('Invalid detail card')
        ids.add(cid)
        url=urlsplit(card['wiki_url'])
        if url.scheme!='https' or url.netloc!='wikiwiki.jp' or not unquote(url.path).startswith('/shinycolors/'):raise ValueError('Unsafe detail URL')
        if set(card['coverage'])-COVERAGE_FIELDS:raise ValueError('Non-public coverage field')
        if any(value not in {'extracted','needs_review','not_collected','no_entry_confirmed','partial_missing_values'} for value in card['coverage'].values()):raise ValueError('Invalid coverage state')
        if not re.fullmatch('[0-9a-f]{64}',card['source_sha256']):raise ValueError('Invalid source hash')
        datetime.fromisoformat(card['fetched_at'])
        for item in card['items']:
            uuid.UUID(item['detail_id'])
            if 'activation_condition' in item:
                if item['kind']!='panel_passive':raise ValueError('Activation condition on non-passive')
                validate_condition(item['activation_condition'],known_idols)
            if 'activation_condition_v2' in item:
                if item['kind']!='panel_passive' or item.get('activation_condition')!={'status':'unsupported'}:raise ValueError('Invalid condition extension owner')
                validate_extension(item['activation_condition_v2'],conditions)
            if 'effect_details' in item:
                if item['kind'] not in {'support_skill','unique_ability','panel_live','mb_live','generated_live','possessed_live','memory_appeal','quick_skill'}:raise ValueError('Invalid effect structure owner')
                validate_effect_details(item['effect_details'],known_idols)
            validate_memory_facts(item)
            validate_generation_parents(item)
            if item['detail_id'] in items or item['kind'] not in KINDS[card['card_kind']]:raise ValueError('Invalid detail item')
            items.add(item['detail_id'])
            if item['kind']=='generated_live' and (item.get('sp') is not None
                    or type(item.get('generation_stage')) is not int or item['generation_stage']<1
                    or not item.get('generated_from_name')):
                raise ValueError('Invalid public generated-live relation')
            if any(set(position)-{'table','row','column','section_anchor','field'} for position in item.get('source_positions',[])):raise ValueError('Non-public source position field')
            if item.get('generation_origin_kind') not in {None,'panel_live','mb_live'}:raise ValueError('Invalid generation origin')
            for option in item.get('random_effect_options',[]):
                if (set(option)!={'metric','target','value','unit','direction','turns'} or option['metric']!='rate'
                        or option['target'] not in {'Vocal','Dance','Visual'} or option['unit']!='percent' or option['direction']!='UP'
                        or type(option['value']) not in (int,float) or not math.isfinite(option['value']) or option['value']<0
                        or type(option['turns']) is not int or option['turns']<1):raise ValueError('Invalid random-effect option')
            if set(item.get('mechanics',[]))-MECHANICS:raise ValueError('Invalid mechanic')
            if 'activation_condition_v3' in item:
                if item['kind']!='panel_passive' or item.get('activation_condition')!={'status':'unsupported'} or 'activation_condition_v2' in item:raise ValueError('Invalid keyword condition owner')
                validate_keyword_condition(item['activation_condition_v3'])
            if set(item)-set(ITEM_FIELDS+['numeric_facts','effect_structure','conditions_not_structured','source_positions','progression','manual_source_ref','activation_condition','activation_condition_v2','activation_condition_v3','effect_details']):raise ValueError('Non-public detail field')
    coverage=doc['coverage'];rows=coverage['card_status']
    if len(rows)!=len(bases) or {r['card_id'] for r in rows}!=set(bases):raise ValueError('Coverage anomaly')
    if coverage['detail_card_count']!=len(ids) or coverage['detail_item_count']!=len(items):raise ValueError('Count anomaly')
    if coverage['status_counts']!=dict(Counter(r['status'] for r in rows)):raise ValueError('Status count mismatch')
    if 'activation_condition_counts' in coverage:
        passives=[i for c in doc['cards'] for i in c['items'] if i['kind']=='panel_passive']
        if any('activation_condition' not in i for i in passives):raise ValueError('Missing passive activation condition')
        expected=dict(Counter(i['activation_condition']['status'] for i in passives))
        actual=coverage['activation_condition_counts']
        if not isinstance(actual,dict) or actual!=expected or any(type(v) is not int or v<0 for v in actual.values()):raise ValueError('Activation condition count mismatch')
    if any('activation_condition_v2' in i for c in doc['cards'] for i in c['items']) and 'activation_condition_search_counts' not in coverage:raise ValueError('Missing extended condition counts')
    if 'activation_condition_search_counts' in coverage:
        passives=[i for c in doc['cards'] for i in c['items'] if i['kind']=='panel_passive']
        if any('activation_condition' not in i for i in passives):raise ValueError('Missing searchable passive condition')
        expected=dict(Counter(i.get('activation_condition_v2',i['activation_condition'])['status'] for i in passives))
        actual=coverage['activation_condition_search_counts']
        if not isinstance(actual,dict) or actual!=expected or any(type(v) is not int or v<0 for v in actual.values()):raise ValueError('Searchable activation condition count mismatch')
    if any('activation_condition_v3' in i for c in doc['cards'] for i in c['items']) and 'activation_condition_current_counts' not in coverage:raise ValueError('Missing current condition counts')
    if 'activation_condition_current_counts' in coverage:
        passives=[i for c in doc['cards'] for i in c['items'] if i['kind']=='panel_passive']
        if any('activation_condition' not in i for i in passives):raise ValueError('Missing current passive condition')
        expected=dict(Counter(i.get('activation_condition_v3',i.get('activation_condition_v2',i['activation_condition']))['status'] for i in passives))
        actual=coverage['activation_condition_current_counts']
        if not isinstance(actual,dict) or actual!=expected or any(type(v) is not int or v<0 for v in actual.values()):raise ValueError('Current activation condition count mismatch')
    if any('effect_details' in i for c in doc['cards'] for i in c['items']) and 'effect_detail_counts' not in coverage:raise ValueError('Missing effect coverage')
    if 'effect_detail_counts' in coverage:
        expected={kind:dict(Counter(i['effect_details']['status'] for c in doc['cards'] for i in c['items'] if i['kind']==kind)) for kind in sorted({i['kind'] for c in doc['cards'] for i in c['items'] if 'effect_details' in i})}
        if coverage['effect_detail_counts']!=expected:raise ValueError('Effect coverage mismatch')
    if coverage['complete'] is not False:raise ValueError('Partial effects must not claim complete')
    body={'base_dataset_version':doc['meta']['base_dataset_version'],'cards':doc['cards'],'coverage':coverage}
    if doc['meta']['detail_version']!='d1-'+digest(body)[:16]:raise ValueError('Detail content version mismatch')
    return {'version':doc['meta']['detail_version'],'cards':len(ids),'items':len(items)}


def prepare(master,base_cards,root,base_version=None):
    root=Path(root);doc=public_document(master,base_cards,base_version);version=doc['meta']['detail_version'];target=root/'details'/version
    if target.exists():
        old=read(target/'details.json');validate_public(old,base_cards)
        if old['cards']!=doc['cards'] or old['coverage']!=doc['coverage']:raise ValueError('Detail version collision')
        write(root/'details/latest.json',{'detail_version':version,'base_dataset_version':doc['meta']['base_dataset_version'],'manifest':version+'/manifest.json'})
        return old
    target.mkdir(parents=True)
    # Compact new bundles only; retain existing immutable bundles byte for byte.
    (target/'details.json').write_bytes((json.dumps(doc,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8'))
    manifest={'detail_schema':'1.0','detail_version':version,'base_dataset_version':doc['meta']['base_dataset_version'],
              'published_at':doc['meta']['published_at'],'files':{'details.json':hashlib.sha256((target/'details.json').read_bytes()).hexdigest()}}
    write(target/'manifest.json',manifest)
    write(root/'details/latest.json',{'detail_version':version,'base_dataset_version':doc['meta']['base_dataset_version'],'manifest':version+'/manifest.json'})
    return doc


def check_tree(root):
    root=Path(root);base_dir=root/'details'
    if not base_dir.exists():return []
    names={p.name for p in base_dir.iterdir()};versions=names-{'latest.json'}
    if 'latest.json' not in names or not versions or any(not re.fullmatch(r'd1-[0-9a-f]{16}',v) for v in versions):raise ValueError('Unexpected detail distribution entry')
    latest=read(base_dir/'latest.json')
    if set(latest)!={'detail_version','base_dataset_version','manifest'} or latest['detail_version'] not in versions or latest['manifest']!=latest['detail_version']+'/manifest.json':raise ValueError('Invalid detail pointer')
    current=read(root/'data/latest.json')['dataset_version']
    if latest['base_dataset_version']!=current:raise ValueError('Detail/base pointer mismatch')
    html=(root/'index.html').read_text(encoding='utf-8')
    markers=re.findall(r"window\.DETAIL_VERSION='(d1-[0-9a-f]{16})'",html)
    if 'window.DETAIL_VERSION' in html and markers!=[latest['detail_version']]:raise ValueError('HTML detail version mismatch')
    results=[]
    for v in sorted(versions):
        path=base_dir/v
        if not path.is_dir() or {p.name for p in path.iterdir()}!={'manifest.json','details.json'}:raise ValueError('Unexpected detail bundle file')
        manifest=read(path/'manifest.json');doc=read(path/'details.json')
        if manifest['detail_version']!=v or manifest['files']!={'details.json':hashlib.sha256((path/'details.json').read_bytes()).hexdigest()}:raise ValueError('Detail file hash mismatch')
        if manifest['published_at']!=doc['meta']['published_at'] or manifest['base_dataset_version']!=doc['meta']['base_dataset_version']:raise ValueError('Detail manifest mismatch')
        base_cards=read(root/'data'/manifest['base_dataset_version']/'cards.json')['cards']
        results.append(validate_public(doc,base_cards))
    return results
