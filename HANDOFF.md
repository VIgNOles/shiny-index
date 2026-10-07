# 現在の状態と再開手順

更新日：2026-10-07 JST。元の実装依頼は継続中。完成ではない。

## 現在の工程

全期間Wiki一覧のローカル収録・Web/配布生成まで進んだ。公開条件の確認、Google Sheets原本の移行、GitHub Pages公開・匿名検証は未完了。ユーザーは以前の一時停止を解除して再開を指示した。

## 実際に確認した状態

- Gitローカルブランチmain、初期実装コミット `8082378`。再開後の変更もローカルコミットとして保存（最新は`git log -1`で確認）。GitHubへのpushは認証がなく失敗し、ユーザーはその時点でローカル保存を選択。再開時の作業ツリーに差分はなく、その後の変更を追加した。design.mdは.gitignore対象でローカルに保持。
- `private/master.xlsx`は1466行、採用revision 5。`dist/data/latest.json`は `v1-f94ad2056247a4ef`。index.htmlと同じ版。旧版も保持。
- 2026-10-07の読み戻しで、dist内の1466行版3つと9行版1つのJSON/CSV/XLSX/manifestをすべて検証成功。古い試作版はprivate/legacy-prototypesへ保存。
- 元のdesign.mdを読んで実装し、変更理由と制約を17章へ追記済み。TASK.mdとHANDOFF.mdは停止中断時には未作成で、再開後に会話と実状態から作成した。
- 再開時点で実行中のデータ更新は見当たらなかった。localhostプレビューのPython http.server（4173/4174）は残っている。停止指示は再開により解除済みだが、公開サービスではない。

## 完了事項

- 少数9実例で取得→原本→Web→JSON/CSV/XLSXを接続後、WikiのP/S一覧、S分冊、コラボ、ロード、追加順を保存しオフライン全件変換。
- 一覧1771掲載行のうち引用重複361を除き1410基礎カード、ロード派生56を追加し1466索引行。P548、S918。日付不明56、Wiki未掲載47。分類未確定21行はW02/W03/W09から解消した。ゲーム全網羅を主張していない。
- 固定ID、明示的手入力統合、手修正優先、型/重複/件数異常の検出、版付きデータとrollback、PC/390px幅の検索・絞り込み・並べ替えをローカル実装。
- 実カードの8→9件追加と1件の確認状態修正、Web表示・配布反映、再取得との統合をprivate/drillで検証。
- 元のローカルコード23ファイルはコミット8082378に保存。再開後の再現性・安全性変更もローカル保存。原本・生応答・配布データはGit対象外。

## 未完了・問題

- Google SheetsインポートはDriveの403 storageQuotaExceeded。現在の原本は完全タブ構成のローカルXLSX。容量解消後の移行とAPI同期が必要。
- Wikiへのヒアリングは未実施。ユーザー方針は「作成後許可を得る」。source_manifest.jsonの公開配布フラグはfalse。一般公開URLはまだない。
- 指定GitHubリポジトリは公開・空、Pages未設定。pushは認証失敗。ユーザーは前回「今回はローカル保存まで」と回答。勝手に認証情報を探さない。
- ロード派生初回日56、ゲーム全網羅・公式照合、新しい特殊表記の継続監査、公開済み重複IDのredirect統合、HTTPリトライ/ETag、Artifact Toolの任意環境での入手は未確認。`XLSX_BACKEND=stdlib` の代替出力は全件照合済み。
- 初期のcredential-manager列挙コマンドは自動承認レビューにより不要なcredential probingとして拒否された。同方式は再試行していない。
- 再開後、標準ライブラリXLSX経路、7ページ逐次取得CLI、RAW_RUN_ROOTによるオフライン再変換を追加。取得runは開始時と各ページ後に進捗記録を残す。新runでは隔離出力先を必須とし、異なる既存候補の上書きを防ぐ。観測日は保存応答の取得日時をJSTへ換算。前回の再現性検証では元原本を変更せず、全件配布・完全原本の読み戻し、1466件の再変換一致を確認。今回はW09を追加し、21行だけ分類を更新した。
- 通常サンドボックスexecは`helper_unknown_error: setup refresh had errors`で失敗することがある。承認済みの拡張実行で作業した。意図的な環境・権限変更はしていない。

## 変更ファイルと私的成果物

