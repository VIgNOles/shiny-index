"""Typed, source-bound effect facts. Unrecognised prose stays private.
Support rules match whole cells. Live duration is attached only to the adjacent
recognised effect, with its mechanic scope; it is never copied to other effects.
"""
import math,re,unicodedata
from src.skill_conditions_v2 import parse as parse_condition, validate_extension, join, idol_name
from src.live_conditions import mechanic_rule, validate_rule
from src.special_live_effects import facts as special_facts, SPECIAL_METRICS, SPECIAL_TARGETS
LIVE={'panel_live','mb_live','generated_live','possessed_live','memory_appeal','quick_skill'}
TARGETS={'Vocal','Dance','Visual','メンタル','SP','体力','絆','テンション','トラブル率','注目度','思い出ゲージ','リアクション回避率','メンタルダメージ','興味','影響力','アピール値','基礎能力値','施設Lv','パーフェクト','エクセレント','イベント発生率','ノウハウ発現率','アドバイス抽選率','交換数','Excellent'}
METRICS={'support_gain','support_recovery','support_cost_down','support_trouble_down','support_rest_gain','support_bond','support_tension_protection','appeal_boost','memory_gain_boost','base_stat_boost','rate_up','rate_down','rate_cut','interest','support_presence_up','support_event_rate','support_knowhow_rate','support_location_level','support_perfect','support_excellent','support_advice_rate','exchange_count_up','appeal'}
TRIGGERS={'produce_start','missed_promise','rest','lesson_or_work','unit_member_present','tension_max','audition_first','vocal_lesson','dance_lesson','visual_lesson','radio','talk','magazine','talk_event','solo_vocal_lesson','solo_dance_lesson','solo_radio','no_trouble','excellent','knowhow_acquired','always','say_halo','appeal_phase_start','turn_2'}
SCOPES={'base','link','plus','change','grow','refrain','memory_link','memory_charge'}
TARGETS.update({'パッシブスキル発動率','パッシブスキル','リラックス','過去のアピール'})
METRICS.update({'mental_recovery','mental_cost','memory_gauge_gain','relax','passive_boost','refrain'})
METRICS.update(SPECIAL_METRICS)
TARGETS.update(SPECIAL_TARGETS)
TRIGGERS.add('mental_zero')
SCALING={
 'メンタルが多いほど効果UP':'mental','メンタルが少ないほど効果UP':'mental_descending',
 'メンタルが低いほど効果UP':'mental_descending','Meが少ない程効果UP':'mental_descending',
 '注目度が高いほど効果UP':'attention','注目度が低いほど効果UP':'attention_descending',
 '注目度が低い程効果UP':'attention_descending','回復回数増加で効果UP':'heal_count',
 '回避率が高いほど効果UP':'evasion','スキル履歴が多いほど効果UP':'history',
 '履歴が多いほど効果UP':'history','思い出ゲージが多いほど効果UP':'memory',
 '所属ユニットが多いほど効果UP':'unit_types','減少値が多いほど効果UP':'mental_spent',
 '経過ターンが短いほど効果UP':'turns_descending','経過ターンが長いほど効果UP':'turns_ascending',
}
ACTIVITIES={'ボーカルレッスン':'vocal_lesson','ダンスレッスン':'dance_lesson','ビジュアルレッスン':'visual_lesson','ラジオ':'radio','トークショー':'talk','雑誌の撮影':'magazine','トークイベント':'talk_event'}
def normalized(value):
 return re.sub(r'\s+','',unicodedata.normalize('NFKC',value or ''))
def amount(text):
 m=re.fullmatch(r'<Lv\*(\d+(?:\.\d+)?)>',text)
 if m:return {'formula':{'variable':'skill_level','coefficient':float(m[1]),'offset':0}}
 if re.fullmatch(r'\d+(?:\.\d+)?',text):return {'value':float(text)}
 return None
def effect(metric,targets,unit,scope='base',**values):
 return {'metric':metric,'targets':targets,'unit':unit,'scope':scope,**values}
