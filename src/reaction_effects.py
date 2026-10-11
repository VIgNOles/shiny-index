"""Reaction-triggered grants; the watch window is not the granted buff duration."""
import re

ATTR=r'(?:Vocal|Dance|Visual|Vo|Da|Vi|ボーカル|ダンス|ビジュアル)'
BLOCK=re.compile(r'(?P<window>\d+)ターンの間(?P<event>回避時|ダメージ時)(?P<body>[^/]*)')
GRANT=re.compile(r'(?P<targets>'+ATTR+r'(?:&'+ATTR+r')*)(?P<value>\d+(?:\.\d+)?)%UP\[(?P<turns>\d+)ターン\]')
ALIASES={'Vo':'Vocal','Da':'Dance','Vi':'Visual','ボーカル':'Vocal','ダンス':'Dance','ビジュアル':'Visual'}
REACTION_TRIGGERS={'reaction_evaded','reaction_damage'}

def parse(part,scope):
 """Return blocked spans even for unsupported reaction bodies, preventing suffix guesses."""
 spans=[];facts=[]
 for m in BLOCK.finditer(part):
  if part[:m.start()].count('[')!=part[:m.start()].count(']'):continue
  if m.start() and part[m.start()-1] not in '/]':continue
  spans.append((m.start(),m.end()))
  body=m['body'];limit=re.search(r'\[(\d+)回\]$',body)
  if not limit:continue
  parts=body[:limit.start()].split('、')
  grants=[GRANT.fullmatch(p) for p in parts]
  window,uses=int(m['window']),int(limit[1])
  if not all(grants) or not 1<=window<=100 or not 1<=uses<=100:continue
  if any(not 1<=int(g['turns'])<=100 for g in grants):continue
  pos=m.start()
  for g in grants:
   targets=[ALIASES.get(t,t) for t in g['targets'].split('&')]
   if len(targets)!=len(set(targets)):continue
   e={'metric':'rate_up','targets':targets,'unit':'percent','scope':scope,
      'value':float(g['value']),'turns':int(g['turns']),'trigger_turns':window,
      'uses':uses,'trigger':'reaction_evaded' if m['event']=='回避時' else 'reaction_damage',
      'restriction_status':'partial'}
   if len(grants)>1:e['shared_uses']=True
   facts.append((pos,e));pos+=len(g[0])+1
 return spans,facts
