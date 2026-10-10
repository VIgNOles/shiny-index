# 管理者の操作手順

## 現在の原本

編集原本は、指定されたGoogleアカウントが所有する非公開Google Sheets「enza P/S card master」です。SheetのURLとIDはGit対象外の `private/sheets-connection.json` に記録しています。所有者だけがアクセスできること、既存9タブ・1,466件と追加6詳細タブ・固定ID・取得値・手修正の往復一致、タイムゾーン Asia/Tokyo を確認しました。

`private/master.xlsx` は最後に承認したローカル作業スナップショットです。日常の手編集はSheetsだけで行い、配布前にSheetsからXLSXを出力して下記の review → apply を通し、ローカルスナップショットを追いつかせます。両方を同時に編集しません。取得候補の採用でローカル側を更新した場合は、後述の手順で完全原本を新しい非公開Sheetに取り込み、往復検証後に原本を切り替えます。

## 追加・修正

1. 指定アカウントで非公開のGoogle Sheets原本を開く。1人で編集し、更新の取込中は編集を止める。
2. 「追加・手修正」タブを編集する。他の内部タブは編集しない。
3. 既存カードはcard_idで該当行を探し、変更したい列だけ入力する。空欄は取得値を使う。
4. 意図的に不明へ戻す場合、`clear_fields`に`["first_implemented_on"]`のようなJSON配列を入れる。同じ列に値も入れる指定は禁止。
5. `reason`に理由、`source_ref`に公開してよい資料ID、`updated_at`に日時（例 `2026-10-07T12:00:00+09:00`）を記入する。秘密・個人情報を書かない。
6. 新規カードは次のコマンドでUUIDを作り、新しい行のcard_idへ貼る。

```powershell
./.venv/Scripts/python.exe -m src.indexer new-id
```

新規行はcard_title、idol_id、idol_name、card_kind（P/S）、variant_kind（通常はbase）を必須とする。
rarityはN/R/SR/SSR/UR、日付はYYYY-MM-DD、series_idsはJSON配列、series_statusはknown/none/unknown。
人物IDは既存の同じ人物の値を使う。新人物の辞書登録UIは未整備なので、現段階では実装担当者と原本台帳を更新する。
入手分類コードはdesign.md 5.5参照。未確認を恒常と推測しない。
Wiki URLは実際に確認したリンクを貼り、未掲載なら空欄とする。

編集後は下記のGoogle Sheets原本XLSX取込手順で review と apply を先に実行する。その後、次を実行する。

```powershell
./.venv/Scripts/python.exe -m src.indexer prepare private/master.xlsx dist
```

prepareで入力エラーが出たら原本を修正する。WebやCSVを直接修正しない。
正常なら表示された版の`dist/data/<版>/manifest.json`とWebを確認する。
同じ公開内容を再prepareしても版は変わらない。新しい隔離先では生成日時が変わるため、内容差分がなければ再公開しない。編集の自動公開はしない。

## 少数取得と再変換

以下のcollect例は取得停止中には実行できません。再開条件を確認するまでは保存済みのprivate/raw入力からtransform以降を実行してください。直接の1ページ取得もsource_manifest.jsonの停止フラグで通信前に拒否されます。

```powershell
./.venv/Scripts/python.exe -m src.indexer collect 'https://wikiwiki.jp/shinycolors/【ほわっとスマイル】櫻木真乃' private/raw/new-run
./.venv/Scripts/python.exe scripts/transform.py private/raw/new-run private/sample-batch.json private/new-batch.json
./.venv/Scripts/python.exe scripts/review_batch.py private/master.xlsx private/new-batch.json private/new-review.json
./.venv/Scripts/python.exe -m src.indexer accept private/new-batch.json private/master.xlsx
./.venv/Scripts/python.exe -m src.indexer prepare private/master.xlsx dist
```

collectとreview_batchは原本を変更しない。transformはネット接続なしで同じ保存応答から再実行できる。reviewの新規・変更・消失キー、手修正衝突、件数警告を確認してからacceptする。候補の監査ファイルは非公開に保つ。
現在のtransformはC01のタイトル・人物・実装日の照合専用。他のカード、全件一覧には使わない。
runフォルダーは新しい名前を使う。403/CAPTCHAは回避せず停止。失敗runは採用しない。
自動リトライ・ETagはまだ実装していない。全期間一覧の再取得はscripts/collect_all.pyで7ページを新しいrunへ保存する。RAW_RUN_ROOTと新しいTRANSFORM_OUTPUT_ROOTを指定し、TRANSFORM_SCOPE=fullでscripts/full_transform.pyを再変換する。既存候補との内容不一致は上書きせず停止する。取得と採用は別操作。再取得候補も`scripts/review_batch.py private/master.xlsx <候補full-batch.json> <新しい非公開review.json>`で原本と比較してから採用する。レビュー出力は既存ファイルを異なる内容で上書きしない。再実行前に原因を確認する。

## 再取得で手入力カードに一致した場合

自動統合しない。P/S・人物・派生・根拠を照合して、候補の取得元キーと既存card_idの対応をJSONに記録する。
キー形式は`wikiwiki:<URLのUnicode表記>:<variant_kind>`。`src.indexer.key()`の結果を使い、手で推測しない。

```powershell
./.venv/Scripts/python.exe -m src.indexer accept private/new-batch.json private/master.xlsx --mapping private/mapping.json
```

既存ID・手修正は維持される。誤同定が疑われる場合は保留する。公開済み重複IDのredirect統合は未実装。

## エラー・復旧

- accept前にバックアップを作り、一時XLSXを読み戻して検証してから置換する。壊れた候補や重複は旧原本を残す。
- 取得失敗時は正常な原本からprepareできる。取得が失敗したことを確認日更新として扱わない。
- prepareは一時領域で各形式を照合し、検証を通った版を出力する。ローカルdistのコピー中にOS停止した場合は、同じprepareを再実行する。ローカルコピーはディレクトリ全体の原子的交換ではない。
- 公開時は必ず完成したdistを一つのPages artifactで配置する。生成途中のdistを同期配信しない。
- 原本を復旧する場合は、バックアップを別名で開き台帳・手修正を照合してから戻す。新しい編集を確認せず過去版で上書きしない。
- 公開成果物だけ戻すローカル操作：

```powershell
./.venv/Scripts/python.exe -m src.indexer rollback dist v1-xxxxxxxxxxxxxxxx
```

原本は変更しない。過去版データの検証後、indexとlatestの版を切り替える。その完成バンドルを再配置する。
PagesでのHTML成果物の更新→元版への切戻しは実地検証済み。異なるカードデータ版への切戻しは未検証。Actions一時artifactだけを長期バックアップにしない。

