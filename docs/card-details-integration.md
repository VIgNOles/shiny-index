# 詳細情報の原本・Web・配布データ接続（UI v5）

2026-10-09 JST。現行基礎索引は1,466件（P548/S918）、基礎版 `v1-93a6a8b8d40e754a`。詳細は段階的な収録で、206カード（P103/S103）・2,845項目、`d1-d3a4bf450390442b`、詳細原本revision7。**全件詳細版は未完成**。公開URLでの最終検証結果は末尾へ追記する。

## 原本と出力

指定アカウントの既存r7をGoogle Sheets上で丸ごとnativeコピーし、元の9タブを保持したまま詳細6タブを加えた。59カード855項目の全値一致と既存9タブ差分0、続く実P【283プロのヒナ】詳細追加1件・名称手修正1件後の60カード865項目一致を、実XLSXエクスポートから確認した。名称訂正は `1/60・NaturalHeart+(☆4)` → `1/60・NaturalHeart+`、特訓4は解放条件として保持する。取得名称は変更していない。

所有者のみ・Asia/Tokyo・15タブ・固定IDと全値一致を確認して編集原本を切り替えた。URL/ID・ローカル基準・バックアップ・履歴は非公開の `private/sheets-connection.json`。旧r7と `private/master-r7-before-details-20261009.xlsx` は保持する。基礎revision7・基礎カード内容と版は不変。

| タブ | 用途 |
|---|---|
| 詳細カード | 固定card_idによるP/S、Sの属性・最大Lv。取得カードレコードを保持 |
| 詳細項目 | 固定detail_id、取得値、手修正、理由・根拠・日時。編集欄はG～M |
| 詳細属性 | サポートスキルの取得Lv／スキルLvの子行 |
| 詳細出典 | 個別Wiki URL・取得日時・応答SHA256・原表の位置 |
| 詳細収録範囲 | 全1,466card_idの原本採用時点の入力・変換状態 |
| _detail_meta | schema・凍結した取得元基礎版・詳細revision・入力候補ハッシュ |

`src/detail_master.py` は取得値と手修正を分離する。再取得は手修正とdetail_idを保持し、同じ同一性キーで先に手入力したスキルを後から取得しても統合する。位置が変わる明確な項目も同じID。曖昧な複数セルには位置を補助キーに使う。名称/SP/解放条件が変わって同一性が判別できない場合、または既存項目が消失した場合は、正常原本を残して対応付けを確認する。

## 公開情報と検索

`details/<d1版>/details.json`、`manifest.json`、`details/latest.json`を別バンドルにする。HTMLに基礎版と詳細版を固定し、JSONと版情報の一致、ファイルSHA256を確認してから表示する。基礎更新後もcard_idとP/Sを確認し、新しい基礎版へ詳細を結ぶ。凍結取得カタログにない新規基礎カードは `not_in_acquisition_catalog` と区別する。

公開するのはスキル名・種類・SP・解放条件・MB段階・機能タグ・上限、S属性・最高Lvの値（空欄はnull）、所持/サポートのLv対応、原セル位置とURL・ハッシュ、認識した個々の参考数値。Wiki原HTML、画像、効果全文、内部入力ディレクトリを配布しない。発動条件・複合効果・追加効果は未構造化のものがあり、参考数値を無条件の全効果と表示しない。ここは残る実装対象。

種類・キーワード・Link/Plus/Change/Grow/Refrainは**同じスキル行**に一致する必要がある。機能の複数選択はOR、種類とキーワードとはAND。機能フィルターに思い出のLinkを混ぜない。Pパネル、MB、S所持ライブ、パッシブ、固有アビリティ、上限、クイック、思い出、サポートを表示上も区別する。Pステージ・適正、Sファイトは今回対象外。未収録を「該当なし」と推測しない。

## 詳細を修正する手順

