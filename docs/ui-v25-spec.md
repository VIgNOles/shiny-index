# UI v25：欲しいカード・性能から探す

実装仕様は[検索フィルター再設計](filter-design-20261012.md)。検証状況は[UI25検証記録](ui-v25-verification.md)。基礎データ版・詳細データ版・原本r21は変更しない。

- 人物を独立配置し、シリーズ・入手の通常欄から重複する区分を取り除く。旧URLのOR/ANDと人物の優先規則は互換欄に保持。
- 探す情報とライブの種類を分け、効果を用途別に分類する。パッシブ/上限の保存済み数値を読取専用で検索へ接続。
- 同じスキル/同じ効果の一致を保ち、一致理由・特訓/SP/Lvと該当箇所を表示。ライブの通常部分とLink等を区別。
- 適用できない条件と正しい0件を分け、部分・グループ解除を用意。全解除でも並べ替えを維持。
- 900px以上は即時反映、899px以下は人物以降を編集→一括適用。キャンセル・Esc・戻る・幅変更で未適用の編集を破棄。
- カレンダー/年月日入力は同じ値を保持。IME確定後180msで検索する。

旧版との意図した差：パッシブ/上限＋属性条件は保存先の制限を修正したため、UI24では0件だったカードも結果に含まれる。継続UPの意味や旧54種類の効果predicateは変更しない。性能検索は未収録/未構造化範囲を含むゲーム全体の不存在判定には使えない。

## 再現

既存セットアップ後に `npm ci`、`npx playwright install chromium`、`npm test`、`npm run test:ui`。Windowsでインストール済みEdgeを使う場合はPowerShellで `$env:UI_BROWSER_PATH='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'`。テストはローカルHTTPサーバーを自動起動する。公開確認は `UI_BASE_URL=https://vignoles.github.io/shiny-index/`、期待版は `UI_EXPECTED_VERSION=ui-v25`。新規依存はなくPlaywright1.62.1を継続する。Linux CIでもブラウザー導入後に同じ受入テストを行う。

候補の5画面資産だけを再作成するには `python scripts/refresh_ui_assets.py private/site-filter-ui25-20261012`。データは再生成せず、既存ポインターの版をHTMLへ埋め込む。検証後に同じ5資産をsiteへ反映する。途中で中断した場合も5資産を再作成して検証し、部分状態を公開しない。

## 切戻し

UI24正常保存点は `ui-v24-before-filter-redesign-20261012`。`python scripts/build_ui_rollback.py --ref ui-v24-before-filter-redesign-20261012 --source site --output private/site-ui24-restore-candidate` で未作成の隔離候補を作り、旧UIの表示・データ版を確認する。原本/取得データを巻き戻さず、候補の5資産のみをsiteへ反映して `publish: ` コミットで公開できる。今回本番の切戻しは行わない。

実行環境補足：この作業環境の共用node_modulesは変更しない。npmが同梱されていなかったため、公式registryのintegrityを検証したnpm11.6.2をprivateへ展開し、隔離projectでpackage-lock.jsonを生成した。ルートにはlockのみを保存。通常のNode+npm環境とCIはnpm ciで再現できる。旧ランダム回帰はr21の回答反映に合わせROOTS_CONFIRMED=1とUI_EXPECTED_VERSION=ui-v25を指定する。

次回UI番号を更新する場合は、HTMLのCSS/appとappのdetails/searchのuiクエリも同じ番号へ揃える。データだけの更新ではUI番号とクエリを変えない。