def support(text,name=""):
 n=normalized(text)
 m=re.fullmatch(r'(ボーカル|ダンス|ビジュアル)レッスン滞在率がUP',n)
 if m:return [effect('support_presence_up',[{'ボーカル':'Vocal','ダンス':'Dance','ビジュアル':'Visual'}[m[1]]],'percent',trigger='always',amount_unknown=True)]
 if n=='ノウハウブック獲得時、ノウハウ発現確率がUP':return [effect('support_knowhow_rate',['ノウハウ発現率'],'percent',trigger='knowhow_acquired',amount_unknown=True)]
 if n in {'スキル発動時に一緒に行動してトラブルが起きなかった場合、行動した場所がレベルアップ','スキル発動時に一緒に行動してトラブルが起きなかった場合パーフェクトが発生'}:
  level='レベルアップ' in n
  return [effect('support_location_level' if level else 'support_perfect',['施設Lv' if level else 'パーフェクト'],'boolean',value=1,trigger='no_trouble')]
 m=re.fullmatch(r'一緒に行動してエクセレントが発生するとエクセレント効果\+(<Lv\*[\d.]+>)%',n)
 if m:return [effect('support_excellent',['エクセレント'],'percent',trigger='excellent',**amount(m[1]))]
 m=re.fullmatch(r'アイドルイベントとサポートイベントの発生率1\+<Lv\*([\d.]+)>倍',n)
 if m:return [effect('support_event_rate',['イベント発生率'],'multiplier',trigger='always',formula={'variable':'skill_level','coefficient':float(m[1]),'offset':1})]
 m=re.fullmatch(r'『say"Halo"』編での(ベスト|メンタル|ビジュアル|お仕事|ダンス|限界突破|ひらめき)アドバイスの抽選確率がスキルLv\.に応じて(大きく|少し)増加',n)
 if m:return [effect('support_advice_rate',['アドバイス抽選率'],'percent',trigger='say_halo',amount_unknown=True,advice=m[1],degree='large' if m[2]=='大きく' else 'small')]
 m=re.fullmatch(r'プロデュース開始時に絆\+(<Lv\*[\d.]+>)',n)
 if m:return [effect('support_bond',['絆'],'points',trigger='produce_start',**amount(m[1]))]
 m=re.fullmatch(r'「約束」を守れなかった場合に(<Lv\*[\d.]+>)%の確率でテンションが下がらない',n)
 if m:return [effect('support_tension_protection',['テンション'],'boolean',value=1,trigger='missed_promise',probability=amount(m[1]))]
 m=re.fullmatch(r'「休む」を選択時に(<Lv\*[\d.]+>)%の確率で体力回復量\+(\d+)',n)
 if m:return [effect('support_rest_gain',['体力'],'points',trigger='rest',probability=amount(m[1]),value=int(m[2]))]
 m=re.fullmatch(r'レッスンかお仕事を選択する時に(<Lv\*[\d.]+>)%の確率で(体力消費量|トラブル率)-(\d+)(%)?',n)
 if m and ((m[2]=='体力消費量' and m[4]) or (m[2]=='トラブル率' and not m[4])):
  return [effect('support_cost_down' if m[2]=='体力消費量' else 'support_trouble_down',['体力' if m[2]=='体力消費量' else 'トラブル率'],'percent' if m[4] else 'points',value=int(m[3]),probability=amount(m[1]),trigger='lesson_or_work')]
 trigger=None;per_member=False;probability=None
 prefix='行動した場所に自分以外のユニットメンバーがいると1人につき'
 if n.startswith(prefix):trigger='unit_member_present';per_member=True;tail=n[len(prefix):]
 elif n.startswith('テンション最高時に一緒に行動すると'):
  trigger='tension_max';tail=n[len('テンション最高時に一緒に行動すると'):]
  # Five saved cells have an extra particle. Accept only the exact known skill/
  # effect pair, retain source bytes and flag this notation in the typed result.
  notation=None
  if (name,tail) in {('テンションマスタリーVo上限＋','でVocal上限+<Lv*1>'),('テンションマスタリーDa上限＋','でDance上限+<Lv*1>')}:
   tail=tail[1:];notation='extra_particle_de' 
  if tail.startswith('確率で'):probability={'unknown':True};tail=tail[len('確率で'):]
 elif n.startswith('オーディションで1位を取ると'):trigger='audition_first';tail=n[len('オーディションで1位を取ると'):]
 else:
  m=re.fullmatch(r'(一緒に)?(ボーカルレッスン|ダンスレッスン|ビジュアルレッスン|ラジオ|トークショー|雑誌の撮影|トークイベント)(?:をすると|すると|へ出演すると|に出演すると)(.+)',n)
  if m:
   trigger=ACTIVITIES[m[2]]
   if not m[1]:
    trigger='solo_'+trigger
    if trigger not in TRIGGERS:return []
   tail=m[3]
 if not trigger:return []
 extra={'trigger':trigger}
 if trigger=='tension_max' and notation:extra['source_notation']=notation
 if per_member:extra['per_member']=True
 if probability:extra['probability']=probability
 m=re.fullmatch(r'(Vocal|Dance|Visual|ボーカル|ダンス|ビジュアル|メンタル|SP)(上限)?\+(<Lv\*[\d.]+>|\d+)',tail)
 if m:
  target={'ボーカル':'Vocal','ダンス':'Dance','ビジュアル':'Visual'}.get(m[1],m[1])
  return [effect('support_gain',[target],'points',cap=bool(m[2]),**amount(m[3]),**extra)]
 m=re.fullmatch(r'体力(<Lv\*[\d.]+>|\d+)回復',tail)
 if m:return [effect('support_recovery',['体力'],'points',**amount(m[1]),**extra)]
 return []
