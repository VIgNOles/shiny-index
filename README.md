# enza版シャニマス カード索引

現在は**全期間のWiki一覧から1,466索引行を収録したローカル版**です。一般公開は許可確認待ちです。
一覧掲載1,410件＋ロード派生56件。個別Wikiページ未作成47件も収録し、未掲載と表示します。
ゲーム全網羅・公式照合は未完了です。P/S・分冊の重複・出典を監査しました。

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

```powershell
./.venv/Scripts/python.exe scripts/sample.py
./.venv/Scripts/python.exe -m src.indexer accept private/sample-batch.json private/master.xlsx
./.venv/Scripts/python.exe -m src.indexer prepare private/master.xlsx dist
./.venv/Scripts/python.exe -m http.server 4173 --bind 127.0.0.1 --directory dist
```

`sample.py`はdesign.mdと`private/raw/sample.html`が必要です。生応答は公開Gitへ入れません。
取得する場合はoperations.mdの少数取得手順を使用してください。
閲覧先はローカルの `http://127.0.0.1:4173`。公開URLではありません。

```powershell
./.venv/Scripts/python.exe -m unittest discover -s tests -v
node --test tests/search.test.mjs
./.venv/Scripts/python.exe scripts/update_drill.py
```

設計変更と制約はdesign.md 17章、操作はoperations.md、結果はdocs/verification.md。
`private/`には原本・取得応答・バックアップを置きます。公開禁止です。
公開するのは検証済み`dist/`だけで、コードとは別にデータの公開条件を確認します。

## 実装範囲

- 1ページの取得、応答・ハッシュ・取得記録の保存
- C01向け保存応答のオフライン照合と全期間の一覧HTMLパーサー
- XLSX原本、固定UUID、取得別名、項目単位出典、手修正優先
- 同一run再適用、照合候補保留、型・日付・欠落・件数異常の停止
- 不変版のJSON/CSV/XLSX、同一内容検証、版選択の復旧
- レスポンシブ検索、複数選択、日付範囲、並べ替え、検索結果CSV

Google Sheetsへの作成はDrive容量超過で失敗しました。Sheetsの自動読書き連携は未実装です。
公開コードの配置先は https://github.com/VIgNOles/shiny-index です。Wiki由来データは許可確認前にpushしません。

## 全件版のオフライン再変換

`private/raw/`内のp-list、s-list、s-volume、collab、road、chronologyの6取得runを使用します。

```powershell
./.venv/Scripts/python.exe scripts/full_transform.py
```

結果はprivate/full-batch.jsonとprivate/full-audit.json。初回全件取込用候補として作成します。
既に全件原本がある場合は、監査後にscopeをfullとして別候補へ保存してacceptします。
件数減少・既存キー消失・5%以上または20件以上の件数変動は自動採用できません。
閾値を回避せず、変更の原因と掲載単位を調査してください。
公開リポジトリのテストは合成データを使い、非公開のWiki生応答に依存しません。

PowerShellで代替出力を選ぶ例：

```powershell
$env:XLSX_BACKEND = 'stdlib'
./.venv/Scripts/python.exe -m src.indexer prepare private/master.xlsx dist
```

同じ論理データ版になりますが、XLSXのバイト列とファイルSHA-256は出力実装によって異なります。

将来の全一覧再取得は新しいrunディレクトリを指定します。1ページずつ5秒以上空け、6ページで終了します。取得失敗時はそのrunを失敗として残し、原本に触れません。

```powershell
./.venv/Scripts/python.exe scripts/collect_all.py private/raw/next-run
$env:RAW_RUN_ROOT = 'private/raw/next-run'
$env:TRANSFORM_OUTPUT_ROOT = 'private/candidates/next-run'
./.venv/Scripts/python.exe scripts/full_transform.py
```

新しい取得runでは`TRANSFORM_OUTPUT_ROOT`が必須です。候補・監査・人物ID台帳を隔離出力し、既存内容と異なるファイルの上書きは拒否します。初期人物IDは`private/idol-registry.json`から引き継ぎます。検証した候補だけを別操作でacceptします。