## GitHub Pages公開・更新手順

1. ユーザー所有の公開リポジトリと無料の標準ランナーが使えることを確認する。
2. sources-policy.mdの現行公開方針とWIKIWIKIの禁止事項を確認する。問い合わせは今回の必須工程ではない。外部から条件変更が示された場合は公開範囲・収集手順を再評価し、公式全網羅の限界を表示する。
3. コードの公開対象を明示的に選ぶ。private、node_modules、.venv、認証情報を含めない。
4. `./.venv/Scripts/python.exe scripts/stage_release.py dist site`で初回の公開候補を新しい`site/`に作り、`./.venv/Scripts/python.exe scripts/check_site.py site`で検証する。`dist/`の過去の試作版は同梱しない。2回目以降は新しい`site-next/`へ`--previous-site site`を指定して作り、検証後に既存の`site/`をバックアップして入れ替える。ステージング先を既存フォルダーへ重ね書きしない。
5. ユーザーの公開指示とsources-policy.mdの範囲で`source_manifest.json`の公開フラグをtrueにする。`check_site.py site`成功後、無視対象の`site/`を`git add -f site`で明示的に追跡対象へ加える。コードとともにコミット・pushし、リポジトリSettings → Pages → SourceをGitHub Actionsにして同梱pages.ymlを手動実行する。private/と生応答は追加しない。
6. 公開URLを未ログインで開き、検索、CSV/XLSX/JSON取得、manifestの版とハッシュを照合する。
7. 1件追加・1件修正を新しい版として公開し、反映を確認する。その後旧artifactへの切り戻しを実証する。

未確認状態を隠すためにcoverage.completeをtrueへ変更しない。公開できることとゲーム全網羅は別の条件。

### 現在の公開状態

公開URLは https://vignoles.github.io/shiny-index/ 。この段落に記す公開実績は2026-10-08 UI更新時点の履歴（データ版v1-ae32f82ff0a94d87、1,466件、2版19ファイル）。現行版は末尾の節で確認する。2026-10-08にUIを更新し、明示公開run 37646437517がsuccess。続けて各カードの出典表示を改善したrun 37647591990もsuccess。匿名GETで19/19ファイルが検証済みsiteとバイト一致し、ログインなしのEdgeでPC幅とタッチ設定付き390px幅の検索・複数絞り込み・並べ替え・リセットを確認した。データ版と原本のカード内容は変更していない。

