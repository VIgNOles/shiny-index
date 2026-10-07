# 現在の状態と再開手順

更新日：2026-10-07 JST。元の実装依頼は継続中。完成ではない。

## 現在の工程

全期間Wiki一覧のローカル収録・Web/配布生成まで進んだ。公開条件の確認、Google Sheets原本の移行、GitHub Pages公開・匿名検証は未完了。ユーザーは以前の一時停止を解除して再開を指示した。

## 実際に確認した状態

- Gitローカルブランチmain、初期実装コミット `8082378`。再開後の変更もローカルコミットとして保存（最新は`git log -1`で確認）。GitHubへのpushは認証がなく失敗し、ユーザーはその時点でローカル保存を選択。再開時の作業ツリーに差分はなく、その後の変更を追加した。design.mdは.gitignore対象でローカルに保持。
- `private/master.xlsx`は1466行、採用revision 4。`dist/data/latest.json`は `v1-53d6c62d6a358a16`。index.htmlと同じ版。
- 2026-10-07の読み戻しで、dist内の1466行版2つと9行版1つのJSON/CSV/XLSX/manifestをすべて検証成功。古い試作版はprivate/legacy-prototypesへ保存。
- 元のdesign.mdを読んで実装し、変更理由と制約を17章へ追記済み。TASK.mdとHANDOFF.mdは停止中断時には未作成で、再開後に会話と実状態から作成した。
- 再開時点で実行中のデータ更新は見当たらなかった。localhostプレビューのPython http.server（4173/4174）は残っている。停止指示は再開により解除済みだが、公開サービスではない。

## 完了事項

- 少数9実例で取得→原本→Web→JSON/CSV/XLSXを接続後、WikiのP/S一覧、S分冊、コラボ、ロード、追加順を保存しオフライン全件変換。
- 一覧1771掲載行のうち引用重複361を除き1410基礎カード、ロード派生56を追加し1466索引行。P548、S918。日付不明56、Wiki未掲載47、分類未確定21を報告。ゲーム全網羅を主張していない。
- 固定ID、明示的手入力統合、手修正優先、型/重複/件数異常の検出、版付きデータとrollback、PC/390px幅の検索・絞り込み・並べ替えをローカル実装。
- 実カードの8→9件追加と1件の確認状態修正、Web表示・配布反映、再取得との統合をprivate/drillで検証。
- 元のローカルコード23ファイルはコミット8082378に保存。再開後の再現性・安全性変更もローカル保存。原本・生応答・配布データはGit対象外。

## 未完了・問題

- Google SheetsインポートはDriveの403 storageQuotaExceeded。現在の原本は完全タブ構成のローカルXLSX。容量解消後の移行とAPI同期が必要。
- Wikiへのヒアリングは未実施。ユーザー方針は「作成後許可を得る」。source_manifest.jsonの公開配布フラグはfalse。一般公開URLはまだない。
- 指定GitHubリポジトリは公開・空、Pages未設定。pushは認証失敗。ユーザーは前回「今回はローカル保存まで」と回答。勝手に認証情報を探さない。
- 特殊分類21、ロード派生初回日56、ゲーム全網羅・公式照合、公開済み重複IDのredirect統合、HTTPリトライ/ETag、Artifact Toolの任意環境での入手は未確認。`XLSX_BACKEND=stdlib` の代替出力は全件照合済み。
- 初期のcredential-manager列挙コマンドは自動承認レビューにより不要なcredential probingとして拒否された。同方式は再試行していない。
- 再開後、標準ライブラリXLSX経路、6ページ逐次取得CLI、RAW_RUN_ROOTによるオフライン再変換を追加。取得runは開始時と各ページ後に進捗記録を残す。新runでは隔離出力先を必須とし、異なる既存候補の上書きを防ぐ。観測日は保存応答の取得日時をJSTへ換算。元原本は変更せず、全件配布・完全原本の読み戻し、1466件の再変換一致を確認。
- 通常サンドボックスexecは`helper_unknown_error: setup refresh had errors`で失敗することがある。承認済みの拡張実行で作業した。意図的な環境・権限変更はしていない。

## 変更ファイルと私的成果物

- 実装：`src/indexer.py`、`src/xlsx_fallback.py`、`scripts/`、`web/`、`tests/`、`.github/workflows/pages.yml`、`source_manifest.json`、`requirements.txt`。
- 手順・検証：`README.md`、`operations.md`、`sources-policy.md`、`docs/verification.md`、`design.md`17章、`TASK.md`、`HANDOFF.md`。
- 非公開：`private/master.xlsx`、`private/raw/`、`private/full-batch.json`、`private/full-audit.json`、`private/drill/`、各バックアップ。Gitへ追加しない。
- ローカル公開候補：`dist/`。一般公開許可が未確認なのでGitへ追加しない。

## 実施済み検証と未検証事項

- Python単体7件、JS検索8件が再開後も成功。再変換1466件の既存候補・新規隔離出力で一致し、新runの出力先省略は変換前に停止。標準ライブラリ経路の完全原本XLSXは1466件の有効値・revision 4が一致。配布済み3版はcheck_siteで全形式読み戻し成功。構文検査・git diff --checkも成功。1万行の検索関数はPC Nodeで約160ms。実スマホ端末・DOMを含む性能は未検証。
- PC/390pxブラウザで検索、P/Sフィルター、レアリティ昇順、全角半角、日本語シリーズ検索、100件追加表示を確認。匿名の公開URLでは未検証。
- 全版のJSON/CSV/XLSX論理値・版・件数・ファイルハッシュは読み戻し成功。Google Sheets反映とPagesでの公開・更新・rollbackは未検証。

## 再開時の具体的な次の操作

1. `git -c safe.directory='D:/THE IDOLM@STER/シャニマス/enza/index' status`、`private/master.xlsx`の読み戻し、`dist/data/latest.json`と`index.html`の版一致を確認する。結果不明の処理を推測で再実行しない。現ホストではGit所有者SIDが異なり、コマンド単位のsafe.directory指定が必要。
2. TASK.md、HANDOFF.mdと実状態を照合し、必要な補正を記録する。
3. 新runは`scripts/collect_all.py private/raw/<新run>`で取得し、`RAW_RUN_ROOT`と新しい`TRANSFORM_OUTPUT_ROOT`を指定して`scripts/full_transform.py`を実行する。候補を監査し、原本採用時は既存キー・件数を照合して変化があれば保留する。
4. Google Drive容量の解消後に完全XLSXを非公開Google Sheetsへ移し、タブ・手修正・IDの読み戻しを検証する。
5. Wiki管理者/運営から取得・CSV/JSON/XLSX配布条件を確認する。ユーザーが後で許可取得予定。回答前に一般公開のフラグをtrueにしない。
6. 公開条件が整いGitHub認証が利用可能になったらコードをpushし、完成バンドルをPagesへ配置。匿名ブラウザで版・検索・ファイル取得を検証し、公開での1件追加・1件修正・rollbackを実証する。

元のユーザー指示を勝手に縮小しない。ローカル収録の完了をプロジェクト全体の完成と扱わない。
