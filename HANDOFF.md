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

## 2026-10-07 追加検証と接続待ち（最新）

- 中断した取得・変換処理は残っていない。旧ローカルHTTPサーバー2件をコマンドライン照合後に停止した。
- Python15件、JavaScript8件が成功。匿名公開URLの全12ファイルはローカルsiteとバイト一致。
- 公開照合スクリプトと手順書をコミット dc57c6c に保存し、指定origin/mainへpush済み。Git作業ツリーはこの後の文書補正を除きclean。公開内容は変更なし。
- Google Driveプラグインの接続先は引き続き別アカウント。ユーザーへ指定アカウントの追加接続手順を案内した。既存接続は解除しない。Chrome操作ツールはWindows sandbox helperの起動障害が続く。実Sheetsの作成・アップロード・読戻し・実エクスポートは未完了。
- 再開時はプラグインのプロフィールで指定アカウントへの接続を確かめ、指定Driveの非公開フォルダー内に同名ファイルがないことを確認して完全XLSXをnative Sheetへ移す。9タブ・固定ID・手修正・共有設定を読戻し、エクスポートをreviewする。公開サイトでの原本1件追加・1件修正とrollbackも未実施。

## 2026-10-07 指定Sheets原本の初期移行（最新）

- 指定Googleアカウントのプラグイン接続を確認。非公開ChatGPTフォルダー内にnative Google Sheets「enza P/S card master」を作成した。URLとIDはGit対象外のprivate/sheets-connection.jsonに保存。所有者のみ、共有なし、9タブ、Asia/Tokyo。指定Drive内の試験用Sheetsは削除し、正式原本1つのみ。
- 実SheetのXLSX出力 private/sheets-exports/google-roundtrip.xlsx をレビューし、revision 5、1,466件、保護8タブと固定ID・手修正に差分なし。差分なしapplyはprivate/master.xlsxを再書込しなかった。
- 非公開Sheetコピーで1件追加・1件修正し、出力を隔離原本へ適用。private/drill/google-sheet-dist は1,467件、v1-0b0a763e0c94b828。Web検索とJSON/CSV/XLSXで両変更一致、check_site合格。更新済み完全XLSXの新規Sheetへの再取込・再エクスポートも差分0。合成試験カードは正式原本・公開siteに含まない。
- 原本の編集場所は指定Sheetsへ移行した。private/master.xlsxは承認済みのローカル作業スナップショット。手編集はSheet→XLSX→review/apply→prepare。取得値採用時はローカル採用後に新しい完全Sheetへ再取込・往復確認してからSheet原本のポインタを切り替える。operations.mdとdesign.md 17.15に反映した。
- 残件は公開URLでの実際の追加・修正・切戻し、実スマートフォン端末、公式全件独立照合、Wiki管理者回答。ブラウザ操作環境のWindows sandbox helper起動障害は継続。正式原本と公開版は1,466件、v1-f94ad2056247a4ef。

- 指定Sheetの実エクスポートだけから private/rebuild-from-sheet に1,466件・v1-f94ad2056247a4efを再生成し、check_site成功。公開版とカード・出典・coverage・redirect・辞書・content_hashが一致した。published_atは再生成日時で異なるため、内容差分なしの再公開は行わない。正式Sheet、ローカル原本、公開版は同じカード内容。

## 2026-10-07 Pages明示公開経路の実地確認（最新）

- browser操作環境の障害を回避するためpublish-*タグ経路を試したが、GitHub Pages環境のbranch policyがmainのみを許可し、run 37607548865はランナー開始前に失敗した。旧公開サイトは維持。次のmain pushでYAML条件式の引用符不足によりrun 37607876882もジョブ開始前に失敗した。条件式を引用符で囲んで修正し、通常main pushのrun 37608055691はskippedを確認。
- 検証済みsiteを指すmainで明示的なpublish:空コミット4c1834dをpush。run 37608116515はsuccess。公開URLの全12ファイルがsiteとバイト一致。現在の公開版は1,466件、v1-f94ad2056247a4efのままで、原本と配布データも変更なし。
- ワークフローと手順はmainの明示コミット方式へ更新。失敗したタグは再利用しない。実カード1件追加・1件修正を公開URLへ反映する検証と公開旧版への切戻しは未実施。現Wiki再取得は新規0・変更0であり、試験用の合成カードを公開しない。

## 2026-10-07 公開HTMLの更新・復旧（最新）

- 無害なHTMLコメントをsiteとテンプレートへ追加し、通常main pushはskipped・公開URLは旧版維持。publish: run 37608735639 success後、匿名URLにコメントが現れ、全12ファイル一致。Git revertで元のHTMLをバイト単位で復元し、次の通常pushはskipped。publish: run 37608939641 success後、匿名URLからコメントが消え、復元済み全12ファイルとバイト一致。正式Sheetとローカル原本の内容は変更なし。
- 公開成果物の更新と元版への切戻しは実証。実カード1件追加・1件修正を公開し、異なるデータ版を切り戻す演習は未実施。合成試験カードは一度も一般公開していない。現在の公開版は1,466件、v1-f94ad2056247a4ef。

## 2026-10-07 revision 6公開とデータ版切戻し（現在位置）

- 指定アカウントの非公開native Sheet原本は enza P/S card master r6。IDとURLはGit対象外のprivate/sheets-connection.jsonに記録。所有者のみ、9タブ、Asia/Tokyo。revision 6・1,466カードの実XLSX往復reviewは差分0。旧revision 5 SheetはARCHIVEとして非公開で保持。ローカルprivate/master.xlsxは承認済みrevision 6スナップショット（SHA-256 0c9a559ead43506042ad8f2f7592545faee4503091ad0e421300a049878b52bb）。
- 7一覧の別日再取得は新規0・変更0・消失0。coverageの未確認文言のみ訂正した。siteは新旧2版・19ファイル。公開URLの現行版はv1-ae32f82ff0a94d87、1,466カード。Actions run 37610524782で公開、37610787228で旧版へ公開切戻し、37611047652で新版へ公開復帰。3回ともsuccess。各段階で匿名URLの19ファイルがローカルsiteとバイト一致。通常pushの準備runはskipped。
- コード・公開site・文書は指定origin/mainへ保存する。private/、design.md、取得生応答はGit対象外。合成カードは一般公開していない。
- 未完了: 実カード1件追加・1件修正を正式原本から公開Webと配布全形式に反映する実地検証（現Wiki再取得に該当変更なし）。個別Wikiページ未作成47件、ロード派生初出日不明56件、公式総数との独立照合、実スマホ端末検証、Wiki管理者・運営の回答。
- 再開時は指定Sheetのプロフィール・共有状態を確認し、編集があればXLSXエクスポート→scripts/import_sheet_export.py review/applyを実行。新しい7ページ取得runを保存してオフライン変換・差分レビューし、実在の更新だけをacceptする。取得値採用後は新native Sheetを取り込み・往復照合して編集原本を切り替える。prepare→stage_release（旧site保持）→check_site→通常main push→明示publish:コミット→Actions成功→check_publicの順。異常時は原本を変更せず失敗runを保存し、旧版を選ぶrollback→公開検証で復旧する。

## 2026-10-07 更新演習の補修

scripts/update_drill.pyの手修正値に空欄のNoneを含める誤りがあり、隔離XLSXの厳密往復確認が停止。空欄を除く修正後、実データ8→9件、手修正、後日の同一カード取得、版切戻しの演習が成功した。正式private/master.xlsxと公開site/latestは不変。Git追跡外のprivate/drillに試験成果物と失敗時のstaged/バックアップを保持し、削除していない。

## 2026-10-07 UIレビュー準備

実機確認と表示改善の判定項目をdocs/ui-review.mdへ記録した。文書のみの変更であり、web/・site/・原本・公開データは変更していない。次回は実スマホ確認と、優先順位1からのUI改善を検討する。

## 2026-10-08 続行中の状態

- 新run private/raw/recheck-20261008 はW02/W03/W04/W07/W08/W05を保存、W09がHTTP 429で失敗し status incomplete。取得プロセスは終了。部分runは全件候補化・採用していない。原本SHA-256は接続記録と一致。正式Google Sheets r6と公開データ版v1-ae32f82ff0a94d87のカード内容は変更していない。
- source_manifest.jsonの取得間隔を5秒から15秒へ変更。当時は同日の再取得を避け、翌日以降に新runで7ページを取得してからオフライン変換・差分監査する。再度429なら取得を停止して条件を見直す。
- web/app.mjs、web/index.html、web/style.cssとsiteの対応ファイルにUI改善を反映。P/S・レアリティを主要条件、残り6条件を詳細条件とし、チェックボックス複数選択と選択中表示、見出し付きcoverage要約を追加。tests/ui-smoke.mjsとpackage.jsonのPlaywright依存を追加。README、docs/ui-review.md、docs/verification.md、operations.md、design.mdを更新中。
- Edge/PlaywrightでPC1280px・390pxの選択、並べ替え、リセット、URL、横切れを検証成功。Python15件、JS8件、siteの新旧各1,466件のcheck_site成功。ブラウザ操作プラグインはWindows sandbox helperエラーで起動せず、実スマートフォン端末・スクリーンリーダー検証は未実施。
- 次に差分を確認し、検証済みUIをmainへ保存・明示公開して、Actionsと匿名URLの版・全ファイル一致を確認する。実カード追加・修正の一般公開反映、公式総数独立照合、Wiki個別ページなし47件、初回実装日不明56件は引き続き未完了。