最初のPages失敗はGitの自動改行変換によるcards.csvハッシュ不一致であり、.gitattributesのsite/** -textで修正した。以後の更新ではsite生成・check_site・Git blobの一致を確認してpushし、main上の明示publish:コミットでPagesを起動する。実カード1件追加・1件修正の一般公開反映は未実施。coverageだけが異なるデータ版の公開切戻しと復帰、HTML成果物の更新と復旧は検証済み。

## Google Sheets原本をXLSXとして取り出す運用

指定アカウントの非公開Google Sheets原本で「追加・手修正」だけを編集し、他の8タブは変更しません。更新の配布前に編集を止め、同じSheetをMicrosoft Excel形式でダウンロードして `private/sheets-exports/<日時>.xlsx` へ保存します。公開リポジトリに入れません。実Sheetエクスポートを用いて9タブ・1,466件の差分なし往復検査と、非公開コピーでの1件追加・1件修正の取込検査を実施済みです。

```powershell
./.venv/Scripts/python.exe scripts/import_sheet_export.py review private/master.xlsx private/sheets-exports/<日時>.xlsx private/audits/sheets-review-<日時>.json
```

reviewは原本を変えません。レポートで追加ID・新規／修正／解除した手修正を確認します。既存ID・出典・取得履歴・保護タブの差異、手入力重複、式、入力不正があれば停止します。意図した変更と一致した場合だけ次を実行します。review後に原本またはエクスポートのバイトが変わればapplyは停止します。

```powershell
./.venv/Scripts/python.exe scripts/import_sheet_export.py apply private/master.xlsx private/sheets-exports/<日時>.xlsx private/audits/sheets-review-<日時>.json
./.venv/Scripts/python.exe -m src.indexer prepare private/master.xlsx dist
./.venv/Scripts/python.exe scripts/stage_release.py dist site-next --previous-site site
./.venv/Scripts/python.exe scripts/check_site.py site-next
```

applyは旧XLSXのバックアップを作り、新XLSXを読み戻してから置換します。新しい公開候補の確認後に旧siteをバックアップしてsite-nextへ入れ替え、site配下のGitバイト一致を確認してコミット・pushし、Pagesの手動ワークフローを実行します。公開URLで版、更新日、Webと配布の変更内容、匿名取得を照合します。新規カードの取得時の重複照合と明示mappingは上記「再取得で手入力カードに一致した場合」を使います。


公開反映後は次を実行し、匿名URLの全ファイルをsite/とバイト単位で照合する。失敗したら公開版を完了扱いにせず、Actions結果とsiteの検証・Git改行属性を確認する。

```powershell
./.venv/Scripts/python.exe scripts/check_public.py site https://vignoles.github.io/shiny-index/
```

## 取得値を採用した後のSheets原本切替

取得候補の採用はローカルスナップショットを先に更新します。Sheetsに未取込の手編集を残したまま accept しないでください。編集を止めてSheetをXLSXとして取り出し、review → apply を済ませてから、取得候補の差分監査と accept を実行します。

accept 後、更新された `private/master.xlsx` を**新しい**非公開Google Sheetsとして同じDriveフォルダーへ取り込みます。旧Sheetを上書きせずに保持し、新Sheetの共有が所有者のみ・タブが9つであることを確認します。新SheetからXLSXを書き出し、次の差分なし review を通します。件数、revision、固定ID、手修正、内部8タブが一致しなければ切り替えません。

```powershell
./.venv/Scripts/python.exe scripts/import_sheet_export.py review private/master.xlsx private/sheets-exports/<新Sheetの出力>.xlsx private/audits/<新Sheetの往復確認>.json
```

成功したら新Sheetのタイムゾーンを Asia/Tokyo にし、`private/sheets-connection.json` のURLとIDを新Sheetへ更新します。この時点で新Sheetが唯一の編集原本です。旧Sheetは更新せずバックアップとして明確に改名・保管し、試験用Sheetは検証後に削除します。Sheetの直接API同期は未実装なので、取得値採用後にこの切替を飛ばすと原本と公開用スナップショットが食い違います。公開は新Sheetの往復検証と `check_site.py` が通った後に行います。


### CLIからの明示的なPages実行

GitHub Pages環境はmainブランチだけをデプロイ元として許可しています。タグからの起動はランナー開始前に拒否されたため使用しません。サイトを含むコミットをmainへpushし、check_siteと公開対象のGit blob一致を確認した後、mainに空コミットを一つ作り、コミットメッセージを必ず `publish: ` で始めてpushします。このメッセージだけが公開ジョブを起動します。通常のmain pushではジョブはスキップされます。ワークフロー内の公開フラグとcheck_siteの検査は維持します。

```powershell
git commit --allow-empty -m "publish: validated site"
git push origin main
```

main上の明示公開コミットでActions実行成功、匿名URLの公開対象全ファイルが意図したsiteとバイト一致することを実地確認済みです。この記録時点の新旧2版構成は19ファイルでした。今後の更新でも、Actionsが成功し、匿名URLで公開対象全ファイルが意図したsiteと一致するまで更新完了扱いにしません。失敗時は原因を直した新コミットを作ってから別のpublish:コミットで再実行します。旧版へ戻す場合も、旧版を選ぶ検証済みsiteをmain上の新コミットにし、別のpublish:コミットで起動します。原本は戻しません。

## HTTP 429で取得が止まった場合

run.json が incomplete、かつ失敗ページがある取得runは全件候補へ変換・採用しない。取得済み応答とfetch.jsonは監査用にそのまま残し、原本と公開中のsiteは変更しない。2026-10-08のW09 HTTP 429後、ユーザーはWikiに迷惑をかける取得を避けるよう指示した。source_manifest.jsonのfull_collection_enabledをfalseにしてWiki取得を停止した。15秒間隔や翌日までの待機だけを安全性の根拠として再試行しない。Wiki管理者／運営から適切な取得経路・頻度を確認するなど、負荷をかけない方法が確立するまではフラグを戻さない。再開時も新しい隔離runに保存し、全7ページ正常取得、オフライン変換、差分レビュー、採用を別操作にする。429を「変更なし」の証拠や収録対象日の更新には使わない。保存済み応答のオフライン監査と公開済みデータの検証は継続可能。この段落の全面停止方針は当時の記録であり、現行の単一ページ限定再開は末尾の節を参照。

## 429後の限定再確認（2026-10-08更新）

ユーザーは過負荷を避けた再開を指示した。7ページ連続取得と直接のcollect CLIは停止したまま。単一ページ用CLIのみ、前回の取得または429から24時間以上経過し、排他ロックがなく、新しい保存先を指定した場合に利用できる。この24時間は当時の慎重な運用上の下限であり、Wiki側が許容した頻度という意味ではない。通常待機は2026-10-09の明示解除で60秒に変更したため、以下の期間制御は当時の記録として扱い、最新の節を優先する。1回につき許可リストの1ページだけ、robots.txtの確認と対象ページ取得のみ行い、自動リトライはしない。429・503時のRetry-Afterが24時間を超える場合は長い方まで待つ。403・確認画面・429・503・形式異常では停止し、繰り返し試さない。

    ./.venv/Scripts/python.exe scripts/collect_one.py status
    # 新環境に状態ファイルがないときだけ、initで設定済みの通常待機を開始する（現行60秒）
    ./.venv/Scripts/python.exe scripts/collect_one.py init
    # statusのcan_fetchがtrueになってから、未使用の保存先で1ページだけ手動実行
    ./.venv/Scripts/python.exe scripts/collect_one.py fetch W09 private/raw/limited-W09-YYYYMMDD

既存のprivate/raw/acquisition-state.jsonには前回429時刻を記録済み。statusとinitは通信しない。fetch後はfetch.jsonとlimited-run.jsonを確認する。limited-run.jsonのfull_run=falseは全件取得runではないという意味であり、full_transform.pyの全件入力には使わない。前回保存済みHTMLとのオフライン差分を見ることはできるが、ほかのページを当日確認したとは扱わない。原本・公開版を更新する前に、対象ページと全件候補の整合性を別途確認する。途中終了でacquisition-state.lockが残った場合は、実行中プロセスと状態ファイル・保存先を確認してから解除し、前回試行からの待機を守る。

WIKIWIKIの[確認画面の案内](https://wikiwiki.jp/pp/security-check-guide)は短時間の多ページ閲覧による再確認を説明している。[REST APIの説明](https://z.wikiwiki.jp/wikiwiki-rest-api/topic/1)では対象Wiki側のAPI許可設定と認証が必要。APIの公表レート上限を通常HTMLの許容頻度として流用しない。管理者・運営から個別の条件が示された場合はそれを優先し、取得方法を見直す。

単一ページ保存後の通信なし比較例：

    ./.venv/Scripts/python.exe scripts/compare_saved_page.py private/raw/recheck-20261007-2/gacha private/raw/limited-W09-YYYYMMDD

この比較は応答ハッシュ、Wiki本文の可視テキスト・本文リンクの一致と、差分件数・最大10件の例を示す。差分0でもほかの6ページや公式全件が新たに確認されたことにはならない。

## 今回の完成条件の更新（2026-10-08）

Wiki管理者・運営への問い合わせと回答取得は、ユーザーの明示指示により今回の必須工程から除外された。過去の問い合わせ案内は履歴であり、これを理由に作業を止めない。現行の取得制御は下記2026-10-09更新を参照し、statusで可能と確認できたときに単一ページから続ける。ユーザー本人がスマートフォンで基本動作を確認済み。未詳のUI不満点は後からの指摘に基づき直す。


## 2026-10-08の確認結果と現行原本

現在の編集原本は指定Googleアカウントの非公開native Sheet「enza P/S card master r7」。ローカル承認済みスナップショットはprivate/master.xlsx、revision 7、1,466件。r6 Sheetとr6 XLSXはバックアップとして保持する。現行の取得状態は `./.venv/Scripts/python.exe scripts/collect_one.py status` で確認し、W09の一度限りの期限前確認後は通常の24時間ゲートに戻った。同じ `--user-authorized-early-fetch` は状態記録により再使用できない。次回以降はstatusのcan_fetchがtrueになるまでWikiへ送信しない。既存の429 runはincompleteのまま保存し、二つの取得runを組み合わせた今回の候補はprivate/raw/composed-20261008-user-early、変換候補はprivate/candidates/composed-20261008-user-early-v2に隔離した。

再実行する場合は既存runを上書きせず、`RAW_RUN_ROOT=private/raw/composed-20261008-user-early`、`TRANSFORM_OUTPUT_ROOT`に新しい保存先、`TRANSFORM_SEED_ROOT=private`、`TRANSFORM_SCOPE=full`を設定してscripts/full_transform.pyを実行し、review_batch.pyで原本と比較する。差分0ならカード行の変更を作らない。配布候補はrevision 7から生成したv1-93a6a8b8d40e754aで、カード・出典は前版と一致し、収録対象日の確認範囲のみ2026-10-08へ更新した。全ゲーム網羅のcompleteはfalseを維持する。


### r7公開後の確認

2026-10-08に公開した現行版はv1-93a6a8b8d40e754a、編集原本は非公開Sheet r7。旧2版を残した3版構成で公開ファイルは26件。準備コミットea51e0dの通常pushはPages skipped、明示公開コミットd2cdd55のrun 37720130993はsuccess。`./.venv/Scripts/python.exe scripts/check_public.py site https://vignoles.github.io/shiny-index/` は26/26一致。公開URL指定のUI試験はPC・390px幅ともPASS。カード行の追加・変更はなく、確認範囲だけ2026-10-08に更新。次の実カード差分が見つかったときも、Sheet手編集→XLSXレビュー、または取得候補レビュー→新Sheet昇格→配布生成→公開URL照合という順を守る。


## 保存済みページを組み合わせて再変換する（通信なし）

429で中断したrunの正常保存分と、後から1ページだけ保存した結果は、元ファイルを編集・上書きせずに scripts/compose_saved_run.py で新しい private/raw/ 配下へ合成する。CLIは7つの登録済みページIDが揃うこと、各URL・canonical・応答SHA-256・取得状態を確認する。誤配置や破損があれば最終出力を作らず停止し、公開フォルダーを出力先に指定することも拒否する。

    $savedPages = @(
      '--page', 'W02=private/raw/recheck-20261008/p-list',
      '--page', 'W03=private/raw/recheck-20261008/s-list',
      '--page', 'W04=private/raw/recheck-20261008/s-volume',
      '--page', 'W07=private/raw/recheck-20261008/collab',
      '--page', 'W08=private/raw/recheck-20261008/road',
      '--page', 'W05=private/raw/recheck-20261008/chronology',
      '--page', 'W09=private/raw/limited-W09-20261008-user-early'
    )
    ./.venv/Scripts/python.exe scripts/compose_saved_run.py private/raw/composed-replay-YYYYMMDD @savedPages
    $env:RAW_RUN_ROOT = 'private/raw/composed-replay-YYYYMMDD'
    $env:TRANSFORM_OUTPUT_ROOT = 'private/candidates/composed-replay-YYYYMMDD'
    $env:TRANSFORM_SEED_ROOT = 'private'
    $env:TRANSFORM_SCOPE = 'full'
    ./.venv/Scripts/python.exe scripts/full_transform.py
    ./.venv/Scripts/python.exe scripts/review_batch.py private/master.xlsx private/candidates/composed-replay-YYYYMMDD/full-batch.json private/candidates/composed-replay-YYYYMMDD/review.json

保存済みページの日付が異なる場合、収録確認日には7ページの日本時間で最も古い取得日を使う。最新の1ページだけの日付で全件を確認済みと表示しない。レビューで新規・変更・消失・分類不明と件数異常がないか確認し、元runと既存原本を保持する。合成先・変換先・レビュー先は毎回未使用の名前にする。

## UI版の保存と切り戻し（2026-10-08）

UI初版はGitタグ `ui-v1-20261008` としてoriginにも保存済み。改訂版は `ui-v2` と表示し、カードデータ版とは別に扱う。UIだけの更新ではGoogle Sheets原本・カード行・データ版を変えない。調査根拠と変更点は [docs/ui-design.md](docs/ui-design.md) を参照する。

公開中のUIに問題があれば、タグから**新しい候補ディレクトリ**を作る。スクリプトは `site/` と原本を変更せず、現在の公開データ版を保ったままタグ時点のUI4ファイルを復元する。既存の出力先を指定すると拒否する。

```powershell
./.venv/Scripts/python.exe scripts/build_ui_rollback.py --ref ui-v1-20261008 --source site --output private/audits/ui-rollback-YYYYMMDD
./.venv/Scripts/python.exe scripts/check_site.py private/audits/ui-rollback-YYYYMMDD
$env:UI_BROWSER_PATH = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
node tests/ui-smoke.mjs private/audits/ui-rollback-YYYYMMDD
```

検証後、`git status --short` で未関係の編集を確認する。公開を戻すと決めた場合だけ、候補の `index.html`、`style.css`、`app.mjs`、`search.mjs` を `site/` の同名ファイルへコピーし、`check_site.py site` と `tests/ui-smoke.mjs site` を再実行する。UI4ファイルだけをコミット・pushしてから、既存の手順どおりmainへ `publish: ` で始まる空コミットをpushする。Pages成功後、`check_public.py` と公開URLのPC・スマホ操作試験で確認する。公開検証が終わるまで切り戻し完了扱いにしない。

改訂版へ復帰する場合も、同じCLIの `--ref ui-v2-20261008` を指定し、**別の未使用出力先**で候補を作る。データ構造が将来変わった場合は、過去UIと現行データの互換性を検証してから公開する。旧データを無断で巻き戻さない。

実績: UI v2はPages run 37739561660で公開成功し、匿名URLの26/26ファイルとPC・390px・320px操作を確認した。初版へ戻す隔離候補は改訂前の匿名公開URLと26/26バイト一致を確認済み。公開サイト自体のUI切り戻しは今回実行していない。

## UI v3の再検証と切り戻し（2026-10-08）

UI v3は4つの画面ファイルだけを変更し、カードデータ版 v1-93a6a8b8d40e754a と原本revision 7を維持した。別環境ではREADMEのPython・Node・Playwrightセットアップ後、以下を実行する。既存Edgeを使う場合はUI_BROWSER_PATHをmsedge.exeの絶対パスへ設定する。

    ./.venv/Scripts/python.exe -m unittest discover -s tests -v
    node --test tests/search.test.mjs
    ./.venv/Scripts/python.exe scripts/check_site.py site
    node tests/ui-v3-smoke.mjs site

UI v3の表示が壊れた場合、公開siteや原本を直接戻さず、まずUI v2の隔離候補を新規ディレクトリへ生成する。出力先は毎回未使用にする。

    ./.venv/Scripts/python.exe scripts/build_ui_rollback.py --ref ui-v2-20261008 --source site --output private/audits/ui-v2-rollback-YYYYMMDD
    ./.venv/Scripts/python.exe scripts/check_site.py private/audits/ui-v2-rollback-YYYYMMDD
    node tests/ui-smoke.mjs private/audits/ui-v2-rollback-YYYYMMDD

検証が通った候補のindex.html、app.mjs、search.mjs、style.cssだけをsiteへコピーし、check_siteと旧UI試験を再実行する。mainへ画面4ファイルの復旧コミットをpushし、別のpublish:空コミットをpushする。Actions成功後、check_public.pyの26/26一致と匿名URLで旧UI試験を確認して完了とする。復帰時は同様にui-v3-20261008タグから新規候補を作り、UI v3試験を通す。原本やカードデータをUI切り戻しに巻き込まない。

UI v3の公開実績: 通常pushのrun 37796618732はskipped、明示公開run 37796666483はsuccess。公開26/26ファイル一致と匿名ブラウザのPC・390px・320px試験PASS。タグui-v3-20261008がUIの固定点であり、切り戻し時は上記の候補生成を再実行する。

## UI v4の検証とUI v3への切り戻し

新しい8区分と詳細2軸の使い分けはdocs/ui-v4-spec.md。UI v4の試験は次を実行する。既存Edge利用時はUI_BROWSER_PATHを設定する。

    node --test tests/search.test.mjs
    ./.venv/Scripts/python.exe scripts/check_site.py site
    node tests/ui-v4-smoke.mjs site

問題時はui-v3-20261008タグからscripts/build_ui_rollback.pyで新規隔離候補を作り、check_siteで3データ版の整合を検証する。UI v3タグの4画面ファイルと候補の生バイト一致も確認する。検証した4画面ファイルだけをsiteへ戻してmainにコミットし、別のpublish:空コミットでPagesへ反映する。公開26ファイル一致と旧画面の検索操作を確認するまで復旧完了としない。過去のUI v3試験はui-v3-20261008タグに保存されている。現行のtests/ui-smoke.mjsはUI v2向けなので、UI v3切り戻し候補へそのまま適用しない。

UI v4で外すのは画面上のCSV取得導線。既存の版付きCSVファイルは公開URLに残る。ファイルそのものを削除する場合は過去版の直接URL、manifest、バンドル検証、元の配布要件への影響を別途確認してから新しいデータ版・公開手順を設計する。

UI v4公開実績: 通常pushのrun 37800885079はskipped、明示公開run 37800969481はsuccess。匿名URLの26/26ファイル一致、PC・390px・320px試験PASS。タグui-v4-20261009が現行UIの固定点。公開版CSV直接URLは残るので、『CSV非公開』をファイル撤去まで拡大する場合はユーザー回答後に設計・検証する。


## 2026-10-09 ローカル待機解除と詳細4件の直接取得（現行制御）

ユーザーの「待機期限を解除して進めて」により、正常時のローカル待機を60秒へ変更した。source_manifest.jsonのsingle_page_cooldown_seconds=60、single_page_failure_backoff_seconds=86400。失敗時にはlast_failure_atと理由を状態へ記録し、後続ページを停止する。HTTP429の時刻、Retry-After、過去の一度限りの早期取得記録は削除せず、local_wait_changesに今回の変更根拠を保存した。通常の60秒という値はWikiの許容頻度を保証するものではなく、並列や大量連続取得は開始しない。full_collection_enabled=falseは維持する。

scripts/collect_one.py statusで現状を確認し、登録済みの1ページを新しいprivate/raw/へ保存する。429/503/403/確認画面/取得形式異常の場合は自動リトライせず、少なくとも新規失敗から24時間とRetry-Afterの長い方を守る。変換の構造エラーは追加通信で直さず、保存入力で対応・再検証する。P/S詳細4件は09:25–09:29 JSTに103/72/89秒の間隔でHTTP200保存し、実HTML変換と504共通項目のキャッシュ照合を完了した。現行の再実行コマンドと入力・候補の場所はdocs/card-details-acquisition.md。原本Sheet r7・公開基礎索引は変更していない。

## 詳細の全件取得・中断・復旧（2026-10-09 現行）

ユーザーの「問題なければ全件への取得を進めてください」により、上の「大量連続取得は開始しない」は旧段階の記録となる。詳細専用の凍結カタログ（1,466カード/1,363URL）に限り、取得完了から60秒以上の逐次取得を明示的に有効化した。一覧用full_collection_enabled=false、共有取得ロック、新規失敗後24時間＋Retry-Afterの停止、自動リトライなしは維持する。問い合わせを追加の必須ゲートにしない。

現在のrunはprivate/raw/detail-catalog-20261009。状態はscripts/collect_detail_catalog.py statusで実際に読み、HANDOFFの件数だけで完了・プロセス停止と判断しない。停止はstopサブコマンド、再開はstopped/worker_is_alive=false確認後のrun --clear-stop。成功した既存入力を再送しない。取得中でもtransform_detail_catalog.pyでオフライン変換できる。詳しい有限予算・PIDロック・不明結果の扱い・24時間復旧は [全件詳細取得の手順](docs/card-details-full-acquisition.md) を参照。

原本Sheet r7、公開基礎索引1,466件、UI v4はこの取得では変更しない。原HTML、原文効果、全件候補・監査・ログはprivateのみで、Gitのforce addや自動採用・公開をしない。全入力を保存し終えても詳細公開版の完成ではない。


## 最新: 詳細原本15タブとUI v5（2026-10-09）

現在の編集原本は同じ指定アカウントのnativeコピーで、基礎revision7・詳細revision6、15タブです。旧9タブのr7はバックアップ。基礎更新は従来の「追加・手修正」、詳細名称/SP/効果/機能タグは「詳細項目」のG～Mを使い、理由・根拠・ISO日時を残します。詳細カード205件・2,825項目の実エクスポート、基礎差分0、1詳細追加/1名称修正・固定ID/手修正保持を確認しました。詳細エクスポートも非公開に保存します。

基礎/詳細を同じエクスポートからreview/applyしてください。詳細のみの編集もdetail_changedで検出し、取得列・式・未知項目・ID/派生衝突は拒否します。再取得採用では既存の手修正を先に取り込み、正常原本を新しくnativeコピーして更新し、15タブを読み戻して切り替えます。詳細の編集・公開・復旧、現在の制約は[詳細接続手順](docs/card-details-integration.md)。古い「9タブのみ」や「詳細は前準備のみ」はその段階の履歴です。

詳細は `details/<d1版>/details.json` と版情報を基礎v1版へ結びます。CSV画面導線は撤去したまま。スキル機能はライブ行だけに適用し、発動条件と効果全文は未構造化のものがあります。全件原入力取得を60秒以上で続行中ですが、今回の205詳細を全件版完成と扱いません。未収録・ロード対応・47件保留をcoverageと手順に残しています。


### 2026-10-09 生成ライブ対応後の現行原本

現行は指定Driveの15タブ、基礎r7/1466件、詳細r7/206件2845項目。旧205/r6のnative原本とローカルXLSXはバックアップ保持。private/sheets-connection.jsonで現在のURL・全値照合・バックアップを確認する。生成ライブはP専用でSP空欄、連係段階/生成元/機能タグを取得値として扱う。手修正は既存G:M列のみ、生成段階やID/source_jsonを直接書き換えない。未記載SPを0にしない。

UI v6と詳細d1-d3a4bf450390442b、基礎版はv1-93a6a8b8d40e754a。切り戻し基準はui-v5-details205-20261009。build_ui_rollback.pyで現行データを維持し、別候補で検査後に明示公開する。旧UIには生成専用表示/検索がないことを確認する。全件入力取得はworkflow009、stdout/stderr-workflow-009.logとworker.lock、state.jsonで確認する。再開前にPID/ロックを必ず照合し、稼働中の重複起動をしない。


### 2026-10-09 256件版での停止

現行原本は指定Driveの基礎r7/詳細r8、15タブ、1466基礎/256詳細(P126/S130)/3685項目。private/sheets-connection.jsonが現在の接続、旧206はバックアップ。UI v7/詳細d1-471997dafba126df、40ファイル、基礎v1不変。切り戻し基準ui-v6-details206-20261009は256データを保持して検証済み。UI v6にはランダム候補の専用表示/検索がない。

今回の上限は256件。全件取得をSTOPで停止し、最終監査/ロック解放/保存入力不変を確認して引き継ぐ。再開指示があるまでclear-stopや追加採用を実行しない。statusのshared_url_pagesは共有URL数28で、派生対応の未完了数ではない（84カードは対応済み）。旧キーshared_url_pages_needing_variant_mappingは過去の表示名で、古いジョブ報告に残る場合がある。


### 2026-10-09 256件版の公開完了

ローカル保存制限はユーザーが明示解除済み。現行公開はUI v7・詳細256件/3685項目/d1-471997dafba126df、基礎1466/v1-93a6a8b8d40e754a不変。公開010f5b7/Actions37910476569成功、匿名40ファイル・PC/390/320操作を確認。切り戻しタグui-v7-details256-20261009はorigin保存済み。旧UI v6へはui-v6-details206-20261009とbuild_ui_rollback.pyで現行データを維持する。

取得は224保存/残1139で停止しSTOP保持。公開許可の解除によって取得や256件超の採用を自動再開しない。次回は採用上限/取得再開の指示を確認してからHANDOFF末尾の状態照合を行う。


## 256件上限解除後の原本（2026-10-09）

最新指示で256件上限を解除し、正式原本は基礎r7/1466不変・詳細r9/282P136S146/4138へ更新。現在の原本URLはprivate/sheets-connection.json。旧256原本とXLSX/接続/siteバックアップは保持。取得011は残1139を有限予算で継続し、成功済みは再送しない。60秒以上、実HTTP失敗/Retry-After停止、単一workerと共通ロックは維持。取得中の原本への自動採用はない。

次の採用は新しいstate凍結と候補監査、現在native原本のfresh export、prepare_detail_adoption.py、native全コピー、全値照合を繰り返す。今回の旧256計画を再適用しない。書込結果不明時はprivate/details/sheet-write-after256-checkpoint-20261009.jsonを確認し実値を読んでから判断する。空のUI_BASE_URLはローカルブラウザ試験として動作する。公開URL確認の最新結果はdocs/verification.mdとHANDOFF.md末尾。


## 282件版の公開確認完了（2026-10-09）

準備7a5d3e5、公開9e1a7ac、タグui-v7-details282-20261009、Actions37914739564 success。匿名公開URL42/42ファイルがsiteと生バイト一致。PC1280/390/320の基本・詳細検索/フィルター/並替、MB/生成/ランダム、最高Lv欠損、JSON版/SHAと取得、横はみ出し/見出し間隔PASS。原本r9/282P136S146/4138と公開d1-6595cad90a13ca0bは一致、基礎1466/v1版不変。private/audits/detail282-public-verification-20261009.json、ui-v7-details282-public-20261009参照。

256件上限は解除済みで取得011は継続中。次の取得済み入力からafter282-next-frozen/after282-next-candidate-20261009を独立変換中。後続候補の採用はfresh native原本から行い、全件版完成とはしない。


## 詳細298件・UI v8（2026-10-09）

原本は基礎r7/1466不変・詳細r10/298P141S157/4418。現在のURLはprivate/sheets-connection.json、旧282原本/XLSX/接続/siteを保持。詳細d1-01d9d4aba38f5334。思い出Link/チャージの参考数値、最大倍率を分けて表示・検索し、未構造化を効果なしと扱わない。原本を再取得・再構築した変更ではない。

UIだけ戻す場合はui-v7-details282-20261009タグとbuild_ui_rollback.pyを使い、現在の298データを維持する。旧UIには追加効果と最大倍率の専用表示・検索はない。全幅基本/詳細の切り戻し候補検証済み。原本/データまで戻す必要がある場合は自動で上書きせず、最新の手編集を保存し旧282バックアップとの差分を確認する。取得011と採用/公開は別工程で、旧256/282採用計画を再送しない。


UI v8の変動倍率対応後は詳細d1-45ed170d94366826。原本r10/298は不変、配布変換だけを更新。直前44ファイルとnative原本は保持し、46ファイル版の検証結果はHANDOFF末尾。更新時には最大/変動倍率を固定値として手入力し直さない。

## 2026-10-09 319件原本・公開候補と298件修正版の公開確認

298件UI v8変動倍率修正版は8a4ceac/5c1bb5f、Actions37917797482 success、匿名46/46ファイル一致、PC1280/390/320基本/詳細・思い出Link/チャージ/実Housekeeping範囲検索PASS。旧UI v7へ戻す候補でも298件と最新詳細d1-45ed170d94366826を保持して同3幅の基本/詳細操作PASS。証拠はprivate/audits/detail298-range-public-verification-20261009.jsonとui-v7-rollback-from298-range-20261009。

次のfrozen state795/263保存ページ・候補3ca632d4a0128b004cf1c10b40d4ed118e0cdacef1f6a7f38986db800d145efaから319カードP144/S175・4796項目を採用。298原本をfresh exportして計画入力/active原本と全値一致、指定アカウントでnative全コピーへ20バッチ（元69バッチ/103 requestsと同じ順序、90KB未満）を書き込んだ。全値読戻し一致、基礎9タブ差分0、旧4418固定ID/手修正保持、元298の更新時刻10:11:35.968UTC不変を確認後、原本接続とmaster.xlsxをr11へ切替。追加378出典URL/実リンク一致、書込14092セルの書式/validation/chips/数式と6タブのフィルター範囲をAPI確認。旧298 native/XLSX/接続/siteバックアップを保存。詳細はprivate/audits/detail-native-319-roundtrip-20261009.json、native319-format-and-links-20261009.json、private/details/sheet-write-after298-checkpoint-20261009.json。

UI v8・基礎v1-93a6a8b8d40e754aは不変、詳細候補d1-5c20f6531f1c8fb1、48ファイル。旧46ファイルの変更はindex.htmlとdetails/latest.jsonだけで旧不変データは全バイト保持。319候補PC1280/390/320の基本/詳細・思い出Link/チャージ/変動倍率/MB/生成/ランダム/最大Lv欠損/JSON版・SHA/横はみ出しPASS。コード変更なし、直前のPython134/JS24 PASSを使用。319公開Actions/匿名48ファイル/公開画面は後続へ記録し、298公開確認と混同しない。

取得workflow011は残全件へ通常60秒以上/1ページ・実HTTP失敗/Retry-After停止で継続する。256/298/319を上限にはしない。取得終了時の自動処理は保存入力からの候補監査までで、原本への追加採用/公開は別工程。未完了は全件詳細取得/採用・複合効果/条件の全面構造化・公式独立網羅・基礎新規実在カード1追加/修正の本番反映実証・日付56・リンク47ユーザー保留・実機/スクリーンリーダー全面検証。Google画面外観はCUA起動不可のため未確認、XLSXの代替表示を確認中。原本/公開の整合性障害や新しいWiki HTTP失敗は確認していない。

319件公開準備の補足: scripts/export_detail_sheet.pyのHTML読書きをbytes経由へ変更し、Windowsでも既存の改行コードを保持する。再生成を実行し、旧HTMLから詳細版文字列だけ置換したバイト列とcandidate/active HTMLが完全一致することを確認。新依存はない。表示検証用にはCodex依存バンドル26.1007.11041のArtifact Toolでnativeエクスポートの読み取りを別privateディレクトリで実行し、原本の値/書式を書き換えない。

## MB補足表と生成技能脚注（2026-10-09）

P【Scene With You】の既知[MB]ランダム効果付与2行表を非公開監査ノートへ分け、生成技能名の厳密なWiki脚注要素だけを照合対象から外す。未知のMB表・不正な脚注・欠落は引き続き検出する。原HTML/セル位置/効果本文を保持し、説明の条件・パッシブ強化効果は全面解析済みとしない。実MB2/生成2/説明2、旧345候補不変、frozen876構造保留0、Python136 PASS。原本319/4796と公開d1-5c20f6531f1c8fb1は変更しない。取得011を保存境界で終了し、全入力/原本/公開の保護ハッシュ維持とロック解放を確認後、残全件を012で再開。354/5405は次の未採用計画。


2026-10-09現在の原本: 基礎r7/1466、詳細r12/397(P168/S229)/6179項目。接続はprivate/sheets-connection.jsonを使う。旧319原本・master-r7-details-r11-before397-20261009.xlsx・sheets-connection-before397-20261009.json・site-details319-before397-20261009を保持。取得012終端監査にcheer+の構造保留が残った場合は、保存入力を最新scripts/transform_detail_catalog.pyで再変換する（再取得不要）。採用/公開はfresh native exportから別工程で行う。


2026-10-09現在の原本は基礎r7/1466、詳細r13/420(P175/S245)/6578項目。旧397はmaster-r7-details-r12-before420-20261009.xlsx、sheets-connection-before420-20261009.json、site-details397-before420-20261009とnative原本を保持。UI v9からui-v8-details397-20261009へ戻す場合も420データを保持できることを3幅で検証。旧UIは複数生成元を先頭だけ表示し生成元検索を省く。原本を編集するときは常にprivate/sheets-connection.jsonの現在URLを使う。


## 2026-10-10 大きい詳細更新のバッチ記録

631件候補では元458小バッチ/642requestsを、順序を維持して152バッチへまとめ、25件のACK済み境界から残りを4バッチずつ最大340KBの関連グループで実行した。分割単位は原本への採用件数上限ではない。コピー先だけへ、基礎9タブを変更せず詳細6タブの内容/行数/新行書式/フィルター範囲を更新する。通常のprepare_detail_sheet_requests.pyは小さいバッチを出力し、API実行の直前に再編成する場合も順序・全request一致を検査する。

書込前にcheckpointへ対象範囲を記録し、API成功応答の後にACKを保存する。グループ結果が不明ならその範囲全体を未確認として扱い、実セルと計画を比較する。前半だけ成功したと推測しない。未知の応答を盲目的に再送せず、完了範囲の再書込/二重起動を避ける。全値読戻し、元の原本変更有無、旧ID/手修正と基礎タブ保護、出典リンク/全書込セルのnative構造、候補のPC/スマホ表示を確認してから接続を切り替える。

取得worker012は開始時のコードを使用する。今回の旧上限UP+表記、MBランダム4行一覧等を終端監査が構造保留とした場合は、最新版transform_detail_catalog.pyで保存入力をオフライン再変換する。取得やゲートの失敗と混同せず、保存済みHTMLを再取得しない。


## 2026-10-10T01:21 JST 公開確認完了・次の工程

631件(P264/S367)・10405項目・原本r14、UI v9・詳細d1-c4c54f3692bd4473を公開確認済み。準備b4bde4e、公開be82002c22506a1b11412754b841ab4b01b59565、タグui-v9-details631-20261010、Actions37957724500 success。匿名54/54ファイルがsiteと生バイト一致。公開PC1280/390/320の基本/詳細・MBランダム選択肢表示/検索・通常技能への非混入・複数生成元・JSON版/SHA/欠損表示PASS、公開320pxのMB画像を視認。631データ保持のUI v8切戻し候補も3幅PASS。private/audits/detail631-public-verification-20261010.json参照。

Googleの後続エクスポートでmtime16:10:24.240UTCとZIP包装差を観測したが、全15タブ実値・詳細セル書式/フィルターが同一で、意味ハッシュ72dfd5ef40cf814b919bcb21becfb7798603ce9786c5dffa8d9deb94cd5d7191は不変。最新包装をactive masterへ保存し接続ハッシュ/最終mtimeを更新。途中の読取監査は空filterの文字列化に失敗したが、原本/公開に変更はなく、Noneを許容して書式実体を比較する修正後にPASS。Google実画面はCUA不可、native全値/API確認済み、XLSX代替描画は継続中（保存原本は変更しない）。

後続654件(P273/S381)・10780項目・原本r15予定の計画をprivate/details/after631-adoption654-20261010へ保存。fresh native631 exportとactiveの全15値・書式一致から作成。入力master hash72dfd5ef40cf814b919bcb21becfb7798603ce9786c5dffa8d9deb94cd5d7191、候補hash478350d08ef199bcae793f9d1a419f380f5bf4b2f612ba5be1d7910bea07e735、出力hash77bdb7f1d6d5ea44cecd55a31fafe6c61e3d690616f88287fbdcc36f2b0eef8c。追加23カード/375項目、10405旧ID/手修正保持、構造保留0。654は未採用・未公開。取得済み入力はさらに増加しており、654を上限にせず次のバッチを最新frozenから広げてもよい。

取得012/worker29464/launcher28492は稼働を維持。2026-10-10T01:20:42JST時点state1865、619保存ページ(新規614/再利用5)/1363、pending744、active_attemptなし、stderr0、STOPなし。60秒以上/1ページ、実HTTP失敗/Retry-After停止、共有ゲートは不変。取得終了後の旧コードによる構造保留は最新の保存入力再変換で確認し、HTMLを再取得しない。原本/公開への自動採用はない。

次操作：取得012のPID/state/locks/active_attempt/logを実照合し二重起動しない→現在nativeのfresh exportと次計画input hash照合（変われば手修正を保って再計画）→詳細だけを書き込むnative全コピー→全値/基礎9タブ/旧ID/override/全書込セル/出典/フィルター確認→別site候補/PCスマホ/旧版保持→原本切替/publish/Actions/匿名確認。631登録checkpointはprivate/details/sheet-write-after420-checkpoint-20261010.jsonで全152相当ACK・unknownなし・published=true。原本/公開の破損、データ欠落、新たなWiki HTTP失敗は確認していない。

未完了：全件詳細取得/原本採用/公開、効果・条件の全面構造化、公式独立網羅、基礎新規実在カードの本番追加/修正実証、日付不明56、全面実機/スクリーンリーダー確認。個別リンク47件はユーザー指定で保留。Pステージ/適正・Sファイトは今回収集対象外。ユーザー操作待ちはなく、取得は継続中であり、安全停止やプロジェクト完成としては扱わない。


## 2026-10-10 拡大版の運用確認

詳細1293カード/21868項目・r15をnative全コピーで採用し、公開d1-b89ba62ab2260b7d/UI v9を匿名56ファイルと3幅で検証した。原本の現行ID/URL・旧631backup・export・全write checkpointはprivateへ保存。編集前はprivate/sheets-connection.jsonのspreadsheet_urlを確認し、古いリンクや過去の停止記録を現行指示として使用しない。今回の359バッチは全ACK/unknownなし。必要な修復は未知範囲の実読戻し後に限定し、成功済みの要求を無条件に再送しない。新規範囲の85KB判定はupdateCellsの行ラッパー/座標を含む実UTF-8オブジェクト全体で行う。詳細原本の複製・検証・昇格と公開は別工程とし、Wikiの取得中stateを原本へ自動反映しない。

## 2026-10-10 全個別ページ分の取得完了後

現在の基礎は1466件、詳細は1419件・r18。編集するSheetはprivate/sheets-connection.jsonのspreadsheet_urlで確認し、古いバックアップへ書かない。取得runはcomplete・workerなし・active_attemptなし。全1363保存ページを再利用でき、新しいWiki通信は通常の詳細再変換に不要。

保存入力からやり直す場合は、scripts/transform_detail_catalog.py private/raw/detail-catalog-20261009 private/audits/<新しい候補名>.jsonを使い、正式原本や旧候補を上書きしない。全件1419候補・47保留を基準に、構造例外・件数・旧値/固定ID/手修正を確認する。古いworkflow-report.jsonは稼働時コードの監査履歴で、正式公開結果は同runのlatest-verified-publication.jsonとdocs/verification.mdを読む。

原本への追加・修正は前述の編集列と根拠・日時を使う。fresh exportをreview/applyし、基礎と詳細を同じエクスポートから新候補へ生成→check_site→PC/スマホ検索→不変版保持→明示公開→匿名確認。検証前に現行原本/サイトへ上書きしない。再取得結果の採用もnative全コピーへの差分登録から始め、元Sheetを保持する。現行版のタグはui-v10-details1419-20261010。UIだけの切戻しではbuild_ui_rollback.pyに現行siteをsourceとして指定し、データを古い版へ戻さない。


## パッシブ発動条件の更新・切戻し（UI v11）

発動条件は原本のパッシブ effect_private の有効値から公開時に導出する。生成JSONや activation_condition を直接編集しない。訂正は既存の手修正列に理由・出典・日時を付け、fresh exportをreview/applyする。未知の表記は未対応のまま保存され、公開からカードを落とさない。複合条件の一部だけを単純条件として登録しない。

原本を変えない公開変換の改善も、旧siteを保存して別の候補ディレクトリへUIを配置し、scripts/export_detail_sheet.pyで詳細を生成する。check_site、Python/JS試験、3幅の基本/詳細検索、旧データ/固定ID/手修正保持、同じデータの旧UI切戻しを確認してから昇格する。発動条件の対応数はcoverage.activation_condition_countsにあり、旧バンドルにはこの任意フィールドがない。

UI v10への切戻しは scripts/build_ui_rollback.py --ref ui-v10-details1419-20261010 --source site --output private/<新しい切戻し候補> を使う。条件フィルターと条件表示は旧UIにないが、現行の基礎・詳細版と配布を保つ。候補を3幅で検証した後にsiteへ昇格し、通常のpublishコミット・Actions・匿名URL照合を行う。条件だけを元に戻す場合も旧不変ファイルを上書きせず、版の組を検証する。


## UI v12の複合条件と切戻し

activation_condition_v2も原本の有効effect_privateから自動導出する。配布JSONを手編集しない。訂正は従来どおり原本のoverrideと理由/出典/日時→fresh export→review/apply→別候補生成→検証→公開。曖昧な名前だけの条件は未対応として保持する。検索集計はactivation_condition_search_counts、旧UI互換集計はactivation_condition_countsを使う。

UIだけをv11へ戻す場合はbuild_ui_rollback.py --ref ui-v11-conditions-20261010 --source site --output private/<新しい候補>で現行データを保つ。旧UIは拡張491項目を未対応と表示し、従来の条件4946項目は引き続き検索できる。原本や新不変版を消さず、3幅検証→publish→Actions→匿名版/全ファイル照合まで行う。
