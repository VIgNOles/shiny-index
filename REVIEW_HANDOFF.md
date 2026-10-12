# 第三者レビュー引き継ぎメモ

確認日：2026-10-12（JST）。対象リポジトリ：`D:\THE IDOLM@STER\シャニマス\enza\index`。以下のファイルパスはリポジトリ直下からの相対パス。
本メモはコード・現行JSON・ローカル原本XLSX・Git状態・保存済み検証記録を照合して作成した。今回、コード変更、取得、原本更新、公開、テスト一式の再実行はしていない。公開表示・Google接続の現在状態は今回再確認しておらず、該当実績は過去の検証記録による。

## 1. 目的と完成状況

enza版シャニマスのP／Sカードを、人物・区分・日付・スキル／効果などから検索する静的Webアプリ。取得と変換を分離し、Google Sheetsを編集原本として、固定ID・手修正を保持した配布データとWebを公開する。

- [公開サイト](https://vignoles.github.io/shiny-index/)／[リポジトリ](https://github.com/VIgNOles/shiny-index)。ログイン不要の検索・JSON／Excel取得を検証済み。
- UI26の改善・検索UI／結果総点検・公開・復旧保存は完了。スマホでは人物／シリーズ／性能の入口を通常ページに置き、常用条件は即時反映、詳しい条件だけ一括適用。
- 凍結した取得対象の個別ページは全件取得済み。ゲーム全カードの最新網羅、全効果の意味の完全構造化を保証する状態ではない。詳細の `coverage.complete` は `false`。
- 取得stateは `complete`／revision4098／`active_attempt=null`、1,363ページ（新規保存1,358／検証再利用5）。run内の `.lock` ファイルなし。進行中・回答待ちはなしという直前の保存記録があるが、OS全プロセスは今回再調査していない。

## 2. 現在のデータ件数・版

現行JSONと `private/master.xlsx` を今回読み取り照合した。

| 対象 | 件数・版 |
|---|---|
| 基礎索引 | 1,466件：P548／S918。原本基礎revision7、`v1-93a6a8b8d40e754a` |
| 詳細 | 1,419カード：P548／S871、24,025項目。詳細原本revision21、`d1-5734710ad392192f` |
| 保存された構造化効果 | `effect_details.effects` 計20,096。検索時に生成するパッシブ／上限の読取表現は別 |
| 詳細手修正 | 13項目（取得値と分離して保持） |
| 未収録詳細 | 個別ページなし47件（すべてS）。基礎索引には存在 |
| 実装日 | 判明分2018-04-24～2026-10-02、不明56件。ゲーム全体の収録保証期間ではない |
| 公開成果物 | `site/` 106ファイル、UI `ui-v26` |

パッシブ発動条件は現行 `activation_condition_current_counts` で5,890／5,890対応。互換用の旧集計には「未対応944」「未対応4」が残るため、現在の残件と混同しない。旧「107／5,032候補」は対応・ユーザー指定スキップ済みであり、未処理107件ではない。これらの数値は全効果の意味網羅率ではない。

## 3. 主要ディレクトリ・ファイル

| パス | 役割 |
|---|---|
| `TASK.md`／`HANDOFF.md` | ユーザー原文・明示変更／最新状態と過去の工程記録 |
| `design.md` | 当初設計と判断追記。ローカルのみ、Git対象外 |
| `operations.md`／`sources-policy.md`／`source_manifest.json` | 更新・復旧／公開情報の範囲／取得・公開フラグと低負荷制御 |
| `src/indexer.py` | 基礎台帳、固定ID、取得候補採用、XLSX／基礎バンドル生成・検証 |
| `src/detail_catalog.py`／`src/wiki_response.py` | 取得対象・状態／応答内容の検査 |
| `src/card_details.py`／`src/detail_master.py`／`src/detail_public.py` | 詳細抽出の共通処理／原本台帳・手修正／公開用変換・検証 |
| `src/skill_conditions*.py`／`src/live_conditions.py` | パッシブ・ライブの条件解析 |
| `src/skill_effects.py` と `*_effects.py` | 効果・期間・対象・特殊効果等の構造化 |
| `scripts/` | 取得、オフライン変換、原本取込、候補生成、公開検査、復旧用CLI |
| `web/` | UIソース5資産。`app.mjs`＝画面・URL・操作状態、`search.mjs`＝基礎検索、`details.mjs`＝詳細検索・表示 |
| `site/` | Git追跡済みの公開完成物。`data/<v1版>/` と `details/<d1版>/` は不変バンドル、各 `latest.json` とHTMLで選択版を指定 |
| `dist/` | 基礎生成先、Git対象外。現行公開版の基準は `site/` |
| `private/` | 原本XLSX、接続記録、生応答、候補、監査、復旧。Git対象外・公開しない |
| `tests/`／`.github/workflows/` | Python／JS／Playwright検証、Windows・Linux CI、GitHub Pages公開 |
| `docs/filter-design-20261012.md`／`docs/ui-v26-*.md` | 検索設計（14章でUI26へ更新）／現行UI仕様・検証結果 |
| `docs/verification.md`／`docs/source-review-decisions-20261012.json` | 完成条件別の記録／ユーザー確認・指定スキップの判断台帳 |

README・operations・詳細接続文書には旧版の「現行」「未完了」が残る。最新の根拠はHANDOFF冒頭の `current-state`、現行ファイル、UI26検証記録。古い記述だけで状態を確定しない。

## 4. データの流れ

1. **取得**：一覧／個別ページを低負荷で保存。`collect_one.py`／`collect_detail_catalog.py` が共通待機・排他・状態を管理し、HTML・応答SHA・日時を `private/raw/` に残す。並列1、正常時60秒以上、失敗時24時間／より長いRetry-Afterを尊重。旧一覧の連続一括取得は無効。取得は原本・公開を変更しない。
2. **変換**：基礎は `full_transform.py`、詳細は `transform_detail_html.py`／`transform_detail_catalog.py`。保存済み入力からネット接続なしで候補・収録範囲を再生成。カード・派生・セル位置・ハッシュを検査。
3. **原本への採用**：基礎は `review_batch.py` → `src.indexer accept`。詳細は `prepare_detail_adoption.py`／`detail_master.adopt` でID・手修正保全を確認し、Google Sheetsへの更新・完全XLSX往復照合を別工程で行う。CLIの候補生成だけではGoogleへ書き込まれない。
4. **日常編集**：非公開Google Sheetsが唯一の編集原本、`private/master.xlsx` は承認済みローカルスナップショット。全15タブ（基礎9＋詳細6）。接続先は `private/sheets-connection.json`。編集停止→新鮮なXLSX出力→`import_sheet_export.py review`→確認済み差分の `apply`。Sheetsとローカルを同時編集しない。
5. **公開用生成**：基礎は `src.indexer prepare`、詳細は `export_detail_sheet.py` → `detail_public.prepare`。同じ原本から基礎／詳細を結合し、公開許可項目だけ出力。生HTML・画像・効果全文・接続情報は公開しない。
6. **公開**：新しい隔離候補を検査・表示確認→`site/`へ採用→Git保存→Pages artifact配置→匿名URLと全ファイル照合。UI番号は画面・操作変更時だけ更新し、データのみの更新では維持する。

Google Sheetsの自動同期・自動公開は未実装。取得値の採用では原本コピー／API更新など明示操作と往復検証が必要。現行r21は同じnative URLを保持して更新した記録があり、常に新URLへ切り替える実装ではない。

## 5. 固定ID・手修正保持

- 基礎：UUIDの `card_id`／`family_id` と取得元別名の台帳。`key()` は取得元キー、またはUnicode URL＋派生種別。同じ別名へ再取得値を反映してもID・手修正を置換しない。手修正優先、意図的な空値は `clear_fields`。
- 手入力カードと後日取得カード：同一人物・P/S・派生・名称の類似候補は自動追加を拒否し、取得キー→既存UUIDの明示 `--mapping` で統合。公開済み重複IDのredirect統合は未実装。
- 詳細：UUIDの `detail_id`。カードID＋正規化名称＋種類／SP／解放条件／MB段階／Lv等を同一性キーにし、曖昧な同名項目では原セル位置を補助に使う。再採用は取得値だけ更新、`override` を保持。先行手入力との同一キー統合も実装・テスト済み。
- 同一性を判定できない名称／条件変更や既存項目消失は停止して確認。全件の消失キー・件数異常、重複・孤児ID、数式、保護列の変更を拒否。Sheetsのreview→apply間は入力SHAを照合し、保存前バックアップ・読み戻し検証を行う。

## 6. 実行コマンド

以下はWindows PowerShell・リポジトリ直下。Linuxでは `.venv/Scripts/python.exe` を `.venv/bin/python` に読み替える。Python3.12.14（Linux）／3.13.16（Windows）、Node24.19.0をCIで検証済み。Python依存は `requirements.txt`、Playwright1.62.1は `package-lock.json`。

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
npm ci
npx playwright install chromium
$env:XLSX_BACKEND = 'stdlib'
./.venv/Scripts/python.exe -m http.server 4173 --bind 127.0.0.1 --directory site
```

`XLSX_BACKEND=stdlib` はCodex依存バンドルなしのXLSX生成経路。既定のArtifact Tool経路は別途 `@oai/artifact-tool` が必要。公開Gitだけで閲覧・検証できるが、生応答・Google原本・接続先は含まれず、原本からの全再生成には別途アクセスが必要。

保存入力の変換例（出力先は未作成の固有名を使う。原本採用・公開なし）：

```powershell
$env:TRANSFORM_SCOPE = 'full'
$env:TRANSFORM_OUTPUT_ROOT = 'private/candidates/review-base-NEW'
./.venv/Scripts/python.exe scripts/full_transform.py
./.venv/Scripts/python.exe scripts/collect_detail_catalog.py status private/raw/detail-catalog-20261009
./.venv/Scripts/python.exe scripts/transform_detail_catalog.py private/raw/detail-catalog-20261009 private/candidates/review-details-NEW.json --save-state-snapshot private/candidates/review-state-NEW.json
```

原本取込・候補生成例。`<日時>` 等は実際の新鮮なエクスポート／未作成出力へ置換し、review結果確認後だけapplyする：

```powershell
./.venv/Scripts/python.exe scripts/import_sheet_export.py review private/master.xlsx private/sheets-exports/<日時>.xlsx private/audits/<日時>-review.json
./.venv/Scripts/python.exe scripts/import_sheet_export.py apply private/master.xlsx private/sheets-exports/<日時>.xlsx private/audits/<日時>-review.json
Copy-Item -LiteralPath site -Destination private/review-release-NEW -Recurse
./.venv/Scripts/python.exe scripts/export_detail_sheet.py private/master.xlsx private/review-release-NEW
```

上は基礎版不変の詳細更新用。基礎も変更する場合は先に `-m src.indexer prepare private/master.xlsx <基礎生成先>` → `scripts/stage_release.py <基礎生成先> <新候補> --previous-site site`、その候補へ詳細をexportする。UIソースの反映は `scripts/refresh_ui_assets.py <新候補>`。候補は検査前に現行siteへ上書きしない。

## 7. テスト・検証

```powershell
./.venv/Scripts/python.exe scripts/run_unit_tests_ci.py
npm test
./.venv/Scripts/python.exe scripts/check_site.py site
npm run test:ui
npm run test:search-ui
```

UI試験はローカル一時HTTPサーバーを自ら起動する。既存Edge使用時は `UI_BROWSER_PATH` に実行ファイルを指定。公開UIの再検証では `UI_BASE_URL=https://vignoles.github.io/shiny-index/` を設定する。通常ローカル試験時はこの環境変数を外す。

- 最新の保存結果：Python352／JS77、ローカル・公開6幅（1280/900/899/768/390/320）、Chromiumタッチ2設定、検索488セット（450をCI再現、追加38を公開で確認）。独立期待集合は97セットで、全488が独立オラクルではない。
- 過去補正／複合／ランダムの個別回帰は `tests/ui-user-confirmations-smoke.mjs`、`tests/ui-v24-compound-smoke.mjs`、`tests/ui-v22-random-smoke.mjs`。全件表示1,466・ID重複0、公開106全バイト一致の記録あり。
- 最新CI：[38206999061](https://github.com/VIgNOles/shiny-index/actions/runs/38206999061)（Windows／Linux成功）。証拠は `docs/ui-v26-verification.md`、ローカル詳細は `private/audits/filter-ui26-20261012/`。
- 隔離障害・復旧は `scripts/recovery_drill.py --output private/recovery/review-NEW`。原本／接続が必要。旧データを本番へ戻す検証ではない。

## 8. 公開・切り戻し

候補の `check_site.py`、単体／UI試験、原本・Web・配布版／ハッシュ、Git blobとローカル成果物の一致を確認してから、旧siteを保持して候補を採用する。公開対象だけ明示してGitへ保存する。`site/` はignore対象だが現行106ファイルは追跡済み、新バンドルの追加には `git add -f site` が必要。`.gitattributes` の `site/** -text` を維持する。

Pagesはmainのコミットメッセージが `publish: ` で始まるpush、または手動workflow_dispatchで起動。通常pushだけでは公開しない。

```powershell
git commit --allow-empty -m "publish: validated site"
git push origin main
./.venv/Scripts/python.exe scripts/check_public.py site https://vignoles.github.io/shiny-index/
```

直近の公開：[Pages38207668344](https://github.com/VIgNOles/shiny-index/actions/runs/38207668344)、公開コミット `a1e7494e78de59a87bf50162d30224ddfafb86c0`。成功後、匿名表示・版・更新日・全ファイル一致まで確認する。

UI25への切り戻し候補（現行原本・不変バンドルを保持し、公開はしない）：

```powershell
./.venv/Scripts/python.exe scripts/build_ui_rollback.py --ref ui-v25-20261012 --source site --output private/review-ui25-rollback-NEW
./.venv/Scripts/python.exe scripts/check_site.py private/review-ui25-rollback-NEW
```

候補の表示はタグ側の対応試験で確認する（現行試験はUI26の画面を期待）。確認した候補だけ新しいmainコミットとして公開する。Git履歴の強制巻戻しや原本の巻戻しは行わない。データ版も戻す場合は対応するHTML・基礎／詳細pointer・モジュールを組で選び、候補検査が必要。`src.indexer rollback` は基礎版用であり、詳細を含む全面復旧を単独で行うコマンドではない。

UI25切戻し候補3幅と、UI26のsite106＋原本＋接続のZIP108実復元は合格記録あり。本番全面障害注入・本番UI25切戻しは未実施。ZIP所在・SHA・復元先は `private/audits/filter-ui26-20261012/archive-proof.json`、手順はoperationsとUI26検証記録を参照。

## 9. 現在のGit状態

- ブランチ `main`、origin `https://github.com/VIgNOles/shiny-index.git`。
- HEAD／origin/main／今回 `ls-remote` で確認したremote main：`dd5f4d9a6753520c995ca25e68c1cf09726fd6bd`（最終検証・引継ぎ文書の保存コミット）。本メモ作成前のworktreeはclean。
- 公開タグ `ui-v26-20261012` → `a1e7494e78de59a87bf50162d30224ddfafb86c0`。前版 `ui-v25-20261012` → `485e5d9e29780ad8f349000de40ed5f3c771954d`。
- 本依頼では `REVIEW_HANDOFF.md` だけ新規作成し、未コミットで保存。コード・データ変更／コミット／push／再公開は行わない。

## 10. 既知の未対応・例外

- **ユーザー指定保留**：個別Wikiページなし47件の詳細、実在する新規基礎カードの本番追加・公開反映実証。基礎追加の隔離試験・詳細追加／修正の反映試験は済んでおり、機能未実装と同義ではない。
- **出典の欠損**：実装日56件、S90カードの最大Lv360セル。期間10項目はユーザー指示で推定せずスキップ。数量が分かる場合だけ構造化し、期間下限検索には一致させない。
- **解決済み**：不明確だった5条件、ユーザーが指定した属性・回復の誤記、ROOTSの倍率単位。根拠はTASKと判断台帳。担当者による独立ゲーム画面照合ではない。
- **対象外／未実装**：Pステージ・適正、Sファイトの収集、新人物辞書の簡単な登録UI、新規詳細スキルの簡単な入力UI、Sheets自動同期。詳細新規入力には構造入力 `add_manual` が必要。
- **公開UI方針**：CSV導線は非表示。旧不変バンドルのCSV直接URLは維持。問い合わせは必須要件から削除済みで、管理者からの回答は未取得。
- **未確認**：全効果・発動制限の独立公式網羅、Google原本の実画面、全面実機Safari／Android／スクリーンリーダー適合、非公開全入力の別PC再変換、本番全面復旧。ブラウザーエミュレーションやCI合格で代替済みとは扱わない。

## 11. 特にレビューしてほしいリスク箇所

以下はレビュー観点であり、未検証の不具合が存在すると断定するものではない。

1. **検索の正確さ**：`web/details.mjs` のパッシブ／上限読取アダプター、同一スキル・同一効果・同一ランダム候補のAND、通常／Link／Plus等の範囲、対象・期間・単位。生JSONの互換集計944を現行値として扱わないこと。
2. **原本・同一性**：`detail_master.alias/adopt` の名称／SP／解放変更・セル移動への挙動、手入力→取得照合、mapping、13手修正保持、Googleとローカルの古いエクスポート・同時編集防止。
3. **公開変換の意味と漏洩防止**：`skill_effects.py` 等の正規表現・隣接効果の誤継承、`detail_public.py` の許可項目・未知フィールド拒否。未収集／原文空欄／未構造化を「効果なし」と誤表示しないこと。
4. **UI状態とURL互換**：`app.mjs` の通常即時反映と詳細下書きの分離、取消・履歴・幅変更・不正入力・0件、旧URLのOR／ANDと人物優先規則、キーボード／フォーカス。
5. **公開・復旧の整合性**：HTML／基礎／詳細／UI資産クエリの版、旧キャッシュ、全ファイルSHA、改行変換、不変版保持。Pagesと検証CIは独立workflowで、Pages内はcheck_site中心、CI成功への `needs` 連結はない。現行手順では公開前のテスト成功確認が別途必要。
6. **停止・再開と取得負荷**：共通ロック・PID判定・保存成功後の状態回復、429／Retry-After／HTTP200エラーページ拒否、二重起動防止。レビューのために全再取得・待機短縮を行う必要はない。
7. **検証・文書の限界**：多くのUI期待値は同じ検索関数を利用し、独立集合は97セット。私的証拠・原本は公開cloneにない。旧版を含む長い手順書の記述と現行コードとの差、Windows日本語パス・環境依存も確認対象。

## 12. 最初に読む順番

1. 本メモ → `HANDOFF.md` 冒頭の `current-state`。
2. `TASK.md` の元依頼・明示変更 → ローカルにあれば `design.md`（Gitにはない）。
3. `docs/ui-v26-spec.md` → `docs/filter-design-20261012.md` 13・14章 → `docs/ui-v26-verification.md`。
4. `docs/verification.md` の完成条件表 → `docs/source-review-decisions-20261012.json`。
5. `operations.md` の該当操作・末尾r21節 → `docs/card-details-integration.md` の原本／編集手順 → `sources-policy.md`／`source_manifest.json`。
6. `src/indexer.py` → `src/detail_master.py` → `src/detail_public.py` と条件／効果解析 → `web/search.mjs`／`web/details.mjs` → `web/app.mjs`。
7. 対応 `tests/` → `.github/workflows/verify.yml`／`pages.yml` → 現行 `site/*/latest.json`・各manifest。ローカル証拠が必要な場合だけ `private/audits/filter-ui26-20261012/` と原本を読む。

## 正式基準版保存時の追記（2026-10-12）

上記Git／未コミット状態は本メモ作成時点の記録。後続の正式基準版B1 `baseline-pre-review-v1-20261012` に本メモとREVIEW_DEVELOPER／REVIEW_PRODUCTを保存する。コード・データ・UI26は維持し、レビュー指摘は未反映。今回再検証した450検索セット・公開106・原本再生成と、正式な復元手順／Git確定状態は [基準版記録](docs/baseline-pre-review-v1-20261012.md) と非公開バックアップBASELINE_MANIFEST.json/save-proof.jsonを参照する。