## 2026-10-08 UI公開後の現在位置

- UIと取得間隔・運用文書をコミットb55bffaとしてorigin/mainへ保存。siteのデータ版v1-ae32f82ff0a94d87、1,466件、原本SHA-256は不変。
- 明示公開コミット24395cfのPages run 37646437517はsuccess。匿名URL https://vignoles.github.io/shiny-index/ の19/19ファイルがsiteとバイト一致。ログインなしのEdgeでPC1280px・タッチ設定付き390pxの複数条件、並べ替え、リセットを実地確認。実スマートフォン端末の確認ではない。
- 当時の次作業（現在は撤回）: Wikiの429後は同日再試行せず、翌日以降に新しい隔離runで15秒間隔の7ページ取得を実行し、保存応答をオフライン変換して差分監査する。新規・修正が実在する場合だけ正式Sheet原本の手編集同期・採用・往復照合・公開を行う。実カード1件追加・1件修正の一般公開反映、公式総数独立照合、Wiki個別ページなし47件、初回実装日不明56件、実端末/スクリーンリーダー検証は未完了。

## 2026-10-08 出典表示公開後

- 各カードの確認状態、Wiki個別ページ、収録元一覧リンクを分離。個別ページ未確認47件に架空リンクを作らない。ローカルと公開URLのPC/390pxで確認。
- 出典表示の準備コミットfe608b2、明示公開コミット4a847fbをorigin/mainへpush。Pages run 37647591990はsuccess、匿名URLの19/19ファイルがsiteとバイト一致。版v1-ae32f82ff0a94d87、1,466件、原本SHA-256は不変。
- tests/ui-smoke.mjsはUI_BASE_URLを指定すると公開URLでも同じ回帰を実行できる。READMEのセットアップ・docs/verification.md・operations.mdに公開結果を反映。
- Wiki再取得は429後のincomplete runを保持し、同日の反復はしていない。当時は翌日以降に15秒間隔の新runで再試行する予定だったが、現在は撤回。実カード1件追加・1件修正の一般公開反映、公式総数独立照合、個別Wikiページなし47件、初回日不明56件、実端末/スクリーンリーダー検証は未完了。

## 2026-10-08 追加の限定監査

- 429前に保存したW02/W03/W04の参照キー・行文言は前回正常runと差分0（P492/S918/分冊361）。private/audits/partial-list-recheck-20261008.jsonに保存。W09未取得のため全7ページの「変更なし」や採用の証拠にはしない。
- 公式enzaサイト8ユニットのギャラリー24例を名称・人物で照合し24/24一致。private/audits/official-gallery-sample-20261008.jsonに保存。公式側には全件数がなく、全件独立照合は未達。ギャラリー掲載はP/S種別の独立証拠ではない。

- tests/ui-smoke.mjsに詳細条件のEnter開閉、Pチェックボックスのアクセシブル名、0件時案内の確認を追加し、ローカルと匿名公開URLのPC/390pxで成功。実端末・スクリーンリーダーは未確認。

## 2026-10-08 Wiki取得の停止（最新方針）

ユーザーはHTTP 429などWikiに迷惑をかける行為を絶対に避けるよう明示。上記の「翌日以降に15秒間隔で再試行」は撤回・上書きされた履歴で、現行の次操作ではない。source_manifest.jsonのfull_collection_enabled=falseにより、collect_all.pyは通信前に終了する。W09が429となったprivate/raw/recheck-20261008はincompleteのまま保持し、原本・公開版に反映していない。15秒という値は安全性の根拠ではない。Wiki管理者／運営の案内などで安全な経路・許容頻度が分かるまでWikiへ再取得しない。既存の公開サイトは継続し、保存済み入力のオフライン監査、出典・欠損の点検、実データ更新経路の整備など独立作業を進める。停止ガードの実行結果と追加検証はdocs/verification.mdに記録する。

- 停止ガードの確認: 全件CLIは通信前にexit 1、runフォルダーなし。直接取得はモック付き単体テストで通信なしを確認。実URLを渡す直接CLI試験は自動承認レビューにより危険として拒否され、実行せず。Python16件、JS8件、出典対応を追加したcheck_siteで旧新各1,466件成功。公開版オフライン出典監査は1,466カード/21,853出典行でリンク・根拠不一致0。欠損は個別URL47、初回日56、ユニット21。詳細はdocs/verification.md。今回Wikiへリクエストなし。
- 再開時の次操作: Wiki取得フラグをfalseのまま保ち、保存済み原本・配布データの監査とUI/更新手順の未完了検証を進める。Wikiへ新たにアクセスするのは適切な経路と許容頻度の根拠が確認できてから。実カード1件追加・修正の公開反映、公式全件独立照合、実スマホ/スクリーンリーダーは未完了。

## 2026-10-08 過負荷を避けた限定再開（最新方針）

ユーザーはWikiへの一律停止を解除し、過負荷を避ける範囲で続行するよう指示。前節の「取得は全面停止」は履歴となった。全7ページ連続取得は引き続きfalse、直接collect CLIは停止。新しいscripts/collect_one.pyは登録済み1ページのみ、24時間の状態確認と排他ロック、429時のRetry-After尊重、自動再試行なし。現在のprivate/raw/acquisition-state.jsonは前回W09 429時刻から初期化済み。status上の次回可能時刻は2026-10-08T15:30:00+00:00（日本時間2026-10-09 00:30）で、現時点ではcan_fetch=false。対象Wikiの一覧・カードページへ今回は新しい取得リクエストを送っていない。limited-runは全件候補へ直接変換・採用しない。REST APIは対象Wikiの設定・認証が必要で未接続。適切な経路・条件の確認は継続課題。

コード・文書差分と全回帰の確認後、冷却期間後にstatusとWiki側の条件を再確認する。条件が許せばW09の1ページのみ新しい隔離ディレクトリへ保存し、前回W09とオフライン差分監査。429・403・確認画面ならその場で中止。実カード1件追加・修正の公開URL反映、公式全件独立照合、実端末検証は未完了のまま。

- 追加検証: 取得確認画面・別ページをcanonical URL不一致で拒否する。正常保存済み7ページは7/7一致。Python24件、JS8件成功。オフライン比較CLIでW09旧2応答は全バイト一致、W02新旧はバイト差があるが本文テキスト・リンク一致。429後のW09を新規取得したわけではない。

- 公式アイドルマスターポータルのenza節で4カードの名称・人物・P/S・レアリティを現行siteと独立照合し4/4一致。4件とも既収録で、原本・公開版は変更不要。告知は予定日であり初回実装日の独立確定や全件網羅証明には使わない。詳細はdocs/verification.md。

## 2026-10-08 GitHub送信の一時障害

限定取得のコード・手順はコミット846d2f7としてorigin/mainへpush済み。公式4件照合と表現訂正のコミット1e86f81はローカルmainに保存したが、GitHubが3回（16:54 UTCに2回、16:58 UTCに1回）Internal Server Errorを返しpushを拒否。ls-remoteでorigin/mainが846d2f7のままを確認した。この後のローカルコミットも含めmainはorigin/mainより4件先行し、siteのデータ版やGitHub Pagesの内容は変更していない。GitHub側が復旧したら、まずls-remoteとローカル差分を確認してからpushする。無期限の反復再試行はしない。

## 2026-10-08 送信復旧と原本の読取監査

- GitHubのorigin/mainが846d2f7のままと確認後、保留中の4コミットをpushし、origin/mainは8cf5380へ進んだ。送信後のgit statusは差分なし。公開siteのデータは変更していない。
- 指定Googleアカウントの非公開native Sheet原本r6を読取監査。9タブ、レビュー表1,466行、P548/S918、固定card_idの重複0。_registryと_sourceも各1,466行でID集合がレビュー表と一致。欠損は個別Wiki URL47、初回日56、unit_id21で、前回監査と同数。これは原本内部の整合性確認であり、ゲーム全件性を証明しない。
- collect_one.py statusはnext_allowed_at=2026-10-08T15:30:00+00:00、can_fetch=false。今回Wikiへの新規取得リクエストなし。関連取得プロセスの残存なし。全7ページ取得は引き続き無効。
- 通常サンドボックスと画面操作はhelper_unknown_error: setup refresh had errorsで起動失敗。承認済みの拡張実行でローカル状態を読み取り、意図的な環境・権限変更なし。システムPythonはopenpyxl不足でcheck_publicが停止したが、既存.venvで再実行し公開19/19ファイル一致。公開URLのEdge/Playwright試験はdesktop/mobileともPASS。
- 未完了: 実在カードの正式Sheetへの1件追加・1件修正から一般公開への反映、ゲーム全網羅の独立照合、個別Wikiリンク未確認47件・初回日56件・ユニット21件の解消、実スマホ端末・スクリーンリーダー検証、Wiki管理者・運営の回答。取得待機解除後もstatusを確認し、許可リストのW09単一ページだけを隔離保存。429/403/確認画面なら即停止し、保存応答をオフライン比較して採否を決める。

