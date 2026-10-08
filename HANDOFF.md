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