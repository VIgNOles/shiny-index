# 改善レビュー反映前の正式基準版 B1

2026-10-12 JST。通常の細かな更新と区別する保存版。正式タグは **`baseline-pre-review-v1-20261012`**。UIは **v26のまま**、基準版B1はUI番号とは別の保存識別子。

コード・データ・公開Webの挙動は変更せず、レビュー指摘は未反映。Gitにあるコード／配布データ／Web／文書と、Git対象外の承認済み原本／入力を組で保持する。基準コミットの完全SHAは `git rev-parse 'baseline-pre-review-v1-20261012^{commit}'` と非公開バックアップの `BASELINE_MANIFEST.json` で照合する。

## 収録状態・主要機能

| 対象 | 基準値 |
|---|---|
| UI | ui-v26 |
| 基礎 | 1,466カード（P548／S918）、原本revision7、v1-93a6a8b8d40e754a |
| 詳細 | 1,419カード（P548／S871）、24,025項目、原本revision21、d1-5734710ad392192f |
| 効果・手修正 | 保存された構造化効果20,096、詳細手修正13 |
| 入力・公開 | 保存済み1,363個別ページ、公開106ファイル |
| 判明実装日 | 2018-04-24～2026-10-02、日付不明56件 |

- P／S・レアリティ・階層人物・シリーズ／入手方法・実装日・詳細収録状態から検索、並べ替え、条件解除、検索URL保存。
- ライブ／MB／生成／所持、パッシブ、思い出、サポート、上限等を区別。Link／Plus／Change／Grow／Refrain、同一スキル／同一効果／同一ランダム候補の条件照合、一致理由と詳細表示。
- PC／スマホ、常用条件の即時反映、詳細条件の下書き／取消／一括適用、履歴・幅変更への対応。
- 匿名閲覧・検索・JSON／Excel取得、出典と個別Wikiリンク、版・更新日・欠損範囲の表示。
- 取得と変換／採用／公開を分離。固定UUID、取得値と手修正の分離、明示mapping、件数／ハッシュ異常停止、不変バンドルと復旧手順。

## 今回の確認結果

| 確認 | 結果 |
|---|---|
| 未完了処理 | 開始前のプロセス一覧・ロック・保存SHAを確認。取得complete／revision4098／active_attempt=null。既存の取得・原本更新処理は検出なし |
| 単体 | Python352／JS77合格。429を含む障害例はmockで、Wikiへ再取得していない |
| 生成物 | check_siteで現行全バンドル合格、原本から隔離再生成した基礎／詳細の版・内容・UIテキスト一致 |
| 検索総点検 | 450セット合格、うち独立期待集合97、無効条件の拒否／復帰7。全1,466表示・ID重複0 |
| 表示・操作 | ローカル／匿名公開1280・900・899・768・390・320、Chromiumタッチ2設定合格。公開PC／スマホ画像を視認 |
| 公開整合 | 106／106ファイルを匿名取得し、全バイトがローカルと一致 |
| 保全 | 前回保護10ファイルのSHA一致、レビュー2文書は原文のまま保持 |

今回再実行した検索は450セット。前回UI26の488セットのうち追加38を今回再実行したという意味ではない。再生成の生成日時・XLSXバイトは新しくなるため、内容版・論理データを照合し、現行siteを置き換えていない。これらの試験成功は、レビュー指摘や全効果の意味の完全性を否定／保証するものではない。

詳細証拠は `private/audits/baseline-pre-review-v1-20261012/`。Git bundle・非公開入力の実復元結果と最終Git状態は、バックアップ側の `BASELINE_MANIFEST.json`／`restoration-proof.json`／`save-proof.json` に保存する。元の原本・公開物へ障害を注入しない。

## 保存物

1. 正式な注釈付きGitタグ `baseline-pre-review-v1-20261012`：コード、site106、依存定義、テスト、手順、REVIEW_HANDOFF／REVIEW_DEVELOPER／REVIEW_PRODUCT。レビュー資料の保存であり、提案実装の採用ではない。
2. `repository.bundle`：正式タグを含むGit履歴。GitHubに接続できなくても別フォルダーへ復元可能。
3. `private-inputs.zip`：4,271ファイル／展開時248,721,529bytes。private/raw全4,266ファイル、承認済みmaster.xlsx、Sheets接続記録、r21台帳、人物ID台帳、design.md。ZIP61,156,527bytes、SHA256 `d2ee7839a1c02a0fed1d056fd588fda81aff0974336d2c54d2a78930380b2793`。
4. `private-inputs-manifest.json`／`BASELINE_MANIFEST.json`／`restore-baseline.py`：全ファイルSHA、Git/tag、復元用ヘルパー。原本・生応答・接続情報はGit／公開siteへ追加しない。