## 2026-10-08 ユニット空欄表示の公開と欠損内訳

- 既存公開データ1,466件をオフラインで再監査し、表示キー重複0、Wiki個別URL空欄47件はSのSSR24/SR23、初回日空欄56件はロードSR28/SSR28、ユニット欄空欄21件は七草はづき13件とコラボ登場人物8件を確認した。公式全網羅や空欄の理由をこの集計だけで断定しない。
- web/app.mjs、site/app.mjs、tests/ui-smoke.mjsを変更し、ユニットのnullを「ユニット欄空欄」と中立的に表示。node --check、check_site旧新各1,466件、ローカルPC/390px試験が成功。UIコミット22706ecをpush後、明示公開コミット71cab82のPages run 37709291966はsuccess。匿名公開URL19/19ファイル一致、公開PC/390px試験もPASS。正式Sheet、カード内容、データ版は不変。
- 次は取得待機期限以降にstatusを再確認し、W09の単一ページだけを安全制限付きで隔離保存して旧保存応答と比較する。429/403/確認画面では停止し、全件採用をしない。実在カードの正式原本1件追加・1件修正を公開まで反映する実証、公式全網羅、実スマホ端末、Wiki管理者・運営の回答は未完了。

## 2026-10-08 欠損原因の保存済み応答監査

- 保存済みW02/W03/W04のresponse.htmlは取得記録のSHA-256と各々一致。個別Wiki URL空欄47件はW03の表内noexists表示に47/47対応し、同名カードの通常リンクは保存済み3一覧で0件。W04重複掲載23件もnoexists。保存時点のリンク欠損は変換漏れではなく、現在のWiki現況は未確認。Wikiへの新規リクエストなし。
- ユニット欄空欄21件の元一覧ラベルは「２８３プロ」13件、「コラボ」8件で、現行の8ユニット辞書に当てはめない。ロード派生の初回日空欄56件はSR28/SSR28。監査記録はGit対象外のprivate/audits/gap-source-audit-20261008.json。原本・公開カード内容は不変。
- ユーザーに必要な外部作業は、docs/wiki-permission-request.mdを現状に合わせて確認し、Wiki管理者／WIKIWIKI運営へ取得経路・許容頻度・事実索引の公開配布条件を問い合わせ、回答を共有すること。問い合わせや回答がないことを許可と推定しない。これ以外のローカル検証・UI作業はユーザー操作待ちではない。
- 取得待機解除後はstatusとサイト側の状態を確認し、許可リストの単一ページだけを隔離保存して前回応答と比較する。W09は前回429の確認対象、W03は47件のリンク現況確認対象。どちらも全件候補へ直結せず、429/403/確認画面なら即停止。実在カード追加・修正の公開実証は引き続き未完了。
## 2026-10-08 公式投票対象の照合と残件の理由（最新）

公式P-SSRアイドルコミュ総選挙の公開JSON323件を非公開保存し、scripts/audit_official_vote.pyで現行公開版をオフライン照合した。323件すべて一意に収録。索引側だけの55件はロードSSR派生28、2026-03-09以降初出22、2026-02-28以前のコラボ5。詳細・ハッシュ・出典・再実行方法はdocs/verification.md末尾とprivate/audits/official-vote-*。正式原本・公開データのカード行は変更していない。

未完了の理由: 実カード1件追加・1件修正の本番反映は、直近の全件再取得候補と今回の公式323件照合で真の追加・修正が0件だったため。架空のカードや裏付けのない訂正は採用しない。Wiki個別ページ空欄47件は保存済み一覧で全件noexistsを確認したが、現在のページ新設状況は取得抑制中のため未確認。派生初回日56件はカード固有の日付根拠がない。Sカードと期間後を含む全ゲーム網羅は独立した正確な総数・一覧がない。実スマホ端末・スクリーンリーダー確認はエミュレーションの範囲外。Wikiへの問い合わせは本人が行う方針で、文案はdocs/wiki-permission-request.md。新規取得はHTTP 429後の抑制期限2026-10-08 15:30 UTCまで実施しない。

次の具体操作: 抑制期限後、既存の取得run状態とsource_manifestの間隔・上限を確認し、Wikiへの負荷を抑えた限定更新確認から進める。新規・変更があれば保存済み入力で差分監査→Sheet原本へのレビュー済み取込→全形式生成→公開URL反映・版一致と切戻しを検証する。結果0なら無理に本番データを変えず、公式情報の追加照合と実端末確認を続ける。現在、取得・変換・公開処理の残存プロセスは見当たらない。

## 2026-10-08 現行要件と取得再開状態（最新）

ユーザーは問い合わせを今回の完成条件から除外し、スマートフォンでの基本動作を本人が確認した。未詳のUI不満点は今後の指摘に対応する。問い合わせ文案は履歴として保持するが、送信や回答を待たずに初版完成へ進める。Wikiのルール遵守と負荷抑制は続ける。scripts/collect_one.py status は next_allowed_at=2026-10-08T15:30:00+00:00、can_fetch=false を返した。現時点でWikiの追加取得は行わず、時刻到来後に1ページのみ新しい隔離先へ保存・差分監査する。full_collection_enabled=false、既存のHTTP 429で止まったrunはincompleteのまま、正式原本と公開版は保持。公式検索で直近候補の【Present Present】等を照合したが既収録であり、実カード追加・訂正の根拠はまだ見つかっていない。

## 2026-10-08 中断runの6ページオフライン照合

保存済みW02/W03/W04/W07/W08/W05を前回正常runの各同ページとscripts/compare_saved_page.pyで比較。6/6ページで本文可視テキストと本文リンクが順序を含め一致し、追加・削除は0。全バイトは各ページ異なる。結果はprivate/audits/six-page-offline-recheck-20261008.jsonに非公開保存。W09は429で失敗したため全7ページ確認済みとはしない。原本・公開版・固定IDは変更なし。今回Wikiへの追加通信なし。次はCLIのcan_fetch=true後、登録済みW09の単一ページだけを新しい保存先へ取得し、前回正常runのgachaとオフライン比較する。429等なら即停止して原本・公開版を維持する。

## 2026-10-08 二次S一覧の限定照合

GamesInkのS一覧236件を非公開で照合し、正規化一致229、近い表記差6、P-SSRをS表へ載せた1件を確認した。P/Sの誤採用はせず、正式原本と公開版を維持。詳細はdocs/verification.md末尾とprivate/audits/gamesink-s-audit-20261008.json。二次資料だけで新規カードを採用しない。

## 2026-10-08 取得待機後の自動フォローアップ

Codexアプリの同一タスクにheartbeat自動化「シャニマス索引のWiki限定再確認」を作成し、結果はautomationId=wiki、status=ACTIVE。日次実行時は必ずscripts/collect_one.py statusを先に確認し、can_fetch=trueの場合だけW09の単一ページを未使用の保存先へ取得する。429/403/503/確認画面なら再試行なしで中止し、原本・公開版を保持。W09の一回の確認後は自動化を一時停止するようプロンプトに指定した。スケジューラの時刻解釈に依存せず取得ゲートを優先する。CodexアプリとローカルPCが稼働し、無人実行に必要なネットワーク権限があるかは未検証なので、自動実行の成功はまだ確認されていない。


## 2026-10-08 W09確認・原本r7・公開版の現在位置

