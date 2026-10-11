"""Status consumption belongs to the adjacent appeal, not a grant or a skill condition."""
import re

ATTR=r'(?:Vocal|Dance|Visual|Vo|Da|Vi|ボーカル|ダンス|ビジュアル)'
TOKEN=re.compile(r'('+ATTR+r')(UP|DOWN)?')
ALIASES={'Vo':'Vocal','Da':'Dance','Vi':'Visual','ボーカル':'Vocal','ダンス':'Dance','ビジュアル':'Visual'}

def adjacent_consumption(part,end):
 """Only a complete first suffix is accepted; & can share its final direction."""
 m=re.match(r'\[消去:([^\[\]]+)\]',part[end:])
 if not m:return None
 tokens=[TOKEN.fullmatch(s) for s in m[1].split('&')]
 if not tokens or not all(tokens) or not tokens[-1][2]:return None
 statuses=[];direction=None
 for token in reversed(tokens):
  direction=token[2] or direction
  statuses.append({'target':ALIASES.get(token[1],token[1]),'direction':direction})
 statuses.reverse()
 if len({(s['target'],s['direction']) for s in statuses})!=len(statuses):return None
 return {'statuses':statuses,'timing':'after_appeal','quantity':'all',
         'scaling':'status_count','passive_included':False}

def validate_consumption(e):
 c=e['status_consumption']
 if e['metric']!='appeal' or e['unit']!='multiplier':raise ValueError('Consumption must belong to an appeal')
 if not isinstance(c,dict) or set(c)!={'statuses','timing','quantity','scaling','passive_included'}:raise ValueError('Invalid consumption fields')
 if c['timing']!='after_appeal' or c['quantity']!='all' or c['scaling']!='status_count' or c['passive_included'] is not False:raise ValueError('Invalid consumption semantics')
 statuses=c['statuses']
 if not isinstance(statuses,list) or not statuses:raise ValueError('Missing consumed status')
 for s in statuses:
  if not isinstance(s,dict) or set(s)!={'target','direction'} or s['target'] not in {'Vocal','Dance','Visual'} or s['direction'] not in {'UP','DOWN'}:raise ValueError('Invalid consumed status')
 if len({(s['target'],s['direction']) for s in statuses})!=len(statuses):raise ValueError('Duplicate consumed status')
 if any(k in e for k in ('turns','turn_range','turns_maximum','uses','trigger','trigger_turns','shared_uses','recipient','duet_target','timing','excludes','grant_count_maximum','formula','amount_unknown')):raise ValueError('Consumption is immediate and has no grant duration')
