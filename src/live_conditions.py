"""Source-bound live conditions, isolated from the passive condition grammar.

Legacy activation_condition is kept for old UI. These optional rules distinguish
Grow level-up events from the current states used to activate Plus/Refrain.
"""
import re
from src.skill_conditions_v2 import idol_name, unit_name, join, validate_expression

GRANT_STATUSES = {'VocalUP','DanceUP','VisualUP','注目度UP','注目度DOWN',
                  'パッシブスキル発動率UP','パッシブスキル強化','リラックス'}
EVENT_FIELDS = {'status_granted','idol_appeal_boost_granted','history_unit_added',
                'audience_reaction_targeted'}

def leaf(field, value, **extras):
    return {'field':field,'operator':'eq','value':value,**extras}

def activation(text, ctx, scope):
    if scope=='plus':
        m=re.fullmatch(r'パッシブスキル(\d+)個以上発動(.+?)全員がライブに参加(?:している場合)?',text)
        if m and (unit:=unit_name(m[2],ctx)):
            return join('all',[{'field':'active_passive_count','operator':'gte','value':int(m[1])},
                               leaf('unit_all_participants',unit)])
        m=re.fullmatch(r'(注目度UP|注目度DOWN)が(\d+)個以上付与(.+?)全員がライブに参加(?:している場合)?',text)
        if m and (unit:=unit_name(m[3],ctx)):
            return join('all',[{'field':'status_count','operator':'gte','value':int(m[2]),'status':m[1]},
                               leaf('unit_all_participants',unit)])
        m=re.fullmatch(r'履歴に(.+?)のアイドル(\d+)人以上又は(.+?)がある場合',text)
        if m and (unit:=unit_name(m[1],ctx)) and (idol:=idol_name(m[3],ctx)):
            return join('any',[{'field':'history_unit_count','operator':'gte','value':int(m[2]),'unit':unit},
                               leaf('history_participant',idol)])
    if scope=='refrain':
        m=re.fullmatch(r'(.+?)のアピール倍率UPが(\d+)個以上付与されている場合',text)
        if m and (idol:=idol_name(m[1],ctx)):
            return {'field':'idol_appeal_boost_count','operator':'gte','value':int(m[2]),'idol':idol}
    return None

def growth(text,ctx):
    if text=='観客からリアクションの対象になる毎':
        return leaf('audience_reaction_targeted',True),1
    m=re.fullmatch(r'履歴に(.+?)アイドル(?:を)?追加',text)
    if m and (unit:=unit_name(m[1],ctx)):
        return leaf('history_unit_added',unit),1
    m=re.fullmatch(r'(.+?)を(?:(\d+)個付与毎|付与)',text)
    if not m:return None
    target=m[1];count=int(m[2] or 1);parts=target.split('又は')
    terms=[]
    # A shared idol-boost suffix may apply to three explicitly named idols.
    shared=target.endswith('のアピール倍率UP') and all(idol_name(p,ctx) for p in target.removesuffix('のアピール倍率UP').split('又は'))
    if shared:
        terms=[leaf('idol_appeal_boost_granted',idol_name(p,ctx)) for p in target.removesuffix('のアピール倍率UP').split('又は')]
    else:
        for part in parts:
            if part in GRANT_STATUSES:terms.append(leaf('status_granted',part))
            elif part.endswith('のアピール倍率UP') and (idol:=idol_name(part.removesuffix('のアピール倍率UP'),ctx)):
                terms.append(leaf('idol_appeal_boost_granted',idol))
            else:return None
    if not terms or len({(p['field'],p['value']) for p in terms})!=len(terms):return None
    return (terms[0] if len(terms)==1 else join('any',terms)),count

def mechanic_rule(part,ctx,scope):
    if ctx is None:return None
    match=re.match(r'((?:\[[^\[\]]*\])+)',part)
    if not match:return None
    brackets=[b.removeprefix('条件:') for b in re.findall(r'\[([^\[\]]*)\]',match[1])]
    # New shorthand grammars require exactly one complete condition bracket.
    if len(brackets)!=1:return None
    if scope=='grow':
        parsed=growth(brackets[0],ctx)
        if not parsed:return None
        expression,count=parsed
        result={'status':'structured','role':'growth','expression':expression,'events_per_level':count,
                'level_up_timing':'next_turn','carry_over':True,'reset_on_use':True}
    else:
        expression=activation(brackets[0],ctx,scope)
        if expression is None:return None
        result={'status':'structured','role':'activation','expression':expression}
    try:validate_rule(result,ctx,scope)
    except ValueError:return None
    return result

def validate_live_expression(p,ctx,role,depth=0,budget=None):
    if budget is None:budget=[64]
    budget[0]-=1
    if depth>4 or budget[0]<0 or not isinstance(p,dict):raise ValueError('Invalid live condition tree')
    if 'terms' in p:
        if set(p)!={'operator','terms'} or p['operator'] not in {'all','any'} or not isinstance(p['terms'],list) or not 2<=len(p['terms'])<=16:
            raise ValueError('Invalid live condition logic')
        for child in p['terms']:validate_live_expression(child,ctx,role,depth+1,budget)
        return
    field=p.get('field');value=p.get('value');op=p.get('operator')
    if role=='growth':
        if set(p)!={'field','operator','value'} or op!='eq' or field not in EVENT_FIELDS:raise ValueError('Invalid growth event')
        if field=='status_granted':valid=isinstance(value,str) and value in GRANT_STATUSES
        elif field=='idol_appeal_boost_granted':valid=isinstance(value,str) and value in ctx['idols']
        elif field=='history_unit_added':valid=isinstance(value,str) and value in ctx['units']
        else:valid=value is True
    elif field in {'active_passive_count','idol_appeal_boost_count'}:
        extra={'idol'} if field=='idol_appeal_boost_count' else set()
        valid=(set(p)=={'field','operator','value'}|extra and op=='gte' and type(value) is int and 1<=value<=100000)
        if extra:valid=valid and isinstance(p.get('idol'),str) and p['idol'] in ctx['idols']
    else:
        validate_expression(p,ctx);return
    if not valid:raise ValueError('Invalid live condition predicate')

def validate_rule(rule,ctx,scope):
    if not isinstance(rule,dict) or rule.get('status')!='structured' or rule.get('role') not in {'activation','growth'}:
        raise ValueError('Invalid mechanic rule')
    keys={'status','role','expression'}
    if rule['role']=='growth':
        keys|={'events_per_level','level_up_timing','carry_over','reset_on_use'}
        if scope!='grow' or type(rule.get('events_per_level')) is not int or not 1<=rule['events_per_level']<=100000 or rule.get('level_up_timing')!='next_turn' or rule.get('carry_over') is not True or rule.get('reset_on_use') is not True:
            raise ValueError('Invalid Grow level rule')
    elif scope not in {'plus','refrain'}:raise ValueError('Invalid activation rule scope')
    if set(rule)!=keys:raise ValueError('Non-public mechanic rule field')
    validate_live_expression(rule['expression'],ctx,rule['role'])
