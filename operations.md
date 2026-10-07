# 管理者の操作手順

## 現在の原本

暫定原本は`private/master.xlsx`です。指定されたGoogleアカウントにはブラウザでログインでき、Driveの空き容量と書込権限を確認しました。Google Sheets原本の作成・全タブ読戻しは未完了です。Chrome拡張のファイルアクセス設定はユーザーが有効にしましたが、ブラウザ操作環境の起動障害で再試行できていません。以前の別アカウントではDrive容量超過とSheets権限不足を確認しました。
CSVを原本へ切り替えていません。指定アカウントで認証・書込権限を確認後、この完全XLSXをGoogle Sheetsへインポートし、全タブと非公開共有を確認してから原本の所在を切り替えます。二つを同時編集しないでください。
Google側への作成に成功していないので、現時点のXLSXは「Sheetsからの取り出し」ではありません。以前の別アカウントでは空のnative Sheet作成もSheets APIの403 `PERMISSION_DENIED`で失敗しました。指定アカウントのDriveには非公開フォルダーを作成できていますが、native Sheetの書込みは未確認です。

## 追加・修正

1. `private/master.xlsx`をバックアップし、Excel等で開く。更新処理中は閉じる。1人で編集する。
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

```powershell
./.venv/Scripts/python.exe -m src.indexer prepare private/master.xlsx dist
```

prepareで入力エラーが出たら原本を修正する。WebやCSVを直接修正しない。
正常なら表示された版の`dist/data/<版>/manifest.json`とWebを確認する。
同じ公開内容を再prepareしても版は変わらない。編集の自動公開はしない。

## 少数取得と再変換

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
Pagesでの実復旧は公開済みだが未検証。Actions一時artifactだけを長期バックアップにしない。

## GitHub Pages公開・更新手順

1. ユーザー所有の公開リポジトリと無料の標準ランナーが使えることを確認する。
2. sources-policy.mdの現行公開方針とWIKIWIKIの禁止事項を確認する。問い合わせはユーザーが別途行う。回答や条件変更が届いたら公開範囲・収集手順を再評価する。公式全網羅の限界を表示する。
3. コードの公開対象を明示的に選ぶ。private、node_modules、.venv、認証情報を含めない。
4. `./.venv/Scripts/python.exe scripts/stage_release.py dist site`で初回の公開候補を新しい`site/`に作り、`./.venv/Scripts/python.exe scripts/check_site.py site`で検証する。`dist/`の過去の試作版は同梱しない。2回目以降は新しい`site-next/`へ`--previous-site site`を指定して作り、検証後に既存の`site/`をバックアップして入れ替える。ステージング先を既存フォルダーへ重ね書きしない。
5. ユーザーの公開指示とsources-policy.mdの範囲で`source_manifest.json`の公開フラグをtrueにする。`check_site.py site`成功後、無視対象の`site/`を`git add -f site`で明示的に追跡対象へ加える。コードとともにコミット・pushし、リポジトリSettings → Pages → SourceをGitHub Actionsにして同梱pages.ymlを手動実行する。private/と生応答は追加しない。
6. 公開URLを未ログインで開き、検索、CSV/XLSX/JSON取得、manifestの版とハッシュを照合する。
7. 1件追加・1件修正を新しい版として公開し、反映を確認する。その後旧artifactへの切り戻しを実証する。

未確認状態を隠すためにcoverage.completeをtrueへ変更しない。公開できることとゲーム全網羅は別の条件。

### 現在の公開状態

公開URLは https://vignoles.github.io/shiny-index/ 。Actionsの公開ワークフロー実行は成功し、匿名GETでHTML、latest、manifest、JSON、CSV、XLSX、coverage、sourcesの8ファイルがローカルsiteとバイト一致した。最初の失敗はGitの自動改行変換によるcards.csvのハッシュ不一致であり、.gitattributesのsite/** -textで修正した。今後の更新ではsite生成・check_site・Git blobの一致を確認してpushし、Pages workflowを手動実行する。更新・復旧の公開URLでの実演はまだ行っていない。


## Google Sheets原本をXLSXとして取り出す運用

指定アカウントの非公開Google Sheets原本への移行が完了した後に使う手順です。現時点ではSheet作成と実エクスポートの検証が未了なので、ローカルXLSXを暫定原本とします。Sheetの「追加・手修正」だけを編集し、他の8タブを変更しないでください。更新の配布前に編集を止め、同じSheetをMicrosoft Excel形式でダウンロードして `private/sheets-exports/<日時>.xlsx` へ保存します。公開リポジトリに入れません。

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