1. `private/sheets-connection.json` の現在の原本を開き、詳細項目でカード名/ID・スキル名を確認する。A～F、N～Pの取得列とIDを変更しない。
2. G（名称）、H（SP）、I（非公開効果）、J（機能タグJSON、例 `["link","plus"]`）の必要な欄だけ編集する。手修正を解除する場合はその欄を空欄にする。Kに理由、Lに根拠（Wiki URL等）、MにISO日時を記入する。数式は使用しない。
3. 更新中は編集を止め、原本をExcel形式で `private/sheets-exports/<日時>.xlsx` にダウンロードする。基礎/詳細を一緒にreviewし、内容と出力ハッシュが一致する場合だけapplyする。ローカルとSheetsを同時編集しない。

```powershell
./.venv/Scripts/python.exe scripts/import_sheet_export.py review private/master.xlsx private/sheets-exports/<日時>.xlsx private/audits/<日時>-review.json
./.venv/Scripts/python.exe scripts/import_sheet_export.py apply private/master.xlsx private/sheets-exports/<日時>.xlsx private/audits/<日時>-review.json
```

4. 基礎版を同じ版で維持する詳細更新では、現行siteを新しい候補フォルダーへコピーする。原本エクスポートから詳細を生成し、検査・ブラウザ試験を通してから明示公開する。既存版ディレクトリを編集しない。

```powershell
Copy-Item -LiteralPath site -Destination private/detail-update-candidate -Recurse
./.venv/Scripts/python.exe scripts/export_detail_sheet.py private/sheets-exports/<日時>.xlsx private/detail-update-candidate --master-snapshot private/details/<日時>.json
./.venv/Scripts/python.exe scripts/check_site.py private/detail-update-candidate
$env:UI_BROWSER_PATH='C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
$env:UI_EXPECTED_VERSION='ui-v6'
node tests/ui-v4-smoke.mjs private/detail-update-candidate
node tests/ui-v5-smoke.mjs private/detail-update-candidate
```

基礎カード追加/修正の手順はoperations.mdの「追加・手修正」。基礎も更新する場合は基礎版のprepareを先に新規候補で実行し、上記詳細エクスポートをその候補へ追加する。card_id/P/Sと収録範囲が一致しない場合は公開せず原本と結合を修復する。取得値の詳細追加は、保存HTMLの変換候補を `adopt` で既存台帳へ採用し、原本をnativeコピーして追加する。新規スキルを原本へ手登録する簡単な画面はまだなく、`add_manual` の構造入力が必要（先行入力後の統合はテスト済み）。

## 取得・中断・復旧

全件1,363個別ページの取得を1件ずつ60秒以上で続行中。正常保存済みページは再送しない。現在の処理状態は `private/raw/detail-catalog-20261009/state.json` とworker.lock、workflow-report.json、stdout/stderr-workflow-009.logで確認する。PC終了や利用上限でジョブが終わった場合、docs/card-details-full-acquisition.mdのPID確認・残留ロック・保存成功回復を先に行う。新しいジョブを重ねて起動しない。

HTTP200短文の誤検知は `private/audits/detail-shape-false-positive-20261009.json` に根拠を保存し、履歴は削除していない。実HTTP失敗・Retry-Afterは解除していない。変換と原本採用、公開は取得とは独立し、異常入力は正常な原本・siteに自動反映しない。詳細数の異常・重複・未知P/S・孤児ID・ファイル改変は検査で拒否する。壊れた更新の復旧は正常な原本コピーと不変d1バンドルから新しい候補を作り、検査後に公開する。UI v4へはタグ `ui-v4-20261009` とbuild_ui_rollback.pyを使う。原本は切り戻さない。

## 検証と未完了