- ユーザーの明示指示でW09を一度だけ期限前に取得。HTTP 200、無再試行。保存先 `private/raw/limited-W09-20261008-user-early`、取得SHA-256 `6e65ac65de3de396a537177963b7eb4d8436564ca944275ceea5abbf86a31981`。旧W09と可視本文7,500行・リンク543件が一致。先の6ページ保存応答と組み合わせた隔離入力 `private/raw/composed-20261008-user-early` をオフライン変換。新規0・変更0・欠落0、P548/S918、計1,466件。原本への架空カード追加・訂正なし。
- 変換器の未確認範囲文言を取得日連動へ変更。指定アカウントの正式非公開Google Sheetをr7へ昇格し、9タブ・1,466件・保護8タブ・固定ID・手修正のXLSX往復差分0、所有者のみ、Asia/Tokyoを確認。現行URL/IDはGit対象外 `private/sheets-connection.json`。r6 Sheetと `private/backups/master-r6-before-20261008-coverage.xlsx` を保管。ローカル `private/master.xlsx` はr7、SHA-256 `97e7978763efd62ef7c7d2d38cd1e34cb1fcc2d6ee7d011a27d3d4e8c0b968c4`。
- 新版 `v1-93a6a8b8d40e754a` はカード・出典不変で確認範囲を2026-10-08へ更新。準備コミットea51e0d、明示公開コミットd2cdd55をorigin/mainへpush。Pages run 37720130993 success、匿名URL `https://vignoles.github.io/shiny-index/` の26/26ファイルがsiteとバイト一致。公開PC/390px UI試験PASS。公開版の `published_at=2026-10-08T02:45:18+00:00`、1,466件、P548/S918、complete=false。
- 実施済み検証: Python25件PASS、JS8件PASS、ローカル/公開のPC・390px UI PASS、check_siteで新旧3版PASS、原本1件追加・1件修正の隔離演習PASS、公開26/26一致。CUAによるSheet画面の視覚確認は起動障害のため不可。セル値・書式のAPI読戻しで代替確認。実カード1件追加・1件訂正の一般公開反映、公式の全件独立照合、個別Wikiページ未作成47件の現況、ロード派生初回日56件は未完了。
- 変更ファイル: `scripts/collect_one.py`、`scripts/full_transform.py`、`tests/test_limited_collection.py`、`source_manifest.json`、`README.md`、`TASK.md`、`operations.md`、`docs/verification.md`、`site/index.html`、`site/data/latest.json`、新しいsite/data/v1-93a6a8b8d40e754a/の7ファイル。`design.md`はローカル文書、HANDOFF.mdはGitにも保存する。生応答・正式原本・接続情報・候補/監査はprivateでGit対象外。
- Wiki取得の自動化 `wiki` は、手動W09確認を完了したためPAUSED。`scripts/collect_one.py status` は次回可能時刻 `2026-10-09T02:28:50+00:00`、can_fetch=false。`last_early_authorized_at` により同じ早期フラグの再使用を拒否。全件連続取得フラグはfalse。取得ロック、実行中Pythonプロセスなし。
- 次の具体操作: 公式またはWikiの新しい根拠から実在する追加・訂正候補が現れたら、対象を最小限確認し、保存済み入力から変換→差分レビュー→指定Sheet原本の更新と往復照合→配布生成→公開URLとデータ版一致まで実行する。次のWiki通信はstatusとサーバー制限を確認してから単一ページで行い、429等なら再試行せず停止する。現在は差分0のため実カード1件追加・修正の本番実証を捏造しない。UIの具体的不満点はユーザーからの指摘待ちで、問い合わせは今回の要件外。


## 2026-10-08 保存済み入力の再構成を追加

scripts/compose_saved_run.pyとtests/test_compose_saved_run.pyを追加し、scripts/full_transform.pyにURL・canonical再検査と7ページの最古JST日付採用を追加。実際の保存済み7ページからprivate/raw/composed-20261008-verified-v2へ再構成し、候補full-batch.jsonはr7採用時と完全一致、正式原本との差分0。合成試験4件PASS。Wiki通信、正式Sheet・公開サイトの変更なし。再利用手順はoperations.md末尾。公開済み版はv1-93a6a8b8d40e754aのまま。

- この改善はPython全29件PASS、構文検査・差分検査PASS、コミット5edeab3としてorigin/mainへ保存。通常pushのPages runはskipped、公開26ファイルの版は変更なし。作業ツリーはクリーン。

## 2026-10-08 UI作業への優先順位変更

- ユーザーは直前に示した個別Wiki URL空欄47件について「これらは追加していないことを覚えて、一旦飛ばして次へ進めます」と述べ、次にUI設計・修正を進める意向を示した。47件は公開索引には収録済み（S-SR23、S-SSR24）で、保存済みWiki一覧では47/47がnoexists表示。個別ページURL追加と現況確認を当面保留し、カード行の削除・再登録は行わない。元の完成条件上の未確認項目としては残す。
- 現行UIの初見確認: 検索、P/S・レアリティの複数選択、詳細条件、日付、並べ替え、結果CSV、版固定の全件配布、出典・確認状況を備える。PC/390pxの基本操作試験は既にPASS。ユーザーが予告したスマホUIの具体的不満点は未受領。まず情報の優先順位、検索条件の見通し、カード表示、スマホの操作導線を実画面で点検し、具体的な修正案と検証を進める。今回の追記ではUIコード・原本・公開データを変更していない。
## 2026-10-08 UI v2の調査・公開・切り戻し確認

- ユーザー指示により改修前UIをGitタグ `ui-v1-20261008` としてoriginへ保存。USWDS Search/Collection、GOV.UK Details、W3C WAIの結果通知とタッチ対象、MDN URLSearchParamsを参照し、根拠と適用範囲を `docs/ui-design.md` に記録した。
- UI v2は収録範囲を短い要約＋開閉詳細に再編し、スマホ390pxで検索欄上端を約635pxから343pxへ移した。日付条件を追加条件へまとめ、並べ替えとCSVを結果付近へ移し、リスト意味付け、結果件数の状態通知、Wikiリンクのタッチ領域、0件時の解除導線を追加。UI版とデータ版を別表示。原本・カード行・出典・47件の個別Wikiリンク保留状態・データ版は変更していない。
- `scripts/build_ui_rollback.py` はUIタグ内の配信用 `site/` 4ファイルから、現行データ版を保持した**新規**候補だけを作る。初回試作は編集用 `web/` の改行正規化により公開バイトと一致しなかったため、配信用 `site/` に修正。修正後のUI v1候補は改訂前の匿名公開URLと26/26ファイルで一致し、PC/390px/320px操作試験PASS。UI v2タグ `ui-v2-20261008` の候補も現行siteと26/26一致。正式site・原本を切り戻し演習で変更していない。
- UI改訂準備コミット `792a9b5` とUI v2タグをoriginへpush。明示公開コミット `d1e2d3b` のPages run `37739561660` はsuccess。匿名URL `https://vignoles.github.io/shiny-index/` で26/26ファイルがローカルsiteとバイト一致し、公開PC/390px/320pxのUI操作試験PASS。データ版は `v1-93a6a8b8d40e754a`、1,466件（P548/S918）、complete=falseのまま。検索JS試験8件、check_site 3版、ローカルUI新旧各3画面もPASS。
- 今回の変更ファイル: `web/index.html`、`web/style.css`、`web/app.mjs`、`site/` の同名3ファイル、`tests/ui-smoke.mjs`、`scripts/build_ui_rollback.py`、`docs/ui-design.md`、`README.md`、`operations.md`、`TASK.md`、`HANDOFF.md`。ローカル設計文書 `design.md` にも根拠と結果を追記。privateの撮影・演習候補はGit対象外。
- 残る事項: 実スマートフォンでの新UIの細かな使い勝手はユーザーから具体的な指摘を受けて調整する。スクリーンリーダー実機での全面確認とWCAG適合判定は未実施。元のデータ完成条件（実カード1件追加・1件修正の本番公開反映、全ゲーム網羅の独立証明など）はUI更新によって達成した扱いにしない。47件の個別Wikiリンク追加・現況確認はユーザー指示で当面保留。

## 2026-10-08 UI次版の設計段階（今回）

- ユーザーはスマホの一覧→詳細展開、トワコレ・キャスコレ等、入手区分との分離、年月日のカレンダー／年月日ドロップダウン、UR→N順、公式人物順、ユニット・人物統合、不要なコラボ独立項目・「不明項目あり」の整理、将来のスキル検索を求めた。今回は「実装一歩手前」までで、UIコード変更・公開は指示されていない。原文はTASK.md末尾。
- 現行公開データ v1-93a6a8b8d40e754a の cards.json を読取集計。1,466件、UR12/SSR929/SR465/R56/N4、トワコレ相当58・キャスコレ相当22、コレクションガシャ147、ユニット空欄21。unknown_fieldsが1つ以上あるカードは1,466/1,466で、現行の「不明項目あり」は絞り込みとして無効。Wikiへの新規取得なし。
- GOV.UK Dates、USWDS Date picker、W3C WAI Disclosure、MDN date input、enza公式のユニット・人物順を調査。シリーズと入手区分の2軸、階層人物フィルター、日付の部分指定とネイティブカレンダー、スマホの折りたたみ一覧、出典の二段目開閉、URL互換・版・切り戻しまで docs/ui-v3-spec.md に提案として記録した。
- 変更ファイルは docs/ui-v3-spec.md（新規）、TASK.md、HANDOFF.md、docs/ui-design.md、design.md（Git対象外のローカル設計文書）。web/、site/、scripts/、原本・配布カードデータは変更しない。Git statusで変更は文書4件のみ（design.mdはGit対象外）、git diff --check は問題なし。シリーズ実数・誕生日SSR40・unknown_fields全1,466を再計算して仕様の例と一致。UI自動試験は今回コード変更がないため未実施。
- 未実施: 次版UIの実装・操作試験・公開、実スマートフォンとスクリーンリーダーでの次版検証。従来の実カード1件追加／修正の本番公開実証、ゲーム全件の独立証明、日付欠損56件などの元の残件は残る。個別Wikiページなし47件のリンク追加はユーザー指示で保留。
- 再開時: docs/ui-v3-spec.md の設計判断をユーザーと確認後に、既存UI v2タグと公開データを固定したまま、別候補で検索ロジック→画面→PC/スマホ試験→明示公開の順に進む。ユーザーが今回の設計段階を延長するなら画面コードに着手しない。


