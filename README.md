# enza版シャニマス カード索引

現在は**全期間のWiki一覧から1,466索引行を収録した公開版**です。[公開サイト](https://vignoles.github.io/shiny-index/)をログインなしで閲覧・検索・取得できることを確認しました。
一覧掲載1,410件＋ロード派生56件。個別Wikiページへのリンクがない47件も索引に収録済みで、リンクの現況確認・追加は一旦保留しています。
公開中のデータ版はv1-93a6a8b8d40e754a（収録確認日2026-10-08、P548/S918）。カード内容は前版と同じで、確認範囲を更新しました。
UI版はui-v4です。旧UIはGitタグ ui-v1-20261008、ui-v2-20261008、ui-v3-20261008 に保存し、[UI設計記録](docs/ui-v4-spec.md)と[切り戻し手順](operations.md)を用意しました。
ゲーム全網羅・公式照合は未完了です。P/S・分冊の重複・出典を監査しました。Wikiの凡例と補助ページで未確定だった入手分類21行を確認し、ローカル版へ反映しました。
編集原本は指定アカウントの非公開Google Sheetsです。9タブ・1,466件を実エクスポートで照合済み。公開用のローカルXLSXは承認済みスナップショットとして保持し、更新手順はoperations.mdに記載しています。

## セットアップ

Windows PowerShell、Python 3.12.14、Node.js 24.19.0で検証しました。

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
```

XLSX生成にはCodex付属 `@oai/artifact-tool` が必要です。今回の依存バンドルは26.909.12148。
`load_workspace_dependencies`でNodeパッケージの場所を取得し、このフォルダーの`node_modules`へジャンクションを作ります。
Codex依存バンドルがない環境では `XLSX_BACKEND=stdlib` を設定するとPython標準ライブラリだけでXLSXを生成します。この経路も全1466件で各形式の読み戻し検証を通しました。通常環境ではArtifact Tool経路を使います。
Python/JS検索テストと保存済み公開ファイルの検証は、それぞれrequirements.txtとNodeだけで実行できます。
検索結果CSVボタンと全件CSVリンクはUI v4で画面から外しました。既存の不変データ版にあるCSVファイルの直接URLは維持しています。JSONとExcelの取得導線は画面に残しています。
UI操作の再現試験はPlaywright 1.62.1を使います。通常のNode/npm環境では npm install と npx playwright install chromium を実行します。既存Edgeを使うWindows環境では UI_BROWSER_PATH に msedge.exe の絶対パスを指定して node tests/ui-v4-smoke.mjs を実行できます。ブラウザ試験はローカルsiteを127.0.0.1の一時サーバーで開き、公開データを変更しません。


別環境で全件版を再生成するには、上記依存関係の導入後、指定アカウントの非公開Google Sheets原本を「ファイル → ダウンロード → Microsoft Excel」から取り出し、Git対象外の `private/master.xlsx` に配置します。取得済み生応答やSheets原本のURL・IDは公開リポジトリに含まれません。新環境でSheetのURL・所有者を確認し、`private/sheets-connection.json` は安全な経路で移すか新しく作成してください。保存した原本を読み戻してから全件版を生成・検証します。

```powershell
./.venv/Scripts/python.exe -m src.indexer prepare private/master.xlsx private/rebuild-site
./.venv/Scripts/python.exe scripts/check_site.py private/rebuild-site
```

```powershell
./.venv/Scripts/python.exe scripts/sample.py
./.venv/Scripts/python.exe -m src.indexer accept private/sample-batch.json private/examples/sample-master.xlsx
./.venv/Scripts/python.exe -m src.indexer prepare private/examples/sample-master.xlsx private/examples/sample-site
./.venv/Scripts/python.exe -m http.server 4173 --bind 127.0.0.1 --directory private/examples/sample-site
```

`sample.py`はdesign.mdと`private/raw/sample.html`が必要です。生応答は公開Gitへ入れません。
取得する場合はoperations.mdの少数取得手順を使用してください。
閲覧先はローカルの `http://127.0.0.1:4173`。公開URLではありません。上の少数例は隔離した原本と表示先を使い、全件原本`private/master.xlsx`や全件バンドル`dist/`を変更しません。既存の全件版を表示するときは`--directory dist`へ切り替えます。

```powershell
./.venv/Scripts/python.exe -m unittest discover -s tests -v
node --test tests/search.test.mjs
$env:UI_BROWSER_PATH = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
node tests/ui-v4-smoke.mjs
./.venv/Scripts/python.exe scripts/update_drill.py
./.venv/Scripts/python.exe scripts/check_public.py site https://vignoles.github.io/shiny-index/
```

公開URLのUIも確認する場合は、UI_BASE_URL を https://vignoles.github.io/shiny-index/ に設定して同じ node tests/ui-v4-smoke.mjs を実行します。UI_BROWSER_PATH を設定しない場合は npx playwright install chromium でブラウザを導入します。

設計変更と制約はdesign.md 17章、操作はoperations.md、結果はdocs/verification.md。
`private/`には原本・取得応答・バックアップを置きます。公開禁止です。
公開するのは`dist/`から検証・隔離した`site/`だけです。private/の原本・生応答は含めません。

## 実装範囲

- 1ページの取得、応答・ハッシュ・取得記録の保存
- C01向け保存応答のオフライン照合と全期間の一覧HTMLパーサー
- XLSX原本、固定UUID、取得別名、項目単位出典、手修正優先
- 同一run再適用、照合候補保留、型・日付・欠落・件数異常の停止
- 不変版のJSON/CSV/XLSX、同一内容検証、版選択の復旧
- レスポンシブな縦一覧と詳細開閉、複数選択、階層人物・8区分の近道・系列／入手区分、部分日付、公式順

ユーザー指定アカウントの非公開Google Sheetsへの原本移行は完了しました。現行原本はrevision 7、1,466件、9タブで、実XLSXエクスポートとの往復一致を確認済みです。Sheetの自動読書き同期は未実装のため、XLSXエクスポートの検証・採用CLIと、取得値採用時の新Sheet切替手順をoperations.mdに記載しています。
公開先は https://github.com/VIgNOles/shiny-index です。ユーザーの明示方針とsources-policy.mdに従い、検証済みの事実索引だけを配置します。Wikiへの問い合わせ回答は未取得です。

## 全件版のオフライン再変換

`private/raw/`内のp-list、s-list、s-volume、collab、road、chronology、gachaの7取得runを使用します。

```powershell
$env:TRANSFORM_SCOPE = 'full'
$env:TRANSFORM_OUTPUT_ROOT = 'private/candidates/replay-example'
./.venv/Scripts/python.exe scripts/full_transform.py
```

中断runと後続の単一ページを組み合わせる場合は、operations.mdのscripts/compose_saved_run.py手順でURL・ハッシュを確認してから新しい非公開入力を作ります。
結果は指定先のfull-batch.jsonとfull-audit.json。原本が未作成の初回だけ`TRANSFORM_SCOPE='initial-full'`を使います。既に全件原本がある場合は`full`候補を`scripts/review_batch.py`で現行原本と比較し、新規・変更・消失・手修正衝突を監査してからacceptします。レビュー出力は原本を変更しません。
件数減少・既存キー消失・5%以上または20件以上の件数変動は自動採用できません。
閾値を回避せず、変更の原因と掲載単位を調査してください。
公開リポジトリのテストは合成データを使い、非公開のWiki生応答に依存しません。
公開候補は`scripts/stage_release.py dist site`で最新の完成版だけを隔離配置できます。`site/`は公開済みの完成版です。更新時も検証後に`git add -f site`で明示的に追加します。ファイルのハッシュを保つため`.gitattributes`でsite配下の改行変換を無効にしています。

PowerShellで代替出力を選ぶ例：

```powershell
$env:XLSX_BACKEND = 'stdlib'
./.venv/Scripts/python.exe -m src.indexer prepare private/master.xlsx dist
```

同じ論理データ版になりますが、XLSXのバイト列とファイルSHA-256は出力実装によって異なります。

2026-10-08のW09 HTTP 429後、ユーザーは過負荷を避ける範囲での再開を指示しました。全7ページの連続取得は引き続き無効（full_collection_enabled=false）で、直接のcollectコマンドも停止します。scripts/collect_one.pyだけが、取得状態ファイルで24時間以上の間隔を確認して、一覧に登録された1ページを手動で確認できます。429なら自動リトライせず、Retry-Afterがあればその期限も守ります。2026-10-08にユーザーが明示した一度限りの期限前確認でW09を1ページ取得し、保存済みの他6ページと組み合わせてオフライン再変換しました。1,466件のカード差分は0で、確認範囲を2026-10-08へ更新したrevision 7を正式Sheetへ昇格しました。以後は通常の24時間ゲートに戻り、全7ページ連続取得は停止したままです。使い方と停止・復旧はoperations.mdを参照してください。

新しい取得runでは`TRANSFORM_OUTPUT_ROOT`が必須です。候補・監査・人物ID台帳を隔離出力し、既存内容と異なるファイルの上書きは拒否します。初期人物IDは`private/idol-registry.json`から引き継ぎます。検証した候補だけを別操作でacceptします。


カードのライブスキル等の詳細情報は未収録です。P/S別の項目、MB・所持スキルとの区別、今後の検索・検証手順は [詳細データの収集前設計](docs/card-details-design.md) を参照してください。今回の設計では原本・公開データを変更していません。