- 実装：`src/indexer.py`、`src/xlsx_fallback.py`、`scripts/`、`web/`、`tests/`、`.github/workflows/pages.yml`、`source_manifest.json`、`requirements.txt`。
- 手順・検証：`README.md`、`operations.md`、`sources-policy.md`、`docs/verification.md`、`design.md`17章、`TASK.md`、`HANDOFF.md`。
- 非公開：`private/master.xlsx`、`private/raw/`、`private/full-batch.json`、`private/full-audit.json`、`private/candidates/classification-20261007/`、`private/drill/`、各バックアップ。Gitへ追加しない。
- ローカル公開候補：`dist/`。一般公開許可が未確認なのでGitへ追加しない。

## 実施済み検証と未検証事項

- Python単体8件、JS検索8件が成功。再変換1466件の既存候補・新規隔離出力で一致し、新runの出力先省略は変換前に停止。標準ライブラリ経路の完全原本XLSXは1466件の有効値・revision 4が一致。配布済み4版はcheck_siteで全形式読み戻し成功。構文検査・git diff --checkも成功。1万行の検索関数はPC Nodeで約150ms。実スマホ端末・DOMを含む性能は未検証。
- PC/390pxブラウザで検索、P/Sフィルター、レアリティ昇順、全角半角、日本語シリーズ検索、100件追加表示を確認。匿名の公開URLでは未検証。
- 全版のJSON/CSV/XLSX論理値・版・件数・ファイルハッシュは読み戻し成功。Google Sheets反映とPagesでの公開・更新・rollbackは未検証。

## 再開時の具体的な次の操作

1. `git -c safe.directory='D:/THE IDOLM@STER/シャニマス/enza/index' status`、`private/master.xlsx`の読み戻し、`dist/data/latest.json`と`index.html`の版一致を確認する。結果不明の処理を推測で再実行しない。現ホストではGit所有者SIDが異なり、コマンド単位のsafe.directory指定が必要。
2. TASK.md、HANDOFF.mdと実状態を照合し、必要な補正を記録する。
3. 新runは`scripts/collect_all.py private/raw/<新run>`で7ページ取得し、`RAW_RUN_ROOT`と新しい`TRANSFORM_OUTPUT_ROOT`、`TRANSFORM_SCOPE=full`を指定して`scripts/full_transform.py`を実行する。候補を監査し、原本採用時は既存キー・件数を照合して変化があれば保留する。
4. Google Drive容量の解消と接続先のSheets作成・書き込み権限の確認後に完全XLSXを非公開Google Sheetsへ移し、タブ・手修正・IDの読み戻しを検証する。
5. Wiki管理者/運営から取得・CSV/JSON/XLSX配布条件を確認する。ユーザーが後で許可取得予定。回答前に一般公開のフラグをtrueにしない。
6. 公開条件が整いGitHub認証が利用可能になったらコードをpushし、完成バンドルをPagesへ配置。匿名ブラウザで版・検索・ファイル取得を検証し、公開での1件追加・1件修正・rollbackを実証する。

元のユーザー指示を勝手に縮小しない。ローカル収録の完了をプロジェクト全体の完成と扱わない。

## 2026-10-07の続行結果

- W09ガシャページをrobots確認後に1件取得し、生応答・取得記録・SHA-256を`private/raw/gacha/`へ保存。Wiki一覧の凡例と合わせて未確定21行を分類。取得・変換・採用は別工程。
- 隔離候補1,466行のキー・原本ID集合・手修正を採用前に比較し、差分が21行の入手区分・シリーズだけと確認。原本バックアップ後、revision 5を読み戻し。新しいWeb・配布版は`v1-f94ad2056247a4ef`。
- ブラウザでAXE8の3行、投票企画選出の14行、版と出典表示を確認。Python8件、JS8件、distの4版の全形式検証が成功。公開URLはない。

- 7ページ逐次再取得CLIを実地実行。run.jsonは全件fetched、7応答のSHA-256は前回と同じ。新runからのオフライン再変換は候補・監査とも完全一致し、同一runを再適用しても原本revision 5のまま。新runは`private/raw/recheck-20261007-1/`、隔離候補は`private/candidates/recheck-20261007-1/`。
- READMEの少数例を隔離原本・隔離表示先へ修正し、全件原本を誤更新しない手順にした。TASK.mdに最新の続行指示を追記。保存前の再検証で原本revision 5／1466件、latestとHTMLの版一致、Python8件、JS8件、配布4版の全形式検証が成功。

