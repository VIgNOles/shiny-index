"""Allowlisted live mechanics from saved R01 and card cells, without raw prose."""
import re
from src.skill_conditions_v2 import unit_name

SPECIAL_METRICS={'resurrection','audience_status_clear','duet','duet_add','interest_minimum','charm','enthusiasm'}
SPECIAL_TARGETS={'観客ステータス','アピール履歴','魅了','熱狂'}
PATTERNS=[
 ('resurrection',re.compile(r'リザレクション効果(?P<value>\d+(?:\.\d+)?)%付与\[(?P<turns>\d+)ターン\]\[(?P<uses>\d+)回\]')),
 ('audience_status_clear',re.compile(r'全観客の興味変動無効以外のステータス効果を解除(?=\[コスト:\d+\]|$|/)')),
 ('duet_add',re.compile(r'このターンのアピールにデュエット\[(?P<target>[^\[\]]+)\]を追加(?=\[コスト:\d+\]|$|/)')),
 ('duet',re.compile(r'デュエット\[(?P<target>[^\[\]]+)\](?=$|/|\[)')),
 ('interest_minimum',re.compile(r'(?P<audience>全観客に|全観客の)?興味最小(?P<value>\d+(?:\.\d+)?)倍\[(?P<turns>\d+)ターン\]')),
 ('charm',re.compile(r'(?P<audience>全観客に|全観客の)?魅了\[(?P<turns>\d+)ターン\]')),
 ('enthusiasm',re.compile(r'(?P<audience>全観客に|全観客の)?熱狂(?:最大(?P<count>\d+)つ付与)?\[(?:(?P<turns>\d+)ターン|(?P<low>\d+)[～〜~\-](?P<high>\d+)ターン|最大(?P<maxturns>\d+)ターン)\]')),
]
def facts(part,scope,ctx):
 out=[]
 for metric,pattern in PATTERNS:
  for m in pattern.finditer(part):
   # Never read a condition bracket or a suffix inside unknown prose as an effect.
   if part[:m.start()].count('[')!=part[:m.start()].count(']'):continue
   if m.start() and part[m.start()-1] not in '/]':continue
   g=m.groupdict()
   e={'metric':metric,'scope':scope,'restriction_status':'partial'}
   if metric=='resurrection':
    e.update(targets=['メンタル'],unit='percent',value=float(g['value']),turns=int(g['turns']),uses=int(g['uses']),trigger='mental_zero')
   elif metric=='audience_status_clear':
    e.update(targets=['観客ステータス'],unit='boolean',value=1,audience='all',excludes=['興味変動無効'])
   elif metric in {'duet','duet_add'}:
    token=g['target']
    if token=='編成アイドル':target={'kind':'formation'}
    elif ctx and token in ctx['idols']:target={'kind':'idol','name':token}
    elif ctx and (u:=unit_name(token,ctx)):target={'kind':'unit','name':u}
    else:continue
    e.update(targets=['アピール履歴'],unit='boolean',value=1,duet_target=target)
    if metric=='duet_add':e['timing']='current_turn'
   elif metric=='interest_minimum':
    if scope!='grow':continue
    e.update(targets=['興味'],unit='multiplier',value=float(g['value']),turns=int(g['turns']))
   else:
    e.update(targets=['魅了' if metric=='charm' else '熱狂'],unit='boolean',value=1)
    if g.get('turns'):e['turns']=int(g['turns'])
    if g.get('count'):e['grant_count_maximum']=int(g['count'])
    if g.get('low'):
     low,high=int(g['low']),int(g['high'])
     if not 1<=low<=high<=100:continue
     e['turn_range']={'minimum':low,'maximum':high}
    if g.get('maxturns'):e['turns_maximum']=int(g['maxturns'])
   if g.get('audience'):e['audience']='all'
   out.append((m.start(),e))
 return out