def ability(text,known_idols):
 n=normalized(text).removeprefix('(アビリティ)');restrictions={};partial=False
 brackets=re.findall(r'\[([^\]]*)\]',unicodedata.normalize('NFKC',text))
 for raw_b in brackets:
  b=normalized(raw_b)
  if b.startswith('グループ:') and 0<len(b[5:])<=200:restrictions['group']=raw_b.split(':',1)[1].strip()
  elif re.fullmatch(r'条件:編成アイドルの所属ユニットが\d+種類(?:以上|以下)の場合',b):
   m=re.search(r'(\d+)種類(以上|以下)',b);restrictions['unit_types_min' if m[2]=='以上' else 'unit_types_max']=int(m[1])
  elif b in {'経過ターンが短いほど効果UP','経過ターンが長いほど効果UP','思い出ゲージが多いほど効果UP','履歴が多いほど効果UP','メンタルが多いほど効果UP'}:
   restrictions['scaling']={'経過ターンが短いほど効果UP':'turns_descending','経過ターンが長いほど効果UP':'turns_ascending','思い出ゲージが多いほど効果UP':'memory','履歴が多いほど効果UP':'history','メンタルが多いほど効果UP':'mental'}[b]
  elif b=='条件:履歴に1ジャンルのみ':restrictions['history_genres']=1
  elif b=='ダメージを受けるまで':restrictions['until_damage']=True
  else:partial=True
 m=re.fullmatch(r'アピールフェイ[ズス]開始(?:毎|ごと)に(\d+)%の確率で(.+)付与',n)
 if m:
  found=live(m[2])
  if len(found)==1:
   found[0].update(trigger='appeal_phase_start',probability={'value':int(m[1])},restriction_status='structured')
   return {'status':'structured','effects':found}
 if n=='2ターン目に交換数UP[1回]':return {'status':'structured','effects':[effect('exchange_count_up',['交換数'],'points',amount_unknown=True,trigger='turn_2',uses=1,restriction_status='structured')]}
 body=re.sub(r'\[[^\]]*\]','',n)
 out=[]
 for part in body.split('、'):
  m=re.fullmatch(r'(?:(.+?)の)?アピール値(?:を\+?|最大)?(\d+(?:\.\d+)?)%UP',part)
  if m:
   ids=[]
   if m[1] and m[1]!='すべて':
    for name in m[1].split('と'):
     matches=[idol for idol in known_idols if normalized(idol)==name]
     if len(matches)!=1:return {'status':'unsupported','effects':[]}
     ids+=matches
   r=dict(restrictions)
   if ids:r['idols']=ids
   e=effect('appeal_boost',['アピール値'],'percent',value=float(m[2]),maximum='最大' in part,restrictions=r,restriction_status='partial' if partial else 'structured')
   out.append(e);continue
  m=re.fullmatch(r'思い出ゲージの増加量を(\d+)%UP',part)
  if m:out.append(effect('memory_gain_boost',['思い出ゲージ'],'percent',value=int(m[1]),restrictions=dict(restrictions),restriction_status='partial' if partial else 'structured'));continue
  m=re.fullmatch(r'フェスユニット編成時にすべての基礎能力値\+(\d+)%',part)
  if m:out.append(effect('base_stat_boost',['基礎能力値'],'percent',value=int(m[1]),restrictions=dict(restrictions),restriction_status='partial' if partial else 'structured'));continue
  partial=True
 if partial:
  for e in out:e['restriction_status']='partial'
 return {'status':'partial' if partial and out else 'structured' if out else 'unsupported','effects':out}
