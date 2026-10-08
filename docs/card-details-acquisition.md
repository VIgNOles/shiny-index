# 詳細カードの直接取得と保存HTMLの再変換

更新日: 2026-10-09 JST。詳細取得の継続指示を受け、前回のP/S各2件を直接取得対象に登録した。今回はWikiへの新規通信を行っていない。前回HTTP 429後の**ローカル取得制御**で、最短の次回確認時刻は2026-10-09 11:28:50 JST。これは本日のWiki応答が429であるという意味でも、Wikiが24時間の待機を規約で指定しているという意味でもない。

## 取得対象と共通制御

source_manifest.jsonのdetail_pagesに次を登録した。detail_base_dataset_versionの基本索引と固定card_id・P/S・URLを照合し、違いがあれば通信・状態更新の前に停止する。一覧／監査／詳細の取得は同じacquisition-state.jsonと排他ロックを使い、別のカードを指定しても待機期限を回避できない。full_collection_enabled=falseは維持する。

| ページID | 種別 | カード | 固定card_id |
|---|---|---|---|
| D01 | P-UR | 【アマテラス】樋口円香 | 6b98f267-3dd0-4e4b-9c25-edce2801b211 |
| D02 | P-SSR | 【切り拓いて・茨】桑山千雪 | 9793b6b2-b10a-434d-9429-42baef1bd47e |
| D03 | S-SSR | 【My Christmas】郁田はるき | 00a533b4-3644-4eca-8237-c34bfaf2c8a0 |
| D04 | S-UR | 【HoP PoP らびっつ】三峰結華 | 1e457013-9c18-4d2e-bd33-e8483fdda5a9 |

```powershell
./.venv/Scripts/python.exe scripts/collect_one.py status
# can_fetch=trueを確認したときだけ、新しい非公開ディレクトリへ1ページ取得
./.venv/Scripts/python.exe scripts/collect_one.py fetch D01 private/raw/detail-D01-20261009
```

日時は実際の実行日に置き換える。取得済みディレクトリは再利用しない。取得器はrobots.txtを確認してから個別ページを1回取得するため、ページ確認1回に最大2リクエストを使う。画像・添付・他の個別ページを追跡せず、自動リトライを行わない。429または503ならRetry-Afterの期限も保存する。認証確認画面やcanonical不一致、本文構造不一致も失敗とし、原本・公開版を変更しない。詳細HTMLの保存先はprivate/raw/に限定する。通常取得の後は再び24時間ゲートになり、4件の連続実行は行わない。現行の慎重な取得間隔を見直す場合も、正常応答を確認してから設計・制御を変更する。

## 実HTMLからの非公開候補

src/card_details.pyとscripts/transform_detail_html.pyはネットワークを使わず、成功したfetch.jsonとresponse.htmlを読み、URL・SHA-256・取得日時・canonical・タイトル・P/S節を確認して候補を作る。入力を更新せず、候補を正式原本へ自動採用しない。

HTMLのrowspan/colspanを展開し、SP・技能名・効果を対応付ける。出典には原セルの表番号・行・列・節アンカーを保存する。思い出アピールのLink共有セルも、各Lvに対応する効果と同じ原セルの根拠を持つ。名称内の色付きspanは単語の途中で分断せず、brは区切りとして扱う。未知の技能・結合の不整合・欠けた思い出Lv・異なるアビリティ二重掲載は失敗とする。現在の上限抽出は単一対象に限定し、複合上限を一部分だけ抽出せず未対応として拒否する。公開効果文の整形は未実装で、候補の効果原文は非公開のまま。

**現在有効なのはP用の実HTML変換**。通常パネル・MB小表・思い出・任意アビリティ照合を実装したが、UR/MBについては合成テストでの検証であり、4件の現行HTMLによる検証は残る。SのHTMLは取得・保存可能だが、変換は実物の表を確認するまで明示的に拒否する。前回のキャッシュ用P/S変換器は別入力形式として維持する。

```powershell
# 実HTMLで保存されている既存Pカードの再変換（追加のWiki通信なし）
./.venv/Scripts/python.exe scripts/transform_detail_html.py private/raw/run-c01 f99df994-2bf6-4389-b608-5fe706ee7542 private/audits/detail-html-c01-20261009.json
# D01取得成功後の再変換
./.venv/Scripts/python.exe scripts/transform_detail_html.py private/raw/detail-D01-20261009 6b98f267-3dd0-4e4b-9c25-edce2801b211 private/audits/detail-html-D01-20261009.json
```

--base-versionで指定した不変の基本索引からcard_idを解決する。省略値は今回のv1-93a6a8b8d40e754a。候補はprivate/内に限定し、同じ内容の再実行は許可、内容の違う既存候補の上書きは拒否する。完全に書いた一時ファイルを同一ファイルシステム内でハードリンクにより排他的に配置するため、中断時に候補を半端なJSONへ置換しない。ハードリンクを利用できない環境では保存を失敗とし、正常な既存候補を維持する。

強制終了後は実行中のプロセスとロックの有無を先に確認する。変換の*.tmpは候補として扱わず、再実行では別の一時ファイルを使う。取得のロックが残る場合はoperations.mdの停止・復旧手順に従う。原本HTMLのハッシュが違う場合は書き換えて帳尻を合わせず、別runに再取得するか取得時のバックアップから復旧する。

## 今回の実データ検証

2026-10-06T16:22:54+00:00に保存されていた【ほわっとスマイル】櫻木真乃の実HTML（HTTP 200）を使った。新規取得でも今回のP2/S2の置換でもない。

- パネル10件: ライブ2、パッシブ6、上限2。ライブ2件はLink、上限はDance+100とVocal+200。特訓☆とE4の解放条件を区別した。
- 思い出Lv1–5。Lv1/2はLink効果の同じ原セル、Lv3/4/5は別の共有原セルに対応することをHTMLと候補で照合した。
- MB・固有アビリティは当該保存HTMLで該当表なし。stage_skill/aptitudeはnot_collected。候補全体のreviewはneeds_review。
- 2回の再変換で内容ハッシュ90d5f4018d940d6e3ddd142d8d25fc6146f53fa94aa4a30d9c89b67f18a80561が一致。
- Python全44テストPASS。HTML追加11テストでは結合セル、色付き単語、MBタグ独立、クイック／パッシブ区別、重複アビリティ、未知効果／崩れた表／Lv異常の拒否、入力改変、原本・公開先保護、保存失敗、詳細取得の共通ゲートを検証した。テストは合成データで、非公開入力には依存しない。

依存関係は既存requirements.txtのbeautifulsoup4とプロジェクト.venvを使用。新規の外部依存は追加していない。正式Sheet revision7、基礎索引1,466件、公開UI v4・データ版は変更していない。残りは4件の直接HTML取得・照合、S実HTML変換、項目レビュー、詳細の固定ID／手修正維持、原本コピーへの採用、詳細Web検索／配布・公開、少数試験後の対象拡大。
