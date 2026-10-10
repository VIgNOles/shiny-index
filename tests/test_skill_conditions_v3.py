import copy,unittest
from src.skill_conditions_v3 import keyword_extension,validate_keyword_condition
class KeywordConditionTests(unittest.TestCase):
 def parse(self,value):
  return keyword_extension({'kind':'panel_passive','effect_private':'[条件:'+value+'] [確率:20%]'})
 def test_keyword_owner_and_conjunction_are_explicit(self):
  self.assertEqual(self.parse('キーワードアイドル')['expression'],{'field':'owner_keyword','operator':'eq','value':'アイドル'})
  p=self.parse('キーワードリーダーシップ、カリスマ')['expression']
  self.assertEqual(p['operator'],'all');self.assertEqual([t['value'] for t in p['terms']],['リーダーシップ','カリスマ'])
 def test_unknown_partial_duplicate_and_wrong_kind_are_rejected(self):
  for text in ['キーワード未知','キーワードアイドル、未知','キーワードアイドル、アイドル','キーワード','キーワードアイドル又はカリスマ','[条件:キーワードアイドル]','キーワードアイドル]']:
   self.assertIsNone(self.parse(text),text)
  self.assertIsNone(keyword_extension({'kind':'panel_live','effect_private':'[条件:キーワードアイドル]'}))
 def test_validator_rejects_prose_bad_types_and_or(self):
  good=self.parse('キーワードリーダーシップ、カリスマ')
  for expression in [None,[],{'field':'owner_keyword','operator':'eq','value':True},{'field':'owner_keyword','operator':'eq','value':'未知'},{'operator':'any','terms':good['expression']['terms']},{'operator':'all','terms':[]},{'operator':'all','terms':[good['expression']['terms'][0]]},{'field':'owner_keyword','operator':'eq','value':'アイドル','raw_private':'本文'}]:
   bad=copy.deepcopy(good);bad['expression']=expression
   with self.assertRaises(ValueError):validate_keyword_condition(bad)
if __name__=='__main__':unittest.main()