# A match includes its own adjacent duration; target aliases are normalized facts.
ATTR=r'(?:Vocal|Dance|Visual|Vo|Da|Vi|ボーカル|ダンス|ビジュアル)'
RATE=re.compile(r'(?P<targets>'+ATTR+r'(?:&'+ATTR+r')*|注目度|思い出ゲージ|リアクション回避率|回避率|メンタルダメージ|メンタル|影響力|パッシブスキル発動率)(?P<maximum>最大)?(?P<value>\d+(?:\.\d+)?)%(?P<direction>UP|DOWN|CUT)(?:\[(?P<turns>\d+)ターン\]|\[(?P<until_damage>ダメージを受けるまで)\])')
APPEAL=re.compile(r'(?P<order>必ず最初に|必ず最後に)?(?P<audience>全観客に)?(?P<targets>'+ATTR+r'(?:&'+ATTR+r')*|Excellent)(?P<maximum>最大)?(?:(?P<minimum>\d+(?:\.\d+)?)[～〜~])?(?P<value>\d+(?:\.\d+)?)倍アピール')
INTEREST=re.compile(r'(?P<audience>全観客に|全観客の)?興味(?P<maximum>最大)?(?P<value>\d+(?:\.\d+)?)倍\[(?P<turns>\d+)ターン\]')
LIVE_EXTRA=[
 (re.compile(r'メンタル(?P<value>\d+(?:\.\d+)?)%回復'),'mental_recovery','メンタル','percent'),
 (re.compile(r'自身のメンタルを(?P<value>\d+(?:\.\d+)?)%減ら(?:す|し)'),'mental_cost','メンタル','percent'),
 (re.compile(r'思い出ゲージ(?P<value>\d+(?:\.\d+)?)%UP(?!\[(?!コスト:\d+\])|\d)'),'memory_gauge_gain','思い出ゲージ','percent'),
 (re.compile(r'リラックス効果(?P<value>\d+(?:\.\d+)?)%付与\[(?P<turns>\d+)ターン\]'),'relax','リラックス','percent'),
 (re.compile(r'パッシブスキル(?P<maximum>最大)?(?P<value>\d+(?:\.\d+)?)%強化\[(?P<turns>\d+)ターン\]'),'passive_boost','パッシブスキル','percent'),
 (re.compile(r'交換数UP\[(?P<value>\d+)回\]'),'exchange_count_up','交換数','points'),
 (re.compile(r'リフレイン\[(?P<value>\d+)ターン前\]'),'refrain','過去のアピール','points'),
]

