# 詳細情報の原本・Web・配布データ接続（UI v5）

2026-10-09 JST。現行基礎索引は1,466件（P548/S918）、基礎版 `v1-93a6a8b8d40e754a`。詳細は段階的な収録で、256カード（P126/S130）・3,685項目、`d1-471997dafba126df`、詳細原本revision8。**全件詳細版は未完成**。公開URLでの最終検証結果は末尾へ追記する。

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
$env:UI_EXPECTED_VERSION='ui-v7'
node tests/ui-v4-smoke.mjs private/detail-update-candidate
node tests/ui-v5-smoke.mjs private/detail-update-candidate
```

基礎カード追加/修正の手順はoperations.mdの「追加・手修正」。基礎も更新する場合は基礎版のprepareを先に新規候補で実行し、上記詳細エクスポートをその候補へ追加する。card_id/P/Sと収録範囲が一致しない場合は公開せず原本と結合を修復する。取得値の詳細追加は、保存HTMLの変換候補を `adopt` で既存台帳へ採用し、原本をnativeコピーして追加する。新規スキルを原本へ手登録する簡単な画面はまだなく、`add_manual` の構造入力が必要（先行入力後の統合はテスト済み）。

## 取得・中断・復旧

全件1,363個別ページのうち224を保存し、今回のユーザー指定で取得は停止済み。再開指示まで実行しない。正常時の間隔は60秒以上。正常保存済みページは再送しない。現在の処理状態は `private/raw/detail-catalog-20261009/state.json` とworker.lock、workflow-report.json、stdout/stderr-workflow-010.logで確認する。PC終了や利用上限でジョブが終わった場合、docs/card-details-full-acquisition.mdのPID確認・残留ロック・保存成功回復を先に行う。新しいジョブを重ねて起動しない。

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


## 256件版の原本接続・公開前検証（2026-10-09）

206件版は準備bca0845、公開84dc136、Actions37895739334 success、匿名38/38一致、PC1280/390/320基本/詳細PASS。今回、凍結state602/200保存ページの256カードP126/S130・3685項目を採用した。候補ハッシュ1811cc0614a84f3d9ff0178db0bb59cf34f5bdbb95f57904087886f6de19fc94。入力待ち1163・個別リンク保留47、構造保留0。全件入力完了ではない。

P【Could Be】ルカの3行型生成表は通常/MBの表見出しを区別し、各生成先名を通常/MBそれぞれの親効果に照合する。生成4件を別ID/SP=nullで保存する。P【Find M Trick】摩美々のランダム表はパネルの正確な名称へ結び、Vocalの候補値・継続ターンだけを構造化。2技能×5候補を公開し、確率や確定発動を推測しない。単なる2行1列の共通説明（Candy等）は従来どおり非公開補足で、未知効果を一般に無視する変更ではない。

指定Driveの206原本をnative全コピー、107バッチ、全値往復一致、基礎9タブ差分0、2845既存ID/手修正保持を確認後、詳細r8の256件へ接続切替。元206の未変更も値/更新時刻で確認した。UI v7・詳細d1-471997dafba126df・40ファイル。PC1280/390/320の基本・詳細、生成通常/MB、ランダム候補検索、版/JSON、横はみ出し/説明文と見出しの非重複を検証した。320pxランダム画面を目視。旧UI v6へ同じ256データを維持する切り戻しの基本/詳細操作もPASS。公開結果は後続に記録する。

ユーザーが今回の採用上限を256件としたため、新たな採用・拡張は止める。取得も安全停止し、原入力と最終監査を保持。再開前にはHANDOFF.md末尾、STOP・state・PID/ロックと現在の正式原本を照合する。取得済み>256の入力を自動採用しない。


## 256件版のGitHub送信が自動承認で停止（2026-10-09）

256件版はローカル583eb58、切り戻しタグui-v7-details256-20261009へ保存済み。コード/検証済みsite40ファイル/文書だけをコミットし、非公開原本・入力・接続は含めていない。GitHubへのpushは過去のその時点のローカル保存制約を理由に自動審査で2回拒否された。TASK47-48の後の公開/Git許可と今回TASK266の256公開確認許可を示して再試行したが拒否され、別経路で回避していない。具体的なpush・公開の明示回答をユーザーへ依頼した。承認/再試行成功までは公開は206件/UI v6/d1-d3a4bf450390442bのままで、256件の匿名URL検証は未実施。取得は停止済み。最新結果はHANDOFF.md末尾を確認する。


## 256件版の公開URL検証完了（2026-10-09 JST）

ユーザーが「ローカル保存」の制限を明示解除したため、承認記録864dcacと保存済みコード/文書/site、切り戻しタグui-v7-details256-20261009をoriginへ送信した。過去の自動審査拒否は解消済み。公開コミット010f5b7、[Actions37910476569](https://github.com/VIgNOles/shiny-index/actions/runs/37910476569) success。[匿名公開URL](https://vignoles.github.io/shiny-index/)全40ファイルがローカルとバイト一致。PC1280/390/320の基本検索・絞込・並替・詳細、通常/MB生成Change、ランダム候補、最高Lv欠損、JSON取得、版/SHA、横はみ出し/説明との間隔がPASS。公開320pxランダム画面を目視確認した。

現行UI v7、基礎v1-93a6a8b8d40e754a/1466、詳細d1-471997dafba126df/256(P126/S130)/3685、詳細原本r8。指定Driveの原本は所有者のみで、最終更新時刻が検証済みエクスポートより前であり、その後の編集がないことも確認。原本/site/接続のSHAと保存済み入力状態は停止時から不変。公開監査はprivate/audits/detail256-public-verification-20261009.json、画像はprivate/audits/ui-v7-details256-public-20261009。

今回の256件版の登録・保存・公開確認は完了。全件版の完成ではない。取得は224ページ・残1139で停止したまま、STOP保持・ロックなし・進行中リクエストなし。256超の追加採用や取得再起動を行っていない。全件詳細・効果条件の全面構造化・基礎新規カード本番追加実証・公式全網羅等は引き続き未完了。


## 2026-10-09 256件上限解除・282件原本/公開候補

ユーザーが256件上限を明示解除したため、取得workflow011を残1139ページの有限予算で再開。成功済み224ページを再送せず保持。通常60秒以上/1ページずつ・共通ロック・実HTTP失敗/Retry-After停止は継続。実worker23128（launcher24800）、ログstdout/stderr-workflow-011.log。旧STOPは正規の--clear-stopで解除した。二重起動しない。

frozen state684の保存226ページから282カードP136/S146・4138項目、構造保留0・入力待ち1137・リンク保留47を変換。2回のオフライン変換はcontent_hash55b4c77e29efbb47f22b994859eb859a1d9987df42c88f9519c14ea7e2303707で全値一致。指定Driveの256原本のfresh exportとactive原本も全値一致。そのnative全コピーへ21バッチ（元70バッチと同じ順序のrequestsを90KB未満で再編成）を適用し、原本r9の全値読戻し一致、基礎9タブ差分0、3685固定ID/手修正維持を確認後切替。旧256原本は最終更新時刻07:12:32.541UTC不変、XLSX/接続/siteバックアップを保存。現在IDはprivate/sheets-connection.json。原本・HTML・接続・監査はGit非公開。

追加453出典URLの表示値とnativeリンクの一致、全書込範囲の書式/validation/chips、フィルターの全使用行をAPIで確認。Google画面のCUAはsandbox setup refreshエラーで起動不可、native画面の外観は未確認。Web候補はPC1280/390/320基本/詳細操作PASS、320px画像を視認。基礎v1-93a6a8b8d40e754a不変、UI v7、詳細d1-6595cad90a13ca0b、全42ファイル。tests/ui-v4/v5-smoke.mjsは空UI_BASE_URLを未指定と扱うよう修正。最初の空URL試験失敗は試験設定の問題で、修正後全幅PASS。成果物index.htmlの改行は旧LFへ揃えた。新依存なし。

証拠: private/audits/detail-native-282-roundtrip-20261009.json、native282-format-and-links-20261009.json、ui-v7-details282-local-20261009、private/details/sheet-write-after256-checkpoint-20261009.json。取得は並行継続し、この原本/公開候補への自動採用はない。公開Actions・匿名URLの結果は後続に追記する。全件詳細/発動条件等の全面構造化/基礎新規カード本番追加実証/公式独立網羅、日付56・個別リンク47保留、実機/スクリーンリーダー全面検証は未完了。


## 282件版の公開確認完了（2026-10-09）

準備7a5d3e5、公開9e1a7ac、タグui-v7-details282-20261009、Actions37914739564 success。匿名公開URL42/42ファイルがsiteと生バイト一致。PC1280/390/320の基本・詳細検索/フィルター/並替、MB/生成/ランダム、最高Lv欠損、JSON版/SHAと取得、横はみ出し/見出し間隔PASS。原本r9/282P136S146/4138と公開d1-6595cad90a13ca0bは一致、基礎1466/v1版不変。private/audits/detail282-public-verification-20261009.json、ui-v7-details282-public-20261009参照。

256件上限は解除済みで取得011は継続中。次の取得済み入力からafter282-next-frozen/after282-next-candidate-20261009を独立変換中。後続候補の採用はfresh native原本から行い、全件版完成とはしない。


## 2026-10-09 298件原本・UI v8公開前検証

frozen state732（242保存ページ）の入力候補ad01f438b35dc959b832b2efaf9e26844b583e588580b768229fb194ea7c080cから、298カードP141/S157・4418項目を採用。構造保留0・入力待ち1121・リンク47保留。282原本のfresh exportとactive原本全値一致、native全コピーへ16バッチ（元53バッチと同じrequests順序を90KB未満に再編成）。原本r10を全値読戻し一致・基礎9タブ差分0・4138旧detail_id/手修正維持で切替。元282の更新時刻09:51:41.455UTC不変、XLSX/接続/siteバックアップを保存。現在の原本はprivate/sheets-connection.json。追加280出典URLのリンク一致、全書込範囲の書式/validation/chips・全使用フィルター範囲をAPI確認。CUA起動不可につきGoogle画面外観は未確認。

原本に保存済みの思い出Link/チャージ効果が公開変換から除外されていたため、参考数値をmemory_link_facts/memory_charge_factsへ分けて公開・表示・検索するUI v8へ修正。観測した効果の有無と、本文があるが数値未構造化の状態を区別し、未対応を効果なしとしない。最大倍率はappeal_maximumとして固定倍率と区別し『最大/条件未構造化』と表示する。最大値の発動条件や継続ターンまで解析済みとは扱わない。Linkとチャージのキーワードを跨いだ誤一致を防ぎ、思い出Linkはライブ機能フィルターへ混ぜない。原本/固定ID/取得入力はこの公開改善で書き換えない。Wiki全文・画像・私的条件テキストは配布しない。memory651行、Linkあり626/数値あり621、チャージあり15/数値あり15。

基礎v1-93a6a8b8d40e754a不変、UI v8・詳細d1-01d9d4aba38f5334・44公開ファイル。旧42ファイルの変更はindex/app/details.mjs/details/latest.jsonだけ、旧データ版全バイト不変。Python133/JS23 PASS。UI v8基本/詳細PC1280/390/320、思い出Link/チャージ表示、通常/MB/生成/ランダム、JSON版/SHA、最高Lv欠損、横はみ出し/間隔PASS、320px思い出画面視認。旧UI v7タグを使う切り戻し候補も298データを維持して全幅基本/詳細PASS。旧UIでは思い出追加効果と最大倍率の専用表示/検索が省かれる。新依存なし。

変更: src/detail_public.py、web/app.mjs/details.mjs/index.html、siteの対応資産と新詳細バンドル、tests/test_detail_public.py/detail-search.test.mjs/ui-v5-smoke.mjs、README/operations/HANDOFF/docs/card-details-design/integration/verification、local design.md17.44（Git対象外）。最初のmemory単体試験はfixtureのcollection名を単数にしたため失敗し、実スキーマのmemory_appealsへ直して全件PASS。133試験の429/ファイル欠落ログはモックの障害試験で、実Wiki失敗ではない。公開Actions・匿名44ファイル・公開PC/スマホ確認は後続に追記する。取得011は継続し自動採用しない。

証拠: private/audits/detail-native-298-roundtrip-20261009.json、native298-format-and-links-20261009.json、detail298-site-preservation-20261009.json、ui-v8-details298-local-20261009、ui-v7-rollback-from298-20261009、private/details/sheet-write-after282-checkpoint-20261009.json。全件詳細/複合効果・条件の全面構造化/基礎新規実在カード本番追加実証/公式独立網羅、日付56/リンク47保留、実機・スクリーンリーダー全面検査は未完了。


## UI v8 思い出変動倍率の追加対応（2026-10-09、公開前）

298件版UI v8の公開はda2e3dd/54381c5/d377d5e、最終Actions37916819260 success、匿名44/44ファイル一致、PC1280/390/320基本/詳細と思い出Link/チャージ表示PASS。private/audits/detail298-public-verification-20261009.json。旧公開資産の改行を維持する追加コミットd377d5eにより、UI v7との差分はapp7追加1削除/details6追加2削除へ収束した。中間の全行改行差分は機能変更ではない。

未構造化のLink5行はP【Housekeeping!】のVocal0.4～2倍/0.9～4.5倍だったため、appeal_range(minimum/maximum)へ対応。固定倍率・最大値・変動範囲を区別し、条件未構造化を明示する。範囲逆転/非有限値/未知フィールドを検査。波ダッシュとASCII~の検索をNFKCで揃え、Linkとチャージの効果区分を跨ぐ誤一致を防ぐ。全文/消去条件は非公開のまま、条件の全面構造化が終わったとは扱わない。651思い出行のうち観測Link626すべてに参考数値、チャージ15すべてに参考数値あり。これは全効果を解析済みという意味ではない。

正式原本r10/298P141S157/4418、固定ID、手修正、基礎r7/1466、native Sheetsは変更せず、公開変換とUI v8を修正。最新native exportとactive master全値一致も再確認。詳細版d1-45ed170d94366826、46ファイル。旧44ファイルの変更はdetails.mjs/index.html/details/latest.jsonだけで旧バンドルは生バイト不変。Python134/JS24、PC1280/390/320基本/詳細・実Housekeeping変動Linkの表示/検索・ライブLinkへの非混入PASS。320px変動倍率画面を視認。依存追加なし。公開Actions/匿名46ファイル/公開画面は後続に追記。

次の保存済み入力はfrozen state795/263ページ、319カードP144/S175、構造保留0・入力待ち1100・リンク47保留、候補3ca632d4a0128b004cf1c10b40d4ed118e0cdacef1f6a7f38986db800d145efa。private/audits/after298-next-candidate-20261009.jsonとfrozenを保持。現在native原本のfresh exportからprivate/details/after298-next-adoption-20261009-03を準備中。これらは候補であり319原本/公開版ではない。取得011は継続し、256/298/319を新しい上限にはしていない。

## 2026-10-09 319件原本・公開候補と298件修正版の公開確認

298件UI v8変動倍率修正版は8a4ceac/5c1bb5f、Actions37917797482 success、匿名46/46ファイル一致、PC1280/390/320基本/詳細・思い出Link/チャージ/実Housekeeping範囲検索PASS。旧UI v7へ戻す候補でも298件と最新詳細d1-45ed170d94366826を保持して同3幅の基本/詳細操作PASS。証拠はprivate/audits/detail298-range-public-verification-20261009.jsonとui-v7-rollback-from298-range-20261009。

次のfrozen state795/263保存ページ・候補3ca632d4a0128b004cf1c10b40d4ed118e0cdacef1f6a7f38986db800d145efaから319カードP144/S175・4796項目を採用。298原本をfresh exportして計画入力/active原本と全値一致、指定アカウントでnative全コピーへ20バッチ（元69バッチ/103 requestsと同じ順序、90KB未満）を書き込んだ。全値読戻し一致、基礎9タブ差分0、旧4418固定ID/手修正保持、元298の更新時刻10:11:35.968UTC不変を確認後、原本接続とmaster.xlsxをr11へ切替。追加378出典URL/実リンク一致、書込14092セルの書式/validation/chips/数式と6タブのフィルター範囲をAPI確認。旧298 native/XLSX/接続/siteバックアップを保存。詳細はprivate/audits/detail-native-319-roundtrip-20261009.json、native319-format-and-links-20261009.json、private/details/sheet-write-after298-checkpoint-20261009.json。

UI v8・基礎v1-93a6a8b8d40e754aは不変、詳細候補d1-5c20f6531f1c8fb1、48ファイル。旧46ファイルの変更はindex.htmlとdetails/latest.jsonだけで旧不変データは全バイト保持。319候補PC1280/390/320の基本/詳細・思い出Link/チャージ/変動倍率/MB/生成/ランダム/最大Lv欠損/JSON版・SHA/横はみ出しPASS。コード変更なし、直前のPython134/JS24 PASSを使用。319公開Actions/匿名48ファイル/公開画面は後続へ記録し、298公開確認と混同しない。

取得workflow011は残全件へ通常60秒以上/1ページ・実HTTP失敗/Retry-After停止で継続する。256/298/319を上限にはしない。取得終了時の自動処理は保存入力からの候補監査までで、原本への追加採用/公開は別工程。未完了は全件詳細取得/採用・複合効果/条件の全面構造化・公式独立網羅・基礎新規実在カード1追加/修正の本番反映実証・日付56・リンク47ユーザー保留・実機/スクリーンリーダー全面検証。Google画面外観はCUA起動不可のため未確認、XLSXの代替表示を確認中。原本/公開の整合性障害や新しいWiki HTTP失敗は確認していない。
