"""Strict factual activation conditions from private passive-skill brackets."""
import re
from unicodedata import normalize

STATUS_NAMES={
 'VocalUP','DanceUP','VisualUP','注目度UP','注目度DOWN',
 'リアクション回避率UP','メンタルダメージCUT','リラックス',
 'パッシブスキル発動率UP','パッシブスキル強化',
}
NUMERIC_FIELDS={'mental_percent':(0,100),'turn':(1,100000),'star_count':(0,100000),
 'audience_count':(0,100000),'maximum_mental':(0,100000),'heal_count':(0,100000),
 'unit_type_count':(1,100000)}
def compact(value):
 return re.sub(r'\s+','',normalize('NFKC',value))
def predicate(field,operator,value,**extra):
 return {'field':field,'operator':operator,'value':value,**extra}
def parse_text(value,known_idols=()):
 value=compact(value)
 for pattern,field in [
  (r'メンタル(\d+)%(以上|以下)','mental_percent'),
  (r'スター(\d+)(以上|以下)','star_count'),
  (r'観客(\d+)(以上|以下)','audience_count'),
  (r'最大メンタル(\d+)(以上|以下)','maximum_mental'),
  (r'回復回数(\d+)回(以上|以下)','heal_count'),
  (r'編成アイドルの所属ユニットが(\d+)種類(以上|以下)の場合','unit_type_count')]:
  match=re.fullmatch(pattern,value)
  if match:
   return predicate(field,'gte' if match[2]=='以上' else 'lte',int(match[1]))
 match=re.fullmatch(r'(\d+)ターン(以前|以降)',value)
 if match:return predicate('turn','lte' if match[2]=='以前' else 'gte',int(match[1]))
 match=re.fullmatch(r'(\d+)位',value)
 if match:return predicate('rank','eq',int(match[1]))
 match=re.fullmatch(r'(Vocal|Dance|Visual|Center|Leader)(?:担当|ポジション担当に編成している場合)',value,re.I)
 if match:return predicate('position','eq',match[1].lower())
 match=re.fullmatch(r'(.+)が(?:(\d+)個以上)?付与されている場合',value)
 if match and match[1] in STATUS_NAMES:
  return predicate('status_count','gte',int(match[2] or 1),status=match[1])
 names={compact(name) for name in known_idols}
 for pattern,field in [(r'(.+)がライブに参加している場合','participant'),
                       (r'履歴に(.+)がある場合','history_participant')]:
  match=re.fullmatch(pattern,value)
  if match and match[1] in names:return predicate(field,'eq',match[1])
 if value=='ライブスキルが生成されている場合':
  return predicate('generated_live_present','eq',True)
 return None

def validate_condition(condition,known_idols=()):
 if not isinstance(condition,dict):raise ValueError('Invalid activation condition')
 if condition=={'status':'unsupported'}:return
 if set(condition)!={'status','expression'} or condition['status']!='structured':
  raise ValueError('Invalid activation condition status')
 p=condition['expression']
 if not isinstance(p,dict) or set(p)!=({'field','operator','value','status'} if p.get('field')=='status_count' else {'field','operator','value'}):
  raise ValueError('Invalid activation condition fields')
 field,op,value=p['field'],p['operator'],p['value']
 if type(field) is not str or type(op) is not str:raise ValueError('Invalid activation condition types')
 if field in NUMERIC_FIELDS:
  low,high=NUMERIC_FIELDS[field]
  valid=op in {'gte','lte'} and type(value) is int and low<=value<=high
 elif field=='rank':valid=op=='eq' and type(value) is int and 1<=value<=100000
 elif field=='position':valid=op=='eq' and isinstance(value,str) and value in {'vocal','dance','visual','center','leader'}
 elif field=='status_count':valid=op=='gte' and type(value) is int and 1<=value<=100000 and isinstance(p['status'],str) and p['status'] in STATUS_NAMES
 elif field in {'participant','history_participant'}:valid=op=='eq' and isinstance(value,str) and value in {compact(n) for n in known_idols}
 elif field=='generated_live_present':valid=op=='eq' and value is True
 else:valid=False
 if not valid:raise ValueError('Invalid activation condition predicate')

def activation_condition(item,known_idols=()):
 if item['kind']!='panel_passive':return None
 text=normalize('NFKC',item.get('effect_private',''))
 remainder=re.sub(r'\[[^\[\]]*\]','',text)
 if '[' in remainder or ']' in remainder:return {'status':'unsupported'}
 matches=list(re.finditer(r'\[条件:([^\[\]]*)\]',text))
 if len(matches)!=1 or text.count('[条件:')!=1:return {'status':'unsupported'}
 parsed=parse_text(matches[0][1],known_idols)
 if parsed is None:return {'status':'unsupported'}
 result={'status':'structured','expression':parsed}
 try:validate_condition(result,known_idols)
 except ValueError:return {'status':'unsupported'}
 return result