def effect_condition(part,ctx,scope=None):
 """Only leading mechanic brackets apply to the following mechanic block."""
 matches=re.match(r'((?:\[[^\[\]]*\])+)',part)
 if not matches:return None
 if ctx is None:return {'status':'unsupported'}
 terms=[]
 for bracket in re.findall(r'\[([^\[\]]*)\]',matches[1]):
  b=bracket.removeprefix('条件:')
  # Saved R01 Link section explicitly binds member abbreviations to appeal history.
  # Do not reinterpret explicit live-participation clauses or unknown names.
  names=[idol_name(n,ctx) for n in re.split(r'[・、]',b)] if scope in {'link','memory_link'} else []
  if names and all(names) and len(names)==len(set(names)):
   ps=[{'field':'history_participant','operator':'eq','value':name} for name in names]
   terms.append(ps[0] if len(ps)==1 else join('all',ps))
  else:terms.append(parse_condition(b,ctx))
 if not all(terms):return {'status':'unsupported'}
 result={'status':'structured','expression':terms[0] if len(terms)==1 else join('all',terms)}
 try:validate_extension(result,ctx)
 except ValueError:return {'status':'unsupported'}
 return result

def adjacent_restrictions(part,end):
 # Read consecutive brackets only; intervening text ends this effect's suffix.
 r={}
 while (m:=re.match(r'\[([^\[\]]*)\]',part[end:])):
  b=m[1]
  if b in SCALING:r['scaling']=SCALING[b]
  elif b=='興味無視':r['ignore_interest']=True
  elif b=='ダメージを受けるまで':r['until_damage']=True
  end+=m.end()
 return r