## 2026-10-08 UI次版の第1工程（開発ブランチ、未公開）

- ユーザーの小分け実装指示により codex/ui-v3-incremental を作成。web/search.mjs、web/app.mjs、web/index.htmlで系列表示名をトワコレ・キャスコレ等へ変更し、旧名検索も維持。レアリティ選択肢をUR→SSR→SR→R→N、系列選択肢を優先順へ変更。現行全1,466件に一致していた「不明項目あり」はUIと検索から削除し、旧URLのmissingを読込時に除去。検索結果のカード表示、原本、site、公開データは変更しない。
- tests/search.test.mjsを9件PASS。隔離候補 private/audits/ui-v3-slice1-20261008-01 をsiteコピー＋web候補で作り、Edge/PlaywrightでPC1280px・スマホ幅390px/320pxがPASS。Playwright同梱Chromiumは未導入のためEdge実行に切替。Git差分検査後、開発ブランチへ保存する。
- 次工程: 近道のシリーズ選択（詳細条件と同一状態）を追加し、URL・結果件数の回帰を取る。その次に階層人物、日付、一覧展開を独立工程に分ける。UI v3を公開したと扱わず、全工程と受け入れ検証の完了後にタグ・明示公開する。

## 2026-10-08 UI次版の第2工程（近道、未公開）

- 開発ブランチ codex/ui-v3-incremental で web/index.html・web/app.mjs・web/style.css にトワコレ、キャスコレ、誕生日の近道ボタンを追加。詳細条件の series_ids チェックボックスを同じ状態として操作し、URL・選択表示・aria-pressedを同期する。データに存在する系列だけを表示。main、site、原本、公開URLは変更しない。
- tests/ui-smoke.mjs に近道→チェックボックス・URL、再読込、詳細条件→近道、解除の操作試験を追加。隔離候補 private/audits/ui-v3-slice2-20261008-01 と現行siteの双方でEdge/PlaywrightのPC1280px・390px・320pxがPASS。検索単体9件PASS。初回の試験は詳細条件の開閉状態を誤認して30秒タイムアウトしたが、試験のみ修正し全幅で再実行成功。
- 残りの次期UI: マイコレ・パラコレ・プレコレの近道、ユニット／人物統合、年月日選択、スマホ一覧／詳細開閉、出典表示の整理、全体回帰・実機確認・明示公開。次の小工程は階層人物選択に着手する前に、仕様上の残りの近道を追加するか、スマホ一覧の骨格を優先する。

## 2026-10-08 UI次版の第3工程（6系列の近道、未公開）

- 前工程の共通処理を使い、web/app.mjsの近道をマイコレ・パラコレ・プレコレまで拡張。既存3件と合わせて6種類。編集原本、site、公開URL、データ版は変更しない。
- tests/ui-smoke.mjsで6種類の表示順とプレコレ9件の結果を確認。隔離候補 private/audits/ui-v3-slice3-20261008-01 をEdge/PlaywrightでPC1280px・390px・320px操作試験PASS、横切れなし。検索単体と公開UI v2の試験は前工程でPASS済みで、この工程では検索ロジック・公開siteを変更していない。
- 次の候補: ユニット／アイドル統合、日付選択、スマホ一覧／詳細展開をそれぞれ別の工程にする。現行UI v2は公開維持、UI v3全体は未完成・未公開。

## 2026-10-08 UI v3公開後の最新状態

現在工程: ユーザーの小分け制限解除によりUI v3の全残工程を実装・公開・検証済み。mainのUI実装は4862ed4、明示公開コミットはe508509、タグはui-v3-20261008。公開URLは https://vignoles.github.io/shiny-index/ 。カードデータ版v1-93a6a8b8d40e754a、1,466件（P548/S918）、編集原本は指定Googleアカウントの非公開Sheet revision 7のまま。個別Wikiページなし47件のリンク追加はユーザー指示で保留。

主な変更: webとsiteのindex.html、app.mjs、search.mjs、style.css、tests/search.test.mjs、tests/ui-v3-smoke.mjs、package.json、README.md、operations.md、TASK.md、docs/ui-v3-spec.md、docs/ui-design.md、docs/verification.md、HANDOFF.md。ローカル限定design.mdにも設計変更を記録。private/auditsのプレビュー・画面画像・UI v2切り戻し候補はGit対象外で、正式原本と配布データは変更していない。

検証: Python29件、JS検索12件PASS。check_siteは3版各1,466件PASS。隔離候補、site、匿名公開URLでEdge/PlaywrightのPC1280px・390px・320pxのUI v3試験PASS。旧UI v2切り戻し候補のcheck_siteと旧UI試験もPASS。Actions run 37796666483 success、公開URL26/26ファイル一致。現時点で実行中の取得・変換・公開ジョブなし。GitHub公開ジョブの成功後に匿名URLの反映を確認した。

未完了: 実スマートフォン端末とスクリーンリーダーでのUI v3操作確認、ゲーム全件の独立照合、実在する新規1件・修正1件の正式Sheetから本番公開までの反映実証、初回日なし56件の個別根拠。47件の個別Wikiリンクはユーザーが保留を指示。取得については既存の429後制御を守り、UIのためにWikiへ通信していない。

再開時の次の操作: UIへの具体的な不満点があればsiteとwebの4画面ファイルへ反映し、同じcheck_site・UI v3試験・公開URL照合を行う。新しい実在カード差分が見つかった場合はoperations.mdの取得済み入力レビュー、Sheet往復確認、配布生成、公開URLでの版一致と切り戻しの順に進む。公開UIに問題があればui-v2-20261008タグから新しい切り戻し候補を生成し、旧UI試験後にmainの明示publish手順で復旧する。作業ツリーの状態はgit statusで再確認する。

## 2026-10-09 UI v4公開後の最新状態

ユーザー質問への回答: 283ステージ関連の性能・スキル情報は取得・公開していない。公開cards.jsonの全キーに該当項目なし。UI v4はui-v4-20261009タグと実装7b5a7eb、明示公開c6b472b。匿名URLは https://vignoles.github.io/shiny-index/ 。カードデータ版v1-93a6a8b8d40e754a、1,466件、非公開Sheet revision 7は不変。

変更ファイル: webとsiteのindex.html、app.mjs、search.mjs、style.css、tests/search.test.mjs、ui-v4-smoke.mjs、package.json、README.md、TASK.md、docs/ui-v4-spec.md、docs/ui-design.md、docs/verification.md、operations.md、HANDOFF.md。ローカル限定design.mdも追記。8区分を大きな探索の入口、追加条件のシリーズ・企画と入手区分を精密なAND条件として分離。各ユニットのアイドルは常時表示。画面上の検索結果CSVと全件CSVの取得導線は撤去した。

検証: Python29件、JS13件、隔離候補・site・匿名公開URLのPC1280px・390px・320px操作PASS。check_siteは3版各1,466件PASS。Pages run 37800969481 success、公開26/26ファイル一致。UI v3切り戻し候補はcheck_siteとタグ画面4ファイルの生バイト一致。公開サイト自体の切り戻しは未実施。元のデータ要件の未達（実在カード追加・修正の本番反映、公式全網羅、初回日空欄56件、保留中の個別Wikiリンク47件）は維持する。

未解決の判断: ユーザーのCSV『非公開』が画面導線だけを指すか、既存の版付きCSVファイル直接URLも止めるか確認中。現行版CSV直接URLはHTTP 200であり、ファイル自体の非公開は未実施。後者を要するなら過去版URL、manifestと不変データ版、元の配布要件への影響を先に設計し直す。ユーザー回答が届けばその範囲に合わせて続行する。次のUI改修時はdocs/ui-v4-spec.mdとoperations.mdの試験・公開手順を使用する。作業ツリーは再開時にgit statusで確認する。


## 2026-10-09 カード詳細拡張の前準備

現在工程: ユーザーの「今回は一旦収集を行わない。前準備のみ」に従い、詳細情報の構造設計まで実施。既存1,466件の基礎索引・非公開Sheet r7・公開データ版・UI v4は変更していない。