非公開バックアップ所在：

```text
C:\Users\VIgNOles\.codex\visualizations\2026\10\06\01a111fa-3b50-7371-bad7-f4a3382e392f\baseline-pre-review-v1-20261012
```

この保存対象は現在の承認済みローカル原本r21。Google上に未取込の編集がないことやGoogle実画面は今回確認していない。クラウド上の編集を自動で戻す保存版ではない。依存ランタイム自体は同梱せず、requirements.txt／package-lock.jsonから再導入する。以前のタグ・復旧ZIPも保持する。

## この版への戻し方

### 安全な完全復元（現在の作業を残す）

リポジトリ直下のPowerShellで、未作成の別フォルダーを指定する。既存の作業フォルダー・原本・Googleへ上書きせず、バックアップのSHAとタグのコミットを照合してGit＋非公開入力を復元する。

```powershell
$baselineStore = 'C:\Users\VIgNOles\.codex\visualizations\2026\10\06\01a111fa-3b50-7371-bad7-f4a3382e392f\baseline-pre-review-v1-20261012'
$restoreFolder = "$baselineStore-restored-NEW"
./.venv/Scripts/python.exe "$baselineStore/restore-baseline.py" $restoreFolder
git -C $restoreFolder status --short
./.venv/Scripts/python.exe "$restoreFolder/scripts/check_site.py" "$restoreFolder/site"
```

別環境ではGitとPythonを用意する。ヘルパーはPython標準ライブラリのみ。復元後は復元先でvenv／requirements.txt／npm ci／Playwrightを導入し、REVIEW_HANDOFFのテストを実行する。復元先はタグのdetached HEADになるため、編集再開時は `git switch -c codex/review-improvements` 等で新しい作業ブランチを作る。

GitHubだけからコード・公開データを戻す場合は、別の新しいフォルダーへcloneし、`git checkout --detach baseline-pre-review-v1-20261012`。非公開原本・保存HTMLはGitにないので、その場合もprivate-inputs.zipが必要。

### 公開だけを戻す

復元した基準版siteを公開候補の基準とし、基礎／詳細のlatestとHTML・UI5資産をこの版へ揃える。将来追加された不変data／detailsディレクトリは削除せず保持し、既存URLを壊さない。候補のcheck_site・表示・Git blob一致を確認してから、現在のmainに**新しい復旧コミット**として保存し、通常の `publish: ` 手順で公開する。匿名の全ファイル一致を確認するまで復旧完了としない。Gitの強制巻戻しや原本の自動巻戻しはしない。

原本も戻す必要がある場合は、現在の編集を先に別途保存し、復元したXLSXと差分を確認する。Googleへは新しい非公開Sheetとして取り込み、往復検証・所有者確認後に明示的に切り替える。現在のSheetを自動上書きしない。詳細はoperations.md／REVIEW_HANDOFF.md。

## 既知の未対応・保留・検証限界

- **レビュー未反映**：複合属性パッシブの検索漏れ（【Present Present】等）の再現報告がREVIEW_DEVELOPER／REVIEW_PRODUCTにある。今回、その不具合の独立再検証・修正は行わない。基準保存は不具合がないという認定ではない。
- **ユーザー保留**：個別Wikiページなし47件の詳細、実在新規基礎カードを本番へ追加する更新実証。基礎追加の隔離試験・詳細の追加／修正反映試験とは区別する。
- **出典欠損／指定スキップ**：日付56件、S90カードの最大Lv360セル、期間10項目。未記載は推定しない。以前の107複合候補、不明確な5条件、属性・回復の指定補正、ROOTS単位は対応／指定スキップ済み。
- **対象外等**：Pステージ／適正、Sファイト、Sheets自動同期、簡単な新人物／詳細新規入力UI。CSV導線は非表示だが旧不変CSV URLは保持。問い合わせは必須ではない。
- **未確認**：全効果・発動制限の独立公式網羅、Google実画面、実機Safari等／スクリーンリーダー全面適合、私的全入力の別PCでの全再変換、本番全面障害・切戻し。今回のローカル原本再生成・別フォルダー復元とは別の検証範囲。

UI26の既存機能を固定する正式基準版であり、プロジェクト全体を完全完了とする宣言ではない。改善レビューの反映は、この保存の後に別の作業単位で行う。