def live(text,scope='base',ctx=None,standalone=None,slot='effect'):
 n=normalized(text);out=[]
 # Only the known mechanic markers change scope. Raw conditions are not distributed.
 pieces=re.split(r'\((Link|Plus|Change|GrowUp|Grow|Refrain|Reflain)\)',n,flags=re.I)
 current=scope
 for idx,part in enumerate(pieces):
  if idx%2:
   current=scope if scope in {'memory_link','memory_charge'} else {'growup':'grow','reflain':'refrain'}.get(part.lower(),part.lower());continue
  in_piece=[];condition=effect_condition(part,ctx,current) if idx or current=='memory_link' else None
  rule=mechanic_rule(part,ctx,current) if condition=={'status':'unsupported'} else None
  for pattern,metric in [(RATE,None),(INTEREST,'interest'),(APPEAL,'appeal')]:
   for m in pattern.finditer(part):
    # Reject a suffix match inside a longer status or '最大' conditional number.
    if m.start() and re.match(r'[\w一-龯ぁ-んァ-ヶ]',part[m.start()-1]) and part[m.start()-1] not in ']':continue
    if part[:m.start()].count('[')!=part[:m.start()].count(']'):continue
    if metric!='appeal' and m.groupdict().get('maximum') and current!='grow':continue
    targets=['興味'] if metric=='interest' else [{'Vo':'Vocal','Da':'Dance','Vi':'Visual','ボーカル':'Vocal','ダンス':'Dance','ビジュアル':'Visual','回避率':'リアクション回避率'}.get(x,x) for x in m['targets'].split('&')]
    e=effect(metric or 'rate_'+m['direction'].lower(),targets,'multiplier' if metric else 'percent',scope=current,value=float(m['value']),restriction_status='partial')
    if metric=='appeal':
     if m['minimum'] is not None:e['minimum']=float(m['minimum'])
     if m['maximum']:e['maximum']=True
     if m['audience']:e['audience']='all'
     if m['order']:e['appeal_order']='first' if m['order']=='必ず最初に' else 'last'
    else:
     if m['turns']:e['turns']=int(m['turns'])
     if m.groupdict().get('maximum'):e['maximum']=True
    r=adjacent_restrictions(part,m.end())
    if m.groupdict().get('until_damage'):r['until_damage']=True
    if m.groupdict().get('audience'):e['audience']='all'
    if r:e['restrictions']=r
    if condition:e['activation_condition']=condition
    in_piece.append((m.start(),e))
  if current=='memory_link' and (m:=re.fullmatch(r'(注目度)(\d+(?:\.\d+)?)%(UP|DOWN)',part)):
   in_piece.append((0,effect('rate_'+m[3].lower(),[m[1]],'percent',scope=current,value=float(m[2]),restriction_status='partial')))
  for pattern,metric,target,unit in LIVE_EXTRA:
   for m in pattern.finditer(part):
    if part[:m.start()].count('[')!=part[:m.start()].count(']'):continue
    if m.start() and re.match(r'[\w一-龯ぁ-んァ-ヶ]',part[m.start()-1]):continue
    if m.groupdict().get('maximum') and current!='grow':continue
    e=effect(metric,[target],unit,scope=current,value=float(m['value']),restriction_status='partial')
    if m.groupdict().get('maximum'):e['maximum']=True
    if m.groupdict().get('turns'):e['turns']=int(m['turns'])
    r=adjacent_restrictions(part,m.end())
    if r:e['restrictions']=r
    if condition:e['activation_condition']=condition
    in_piece.append((m.start(),e))
  for pos,e in special_facts(part,current,ctx):
   if condition:e['activation_condition']=condition
   in_piece.append((pos,e))
  if rule:
   for _,e in in_piece:e['mechanic_condition']=rule
   if not in_piece and standalone is not None:standalone.append({'slot':slot,'segment':idx//2,'scope':current,'condition':rule})
  out.extend(e for _,e in sorted(in_piece,key=lambda pair:pair[0]))
 return out
def effect_details(item,known_idols=(),condition_context=None):
 kind=item['kind']
 if kind=='support_skill':
  effects=support(item.get('effect_private',''),item.get('name',''));return {'status':'structured' if effects else 'unsupported','effects':effects}
 if kind=='unique_ability':return ability(item.get('effect_private',''),known_idols)
 if kind in LIVE:
  standalone=[]
  text=item.get('effect_private','')
  # Candidate-table alternatives are separate. A source cell explicitly saying
  # random effects are granted can still contain independent deterministic effects.
  candidate_only=bool(item.get('random_effect_options')) and not re.search(r'ランダム効果\d+個付与',normalized(text))
  effects=[] if candidate_only else live(text,ctx=condition_context,standalone=standalone)
  if kind=='memory_appeal':
   for slot in ('link','charge'):effects+=live(item.get(slot+'_appeal_private',''),'memory_'+slot,condition_context,standalone,slot)
  return {'status':'partial' if effects or standalone else 'unsupported','effects':effects,**({'mechanic_conditions':standalone} if standalone else {})}
 return None

def validate_amount(v,probability=False):
 if v=={'amount_unknown':True} or (probability and v=={'unknown':True}):return
 if set(v)=={'value'}:
  if type(v['value']) not in (int,float) or not math.isfinite(v['value']) or v['value']<0:raise ValueError('Invalid effect value')
 elif set(v)=={'formula'}:
  f=v['formula']
  if set(f)!={'variable','coefficient','offset'} or f['variable']!='skill_level' or any(type(f[k]) not in (int,float) or not math.isfinite(f[k]) or f[k]<0 for k in ('coefficient','offset')):raise ValueError('Invalid effect formula')
 else:raise ValueError('Invalid effect amount')
def validate_effect_details(doc,known_idols,condition_context=None):
 if not isinstance(doc,dict) or not {'status','effects'}<=set(doc) or set(doc)-{'status','effects','mechanic_conditions'} or doc['status'] not in {'structured','partial','unsupported'} or not isinstance(doc['effects'],list) or bool(doc['effects'] or doc.get('mechanic_conditions'))!=(doc['status']!='unsupported'):raise ValueError('Invalid effect structure')
 if 'mechanic_conditions' in doc:
  rules=doc['mechanic_conditions']
  if not isinstance(rules,list) or not rules or condition_context is None:raise ValueError('Invalid standalone mechanic conditions')
  seen=set()
  for r in rules:
   if not isinstance(r,dict) or set(r)!={'slot','segment','scope','condition'} or r['slot'] not in {'effect','link','charge'} or type(r['segment']) is not int or not 1<=r['segment']<=100:raise ValueError('Invalid mechanic segment')
   key=(r['slot'],r['segment'])
   if key in seen:raise ValueError('Duplicate mechanic segment')
   seen.add(key);validate_rule(r['condition'],condition_context,r['scope'])
 for e in doc['effects']:
  if set(e)-{'metric','targets','unit','scope','value','formula','trigger','probability','per_member','cap','turns','restrictions','restriction_status','maximum','amount_unknown','advice','degree','uses','source_notation','minimum','audience','activation_condition','appeal_order','mechanic_condition','duet_target','timing','excludes','turn_range','turns_maximum','grant_count_maximum'}:raise ValueError('Non-public effect field')
  if e.get('metric') not in METRICS or not isinstance(e.get('targets'),list) or not e['targets'] or len(e['targets'])!=len(set(e['targets'])) or set(e['targets'])-TARGETS or e.get('unit') not in {'points','percent','multiplier','boolean'} or e.get('scope') not in SCOPES:raise ValueError('Invalid effect fact')
  validate_amount({k:e[k] for k in ('value','formula','amount_unknown') if k in e})
  if e['metric']=='refrain' and (e['unit']!='points' or type(e.get('value')) not in (int,float) or e['value']%1 or e['value']<1):raise ValueError('Invalid refrain distance')
  if 'appeal_order' in e and (e['metric']!='appeal' or e['appeal_order'] not in {'first','last'}):raise ValueError('Invalid appeal order')
  if 'activation_condition' in e and e['activation_condition']!={'status':'unsupported'}:
   if condition_context is None:raise ValueError('Missing effect condition context')
   validate_extension(e['activation_condition'],condition_context)
  if 'mechanic_condition' in e:
   if condition_context is None or e.get('activation_condition')!={'status':'unsupported'}:raise ValueError('Invalid mechanic condition fallback')
   validate_rule(e['mechanic_condition'],condition_context,e['scope'])
  if 'minimum' in e and (e['metric']!='appeal' or type(e['minimum']) not in (int,float) or not math.isfinite(e['minimum']) or not 0<=e['minimum']<=e['value']):raise ValueError('Invalid effect range')
  if 'audience' in e and (e['metric'] not in {'appeal','interest','interest_minimum','audience_status_clear','charm','enthusiasm'} or e['audience']!='all'):raise ValueError('Invalid appeal audience')
  if e['metric'] in SPECIAL_METRICS:
   metric=e['metric']
   expected={'resurrection':(['メンタル'],'percent'),'audience_status_clear':(['観客ステータス'],'boolean'),'duet':(['アピール履歴'],'boolean'),'duet_add':(['アピール履歴'],'boolean'),'interest_minimum':(['興味'],'multiplier'),'charm':(['魅了'],'boolean'),'enthusiasm':(['熱狂'],'boolean')}
   if (e['targets'],e['unit'])!=expected[metric] or 'value' not in e or ('boolean'==e['unit'] and e['value']!=1):raise ValueError('Invalid special effect')
   if metric=='resurrection' and (e.get('trigger')!='mental_zero' or 'turns' not in e or 'uses' not in e):raise ValueError('Invalid resurrection bounds')
   if metric=='interest_minimum' and (e['scope']!='grow' or 'turns' not in e):raise ValueError('Invalid minimum interest')
   if metric=='audience_status_clear' and (e.get('audience')!='all' or e.get('excludes')!=['興味変動無効']):raise ValueError('Invalid status exclusion')
   if metric in {'duet','duet_add'}:
    t=e.get('duet_target')
    if not isinstance(t,dict) or t.get('kind') not in {'formation','idol','unit'}:raise ValueError('Invalid duet target')
    if t['kind']=='formation':
     if set(t)!={'kind'}:raise ValueError('Invalid formation duet')
    else:
     names=known_idols if t['kind']=='idol' else (condition_context or {}).get('units',set())
     if set(t)!={'kind','name'} or t['name'] not in names:raise ValueError('Unknown duet target')
    if metric=='duet_add' and e.get('timing')!='current_turn':raise ValueError('Invalid duet addition timing')
   if metric in {'charm','enthusiasm'} and not any(k in e for k in ('turns','turn_range','turns_maximum')):raise ValueError('Missing status duration')
  if 'duet_target' in e and e['metric'] not in {'duet','duet_add'}:raise ValueError('Unexpected duet target')
  if 'timing' in e and (e['metric']!='duet_add' or e['timing']!='current_turn'):raise ValueError('Invalid special timing')
  if 'excludes' in e and (e['metric']!='audience_status_clear' or e['excludes']!=['興味変動無効']):raise ValueError('Invalid exclusion')
  if 'turn_range' in e:
   r=e['turn_range']
   if e['metric']!='enthusiasm' or not isinstance(r,dict) or set(r)!={'minimum','maximum'} or any(type(r[k]) is not int for k in r) or not 1<=r['minimum']<=r['maximum']<=100 or 'turns' in e or 'turns_maximum' in e:raise ValueError('Invalid variable duration')
  if 'turns_maximum' in e and (e['metric']!='enthusiasm' or type(e['turns_maximum']) is not int or not 1<=e['turns_maximum']<=100 or 'turns' in e):raise ValueError('Invalid maximum duration')
  if 'grant_count_maximum' in e and (e['metric']!='enthusiasm' or type(e['grant_count_maximum']) is not int or not 1<=e['grant_count_maximum']<=100):raise ValueError('Invalid maximum grant count')
  if 'probability' in e:validate_amount(e['probability'],True)
  if 'source_notation' in e and e['source_notation']!='extra_particle_de':raise ValueError('Invalid source notation')
  if 'advice' in e and e['advice'] not in {'ベスト','メンタル','ビジュアル','お仕事','ダンス','限界突破','ひらめき'}:raise ValueError('Invalid advice fact')
  if 'degree' in e and e['degree'] not in {'large','small'}:raise ValueError('Invalid qualitative effect')
  if 'uses' in e and (type(e['uses']) is not int or e['uses']<1):raise ValueError('Invalid effect uses')
  if 'trigger' in e and e['trigger'] not in TRIGGERS:raise ValueError('Invalid effect trigger')
  for k in ('per_member','cap','maximum'):
   if k in e and type(e[k]) is not bool:raise ValueError('Invalid effect flag')
  if 'turns' in e and (type(e['turns']) is not int or not 1<=e['turns']<=100):raise ValueError('Invalid effect duration')
  if 'restriction_status' in e and e['restriction_status'] not in {'structured','partial'}:raise ValueError('Invalid effect restriction')
  if 'restrictions' in e:
   r=e['restrictions']
   if not isinstance(r,dict) or set(r)-{'group','idols','unit_types_min','unit_types_max','history_genres','until_damage','scaling','ignore_interest'}:raise ValueError('Non-public effect restriction')
   if 'group' in r and (not isinstance(r['group'],str) or not 0<len(r['group'])<=200):raise ValueError('Invalid effect group')
   if 'idols' in r and (not isinstance(r['idols'],list) or not r['idols'] or any(x not in known_idols for x in r['idols'])):raise ValueError('Unknown effect idol')
   if 'scaling' in r and r['scaling'] not in set(SCALING.values()):raise ValueError('Invalid effect scaling')
   for k in ('unit_types_min','unit_types_max','history_genres'):
    if k in r and (type(r[k]) is not int or r[k]<1):raise ValueError('Invalid effect threshold')
   if 'until_damage' in r and r['until_damage'] is not True:raise ValueError('Invalid effect until')
   if 'ignore_interest' in r and r['ignore_interest'] is not True:raise ValueError('Invalid effect interest flag')