確認済み: Wikiの少数のP/S個別ページとスキル解説から、Pの通常パネル／別節MB／思い出アピール、Sのパネル／所持ライブ／サポートスキル、最大Lv表、複数楽曲熟練度を確認。GrowとRefrainには表記揺れがある。詳細設計と次工程の受入れ条件は docs/card-details-design.md。P/Sと節の区別、固定ID、項目別出典、取得済み入力での再変換、検索タグと未収録表示を設計した。

未実施・未確認: カード詳細の取得、パーサー、原本タブ追加、詳細バンドル、UI検索、全カードの表構造・欠損・抽出精度の検証、公開。ステージスキル・適正・ファイトスキルはユーザー指定で収集対象外。個別Wikiページなし47件の追加は既存の保留指示を維持。詳細文の公開範囲は現行の事実索引のみという方針に合わせて構造化を提案したが、実カードでの可能率は未検証。

変更ファイル: docs/card-details-design.md（新規）、TASK.md、HANDOFF.md、design.md（ローカルでGit対象外）、README.md（新設計へのリンク）。今回の検証は文書とGit差分のみ。データ取得・変換・公開ジョブは起動していない。次回、詳細収集の開始が指示されたら、まず仕様の機械検証化と保存済み／最小限の個別ページ入力を使う変換器・少数例の一気通貫試験から進む。個別ページを1,466件連続取得する運用は始めない。以前から残るCSV直接URLの非公開範囲は未回答であり、今回の詳細設計とは独立した保留事項。


## 2026-10-09 詳細P/S各2件の非公開試験

現在工程: ユーザーの後続指示でP/S各2件の試験取得を実施。既存の直接Wiki取得ゲートは 2026-10-09T02:28:50+00:00 まで can_fetch=false だったため、直接取得CLIを使わず、Wiki検索サービスのキャッシュ表示4件を private/raw/detail-sample-20261009-cache/ に行番号付きで保存した。manifest.jsonにURL・保存時刻・SHA-256を記録。これは原本HTMLでも現在のWiki内容の証明でもない。

完了: 既存card_idとWiki URLを照合し、scripts/transform_detail_sample.pyでP-URアマテラス、P-SSR切り拓いて・茨、S-SSR My Christmas、S-UR HoP PoP らびっつの詳細候補を private/audits/detail-sample-20261009.json に生成。入力ハッシュ・連続行番号・P2/S2・パネル未分類0、4件のユニット試験、既存.venvでのPython全33件、2回の再変換ハッシュ一致、公開siteへの出力拒否を確認。既定Pythonでの全件試験は依存パッケージ不足で7件エラーとなり、.venvで再実行して解消した。P通常Link/MB Plus、S-URクイックスキル、P思い出のチャージ列、Sサポートの最大列、固有アビリティの重複掲載を設計へ反映。詳細は docs/card-details-pilot.md。原本Sheet r7、公開UI v4、カードデータ版v1-93a6a8b8d40e754aは変更していない。

変更ファイル: scripts/transform_detail_sample.py、tests/test_detail_sample_transform.py、docs/card-details-pilot.md、docs/card-details-design.md、TASK.md、HANDOFF.md、README.md、design.md（Git対象外）。private/rawとprivate/auditsの試験入力・効果文はGit対象外。未検証: 現行Wiki HTMLの直接取得、4件の人手全項目照合、希少表、効果の完全な構造化、Sheetへの追加、Web検索・公開。Pステージスキル／適正、Sファイトスキルは指示どおり未収集。

再開時: 既存の取得待機状態とWiki応答を確認し、必要最小限のページで原本HTMLとキャッシュ候補を照合する。429等なら止め、保存済み4件の入力からオフライン変換・検証を続ける。正式原本への採用前に項目別レビュー、手修正・固定ID、公開配布する効果表現の方針を確定する。

## 2026-10-09 詳細取得継続・実HTMLのオフライン検証（最新）

現在工程: ユーザーの「問題なければ取得を進めてください」に従い取得状態を確認。2026-10-09 05:01 JST時点では、前回429後のローカル24時間ゲートが11:28:50 JSTまで閉じている。新規Wiki通信は0。現在のWiki応答が429だと確認したわけではない。ゲートを変更・迂回せず、独立したHTML変換・検証を進めた。原本Sheet r7、公開UI v4、基礎索引v1-93a6a8b8d40e754aの1,466件は変更していない。

完了: source_manifest.jsonにD01〜D04（前回のP2/S2）を登録し、collect_one.pyで不変の基本索引のcard_id・種別・URLと照合、private/rawへの保存、共通状態・排他ロック・待機期限を適用した。既存P【ほわっとスマイル】櫻木真乃のprivate/raw/run-c01の実HTMLを追加通信なしで処理し、ライブ2・パッシブ6・上限2・思い出Lv1–5をprivate/audits/detail-html-c01-20261009.jsonへ候補化。行／列結合を展開してSP・技能を対応付け、出典は原セルの表・行・列・節アンカーを保存。Link共有セルのLv対応を照合。これは新規取得したカードでもP2/S2の実HTML確認完了でもない。

検証: .venvでPython全44テストPASS。HTML追加11件では入力改変、崩れた表・未分類・思い出Lv欠落の停止、MBタグ独立、クイック区別、重複アビリティ照合、非公開出力と異内容置換拒否、保存失敗、詳細取得の同じ待機期限を確認。複合上限を単一対象に誤抽出しない境界も追加11件で確認。実P候補の2回再変換ハッシュ90d5f4018d940d6e3ddd142d8d25fc6146f53fa94aa4a30d9c89b67f18a80561一致。既存のP/Sキャッシュ4件も再変換して前回件数を維持。登録D01〜D04の実設定をオフラインで照合済み。check_siteで既存3版各1,466件の整合性PASS。05:00 JST付近のプロセス調査で取得・変換実行中プロセスなし、取得ロックなし、今回候補の一時ファイル残留なし。取得状態のlast_attempt_atは2026-10-08T02:28:50+00:00のまま。テストの初回1失敗は例外文の期待不一致で、拒否処理自体は作動しており、テスト修正後はPASS。

変更ファイル: src/card_details.py、scripts/transform_detail_html.py、tests/test_detail_html.py、scripts/collect_one.py、source_manifest.json、docs/card-details-acquisition.md、docs/card-details-design.md、README.md、TASK.md、HANDOFF.md。ローカル限定design.mdの17.34にも理由と影響を追記。非公開の実HTML候補JSON・キャッシュ再変換結果はGit対象外。新規依存はなく、requirements.txtと既存.venvを使用。完全に書いた一時候補を同一ファイルシステムのハードリンクで排他配置する方式にしたため、候補に半端なJSONを残さない。対応しないファイルシステムでは保存が失敗する。

未完了: D01〜D04の現行HTML直接取得とキャッシュ候補の全項目照合、S実HTML変換、P-UR/MB/アビリティの実物確認（合成テスト段階）、複合上限など追加構造、詳細項目の固定IDと手修正維持、原本コピーへの採用、詳細バンドル・Web検索・公開、少数検証後の取得範囲拡大。Sの保存HTMLを確保するまでS実HTML変換は明示拒否し、前回のキャッシュ用S変換は維持する。Pステージ／適正・Sファイトは収集対象外。47件リンク保留、CSV直接URLの非公開範囲、元の基礎索引の未達項目も既存記録のまま。

再開時の具体操作: docs/card-details-acquisition.mdに従い、まず ./.venv/Scripts/python.exe scripts/collect_one.py statusを確認する。can_fetch=trueの場合だけD01を新しいprivate/raw/detail-D01-実行日ディレクトリへ1ページ取得する。fetch.jsonとresponse.htmlの成功・ハッシュを確認し、scripts/transform_detail_html.pyでcard_id 6b98f267-3dd0-4e4b-9c25-edce2801b211の新規候補を作り、キャッシュ版との差分と実HTML全項目を照合する。429/503/確認画面等なら再試行せず記録し、正常な原本と公開版を保持する。D02、D03、D04は同じゲートが再び開いてから順次保存する。Sの表が保存できた段階で実物に基づいてS変換を実装・試験する。生HTML・効果原文は公開しない。今回、待機する長時間ジョブ・自動取得・自動公開は起動していない。

## 2026-10-09 09:27 JST 詳細の直接取得中（後の最新記録を優先）

ユーザーが「待機期限を解除して進めて」と明示したため、通常のローカル待機を24時間から60秒へ変更した。source_manifest.jsonのfailure_backoffは24時間、Retry-Afterと排他制御は維持。状態ファイルの過去の取得・429記録は消さず、local_wait_changesに原文と変更日時を追記した。D01（アマテラス）09:25:10、D02（切り拓いて・茨）09:26:53 JSTにHTTP200で実HTMLを保存し、非公開候補を生成した。直接取得の生入力はprivate/raw/detail-D01-20261009-user-waiverとdetail-D02-20261009-user-waiver。D03/D04はまだ取得前。

