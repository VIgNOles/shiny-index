# 人物読み・短い検索案内（2026-10-13）

## 着手前の確認

`REVIEW_DECISIONS.md` 優先7の採用範囲を確認した。基礎検索 `web/search.mjs` はNFKC・空白区切りAND・表示文字列の部分一致に対応済みだが、人物の読みは未収録で、`まどか`／`ひぐちまどか`では樋口円香のカードを探せなかった。公開基礎辞書は33人物（通常28・七草はづき・コラボ4）、読みフィールドなし。検索URL・人物選択・既存カード名・ユニット・シリーズ検索を活かす局所変更とした。

## 変更と検証

- `web/search.mjs` 内に33人物の固定読み辞書を追加。既存qの各語を、従来の対象文字列または当該人物の読みで照合する。ひらがな／カタカナ／半角カタカナ／姓と名の間の全半角空白に対応。
- 表示用人物名・ID・原本・公開データの辞書は変更しない。未知人物の読み、誤字、愛称を推測しない。補完UI・曖昧検索は保留のまま。
- 独立期待読み表をテスト側に置き、現行の全33人物・各4形式でカードID集合を検証（132集合）。既存の人物・カード名・シリーズAND、半角、混在語、誤記の除外、未知人物、空白入り人物名も確認。
- `node --test tests/search.test.mjs`：16成功。`node --test tests/search.test.mjs tests/detail-search.test.mjs tests/compound-passive.test.mjs`：87成功（2026-10-13、並行作業中のその時点のファイル）。10,000行検索は約44〜47ms。この値は環境依存の観測で、保証閾値ではない。

難読名は[公式アイドル紹介](https://shinycolors.idolmaster-official.jp/idol/)、[緋田美琴](https://shinycolors.idolmaster-official.jp/idol/shhis/mikoto/)、[斑鳩ルカ](https://shinycolors.idolmaster-official.jp/idol/cometik/luca/)、[鈴木羽那](https://shinycolors.idolmaster-official.jp/idol/cometik/hana/)、[郁田はるき](https://shinycolors.idolmaster-official.jp/idol/cometik/haruki/)、[幽谷霧子](https://shinycolors.idolmaster-official.jp/idol/lantica/kiriko/)、[西城樹里](https://shinycolors.idolmaster-official.jp/idol/hokagoclimaxgirls/juri/)、[和泉愛依](https://shinycolors.idolmaster-official.jp/idol/straylight/mei/)で確認。コラボ名は[作品公式の人物表記](https://ichigoproduction.com/talent/)と[公式の英字表記](https://ichigoproduction.com/Season1/special/abroad.html)を確認した。ゲームデータの追加取得・collector実行はない。

## 画面に組み込む短い説明案

必要時に開く「用語と検索例」内にまとめ、普段の画面を圧迫しない。

- 読み：人物は読み仮名でも検索できます。空白区切りはすべての語に一致します。
- P／S：Pはプロデュースカード、Sはサポートカードです。
- Link：Link付きスキルは、Link機能を持つライブを探します。追加部分の効果だけを探すには「効果の範囲」でLinkを選びます。
- 効果量：明記された確定数値を探します。条件で変わる最大値や発動確率は含みません。
- 必要特訓：一致したスキルに明記された解放段階で探します。不明な段階は含みません。
- 育成特性：Sカードのアイデア・ひらめき・楽曲熟練度の種類を組み合わせて探せます。詳細未収録のカードは含みません。

## 実在データで確認した用途例

基礎 `v1-93a6a8b8d40e754a`、詳細 `d1-4123183cd3640b4e`、作業中の現行検索関数で確認した。件数は確認記録用で、画面の例には固定件数を載せない。

| 用途・画面のリンク名 | URLクエリ | 確認件数・正例 |
|---|---|---|
| 読みで探す：まどか Hug？ | `q=まどか Hug?` | 1件、樋口円香【Hug？】 |
| 人物＋シリーズ：さくらぎまの トワコレ | `q=さくらぎまの トワコレ` | 2件、櫻木真乃【だいすきだよ】／【interStellar-Stella】 |
| Vocal上限100以上のSカード | `card_kind=S&effect_type=cap_increase&effect_target=Vocal&effect_unit=points&effect_min=100` | 137件、鈴木羽那【Present Present】等 |
| Link部分にアピールがあるパネルライブ | `skill_kind=panel_live&mechanic=link&effect_scope=link&effect_type=appeal` | 245件、三峰結華【映す光】等 |
| ボーカルのアイデアを持つSカード | `card_kind=S&trait_idea=vocal` | 227件、月岡恋鐘【Re:パラレル！】等 |
| メンタルのひらめきを持つSカード | `card_kind=S&trait_inspiration=mental` | 181件、和泉愛依【三つ子の魂えたーなる！】等 |
| 歌唱力の楽曲熟練度を持つSカード | `card_kind=S&trait_music=singing` | 259件、小宮果穂【Heavy,Heavy Rain】等 |
| 育成特性を3種類組み合わせる | `card_kind=S&trait_idea=vocal&trait_inspiration=mental&trait_music=singing` | 46件、月岡恋鐘【Re:パラレル！】／福丸小糸【なんでもない夏】等 |

リンク組込みは通常の検索URLを使用し、条件を一式置き換える形で挙動を明確にする。新しい検索保存機能は増やさない。数値の例は単位を必ず指定し、「Link付き」と「Link範囲」を混同しない。読みと育成特性の案内を加えた画面の確認は統合側のUI27検証で行う。
