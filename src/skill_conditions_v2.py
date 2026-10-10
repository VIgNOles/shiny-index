"""Typed extensions for passive conditions, keeping the v1 representation intact."""
import re
from unicodedata import normalize
from src.skill_conditions import compact, parse_text, predicate, validate_condition

UNIT_ALIASES = {
 'イルミネ':'イルミネーションスターズ','放クラ':'放課後クライマックスガールズ',
 'アルスト':'アルストロメリア','ストレイ':'ストレイライト',
 'アンティーカ':'アンティーカ','ノクチル':'ノクチル','シーズ':'シーズ','コメティック':'コメティック',
}
EXTRA_STATUSES = {'瞳の輝き','メランコリー','リザレクション効果'}
NUMERIC = {'history_genre_count','unit_participant_count','history_unit_count','history_participant_count'}
UNIT_FIELDS = {'unit_all_participants','unit_all_formation','history_unit_all','unit_appeal_boost_all'}
IDOL_FIELDS = {'idol_appeal_boost'}
BOOLEAN_FIELDS = {'history_memory_present'}

def context(base_cards):
 idols = {compact(c['idol_name']) for c in base_cards if c.get('idol_name')}
 units = {compact(c['unit_name']) for c in base_cards if c.get('unit_name')}
 members = {u:{compact(c['idol_name']) for c in base_cards if compact(c.get('unit_name') or '')==u} for u in units}
 return {'idols':idols,'units':units,'members':members}

def idol_name(value, ctx):
 value=compact(value)
 if value in ctx['idols']:return value
 matches=[n for n in ctx['idols'] if n.endswith(value)]
 return matches[0] if len(value)>=2 and len(matches)==1 else None

def unit_name(value, ctx):
 value=compact(value);name=UNIT_ALIASES.get(value,value)
 return name if name in ctx['units'] else None

def join(operator, terms):
 flattened=[]
 for p in terms:
  if p.get('operator')==operator and 'terms' in p:flattened.extend(p['terms'])
  else:flattened.append(p)
 return {'operator':operator,'terms':flattened}

def bounds(field,low,high,**extra):
 if not 0<=low<=high<=100000:return None
 return join('all',[predicate(field,'gte',low,**extra),predicate(field,'lte',high,**extra)])

