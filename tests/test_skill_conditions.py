import copy,unittest
from src.skill_conditions import activation_condition,validate_condition
class SkillConditionTests(unittest.TestCase):
 def parse(self,value,**extra):
  return activation_condition({'kind':'panel_passive','effect_private':'[条件:'+value+'] [確率:20%] [最大:1回]',**extra},['櫻木真乃','黛冬優子'])
 def test_numeric_boundaries_and_units(self):
  for raw,field,op,value in [('メンタル75%以上','mental_percent','gte',75),('メンタル０％以下','mental_percent','lte',0),('3ターン以前','turn','lte',3),('1ターン以降','turn','gte',1),('スター0以上','star_count','gte',0),('観客3以上','audience_count','gte',3),('最大メンタル4500以上','maximum_mental','gte',4500),('回復回数5回以上','heal_count','gte',5),('編成アイドルの所属ユニットが3種類以上の場合','unit_type_count','gte',3),('2位','rank','eq',2)]:
   with self.subTest(raw=raw):self.assertEqual(self.parse(raw),{'status':'structured','expression':{'field':field,'operator':op,'value':value}})
 def test_position_and_named_participation(self):
  self.assertEqual(self.parse('Vocalポジション担当に編成している場合')['expression']['value'],'vocal')
  self.assertEqual(self.parse('Centerポジション担当に編成している場合')['expression']['value'],'center')
  self.assertEqual(self.parse('黛 冬優子がライブに参加している場合')['expression']['value'],'黛冬優子')
  self.assertEqual(self.parse('履歴に櫻木 真乃がある場合')['expression']['field'],'history_participant')
 def test_status_presence_and_count_are_distinct(self):
  for raw,count in [('VocalUPが 付与されている場合',1),('注目度UPが2個以上付与されている場合',2)]:
   self.assertEqual(self.parse(raw)['expression'],{'field':'status_count','operator':'gte','value':count,'status':'VocalUP' if count==1 else '注目度UP'})
 def test_unknown_or_compound_conditions_never_get_partial_predicates(self):
  for raw in ['摩美々','未知名がライブに参加している場合','VoDaViUP全てが付与されている場合','3ターン以降 履歴に1ジャンル以下','最大メンタル4500以上メンタル74%以下','メンタル75%以上または3ターン以前','メンタル75%以上かつ未対応','メンタル75%以上の時以外','スター10回以上','0ターン以前','メンタル101%以上','メンタル-1%以下','注目度UPが0個以上付与されている場合','']:
   with self.subTest(raw=raw):self.assertEqual(self.parse(raw),{'status':'unsupported'})
 def test_missing_duplicate_and_nested_brackets_are_unsupported(self):
  for text in ['', '[条件:メンタル75%以上] [条件:3ターン以前]','[条件:[条件:メンタル75%以上]]','[別枠[条件:メンタル75%以上]]']:
   self.assertEqual(activation_condition({'kind':'panel_passive','effect_private':text}),{'status':'unsupported'})
 def test_only_passives_get_activation_conditions(self):
  self.assertIsNone(self.parse('メンタル75%以上',kind='panel_live'))
 def test_allowlist_rejects_prose_bad_types_and_forged_names(self):
  good=self.parse('メンタル75%以上')
  for change in [{'value':True},{'value':75.0},{'value':float('nan')},{'operator':'or'},{'field':'secret'},{'raw_private':'全文'},{'field':[]},{'operator':{}},{'field':'position','operator':'eq','value':[]}]:
   bad=copy.deepcopy(good);bad['expression'].update(change)
   with self.subTest(change=change),self.assertRaises(ValueError):validate_condition(bad)
  with self.assertRaises(ValueError):validate_condition({'status':'unsupported','raw_private':'非公開'})
  with self.assertRaises(ValueError):validate_condition({'status':'structured','expression':{'field':'participant','operator':'eq','value':'非公開文章'}})
 def test_generated_presence_is_a_boolean(self):
  self.assertEqual(self.parse('ライブスキルが生成されている場合')['expression']['value'],True)
if __name__=='__main__':unittest.main()