- 同日、revision 5の完全XLSX（1,057,337 bytes）を非公開Google Sheetsへ再インポートしたが、Driveは再び403 `storageQuotaExceeded`を返した。同名のDrive検索も0件で、Sheet作成は未成功。容量解消後に再試行し、全タブ・ID・手修正の読み戻しが必要。
- READMEの隔離した9件採用とWeb/配布生成を実行し、`private/examples/sample-master.xlsx` revision 1／9件、`private/examples/sample-site`のJSON/CSV/XLSX照合が成功。全件原本はrevision 5／1466件、全件latestは`v1-f94ad2056247a4ef`のまま。試作成果物はGit対象外。

## 2026-10-07の追加続行

- 原本の「取得候補」タブが読み戻しで捨てられる不具合を修正。保存時の読み戻し比較を解決済みカードだけから、原本の全構成要素へ広げた。合成候補と手修正を含む回帰テストを追加し、Python9件成功。
- revision 5／1466件の実原本を`private/audits/master-roundtrip-20261007.xlsx`へ隔離保存し、全状態の読み戻しが成功。出典21853行、取得履歴5行。元の`private/master.xlsx`と`dist/`には変更を加えていない。
- 実データを基にした失敗・1件欠落・20件増加の候補はすべて採用前に停止し、原本内容と最新配布版のハッシュを保持。結果は`private/audits/failure-drill-20261007.json`。公開先の復旧検証、Google Sheets移行、Wiki配布条件、Pages匿名検証は引き続き未完了。

- 公開成果物検証を厳格化し、余分なファイル・不正latest・分割JSONとcards.jsonの差異を拒否する。合成テストを含むPython11件、既存dist4版の再検証が成功。
- `scripts/stage_release.py`を追加。ローカル`site/`には最新の1466件版`v1-f94ad2056247a4ef`だけを隔離配置し、`check_site.py site`成功。9件試作版は同梱していない。`site/`は.gitignore対象でGit・Pagesへ未配置。公開条件解決後の手順はoperations.mdを参照。
- 公式ニュースのenza欄と最近のP2件・S2件を限定照合し、名称・人物・P/S・レアリティが一致。P2件とS1件のシリーズも一致。4件のサンプルであり、公式全件監査や初回日確定ではない。記録は`private/audits/official-sample-20261007.json`。
- Wiki管理者／運営に確認するための未送信文案を`docs/wiki-permission-request.md`へ作成。取得済み7ページ、頻度、配布予定の項目・形式、出典リンク、除外・撤回条件を具体化した。送信と回答の記録、公開フラグの変更は未実施。
- `scripts/review_batch.py`で採用前の差分監査を追加。実際の再取得候補は1466件すべて現行原本と一致し、新規・変更・消失・警告が0。結果は`private/audits/recheck-review-20261007.json`。合成異常の回帰を含むPython12件成功。
- ステージング済みsiteを実ブラウザでデスクトップ幅と390px幅に表示し、1466件、AXE8検索3件、個別Wikiリンク、W03/W09出典、版、JSON/CSV/Excelリンクを確認。実スマホ端末と一般公開URLは未検証。一時ブラウザタブ・4175番サーバーは終了した。

## Google Sheets別経路の再確認（2026-10-07）

- 完全XLSXのDriveインポートは403 `storageQuotaExceeded`のまま。さらに接続済みGoogle Driveのnative Sheet作成APIは403 `PERMISSION_DENIED`（caller does not have permission）を返した。同名ファイルのDrive検索は0件。空Sheetも作成できておらず、原本は引き続き`private/master.xlsx`。容量解消に加え、対象アカウント・Sheets書き込み権限／接続設定の確認が必要。原因を一つに断定しない。勝手に権限を拡大していない。

## 2026-10-07 ユーザー方針更新と現在位置