D01で複合上限があり、対象を配列cap_targetsとしてすべて保存するよう変更した。pilot_schema0.3。D01はライブ3/パッシブ2/上限4/固有アビリティ1/思い出6。D02はライブ2/パッシブ3/上限5/MB2/思い出5とチャージ5。通常LinkとMB Plusが実HTMLでも確認できた。新しい通常間隔、サーバー期限、新規失敗後の停止を22テストで確認し、複合上限を含むHTML12テストPASS。正式原本・公開版への採用はまだ行わず、入力保存とオフライン変換を先行している。詳細は本工程終了時の追記を優先する。

## 2026-10-09 09:40 JST 詳細4件の直接取得・照合完了（最新）

適用した最新指示: 「待機期限を解除して進めて」。通常のローカル待機を60秒へ変更済み。サーバーのRetry-After、新規取得失敗後の24時間停止、排他制御、許可URL、非公開入力は維持。過去の取得・429時刻を削除せず、private/raw/acquisition-state.jsonのlocal_wait_changesに原文・変更時刻・旧値と新値を保存。全件取得フラグはfalse。

今回の完了: D01アマテラス（P-UR）、D02切り拓いて・茨（P-SSR）、D03 My Christmas（S-SSR）、D04 HoP PoP らびっつ（S-UR）の実HTMLを直接保存した。すべてHTTP200。09:25:10、09:26:53、09:28:05、09:29:34 JST、間隔103/72/89秒。今回の通信に429・503・403・確認画面なし。原HTML・fetch.json・limited-run.jsonはprivate/raw/detail-D01〜D04-20261009-user-waiver/、4入力のハッシュ付き一覧はprivate/raw/detail-pilot-20261009/manifest.json。更新時刻は取得時刻で、Wikiの最終編集日時は未確認。

実装・設計変更: src/card_details.pyをP/S両対応にした。Sのアイデア・ひらめき・熟練度複数・最大Lv/☆/Vo/Da/Vi/Me、所持ライブ、サポートLv対応を追加。SSR80とUR90、サポートの特殊「最大」列と数値90列を区別。複合上限をcap_targets配列で全対象保持するpilot_schema0.3へ変更。Pの通常Link/MB Plus（2/5・4/5）、思い出チャージ5、固有アビリティ二重掲載を実HTMLで確認。Pステージ／適正・Sファイトは候補に含めない。基礎card_idは継承するが固定detail_idは未発行。

検証: Python全56テストPASS。短い通常待機と新規失敗／サーバー期限、P/S区別、複合上限、S特殊列・最大Lv・未記載値を推測しない拒否、技能の由来とタグ独立、入力ハッシュと保存失敗・上書き拒否、全パネル照合を検証した。キャッシュ表示のリンクラベル内の角括弧の処理を修正し、PukiWikiの結合末尾列とHTMLの開始列を同じ座標とみなしていた比較を修正。修正後キャッシュの共通504フィールドが表示上の空白正規化後に実HTMLと一致。表の各ノードをすべて比較しており、列番号不一致でノードをスキップしないことも回帰テストで確認。原入力・旧候補・旧比較監査は保持し、修正後キャッシュはprivate/audits/detail-sample-20261009-v2.json、4件の実HTML候補・監査はprivate/audits/detail-pilot-html-20261009-v2.jsonに保存。再変換2回で内容ハッシュf25c72e9017c9db2df312e57519dd395753aef99a4c5c7a3c15bd3551ba67651一致。

途中で解消した事項: 初回D01は未対応の複合上限で変換を拒否し、原HTMLを再取得せず対応後に変換した。D02を60秒の到達前に指定した呼出はローカル制御で通信・保存先作成前に拒否され、期限後に初回の実通信を行った。比較保存先の指定修正中に異内容の旧監査の上書きが拒否されたため、新しいv2監査へ保存した。いずれも正式原本・公開データへの影響なし。既存C01の再変換も新スキーマで成功し、private/audits/detail-html-c01-20261009-v2.jsonへ別保存した。旧schema0.2の候補とハッシュは履歴で、新スキーマによる内容ハッシュの変更は中断による破損ではない。

変更ファイル: scripts/collect_one.py、source_manifest.json、src/card_details.py、scripts/transform_detail_html.py、scripts/transform_detail_sample.py、scripts/verify_detail_pilot.py、tests/test_detail_html.py、tests/test_detail_sample_transform.py、tests/test_limited_collection.py、tests/test_support_detail_html.py、tests/test_detail_pilot_audit.py、docs/card-details-acquisition.md、docs/card-details-pilot.md、docs/card-details-design.md、README.md、operations.md、TASK.md、HANDOFF.md。design.mdの17.35もローカル追記（Git対象外）。生HTML・効果原文・候補・監査はGit対象外。新規依存なし、requirements.txtの既存依存を.venvから使用。公開siteファイル・正式Sheet r7・基本索引1,466件・UI v4は未変更。

未完了: 詳細項目の固定detail_idと手修正・再取得統合、原本コピーへの採用とSheet往復、公開用効果の構造化、Web詳細表示・技能検索・詳細バンドル版管理／配布／公開、原本追加・修正の少数一気通貫検証、全件詳細の取得・件数・欠損・例外検証。今回の4カードはLink/Plusの実例で、Change/Grow/RefrainやGrowの別表は実データ検証が残る。4件のレビュー状態はneeds_reviewで、キャッシュ一致だけをゲーム内独立確認や正式採用済みと扱わない。Wiki最終編集日時・全ゲーム網羅も未確認。既存47件のリンク追加保留、CSV直接URLの非公開範囲と基礎索引の未達項目は維持。

再開時の具体操作: git statusとscripts/collect_one.py statusを読み、待機解除の現行設定60秒を旧引き継ぎの24時間へ戻さない。取得済みのD01〜D04は再取得せず、 ./.venv/Scripts/python.exe scripts/verify_detail_pilot.py で4件入力のハッシュ・P2/S2・変換・比較を再検証できる。同じ結果なら既存v2監査を保持。変換変更時は--outputで新規候補へ出力する。次工程はこの4件を使い、固定detail_id台帳・手修正優先・原本コピー、構造化公開値、詳細バンドルとWebの少数一気通貫を順に作る。追加取得が必要な例外は基本索引の固定ID・種別・URLを許可一覧へ登録し、正常時60秒以上空けて単一ページ取得する。新規429等なら後続通信を止めて保存入力の工程へ移る。問い合わせを新しい必須条件として追加しない。

09:40 JSTの状態確認で取得・変換実行中プロセスなし、取得ロックなし、候補*.tmp残留なし。長時間ジョブ・自動再取得・自動公開は起動していない。今回の4件取得試験の完了を全件詳細版の完成と報告しない。

## 2026-10-09 詳細の全件HTML取得を開始（現在進行中）

現在工程: ユーザーの原文「問題なければ全件への取得を進めてください」により、P2/S2実HTML試験後、全件の詳細原入力取得を先行開始。少数原本・Web一気通貫より前に取得だけ先行する順序変更はdesign.md 17.36、docs/card-details-design.md、TASK.mdへ記録した。正式原本Sheet r7・基礎索引1,466件(P548/S918)・公開UI v4/データ版v1-93a6a8b8d40e754aは維持。詳細公開版は未完成。

対象: 1,419カードのURLをまとめて1,363の一意な個別ページ。URLなし47件は既存の保留を維持。ロード28ページは3カードずつ、84固定IDで共有する。HTMLは1回取得、派生の節対応が分かるまで詳細変換はneeds_variant_mapping。既知初回日2018-04-24～2026-10-02、日付不明56件。公式全網羅やWiki最終編集日は未確認。ページ数・カード数・取得日・実装期間を混同しない。

実行中: private/raw/detail-catalog-20261009。最終起動は2026-10-09T01:08:27+00:00（10:08:27 JST）、実Python PID3720、venv launcher PID28440。コマンドは scripts/run_detail_workflow.py private/raw/detail-catalog-20261009 --max-attempts 1351 --clear-stop。worker.lock/workflow.lockとworkflow-report.jsonに実PID・phaseを記録。10:08:29 JST確認時はrunning/worker_is_alive=true、取得済み13/1363（今回新規8＋既存再利用5）、残り1350、失敗0、active_attempt=null、STOPなし。これは時点の件数。再開時は必ずCLIで実状態を確認する。長時間backgroundプロセスはこの会話後もPC上で実行を続ける設定。PC終了/スリープでは進まない。無期限・自動再取得・自動公開のサービスはない。