- Pythonの固定ID、手修正保持、手入力→取得統合、消失拒否、正の公開項目、件数/ハッシュ異常拒否、式拒否、詳細タブ保存、基礎/詳細同時取込を検証。
- JSの同一スキル行の条件一致、思い出とライブの分離、全角検索、未収録除外を検証。
- PC1280px・390px・320pxの基礎回帰と詳細検索/開閉/URL再読込/数値/JSON取得をEdgeでPASS。スマホ幅の実表示画像も確認。最高Lv空欄を低いLv値へ置き換えない。
- 原本1詳細追加・1項目修正がローカルWeb/配布データへ反映し、再変換後も修正/IDを保持。これは基礎カードの新規追加を本番反映した実証ではない。
- 未完了: 全件詳細取得・全節構造対応・84ロード関連card_idの派生対応・効果条件の全面構造化・公式独立照合。個別ページなし47件は指示により保留、初回実装日不明56件は未解決。実機スマホ/スクリーンリーダー全面検査も未実施。


## 公開URLでの結果（2026-10-09）

準備コミット0de2db2とタグui-v5-20261009をoriginへ保存。明示公開コミットb82cebbの[Actions run 37886161208](https://github.com/VIgNOles/shiny-index/actions/runs/37886161208)はsuccess。匿名の[公開サイト](https://vignoles.github.io/shiny-index/)で32/32ファイルがsiteとバイト一致し、基礎・詳細のPC1280px/390px/320pxの操作、MB Plusと通常Linkの分離、最高Lv欠損表示、版とJSON取得がPASS。画面と詳細JSONはd1-ee415ee7fa6b3d80で一致する。基礎v1版と1,466カードは不変。

名称訂正とP詳細追加の原本内容が、公開JSONと表示へ反映された。再取得入力のオフライン再採用でも固定IDと手修正を保持した。未取得の全カードへ拡張した実証とは扱わない。検証画像はprivate/audits/ui-v5-public-20261009、実原本の読戻しと更新反映報告はprivate/audits/detail-native-final-roundtrip-20261009.json、detail-update-reflection-20261009.json。

後続候補は、新鮮な原本エクスポートと保存入力監査から `scripts/prepare_detail_adoption.py <原本XLSX> <候補JSON> <新しいprivate計画フォルダー>` で準備できる。固定ID・手修正を確認しmaster.json/tables.json/review.jsonを生成する。取得済み入力だけを使い、原本書込・公開はしない。計画作成後に原本を編集した場合は古い計画を使わず、再度エクスポートして再準備する。

## 100件への拡張（2026-10-09、公開前検査完了）

追加40カードを含む100カード（P15/S85）、1,435項目を取得済みHTMLから検証し、60件原本のnative完全コピーへ登録した。詳細revision4。実XLSX読戻しで全値一致、既存9タブの基礎内容差分0、既存865固定detail_idと名称手修正の保持を確認した。新旧の非公開原本・エクスポート・接続履歴は保持。計画はprivate/details/next-adoption-20261009-02、原本照合はprivate/audits/detail-native-100-roundtrip-20261009.json。

S【Actors】の補足説明表は原文監査用に分離し、ライブスキルに誤分類しない。P【B!c,Cib】の専用節だけにある固有アビリティも収録するが、記載のないSPはnull（不明）とし無料と推定しない。詳細版d1-523ec92ea52303c4の候補は34配信ファイル、PC1280/390/320の基礎・詳細UI試験PASS。旧32ファイルのうち変更はindex.htmlとdetails/latest.jsonのみで、旧基礎3版・旧詳細2版のバイトは保持した。Python111/JS19 PASS。公開URLの検証はこれから行う。

## 100件版の公開URL検証

準備9320503、HTML改行維持f778dba、明示公開f409e8a。[Actions run 37888246800](https://github.com/VIgNOles/shiny-index/actions/runs/37888246800) success、[匿名公開URL](https://vignoles.github.io/shiny-index/)全34ファイルの生バイト一致、PC1280/390/320の基本/詳細検索・版・JSON取得PASS。公開d1-523ec92ea52303c4は原本r4の100件1435項目と一致し、旧865 detail_idと実名称修正も保持。実原本に追加した詳細を段階公開したもので、全件詳細・基礎新規1カード追加実証は未完了。報告はprivate/audits/detail100-public-verification-20261009.json。

後続のCHILLY/CONTRAILの別リンク条件表は保存HTMLで対応した。画像そのものを取得せず、条件画像のalt/srcと原セルを非公開根拠として残す。公開効果条件の完全構造化とは区別する。

## 205件・ロード全84カードの原本接続（2026-10-09、公開直前）

156件/r5候補をnativeコピーと全値往復で検証した後、ロード28ページすべてを保存・変換できたため、205件P102/S103・2825項目/r6へ広げた。原本は指定Driveのnative完全コピー15タブ、全値読戻し一致、基礎9タブ差分0、既存1435固定IDと名称手修正保持を確認して切り替えた。切替前の100原本に編集が入っていないこともDrive更新日時と値で確認。旧100原本、156候補、各XLSX、接続履歴はprivateに保持。

ロード84の各card_idに結ぶパネル・思い出の表集合が、同じURLの他派生と重ならないことを検証した。新詳細版d1-0d933fce3b2fb3b6、全36配信ファイル。PC1280/390/320の基本・詳細UI試験PASS、320px実表示画像も確認。公開URL照合は後続で行う。原本読戻しはprivate/audits/detail-native-205-roundtrip-20261009.json、ロード/固定IDはroad84-and-205-id-validation-20261009.json。

凍結時点のcoverageは205収録・入力待ち1213・リンク保留47・構造対応待ち1（Cherish You）。全件収集と発動条件・生成技能等の全面構造化は未完了。公開中の収録状況は固定した原本スナップショットであり、取得ジョブの後続件数とは区別する。

新しい原本書込計画は `scripts/prepare_detail_sheet_requests.py <新鮮な原本XLSX> <採用計画フォルダー> <nativeメタデータJSON> <新しいprivate出力>` で作れる。6詳細タブだけ、値更新・必要な行拡張・既存データ行からの書式複製・フィルター範囲を用意し、実際のAPI送信は行わない。必ず完全nativeコピーへ適用する。構造化requestsを順に送信し成功位置を記録する。ツールからJSONを読む場合はcompact JSONを使い、読取り打切りを検出してから送信する。送信結果が不明なら実値を確認し、確認せず次へ進まない。


## 205件版の公開確認と206件への更新（2026-10-09）

205件版は準備0ade31f、公開b796703、Actions 37893156287 success、匿名URL36/36ファイル一致、PC1280/390/320の基本/詳細操作PASS。公開結果はprivate/audits/detail205-public-verification-20261009.json。前節の「公開直前」は履歴である。

P【Cherish You】鈴木羽那の保存HTMLにある生成ライブ連係表を追加対応した。同じ150ページの凍結入力を再変換し206件P103/S103・2845項目、構造保留0（入力待ち1213、リンク保留47）となった。通常パネル3ライブと生成4ライブを重複させない。生成元の本文に明記された生成先名を照合し、初手と連係段階、矢印、原セルを検証する。生成スキルのSPはnull、1/2連目と生成元名を保存する。PlusとChangeはその行の効果から独立抽出する。未知の形・異なる生成先・終端未解決・重複は採用しない。

指定Driveの205原本をnative完全コピーし、更新11バッチ、全値読戻し一致・基礎9タブ差分0、既存2825固定ID/名称手修正保持を確認。旧205原本の未変更もDrive更新日時と実値で確認後、詳細r7へ切り替えた。原本/監査/バックアップは非公開。接続ファイル内の古い100件のdetail_roundtrip_result表示も206件の実検証結果へ同期した。

UI v6では「生成ライブスキル」を独立表示・検索し、生成元と段階を表示する。新詳細版d1-d3a4bf450390442b、38ファイル。ローカルPC1280/390/320の基本/詳細操作、生成Change検索とパネルとの分離、JSON版一致を確認。公開URLの結果は後続に追記する。旧UI v5タグを使う切り戻し候補では206件データを維持し、生成専用機能だけ旧UIの範囲外になる。
