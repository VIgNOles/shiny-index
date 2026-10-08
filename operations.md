# 管理者の操作手順

## 現在の原本

編集原本は、指定されたGoogleアカウントが所有する非公開Google Sheets「enza P/S card master」です。SheetのURLとIDはGit対象外の `private/sheets-connection.json` に記録しています。所有者だけがアクセスできること、9タブ・1,466件・固定ID・取得値・手修正の往復一致、タイムゾーン Asia/Tokyo を確認しました。

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

ユーザーは過負荷を避けた再開を指示した。7ページ連続取得と直接のcollect CLIは停止したまま。単一ページ用CLIのみ、前回の取得または429から24時間以上経過し、排他ロックがなく、新しい保存先を指定した場合に利用できる。この24時間は慎重な運用上の下限であり、Wiki側が許容した頻度という意味ではない。1回につき許可リストの1ページだけ、robots.txtの確認と対象ページ取得のみ行い、自動リトライはしない。429・503時のRetry-Afterが24時間を超える場合は長い方まで待つ。403・確認画面・429・503・形式異常では停止し、繰り返し試さない。

    ./.venv/Scripts/python.exe scripts/collect_one.py status
    # 新環境に状態ファイルがないときだけ、initで24時間の待機を開始する
    ./.venv/Scripts/python.exe scripts/collect_one.py init
    # statusのcan_fetchがtrueになってから、未使用の保存先で1ページだけ手動実行
    ./.venv/Scripts/python.exe scripts/collect_one.py fetch W09 private/raw/limited-W09-YYYYMMDD

既存のprivate/raw/acquisition-state.jsonには前回429時刻を記録済み。statusとinitは通信しない。fetch後はfetch.jsonとlimited-run.jsonを確認する。limited-run.jsonのfull_run=falseは全件取得runではないという意味であり、full_transform.pyの全件入力には使わない。前回保存済みHTMLとのオフライン差分を見ることはできるが、ほかのページを当日確認したとは扱わない。原本・公開版を更新する前に、対象ページと全件候補の整合性を別途確認する。途中終了でacquisition-state.lockが残った場合は、実行中プロセスと状態ファイル・保存先を確認してから解除し、前回試行からの待機を守る。

WIKIWIKIの[確認画面の案内](https://wikiwiki.jp/pp/security-check-guide)は短時間の多ページ閲覧による再確認を説明している。[REST APIの説明](https://z.wikiwiki.jp/wikiwiki-rest-api/topic/1)では対象Wiki側のAPI許可設定と認証が必要。APIの公表レート上限を通常HTMLの許容頻度として流用しない。管理者・運営から個別の条件が示された場合はそれを優先し、取得方法を見直す。

単一ページ保存後の通信なし比較例：

    ./.venv/Scripts/python.exe scripts/compare_saved_page.py private/raw/recheck-20261007-2/gacha private/raw/limited-W09-YYYYMMDD

この比較は応答ハッシュ、Wiki本文の可視テキスト・本文リンクの一致と、差分件数・最大10件の例を示す。差分0でもほかの6ページや公式全件が新たに確認されたことにはならない。

## 今回の完成条件の更新（2026-10-08）

Wiki管理者・運営への問い合わせと回答取得は、ユーザーの明示指示により今回の必須工程から除外された。過去の問い合わせ案内は履歴であり、これを理由に作業を止めない。Wiki取得は429後の24時間待機を守り、次回可能時刻に単一ページから続ける。ユーザー本人がスマートフォンで基本動作を確認済み。未詳のUI不満点は後からの指摘に基づき直す。


## 2026-10-08の確認結果と現行原本

現在の編集原本は指定Googleアカウントの非公開native Sheet「enza P/S card master r7」。ローカル承認済みスナップショットはprivate/master.xlsx、revision 7、1,466件。r6 Sheetとr6 XLSXはバックアップとして保持する。現行の取得状態は `./.venv/Scripts/python.exe scripts/collect_one.py status` で確認し、W09の一度限りの期限前確認後は通常の24時間ゲートに戻った。同じ `--user-authorized-early-fetch` は状態記録により再使用できない。次回以降はstatusのcan_fetchがtrueになるまでWikiへ送信しない。既存の429 runはincompleteのまま保存し、二つの取得runを組み合わせた今回の候補はprivate/raw/composed-20261008-user-early、変換候補はprivate/candidates/composed-20261008-user-early-v2に隔離した。

再実行する場合は既存runを上書きせず、`RAW_RUN_ROOT=private/raw/composed-20261008-user-early`、`TRANSFORM_OUTPUT_ROOT`に新しい保存先、`TRANSFORM_SEED_ROOT=private`、`TRANSFORM_SCOPE=full`を設定してscripts/full_transform.pyを実行し、review_batch.pyで原本と比較する。差分0ならカード行の変更を作らない。配布候補はrevision 7から生成したv1-93a6a8b8d40e754aで、カード・出典は前版と一致し、収録対象日の確認範囲のみ2026-10-08へ更新した。全ゲーム網羅のcompleteはfalseを維持する。
