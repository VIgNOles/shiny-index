import copy,unittest
from src.skill_conditions_v2 import context,activation_extension,validate_extension
from src.skill_conditions import activation_condition
BASE=[
 {'idol_name':'櫻木真乃','unit_name':'イルミネーションスターズ'},
 {'idol_name':'風野灯織','unit_name':'イルミネーションスターズ'},
 {'idol_name':'八宮めぐる','unit_name':'イルミネーションスターズ'},
 {'idol_name':'白瀬咲耶','unit_name':'アンティーカ'},
 {'idol_name':'幽谷霧子','unit_name':'アンティーカ'},
 {'idol_name':'黛冬優子','unit_name':'ストレイライト'},
 {'idol_name':'大崎甘奈','unit_name':'アルストロメリア'},
 {'idol_name':'大崎甜花','unit_name':'アルストロメリア'},
 {'idol_name':'斑鳩ルカ','unit_name':'コメティック'},
 {'idol_name':'浅倉透','unit_name':'ノクチル'},
 {'idol_name':'緋田美琴','unit_name':'シーズ'},
 {'idol_name':'小宮果穂','unit_name':'放課後クライマックスガールズ'},
]
class ConditionExtensionTests(unittest.TestCase):
 def setUp(self):self.ctx=context(BASE)
 def parse(self,text):
  return activation_extension({'kind':'panel_passive','effect_private':'[条件:'+text+'] [確率:20%] [最大:2回]'},self.ctx)
 def expression(self,text):
  result=self.parse(text);self.assertIsNotNone(result,text);return result['expression']
 def test_unit_all_and_only_are_different_quantifiers(self):
  all_=self.expression('コメティック全員がライブに参加している場合')
  only=self.expression('コメティックからルカのみがライブに参加')
  self.assertEqual(all_,{'field':'unit_all_participants','operator':'eq','value':'コメティック'})
  self.assertEqual(only,{'field':'unit_only_participant','operator':'eq','value':'斑鳩ルカ','unit':'コメティック'})
  self.assertIsNone(self.parse('コメティックから真乃のみがライブに参加'))
 def test_formation_is_not_live_participation(self):
  self.assertEqual(self.expression('アルスト全員が編成されている場合')['field'],'unit_all_formation')
  self.assertEqual(self.expression('アルスト全員がライブに参加')['field'],'unit_all_participants')
 def test_ranges_preserve_both_bounds(self):
  for raw,field,lo,hi in [('メンタル35%以上64%以下','mental_percent',35,64),('スター2以上8以下','star_count',2,8),('イルミネ1～2人がライブに参加している場合','unit_participant_count',1,2)]:
   p=self.expression(raw);self.assertEqual(p['operator'],'all');self.assertEqual([(x['field'],x['operator'],x['value']) for x in p['terms']],[(field,'gte',lo),(field,'lte',hi)])
  self.assertIsNone(self.parse('メンタル75%以上64%以下'));self.assertIsNone(self.parse('メンタル35%以上101%以下'))
 def test_adjacent_complete_clauses_require_all(self):
  p=self.expression('最大メンタル4500以上メンタル74%以下')
  self.assertEqual(p['operator'],'all');self.assertEqual([x['field'] for x in p['terms']],['maximum_mental','mental_percent'])
  p=self.expression('3ターン以降アンティーカ全員がライブに参加している場合')
  self.assertEqual([x['field'] for x in p['terms']],['turn','unit_all_participants'])
  self.assertIsNone(self.parse('最大メンタル4500以上メンタル74%以下未知条件'))
 def test_explicit_or_keeps_both_branches(self):
  p=self.expression('履歴に幽谷霧子がある場合又は5ターン以降')
  self.assertEqual(p['operator'],'any');self.assertEqual([x['field'] for x in p['terms']],['history_participant','turn'])
  p=self.expression('Vocal又はDanceポジション担当に編成している場合');self.assertEqual([x['value'] for x in p['terms']],['vocal','dance'])
  p=self.expression('パッシブスキル発動率UP又は強化が付与されている場合');self.assertEqual(p['operator'],'any')
  self.assertIsNone(self.parse('メンタル75%以上又は未知条件'))
  self.assertIsNone(self.parse('メンタル75%以上かつ3ターン以前又は5ターン以降'))
 def test_all_three_statuses_preserve_count_for_each(self):
  p=self.expression('VoDaViUP全てが2個以上付与されている場合')
  self.assertEqual(p['operator'],'all');self.assertEqual([(x['status'],x['value']) for x in p['terms']],[('VocalUP',2),('DanceUP',2),('VisualUP',2)])
  self.assertIsNone(self.parse('VoDaViUP全てが0個以上付与されている場合'))
 def test_named_lists_preserve_all_or_any(self):
  for raw,operator in [('真乃、灯織がライブに参加している場合','all'),('真乃、灯織いずれかがライブに参加している場合','any'),('履歴に真乃、灯織いずれかがある場合','any')]:
   p=self.expression(raw);self.assertEqual(p['operator'],operator);self.assertEqual([x['value'] for x in p['terms']],['櫻木真乃','風野灯織'])
  self.assertIsNone(self.parse('真乃、未知名いずれかがライブに参加している場合'))
 def test_documented_old_short_names_are_participation_conditions(self):
  self.assertEqual(self.expression('真乃'),{'field':'participant','operator':'eq','value':'櫻木真乃'})
  self.assertEqual(self.expression('透')['value'],'浅倉透')
  self.assertIsNone(self.parse('未知'))
  self.assertIsNone(self.parse('智世子'))
  self.assertIsNone(self.parse('乃'))
  self.assertEqual(self.expression('真乃がライブに参加している場合')['value'],'櫻木真乃')
  ambiguous=context(BASE+[{'idol_name':'別人真乃','unit_name':'アンティーカ'}])
  self.assertIsNone(activation_extension({'kind':'panel_passive','effect_private':'[条件:真乃がライブに参加している場合]'},ambiguous))
 def test_history_counts_and_unit_all_are_distinct(self):
  self.assertEqual(self.expression('履歴にコメティックのアイドルが4人以上ある場合'),{'field':'history_unit_count','operator':'gte','value':4,'unit':'コメティック'})
  self.assertEqual(self.expression('履歴にシーズ全員がある場合')['field'],'history_unit_all')
  self.assertEqual(self.expression('履歴に櫻木真乃が2個以上ある場合')['idol'],'櫻木真乃')
  self.assertEqual(self.expression('履歴に1ジャンル以下又は3ジャンル以上')['operator'],'any')
  p=self.expression('履歴に真乃1ジャンル以下')
  self.assertEqual(p,{'operator':'all','terms':[{'field':'history_participant','operator':'eq','value':'櫻木真乃'},{'field':'history_genre_count','operator':'lte','value':1}]})
  self.assertIsNone(self.parse('履歴に未知1ジャンル以下'))
 def test_special_states_keep_their_target(self):
  self.assertEqual(self.expression('魅了を観客に付与している場合')['field'],'audience_status')
  self.assertEqual(self.expression('緋田美琴のアピール倍率UPが付与されている場合')['value'],'緋田美琴')
  self.assertEqual(self.expression('瞳の輝きが2個以上付与されている場合')['status'],'瞳の輝き')
  self.assertEqual(self.expression('放クラ全員のアピール倍率UPが付与されている場合')['field'],'unit_appeal_boost_all')
 def test_shared_unit_or_preserves_all_in_both_branches(self):
  p=self.expression('イルミネ又はアルスト全員がライブに参加')
  self.assertEqual(p,{'operator':'any','terms':[{'field':'unit_all_participants','operator':'eq','value':'イルミネーションスターズ'},{'field':'unit_all_participants','operator':'eq','value':'アルストロメリア'}]})
  self.assertIsNone(self.parse('イルミネ又は未知全員がライブに参加'))
  self.assertIsNone(self.parse('真乃又は甘奈全員がライブに参加'))
 def test_exact_audience_count_keeps_both_inclusive_bounds(self):
  self.assertEqual(self.expression('観客1'),{'operator':'all','terms':[{'field':'audience_count','operator':'gte','value':1},{'field':'audience_count','operator':'lte','value':1}]})
  self.assertIsNone(self.parse('観客不明'))
 def test_observed_complete_clauses_and_named_list(self):
  self.assertEqual(self.expression('注目度UPリアクション回避率UPが付与されている場合')['operator'],'all')
  self.assertEqual(self.expression('咲耶、霧子、透いずれかがライブに参加している場合')['operator'],'any')
  self.assertEqual(self.expression('履歴に櫻木真乃が2個以上がある場合')['value'],2)
  self.assertIsNone(self.parse('パッシブスキル発動率UP強化が付与されている場合'))
  self.assertIsNone(self.parse('最大メンタル4500以上未知条件'))
 def test_unsupported_brackets_or_kind_never_get_an_extension(self):
  for raw in ['[条件:真乃がライブに参加している場合][条件:3ターン以前]','[条件:[条件:真乃がライブに参加している場合]]','[条件:観客1]]']:
   self.assertIsNone(activation_extension({'kind':'panel_passive','effect_private':raw},self.ctx))
  self.assertIsNone(activation_extension({'kind':'panel_live','effect_private':'[条件:3ターン以降アンティーカ全員がライブに参加]'},self.ctx))
 def test_strict_tree_validation_rejects_prose_bad_types_and_sizes(self):
  good=self.parse('3ターン以降アンティーカ全員がライブに参加')
  for mutate in [
   lambda d:d['expression'].update(raw_private='private text'),
   lambda d:d['expression'].update(operator='not'),
   lambda d:d['expression'].update(terms=[]),
   lambda d:d['expression']['terms'][0].update(value=True),
   lambda d:d['expression']['terms'][1].update(value='架空ユニット'),
   lambda d:d.update(status='unsupported'),
  ]:
   bad=copy.deepcopy(good);mutate(bad)
   with self.assertRaises(ValueError):validate_extension(bad,self.ctx)
  atom={'field':'turn','operator':'gte','value':3}
  for tree in [{'operator':'all','terms':[atom]*17},{'operator':'all','terms':[{'operator':'all','terms':[atom]*16}]*16}]:
   with self.assertRaises(ValueError):validate_extension({'status':'structured','expression':tree},self.ctx)
 def test_legacy_atomic_representation_stays_the_same(self):
  item={'kind':'panel_passive','effect_private':'[条件:メンタル75%以上]'}
  self.assertEqual(activation_extension(item,self.ctx),activation_condition(item,self.ctx['idols']))
if __name__=='__main__':unittest.main()