- ユーザーは一般公開を明示的に許可し、Wikiへの問い合わせは本人が別途行う。旧「回答前に公開しない」方針は更新。WIKIWIKI規約・利用ルール・Wikiコピーライトを再確認し、画像・記事本文・取得HTMLを含まない事実索引と出典リンクのみを公開対象とした。問い合わせ回答・許諾は未取得。
- `ユーザー指定のGoogleアカウント` のDriveを原本に使う希望。既存Connectorの接続先は別アカウント。指定アカウントはGoogleログインのパスワード画面まで進んだが、本人認証待ち。接続先切替と原本移行・読戻しは未完了。暫定原本`private/master.xlsx`は変更していない。
- `git status`は開始時clean、originは指定URL、`git ls-remote origin HEAD`は空リポジトリとして成功。`gh` CLIは未インストール。`scripts/check_site.py site`は1466件・`v1-f94ad2056247a4ef`で成功。公開前の候補・原本は保持。
- 今回、source_manifestと公開方針・設計・操作・検証文書をユーザーの最新指示へ更新中。次は差分・公開候補を確認し、Git pushを通常経路で試す。成功した場合はPagesを設定して匿名ブラウザで検証する。認証不能なら必要なGit操作だけユーザーへ示す。

## 2026-10-07 公開後の現在位置（上記の旧時点記録より優先）

- 全件版1,466行、原本revision 5、版v1-f94ad2056247a4efは維持。GitHub Pages https://vignoles.github.io/shiny-index/ を公開し、未ログイン閲覧・検索・390px幅の表示・8配布ファイルのHTTP 200とローカルsiteとのバイト一致を確認した。
- Actions初回はGit自動改行変換でcards.csvハッシュ不一致。site/** -textを.gitattributesへ追加して再実行成功。公開サイトに失敗版は出ていない。
- ユーザー指定GoogleアカウントはChromeでログイン済みと確認し、Driveは15GB中4.96GB使用。ChatGPTフォルダーを新規作成した。完全XLSXのnative Sheetへのインポート、全タブ読戻し、原本の切替は未完了。既存private/master.xlsxを編集・破棄しない。
- 次は指定DriveのChatGPTフォルダーへ非公開の完全XLSXをインポートし、native Sheetsのタブ・件数・ID・手修正を読み戻す。検証完了までXLSXを暫定原本とする。公開URLでの更新・復旧実演も未完了。
- 公開文書内の個人アカウント表記は削除した。旧記録の未公開・ログイン待ちなどは履歴であり、現在の状態を表さない。

## 2026-10-07 再取得とSheets更新経路（現在位置）

- 新run `private/raw/recheck-20261007-2/` の7ページ取得は成功。隔離変換 `private/candidates/recheck-20261007-2/` と監査 `private/audits/recheck-review-20261007-2.json` は1,466件完全一致、新規・変更・消失0、警告0。既存原本・公開版の変更は不要。
- `scripts/import_sheet_export.py` と `tests/test_sheet_import.py` を追加。Python15件成功。隔離した実原本コピーで差分0のレビューと適用無変更を確認。Google Sheetsからの実エクスポートにはまだ使えていない。
- 指定DriveのChatGPTフォルダーは最後に確認した時点では空で、XLSXアップロードは最初にChrome拡張のファイルURLアクセス設定で拒否。ユーザーは設定を有効にした。その後、ブラウザ操作ツールのWindows sandbox helperが起動できない状態が反復し、再試行の成否は未確認。指定Googleアカウントのnative Sheetは未作成。既存の `private/master.xlsx` revision 5 を保持。
- 公開Git履歴内の個人アカウント表記を除くため、自分の直近2コミットをまとめ直した。リモートmainは `75effd1`、変更前HEADと一致を確認してからlease付きで更新。公開サイトのHTML、latest、manifest、CSV、XLSXはその後も手元siteとバイト一致。Pagesワークフローを新HEADで再実行しようとしたところブラウザ操作環境が落ちたため、再実行は未完了。公開中のデータ内容は同じ。
- 次はブラウザ操作が回復したらDriveの指定フォルダーに同名ファイルがないことを確認し、完全XLSXをアップロードしてnative Sheetに変換。全9タブ・固定ID・手修正・共有非公開を読み戻し、実Sheetエクスポートを`import_sheet_export.py review`で検査する。新HEADでPagesを再実行し成功と匿名ファイル一致を確認する。

- 公開GitHub APIの読取ではPages実行は#1失敗、#2成功のみ。新HEADの#3は起動していない。公開中のHTML・latest・manifest・CSV・XLSXは新HEADのsiteファイルとバイト一致。IABの390px一時viewportを戻す操作もブラウザ操作環境の復旧後に必要。

- `scripts/check_public.py`の実行で公開URLの全12ファイルが手元siteとバイト一致。新HEADでのActions再実行はなお未実施だが、現在の公開内容は同一。