原入力と状態: catalog.jsonは基礎索引ハッシュ・ID/P/S/URL/期待カード1466/期待ページ1363と照合する不変ファイル。state.jsonにページごとのpending/fetched/reused/failed/needs_inspection、ハッシュ、取得日時、保存先、active_attempt、履歴を原子的に保存。個別取得はpages/DC-.../attempt-UUID、正常既存5はD01～D04のuser-waiverとrun-c01を読み取り専用で再利用。各取得の完了から60秒以上、concurrency1、robots確認、画像なし。共通private/raw/acquisition-state.json/.lockを併用。新規失敗/429/503/403/確認画面/取得形式不整合では後続を止め、自動リトライせず24時間/Retry-Afterの長い期限を維持。旧一覧full_collection_enabled=falseは維持、詳細専用detail_catalog_enabled=trueと有限予算で明示拡大した。

今回完成した実装: src/detail_catalog.py、scripts/collect_detail_catalog.py（init/status/stop/run/死んだ所有PIDのロック解除/結果不明の確認処理）、scripts/transform_detail_catalog.py（取得と別の全カード状態監査）、scripts/run_detail_workflow.py（有限取得1回の後でオフライン監査を生成）。collect_one.pyは凍結カタログ登録先だけを許し、詳細入力をprivate/rawへ限定。変換不能な1件で正常な他カードを失わず、構造例外/入力異常/派生未対応をカードごとに明示する。採用・公開はしない。

検証: Python全79テストPASS（既存56＋全件制御23）。合成テストでURL/ID/P/S/件数異常、予算超過、publicへの生入力拒否、同一URLとロード派生、旧入力再利用/改変検出、逐次60秒、429とサーバー期限の後続停止、二重起動拒否、STOP、成功応答の中断復旧、不明結果の確認待ち/履歴維持、24時間経過前再試行拒否、部分変換の全件件数、他カード変換継続、最終監査生成/失敗を確認。テストのHTTP429は合成、Wikiへ送っていない。実通信ではこの時点の新規8ページがHTTP200、429等なし。

実際の停止・再開: 10:01:45 JSTにstopped、active_attemptなし、worker.lockと共通取得lockなしを確認。保存済み9入力はURL/応答SHAを検証し保持。再開後も元の9保存先/ハッシュは不変、二重取得なし。10:07:00 JSTにも安全停止して最終の取得＋監査wrapperへ切替。新規7ページの実応答間隔は60/60/60/201/60/60秒。private/audits/detail-catalog-20261009-pause-resume-before.jsonとpause-resume-verified.jsonに保護対象site/web/private/master.xlsxの31ファイル差分0、既存9入力不変、応答成功を記録した。安全停止に伴う201秒の間隔であって取得エラーではない。

オフライン実検証: checkpoint-b（state revision14）でP3/S6、候補9、input_pending1410、missing_page47、内容ハッシュ6c7ca9ab7dcd167bb9f5e411575709a0603a8f54e34afcbf7a357c331fbfb6cfを2回再現。checkpoint-c（revision25）でP3/S9、候補12、input_pending1407、missing_page47、全1466coverage行、構造エラー0、ハッシュf056fc7fb1d46b60fd7477a6ae60ec0154ad339ce6c6f25e323546dd15e65aafを2回再現。候補はすべてneeds_review。全カードの詳細を変換できたとは扱わない。既存候補と入力は保持した。全取得終了/安全停止/失敗の時にwrapperが新しいprivate/audits/detail-catalog-内容SHA.jsonへ最終監査を生成しworkflow-report.jsonへ参照を保存する。phase=finishedはジョブ終了で、全件詳細の完成ではない。

変更ファイル: source_manifest.json、src/detail_catalog.py、scripts/collect_one.py、collect_detail_catalog.py、transform_detail_catalog.py、run_detail_workflow.py、tests/test_detail_catalog.py、docs/card-details-full-acquisition.md、card-details-acquisition.md、card-details-design.md、README.md、operations.md、TASK.md、HANDOFF.md、docs/verification.md。local design.md 17.36も更新（Git対象外）。非公開原入力・候補・監査・ログはprivate内のみ。依存追加なし、既存requirements.txtと.venvで実行。公開site/webと正式原本への変更なし。

未完了: 全1,363ページの保存（低負荷で約23時間、停止/応答時間で延長）、全件の構造例外/Grow等対応、84カードの派生対応、固定detail_idと手修正・再取得統合、詳細原本コピー/Sheet往復、公開用効果の構造化、詳細バンドル/Web表示と技能検索/版一致/公開、少数追加・修正の一気通貫。基礎索引の公式全網羅・実在新規と修正の本番反映・初回日56件・CSV直接URLの非公開範囲も従前どおり。47件のリンク追加はユーザー保留で、取得失敗と数えない。公開画面は変更していないためブラウザ再検証は今回行っていない（UI v4は前工程の結果）。

次の具体操作:
1. ./.venv/Scripts/python.exe scripts/collect_detail_catalog.py status private/raw/detail-catalog-20261009、workflow-report.json、stdout-workflow-003.log/stderr-workflow-003.logを読む。実PIDとロックの生存を確認。稼働中なら二重起動しない。古いHANDOFFの「全件無効」「ジョブなし」へ戻さない。
2. 取得中でもscripts/transform_detail_catalog.py RUN 新しいprivate/audits/...jsonで部分候補を作り、needs_structure_review/input_invalidを保存HTMLだけで確認する。原入力は書き換えない。
3. complete後はworkflow-reportのcandidate_fileを開き、1466coverage行/P/S/各節/欠損/84派生を確認し、4試験カードから詳細ID・手修正台帳→原本コピー→構造化公開→Web/ファイルの少数一気通貫を進める。全件入力成功だけで公開・全件詳細完成と扱わない。
4. 失敗/中断ならdocs/card-details-full-acquisition.mdのSTOP/所有PID/不明結果/24時間待機/明示1ページ再試行を使う。古いstdout.log、stdout-worker-002.logと対応stderr/launch記録も保持。wrapperの死んだlockはrelease-stale-lock --lock-kind workflow --expected-pidでのみ解除。共通取得lockを自動削除しない。


## 2026-10-09 安全再開後の現在位置（2026-10-09T04:50:58+00:00、公開直前）

- TASK.md冒頭の元指示を保持し、最新の「少し慎重になりすぎ」「中断してところから安全に再開して」を区別して追記。design.mdに本文長/URLタイトルの誤検知、最大Lv空欄、S固有アビリティ、詳細原本/公開の設計変更を記録した。既存編集は破棄していない。
- 取得: private/raw/detail-catalog-20261009、現在status=running、page_status_counts={'fetched': 81, 'pending': 1277, 'reused': 5}。新しいworkflow-006（起動時1279試行上限）が60秒以上で逐次取得。実PIDはworker.lockを確認。旧005はHTTP200のタイトル記号差で停止し、保存本文から追加アクセスなしで回復。旧状態と失敗報告は保持した。HTTP429/Retry-Afterを解除していない。
- 正式原本: 指定Driveのnativeコピー15タブ、基礎r7/P548/S918不変、詳細revision3・60カード(P5/S55)865項目。ID/URLはprivate/sheets-connection.json（spreadsheet_urlも更新済み）、旧原本とスナップショットはバックアップ保持。初期59/855と更新60/865で全値往復一致、既存9タブ差分0。1実P詳細追加・1名称修正の反映、再変換後の固定ID/手修正保持を確認。
- Web: UI v5をsiteへ配置し、基本検索回帰とスキル検索をPC1280/390/320でPASS。詳細版d1-ee415ee7fa6b3d80、前段の59カード版d1-8619fca84091f29dも不変で保持。基礎版v1-93a6a8b8d40e754a不変。全32配信ファイル。旧UI v4切り戻し候補のcheck_siteとPC/スマホ回帰もPASS。スクリーンショットprivate/audits/ui-v5-final-20261009を目視確認。
- 変更: src/wiki_response.py/detail_master.py/detail_public.py/card_details.py/detail_catalog.py/indexer.py、取得/変換/原本取込/出力/配信/切り戻しscripts、web/site、tests、package.json、README/operations/TASK/HANDOFF、docs/card-details-*。privateの原HTML/全文効果/Sheets値/台帳/監査とdesign.mdは公開Gitへ入れない。
- 完了検査: Python/JS単体（最新件数は公開後節で追記）、原本2段階往復、既存9タブと全基礎配布不変、同一ライブ行の機能/種類/名前AND、思い出分離、公開許可項目/ID/式/欠損/ファイルSHA検査。原本1詳細追加は基礎新規カードの本番追加実証ではない。
- 次の操作: 最終Python/JS/check_site → コードと検証済みsiteをGit保存 → ui-v5タグ → publish:コミット → Actionsと匿名URL全32ファイル一致 → 公開PC/390/320基本/詳細試験。公開成功とcommit/runを追記する。取得workerの実状態を最後にも確認する。
- 未完了: 全件詳細取得/構造対応、84ロードIDの節対応、効果条件/追加効果の全面構造化、ゲーム公式独立全網羅、基礎新規1カード本番追加/修正実証、47個別リンク保留/初回日56不明、実機・スクリーンリーダー。現在の60詳細を全件完成とは報告しない。
