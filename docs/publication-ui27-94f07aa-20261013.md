# UI27公開完了記録（2026-10-13 JST）

公開URL：[enza カード索引](https://vignoles.github.io/shiny-index/)。ユーザーが明示承認した [94f07aa](https://github.com/VIgNOles/shiny-index/commit/94f07aad3e92e98617ce494e3562bbe9c6dfe57a) をそのまま公開した。公開後の実URLで内容と操作を確認し、重大な不一致・失敗は検出しなかった。保存タグは `ui-v27-20261013`（対象commitは94f07aa）。この記録を含む後続コミットは文書だけで、公開資産を変更しない。

## クラウドCIと公開成果物

| 確認 | 結果 |
|---|---|
| コミット | full `94f07aad3e92e98617ce494e3562bbe9c6dfe57a`。通常のfast-forwardでmainへpush |
| 通常CI | [38357356411](https://github.com/VIgNOles/shiny-index/actions/runs/38357356411)、Linux／Windowsとも成功 |
| 公開CI・Pages | [38357469472](https://github.com/VIgNOles/shiny-index/actions/runs/38357469472)、同じcommitのLinux／Windows検証とdeployが成功 |
| クラウド試験 | 両OSでPython379件・JS97件成功。クラウドではsymlink試験も通過しskipなし |
| 試験済みartifact | `github-pages`／ID11794241873／56,063,930 bytes。試験前後の108ファイルと、upload後の実tarの全ファイル集合／SHA一致を確認 |
| Deployment | ID7031947212、SHA94f07aa・公開URL・上記runの対応とsuccessを確認 |

artifact digest：`sha256:2f830957ca667019728ebb38c0f6992e3163bf69836b169585f660376c2d0a08`。CI内でsiteを再生成せず、検証した同じartifactを配置した。pushによるPages run38357356883はcommitメッセージ条件により設計どおりskipであり、公開は上記手動runで実行した。

## 実公開URLでの確認

- Git blobから直接確定した108ファイルと、匿名GETの全108ファイルがHTTP200・全バイト／SHA一致。ブラウザーが参照する `?ui=27` 付きapp／style／search／detailsも4件すべて一致。
- 基本・詳細検索450セットが成功（独立期待97）。全1466件のID重複なし、Wikiリンク1419、個別ページなし47、不正条件からの復帰7を確認。
- PC／スマホ1280・900・899・768・390・320幅、ChromiumのiPhone13／Pixel7タッチ設定、数値・範囲・必要特訓・育成特性の3幅が成功。
- 固定ID個別URL、条件コピー、2〜4枚比較を1280／390／320幅で確認。値・条件・確率・回数・解放段階、Lv式・取得表、旧チャージ参考値、履歴と下書きの扱いを保持。
- 共有URL欄の再発試験を実公開ページの3幅で実施。入力直後・条件選択・解除・並べ替え・履歴・スマホ詳細条件で旧URLと通知を消去。180ms待ち前の遅延clipboard成功／拒否、逆順のコピー結果、IME入力でも旧表示が復活しない。条件不変の比較・詳細展開・追加表示では現在のURLを維持。
- 公開画面のPC／スマホ画像を目視確認し、ページ外への横はみ出し・表示崩れを検出しなかった。スマホ比較表の長さは保留のままで、表示設計を変更していない。

公開用2試験が元々local server固定だったため、追跡ソースを変えずprivateの一時実行版で配信元だけを実公開URLへ差し替えた。期待値は94f07aaのデータから照合した。故障ケースのネットワーク／clipboard差し替えはブラウザー内の試験だけで、公開サーバーを変更していない。

## 保全・状態・証拠

UI27／基礎v1-93a6a8b8d40e754a・1466件／詳細d1-4123183cd3640b4e・1419カード・24025項目・20096効果。原本r21／13手修正は不変。原本・接続・保存入力4268ファイルのSHAを再確認し変更0。基準版B1と旧公開版の復旧保存を保持し、Google原本書込・Wiki取得は行っていない。

実機Safari・物理端末全面・スクリーンリーダー・全効果の独立公式網羅は今回の確認範囲外。47個別ページ、曖昧表記7項目、高度な可変値／確率検索、索引分割等の保留・不採用は維持する。

証拠は `private/audits/publication-94f07aa-20261013/`：Git由来manifest、CI／artifact／deploymentのAPI応答・独立監査、匿名108件・query4件のSHA、公開UI／検索／共有／再発試験のログ・JSON・画像、原本保全、publication-complete.json。データ全コピーや原本の再生成は行わず、省容量で保存した。