def atom(value, ctx):
 old=parse_text(value,ctx['idols'])
 if old is not None:
  try:validate_condition({'status':'structured','expression':old},ctx['idols']);return old
  except ValueError:return None
 m=re.fullmatch(r'(メンタル|スター)(\d+)(%?以上)(\d+)(%?以下)',value)
 if m and ((m[1]=='メンタル' and m[3]=='%以上' and m[5]=='%以下') or (m[1]=='スター' and m[3]=='以上' and m[5]=='以下')):
  if m[1]=='メンタル' and int(m[4])>100:return None
  return bounds('mental_percent' if m[1]=='メンタル' else 'star_count',int(m[2]),int(m[4]))
 m=re.fullmatch(r'(?:編成アイドルの所属ユニットが|編成ユニットが)(\d+)種類(以上|以下)',value)
 if m:return predicate('unit_type_count','gte' if m[2]=='以上' else 'lte',int(m[1]))
 m=re.fullmatch(r'(.+?)全員が(ライブに参加(?:している場合)?|編成されている場合)',value)
 if m:
  unit=unit_name(m[1],ctx)
  if unit:return predicate('unit_all_formation' if m[2]=='編成されている場合' else 'unit_all_participants','eq',unit)
 m=re.fullmatch(r'(.+?)(\d+)(?:[~～〜](\d+)人|人(以上|以下))がライブに参加(?:している場合)?',value)
 if m:
  unit=unit_name(m[1],ctx)
  if unit:
   return bounds('unit_participant_count',int(m[2]),int(m[3]),unit=unit) if m[3] else predicate('unit_participant_count','gte' if m[4]=='以上' else 'lte',int(m[2]),unit=unit)
 m=re.fullmatch(r'(.+?)から(.+?)のみがライブに参加(?:している場合)?',value)
 if m:
  unit=unit_name(m[1],ctx);name=idol_name(m[2],ctx)
  if unit and name in ctx['members'][unit]:return predicate('unit_only_participant','eq',name,unit=unit)
 m=re.fullmatch(r'履歴に(.+?)のアイドルが(\d+)人(以上|以下)ある場合',value)
 if m:
  unit=unit_name(m[1],ctx)
  if unit:return predicate('history_unit_count','gte' if m[3]=='以上' else 'lte',int(m[2]),unit=unit)
 m=re.fullmatch(r'履歴に(.+?)全員がある場合',value)
 if m:
  unit=unit_name(m[1],ctx)
  if unit:return predicate('history_unit_all','eq',unit)
 m=re.fullmatch(r'履歴に(.+?)が(\d+)個以上ある場合',value)
 if m:
  name=idol_name(m[1],ctx)
  if name:return predicate('history_participant_count','gte',int(m[2]),idol=name)
 m=re.fullmatch(r'履歴に(\d+)ジャンル(以上|以下)',value)
 if m:return predicate('history_genre_count','gte' if m[2]=='以上' else 'lte',int(m[1]))
 if value=='履歴に思い出アピールがある場合':return predicate('history_memory_present','eq',True)
 m=re.fullmatch(r'VoDaViUP全てが(?:(\d+)個以上)?付与されている場合',value)
 if m:return join('all',[predicate('status_count','gte',int(m[1] or 1),status=n) for n in ('VocalUP','DanceUP','VisualUP')])
 m=re.fullmatch(r'(.+?)が(?:(\d+)(?:個|つ)以上)?付与されて(?:いる|る)場合',value)
 if m and m[1] in EXTRA_STATUSES | {'VocalUP','DanceUP','VisualUP','リアクション回避率UP'}:
  return predicate('status_count','gte',int(m[2] or 1),status=m[1])
 if value=='魅了を観客に付与している場合':return predicate('audience_status','eq','魅了')
 m=re.fullmatch(r'(.+?)(全員)?のアピール倍率UPが付与されている場合',value)
 if m:
  name=unit_name(m[1],ctx) if m[2] else idol_name(m[1],ctx)
  if name:return predicate('unit_appeal_boost_all' if m[2] else 'idol_appeal_boost','eq',name)
 for pattern,field in [(r'(.+?)(いずれか)?がライブに参加(?:している場合)?','participant'),
                       (r'履歴に(.+?)(いずれか)?がある場合','history_participant')]:
  m=re.fullmatch(pattern,value)
  if m:
   parts=m[1].split('、');names=[idol_name(n,ctx) for n in parts]
   if names and all(names) and len(names)==len(set(names)):
    terms=[predicate(field,'eq',n) for n in names]
    return terms[0] if len(terms)==1 else join('any' if m[2] else 'all',terms)
 return None

def parse(value, ctx, depth=0):
 if depth>4 or not value or len(value)>400:return None
 if re.search(r'又は|または',value) and re.search(r'かつ|且つ',value):return None
 p=atom(value,ctx)
 if p is not None:return p
 # Fully specified OR clauses, or an explicitly shared suffix.
 m=re.fullmatch(r'(Vocal|Dance|Visual|Center|Leader)(?:又は|または)(Vocal|Dance|Visual|Center|Leader)ポジション担当に編成している場合',value)
 if m:return join('any',[predicate('position','eq',n.lower()) for n in m.groups()])
 m=re.fullmatch(r'履歴に(\d+)ジャンル(以上|以下)(?:又は|または)(\d+)ジャンル(以上|以下)',value)
 if m:return join('any',[predicate('history_genre_count','gte' if m[2]=='以上' else 'lte',int(m[1])),predicate('history_genre_count','gte' if m[4]=='以上' else 'lte',int(m[3]))])
 m=re.fullmatch(r'編成アイドルの所属ユニットが(\d+)種類以上(?:又は|または)(\d+)種類',value)
 if m:return join('any',[predicate('unit_type_count','gte',int(m[1])),predicate('unit_type_count','eq',int(m[2]))])
 m=re.fullmatch(r'(.+?)(?:又は|または)(.+?)が付与されている場合',value)
 if m:
  a,b=m.groups()
  if a=='パッシブスキル発動率UP' and b=='強化':b='パッシブスキル強化'
  from src.skill_conditions import STATUS_NAMES
  if a in STATUS_NAMES and b in STATUS_NAMES:return join('any',[predicate('status_count','gte',1,status=n) for n in (a,b)])
 for separator,operator in [('又は','any'),('または','any'),('かつ','all'),('且つ','all')]:
  if separator in value:
   parts=value.split(separator)
   if len(parts)!=2:return None
   terms=[parse(v,ctx,depth+1) for v in parts]
   return join(operator,terms) if all(terms) else None
 # Adjacent complete clauses in one condition bracket are conjunctive.
 # Every character must belong to a supported clause; unknown tails reject all.
 for index in range(1,len(value)):
  first=atom(value[:index],ctx)
  if first is None:continue
  rest=parse(value[index:],ctx,depth+1)
  if rest is not None:return join('all',[first,rest])
 return None

