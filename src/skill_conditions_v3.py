"""Keyword ownership conditions (R01), optional to preserve older UI semantics."""
import re
from unicodedata import normalize
from src.skill_conditions import compact,predicate
KEYWORDS={'歌姫','プロダンサー','トップモデル','リーダーシップ','カリスマ','アイドル'}

def validate_keyword_condition(condition):
 if not isinstance(condition,dict) or set(condition)!={'status','expression'} or condition['status']!='structured':raise ValueError('Invalid keyword condition')
 p=condition['expression']
 if not isinstance(p,dict):raise ValueError('Invalid keyword expression')
 terms=p.get('terms') if isinstance(p,dict) and p.get('operator')=='all' else [p]
 if not isinstance(terms,list) or not 1<=len(terms)<=6:raise ValueError('Invalid keyword terms')
 if 'terms' in p and (set(p)!={'operator','terms'} or len(terms)<2):raise ValueError('Invalid keyword conjunction')
 seen=set()
 for t in terms:
  if not isinstance(t,dict) or set(t)!={'field','operator','value'} or t['field']!='owner_keyword' or t['operator']!='eq' or not isinstance(t['value'],str) or t['value'] not in KEYWORDS or t['value'] in seen:raise ValueError('Invalid keyword predicate')
  seen.add(t['value'])

def keyword_extension(item):
 text=normalize('NFKC',item.get('effect_private',''))
 remainder=re.sub(r'\[[^\[\]]*\]','',text)
 matches=list(re.finditer(r'\[条件:([^\[\]]*)\]',text))
 if item['kind']!='panel_passive' or '[' in remainder or ']' in remainder or len(matches)!=1 or text.count('[条件:')!=1:return None
 value=compact(matches[0][1])
 if not value.startswith('キーワード'):return None
 names=value.removeprefix('キーワード').split('、')
 terms=[predicate('owner_keyword','eq',name) for name in names]
 result={'status':'structured','expression':terms[0] if len(terms)==1 else {'operator':'all','terms':terms}}
 try:validate_keyword_condition(result)
 except ValueError:return None
 return result