def validate_expression(p, ctx, depth=0, budget=None):
 if budget is None:budget=[64]
 budget[0]-=1
 if depth>4 or budget[0]<0 or not isinstance(p,dict):raise ValueError('Invalid condition tree size')
 if 'terms' in p:
  if set(p)!={'operator','terms'} or p['operator'] not in ('all','any') or not isinstance(p['terms'],list) or not 2<=len(p['terms'])<=16:raise ValueError('Invalid logical condition')
  for child in p['terms']:validate_expression(child,ctx,depth+1,budget)
  return
 field,op,value=p.get('field'),p.get('operator'),p.get('value')
 if type(field) is not str or type(op) is not str:raise ValueError('Invalid condition leaf')
 extras={'unit'} if field in {'unit_participant_count','history_unit_count','unit_only_participant'} else {'idol'} if field=='history_participant_count' else {'status'} if field=='status_count' else set()
 if set(p)!={'field','operator','value'}|extras:raise ValueError('Invalid condition leaf fields')
 if field in NUMERIC:
  valid=op in ('gte','lte','eq') and type(value) is int and 0<=value<=100000
  if 'unit' in extras:valid=valid and isinstance(p['unit'],str) and p['unit'] in ctx['units']
  if 'idol' in extras:valid=valid and isinstance(p['idol'],str) and p['idol'] in ctx['idols']
 elif field in UNIT_FIELDS:valid=op=='eq' and isinstance(value,str) and value in ctx['units']
 elif field in IDOL_FIELDS:valid=op=='eq' and isinstance(value,str) and value in ctx['idols']
 elif field in BOOLEAN_FIELDS:valid=op=='eq' and value is True
 elif field=='unit_only_participant':valid=op=='eq' and isinstance(p['unit'],str) and p['unit'] in ctx['units'] and isinstance(value,str) and value in ctx['members'][p['unit']]
 elif field=='audience_status':valid=op=='eq' and value=='魅了'
 elif field=='unit_type_count' and op=='eq':valid=type(value) is int and 1<=value<=100000
 elif field=='status_count' and isinstance(p['status'],str) and p['status'] in EXTRA_STATUSES:valid=op=='gte' and type(value) is int and 1<=value<=100000
 else:
  validate_condition({'status':'structured','expression':p},ctx['idols']);return
 if not valid:raise ValueError('Invalid extended condition predicate')

def validate_extension(condition,ctx):
 if not isinstance(condition,dict) or set(condition)!={'status','expression'} or condition['status']!='structured':raise ValueError('Invalid condition extension')
 validate_expression(condition['expression'],ctx)

def activation_extension(item,ctx):
 text=normalize('NFKC',item.get('effect_private',''))
 remainder=re.sub(r'\[[^\[\]]*\]','',text)
 matches=list(re.finditer(r'\[条件:([^\[\]]*)\]',text))
 if item['kind']!='panel_passive' or '[' in remainder or ']' in remainder or len(matches)!=1 or text.count('[条件:')!=1:return None
 p=parse(compact(matches[0][1]),ctx)
 if p is None:return None
 result={'status':'structured','expression':p}
 try:validate_extension(result,ctx)
 except ValueError:return None
 return result
