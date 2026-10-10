# 詳細情報の原本・Web・配布データ接続（UI v10）

2026-10-10 JST。基礎1,466件（P548/S918）・v1-93a6a8b8d40e754aを維持。**個別ページあり全1,419カード（P548/S871）・24,025項目を原本r18へ登録し、詳細d1-7a9722efb8a845e1を公開・匿名確認済み**。1,363ページ保存・現行全入力再変換で構造例外0。取得は正常終了し実行ロックなし。47ページなしは保留。全ゲーム網羅・全効果/条件構造化の完成は主張しません。完成条件別結果はverification.md、後続の版別記録は当時の履歴です。

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
$env:UI_EXPECTED_VERSION = [regex]::Match((Get-Content -LiteralPath 'private/detail-update-candidate/index.html' -Raw), "window.UI_VERSION='([^']+)'").Groups[1].Value
node tests/ui-v4-smoke.mjs private/detail-update-candidate
node tests/ui-v5-smoke.mjs private/detail-update-candidate
```

基礎カード追加/修正の手順はoperations.mdの「追加・手修正」。基礎も更新する場合は基礎版のprepareを先に新規候補で実行し、上記詳細エクスポートをその候補へ追加する。card_id/P/Sと収録範囲が一致しない場合は公開せず原本と結合を修復する。取得値の詳細追加は、保存HTMLの変換候補を `adopt` で既存台帳へ採用し、原本をnativeコピーして追加する。新規スキルを原本へ手登録する簡単な画面はまだなく、`add_manual` の構造入力が必要（先行入力後の統合はテスト済み）。

## 取得・中断・復旧

以下の224ページ・256件での停止は過去の記録。現在の停止指示ではない。最新は取得012を60秒以上/1ページで継続し、正常保存済み入力を再取得せず、別工程で変換・原本採用・公開する。現在のstate/PID/locksを照合してから再開し、稼働中の処理を二重起動しない。

全件1,363個別ページのうち224を保存し、今回のユーザー指定で取得は停止済み。再開指示まで実行しない。正常時の間隔は60秒以上。正常保存済みページは再送しない。現在の処理状態は `private/raw/detail-catalog-20261009/state.json` とworker.lock、workflow-report.json、stdout/stderr-workflow-010.logで確認する。PC終了や利用上限でジョブが終わった場合、docs/card-details-full-acquisition.mdのPID確認・残留ロック・保存成功回復を先に行う。新しいジョブを重ねて起動しない。

HTTP200短文の誤検知は `private/audits/detail-shape-false-positive-20261009.json` に根拠を保存し、履歴は削除していない。実HTTP失敗・Retry-Afterは解除していない。変換と原本採用、公開は取得とは独立し、異常入力は正常な原本・siteに自動反映しない。詳細数の異常・重複・未知P/S・孤児ID・ファイル改変は検査で拒否する。壊れた更新の復旧は正常な原本コピーと不変d1バンドルから新しい候補を作り、検査後に公開する。UI v4へはタグ `ui-v4-20261009` とbuild_ui_rollback.pyを使う。原本は切り戻さない。

## 検証と未完了

- Pythonの固定ID、手修正保持、手入力→取得統合、消失拒否、正の公開項目、件数/ハッシュ異常拒否、式拒否、詳細タブ保存、基礎/詳細同時取込を検証。
- JSの同一スキル行の条件一致、思い出とライブの分離、全角検索、未収録除外を検証。
- PC1280px・390px・320pxの基礎回帰と詳細検索/開閉/URL再読込/数値/JSON取得をEdgeでPASS。スマホ幅の実表示画像も確認。最高Lv空欄を低いLv値へ置き換えない。
- 原本1詳細追加・1項目修正がローカルWeb/配布データへ反映し、再変換後も修正/IDを保持。これは基礎カードの新規追加を本番反映した実証ではない。
- 256件段階の未完了記録: 全件詳細取得・全節構造対応・84ロード関連card_idの派生対応・効果条件の全面構造化・公式独立照合。ロード派生対応は後続工程で実装・採用済み。現在の残件はverification.mdを参照。個別ページなし47件は指示により保留、初回実装日不明56件は未解決。実機スマホ/スクリーンリーダー全面検査も未実施。


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

## 2026-10-09T11:03:03UTC 最新状態：319件公開、全件取得継続

現行原本は指定Googleアカウントの非公開native Sheets・基礎r7/1466(P548/S918)・詳細r11/319(P144/S175)/4796項目・15タブ。URLはprivate/sheets-connection.jsonの現在値を使う。公開UI v8、基礎v1-93a6a8b8d40e754a、詳細d1-5c20f6531f1c8fb1。準備6706452、公開769014760e96c17b40b46040e10bfc5bc70d15d2、タグui-v8-details319-20261009、Actions37919802687 success。匿名48/48ファイルが生バイト一致、PC1280/390/320の基本/詳細・思い出Link/チャージ/変動倍率/MB/生成/ランダム/JSON版とSHA確認PASS。320pxの変動倍率画面を視認。private/audits/detail319-public-verification-20261009.json参照。旧UI v7へ戻す319データ維持候補を生成し全ファイル検証PASS（319切戻し候補の操作試験は未実施、同UIの298最新データでの3幅操作はPASS済み）。

原本の全値/基礎9タブ不変/固定ID・手修正保持/378追加出典URL一致/14092書込セルのnative書式確認に加え、native XLSXをArtifact Toolで読み取り、詳細6タブの先頭と追加端の11画像を確認した。固定150pxのID/JSON/長文列は従来どおり省略表示で、セルの内容は保持。Google実画面はCUA起動不可で未検証、APIとエクスポート表示を代替確認した。新たな原本著者変更はfresh exportと全15タブの実値一致で確認。public/source本文を変更していない。

後続のP【Scene With You】鈴木羽那で「MB stage/effect missing」を検出。実際は2行の[MB]ランダム効果説明表を技能として読んだ誤分類だった。既知の説明表だけを非公開監査ノートへ保存し、未知MB表や欠落は引き続き拒否する。生成技能のa.note_super/id=notetext数字/表示*数字という実脚注を名称から除外して生成元へ照合する。字面のアスタリスクは除外せず、効果本文や保存HTMLを改変しない。MB2技能・通常/MB由来の生成2技能・補足2表を分離、脚注は原セル証拠から追跡可能。ランダム説明の複合条件やパッシブ強化値を全面構造化したとは扱わない。synthetic境界試験を2件追加、Python136 PASS。直前のUI/JS24 PASSはコード変更のない範囲で維持。モック429ログは試験だけで実Wiki再失敗ではない。同じfrozen876の旧345候補の内容不変、346候補で構造保留0を確認。

取得工程は新版パーサーを読み込むため011をSTOPで保存境界へ終了し、active_attemptなし、旧PID23128/24800終了、worker/workflow/共通requestロック解放、298保存入力と原本/接続/site全保護ハッシュ不変を確認。旧011のログ・workflow-report-011-parser-restart-finished.json・before/proofを保持した。残1065を有限予算とする012へ--clear-stopで再開。実worker29464、launcher28492、通常60秒以上/1ページ、共有ゲート/HTTP失敗/Retry-After停止は不変。11:03:03UTC確認時はrunning、revision914、成功302ページ(新規297+再利用5)/1363、pending1061、STOPなし、実worker生存、stderr空。保存済みを再取得せず、256/319/354を上限にしない。012は取得完了/停止後に候補監査を行うだけで、正式原本や公開へ自動採用しない。

次の採用計画はprivate/details/after319-next-adoption-20261009-04。fresh native319 exportとactive原本の全15タブ実値一致から、frozen901/298ページ・候補2107776bb3aaae8a12a14aff13b7dfa06975df8e2e4ef5b61f89b3b3e712e811を使い、354カードP155/S199・5405項目(319から35カード/609項目追加)へ準備した。4796旧IDと手修正保持、構造保留0、入力待ち1065、リンク47保留。354は計画のみで、正式原本/公開は319のまま。frozenのstatus=stoppedは011保存境界時点の記録であり、現在012の稼働停止を意味しない。

再開/次の具体操作: TASK最新指示→この末尾→Git/原本接続→012のPID/state/locks/active_attempt/ログを実照合し、稼働中なら二重起動しない。354採用前に現在のnative原本を再エクスポートし、計画input_master_hashと照合（変わっていれば新計画へ再作成）。native全コピーへ詳細6タブだけを書き込み、全値/旧ID/手修正/9タブ保護/書式と出典を検証後に原本切替・別site候補生成・PC/スマホ検証・明示publish:・Actions/匿名一致確認を行う。012終了時は最終監査にある新しい構造保留を保存HTMLから解消し、最新入力へ採用対象を広げる。今回ユーザー操作待ちはない。

未完了: 残全件の詳細入力取得/原本採用/公開、複合効果・条件の全面構造化、公式資料による全ゲーム独立網羅、基礎新規実在カード1追加と1修正の本番反映実証、初回日56不明、実スマホ/スクリーンリーダー全面検証。個別リンク47件はユーザー指定で保留し追加していない。Pステージ/適正・Sファイトは今回収集対象外。319公開を全件詳細/プロジェクト全体の完成とは扱わない。


## 2026-10-09 397件版の原本更新・公開前検証

原本r12・397件(P168/S229)・6179項目、UI v8・詳細d1-af5ad928b7b6d0b4へ更新。319から78カード(追加P24/S54)・1383項目を追加。指定アカウントで319原本を全コピーし、53バッチ（175小バッチ/262requestsと同じ順序）を適用した。全値読戻し一致、基礎9タブ/1466件不変、旧4796 detail_id・手修正1件保持、40426書込セルの書式/validation/chips/数式、追加1383出典URL/実リンク一致、5フィルターの全使用範囲を確認。metadata取得用no-match probeで更新時刻が進んだため、再度fresh exportして全15タブ実値不変を確認後、バックアップを保持してmaster/接続/siteを切り替えた。元319nativeは更新時刻10:39:07.427UTC不変で保持。

候補と同じデータをnativeエクスポートから再生成し、PC1280/390/320の基本/詳細・MB/生成/思い出Link/チャージ/変動倍率/JSON版/欠損表示がPASS。新規cheer+のVo/Da/Vi+25表示、Scene With YouのMB生成元と脚注除外も3幅PASS、320px実画像を確認。公開50ファイル、旧48ファイルの変更はindex.html/details/latest.jsonのみで全旧データ版の生バイトを保持。Python137/JS24 PASS。Google実画面はCUA起動不可、native書式API検証済み・XLSX代替画像を別プロセスで描画中。公開Actions/匿名URL確認は後続追記する。

証拠: private/audits/detail-native-397-roundtrip-20261009.json、native397-format-and-links-20261009.json、detail397-site-preservation-20261009.json、ui-v8-details397-local-20261009、private/details/sheet-write-after319-checkpoint-20261009.json。新依存なし。取得012/PID29464は全残件へ通常60秒以上/1ページで継続し、正式原本/公開へ自動採用しない。後続406候補は構造保留0、まだ未採用。全件詳細/条件の全面構造化/公式独立網羅/基礎新規カード本番追加実証等は引き続き未完了、リンク47はユーザー保留。


## 2026-10-09 420件原本・UI v9公開前検証

397のfresh native exportとactive原本の全15タブ実値一致から、frozen state1100/364保存ページ・候補53df759cd4480c2f00ca5bb08478aeeaacaf48ca8bd7dfb09c0850273b4ce120を採用。原本r13・420(P175/S245)/6578項目。397から23カード/399項目追加、今回開始時319から101カード/1782項目追加。新native全コピーへ23バッチ（元78/114requests、同順序90KB未満）を適用。全値読戻し一致、基礎9タブ/1466不変、6179旧固定ID/手修正1件保持、15601書込セルの書式/validation/chips/数式、399追加出典URL/実リンク、5フィルターを確認した。no-match metadata probe後にfresh exportして全15タブ実値不変を再確認し、旧397native/XLSX/接続/siteバックアップを保持して切替。元397の更新時刻11:57:16.837UTC不変。

UI v9は複数の明示生成元を表示・検索する。生成先を1技能として保持し、固定ID/スキーマの互換性と生成先自身のChange等の区分を維持。詳細d1-e227c840bd91a50b、公開候補52ファイル、旧50ファイルの変更はindex/app/details.mjs/details/latest.jsonのみで全旧データバンドル不変。HTML/JSは既存改行を維持。Python140/JS25、PC1280/390/320の基本/詳細と実new or …の複数生成元表示/親名検索PASS、320px画像を確認。420データ維持の旧UI v8切戻し候補も3幅基本/詳細PASS（複数生成元は先頭表示のみ）。依存追加なし。Google実画面はCUA不可、native API検証済み・XLSX代替表示を描画中。公開Actions/匿名確認は後続追記。

証拠: private/audits/detail-native-420-roundtrip-20261009.json、native420-format-and-links-20261009.json、detail420-site-preservation-20261009.json、ui-v9-details420-local-20261009、ui-v8-rollback-details420-20261009、private/details/sheet-write-after397-checkpoint-20261009.json。取得012/PID29464は通常60秒以上/1ページで全残件へ継続。終端監査が旧パーサー由来の2形式を保留と出した場合は、保存入力を最新版で再変換する。420は採用上限ではない。全件詳細/複合効果と条件の全面構造化/公式独立網羅/基礎新規カードの本番追加実証等は未完了。日付不明56、リンク47保留、Pステージ/適正・Sファイト対象外を維持する。


## 2026-10-10 再開照合：420件公開確認と中断位置

中断直前に420件(P175/S245)・6578詳細項目・原本r13・UI v9を公開済みだった。公開41606b741b4e85593f9be6d10a5a86a6ef06c75b、Actions37930093359 success、タグui-v9-details420-20261009。匿名52/52ファイル一致、PC1280/390/320の基本/詳細と実new or …複数生成元の表示・親名検索PASS。420データを維持する旧UI v8候補も3幅PASS（複数生成元は先頭のみ、親名検索なし）。private/audits/detail420-public-verification-20261009.json参照。基礎r7/1466(P548/S918)/v1-93a6a8b8d40e754aと詳細d1-e227c840bd91a50bを照合済み。全件詳細の完成ではない。

中断したのは、native420エクスポートの表示11画像を確認した後のGit状態確認・最終文書記録だった。自動承認レビューが利用上限で実行不能となった（危険判定ではない）。残っていた編集はsummer breakのMB補足見出しに付く実脚注を厳密除外するパーサー/試験/設計の3ファイル。Python141件は中断前にPASS済み。原本420と公開データにはこの修正で追加採用していない。11画像の視認記録をnative420-format-and-links監査へ補完した。Google実画面はCUA起動不可で未確認、APIとXLSX表示を代替確認した。

中断前の次工程は438件(P181/S257)/6909項目の採用計画（private/details/after420-adoption438-20261009）。これは未採用・未公開。再開時は実際の取得済み入力が増えたため、438を上限にせず新しいfrozen snapshotからオフライン候補を作成する。native420の最終更新12:21:27.396UTCは不変、指定アカウントowner-only・15タブを再確認。原本への不明バッチ・破損・二重公開は確認していない。

取得workflow012は中断中も正常継続しworker29464/launcher28492を確認。2026-10-09T15:35:25UTC時点でstate1730、574保存ページ（新規569/再利用5）/1363、pending789、active_attemptなし、stderr0。60秒以上/1ページ、共有ゲート、実HTTP失敗/Retry-After停止を維持。STOPなし、再起動していない。012は旧コードを読み込み済みのため、終端監査のcheer+改行/共有生成元/summer break脚注の保留は保存入力を最新コードで再変換する。原本/公開へ自動採用しない。

再開後の順序：中断していた修正・検証文書を保存→新frozen候補を変換/例外照合→native原本fresh exportから追加採用計画→全nativeコピーの詳細6タブ更新→全値/旧ID/手修正/基礎9タブ/書式と出典確認→別site候補/PCスマホ検証→明示publishとActions/匿名確認。取得済み入力を再取得しない。

未完了は全件詳細取得・採用・公開、複合効果/条件の全面構造化、公式独立網羅、基礎新規実在カード1追加/1修正の本番実証、日付不明56、全面実機/スクリーンリーダー確認。47個別リンクはユーザー保留。Pステージ/適正・Sファイトは今回収集対象外。


## 2026-10-10 631件原本・公開準備の検証

原本r14・631件(P264/S367)・10405項目へ更新し、420から211カード/3827項目を追加した。frozen state1733/575保存ページの最新全再変換は候補b4c4534b60243e75ca6ca5978c9451eed7a803ba6c32381176617f41848bb82dと全JSON一致。構造保留0、入力待ち788、個別リンク47ユーザー保留。基礎r7/1466(P548/S918)/v1-93a6a8b8d40e754aは不変。

指定アカウントの420nativeをfresh exportし全15タブ実値一致/owner-onlyを確認して全コピー。458元バッチ/642requestsを順序不変で152バッチへまとめ、25ACK境界から残りを4つずつ最大340KBの原子的グループで実行。152相当すべてACK、unknownなし。nativeの全値読戻しが計画と一致、基礎9タブ実値不変、旧420カードの全source/6578 detail_id/手修正1件保持。全106106書込セルの書式/validation/chips/数式、追加3827出典URLの実リンクと表示値、全5フィルター使用範囲をnative APIで確認。参照/コピーにnative tablesなし。no-match probe後のcomplete exportを使用し、最終mtime16:09:55.090UTC不変を再確認。元420nativeは12:21:27.396UTC不変。

nativeから再生成した54公開ファイルは、PC1280/390/320で基本/詳細/MBランダムの表示・検索・通常技能への非混入を検証した候補と全バイト一致。UI v9・詳細d1-c4c54f3692bd4473。旧52ファイルの変更はindex.html/details/latest.jsonだけで、旧不変データを全バイト保持。631データを保持した旧UI v8候補も3幅基本/詳細PASS（複数生成元は先頭だけ/親名検索なし）。Python143/JS25 PASS、新依存/UIコード変更なし。最大Lv能力値が未掲載のS41件は4能力値を未記載のまま保持する。全面構造化とは扱わない。

原本/接続/siteを切り替え、旧420native/XLSX/接続/siteを保存した。新原本ID/URLはprivate/sheets-connection.json、ACKと切替はprivate/details/sheet-write-after420-checkpoint-20261010.jsonが正とする。公開Actions/匿名54ファイル/公開画面は後続に追記する。Google実画面はCUA不可、API確認済み・XLSX代替表示を描画中。証拠：private/audits/detail-native-631-roundtrip-20261010.json、native631-format-and-links-20261010.json、detail631-site-preservation-20261010.json、ui-v9-details631-preliminary-20261010、ui-v8-rollback-details631-preliminary-20261010。

取得012/worker29464/launcher28492は60秒以上/1ページで継続し、原本/公開へ自動採用しない。後続frozen1802/598保存ページから654候補(P273/S381)・構造保留0を作成、旧631カード内容不変。private/audits/after631-next-candidate-20261010.json（hash478350d08ef199bcae793f9d1a419f380f5bf4b2f612ba5be1d7910bea07e735）。これは未採用/未公開。最新native631のfresh exportから次計画を作る。631/654を上限にしない。全件詳細取得/採用/公開、複合効果・条件の全面構造化、公式独立網羅、基礎新規実在カード1追加/1修正の本番実証、日付不明56、全面実機/スクリーンリーダー検証は未完了。47リンク保留とPステージ/適正・Sファイト対象外は維持する。


## 2026-10-10T01:21 JST 公開確認完了・次の工程

631件(P264/S367)・10405項目・原本r14、UI v9・詳細d1-c4c54f3692bd4473を公開確認済み。準備b4bde4e、公開be82002c22506a1b11412754b841ab4b01b59565、タグui-v9-details631-20261010、Actions37957724500 success。匿名54/54ファイルがsiteと生バイト一致。公開PC1280/390/320の基本/詳細・MBランダム選択肢表示/検索・通常技能への非混入・複数生成元・JSON版/SHA/欠損表示PASS、公開320pxのMB画像を視認。631データ保持のUI v8切戻し候補も3幅PASS。private/audits/detail631-public-verification-20261010.json参照。

Googleの後続エクスポートでmtime16:10:24.240UTCとZIP包装差を観測したが、全15タブ実値・詳細セル書式/フィルターが同一で、意味ハッシュ72dfd5ef40cf814b919bcb21becfb7798603ce9786c5dffa8d9deb94cd5d7191は不変。最新包装をactive masterへ保存し接続ハッシュ/最終mtimeを更新。途中の読取監査は空filterの文字列化に失敗したが、原本/公開に変更はなく、Noneを許容して書式実体を比較する修正後にPASS。Google実画面はCUA不可、native全値/API確認済み、XLSX代替描画は継続中（保存原本は変更しない）。

後続654件(P273/S381)・10780項目・原本r15予定の計画をprivate/details/after631-adoption654-20261010へ保存。fresh native631 exportとactiveの全15値・書式一致から作成。入力master hash72dfd5ef40cf814b919bcb21becfb7798603ce9786c5dffa8d9deb94cd5d7191、候補hash478350d08ef199bcae793f9d1a419f380f5bf4b2f612ba5be1d7910bea07e735、出力hash77bdb7f1d6d5ea44cecd55a31fafe6c61e3d690616f88287fbdcc36f2b0eef8c。追加23カード/375項目、10405旧ID/手修正保持、構造保留0。654は未採用・未公開。取得済み入力はさらに増加しており、654を上限にせず次のバッチを最新frozenから広げてもよい。

取得012/worker29464/launcher28492は稼働を維持。2026-10-10T01:20:42JST時点state1865、619保存ページ(新規614/再利用5)/1363、pending744、active_attemptなし、stderr0、STOPなし。60秒以上/1ページ、実HTTP失敗/Retry-After停止、共有ゲートは不変。取得終了後の旧コードによる構造保留は最新の保存入力再変換で確認し、HTMLを再取得しない。原本/公開への自動採用はない。

次操作：取得012のPID/state/locks/active_attempt/logを実照合し二重起動しない→現在nativeのfresh exportと次計画input hash照合（変われば手修正を保って再計画）→詳細だけを書き込むnative全コピー→全値/基礎9タブ/旧ID/override/全書込セル/出典/フィルター確認→別site候補/PCスマホ/旧版保持→原本切替/publish/Actions/匿名確認。631登録checkpointはprivate/details/sheet-write-after420-checkpoint-20261010.jsonで全152相当ACK・unknownなし・published=true。原本/公開の破損、データ欠落、新たなWiki HTTP失敗は確認していない。

未完了：全件詳細取得/原本採用/公開、効果・条件の全面構造化、公式独立網羅、基礎新規実在カードの本番追加/修正実証、日付不明56、全面実機/スクリーンリーダー確認。個別リンク47件はユーザー指定で保留。Pステージ/適正・Sファイトは今回収集対象外。ユーザー操作待ちはなく、取得は継続中であり、安全停止やプロジェクト完成としては扱わない。


## 2026-10-10 631件原本の代替表示確認とN最大Lv対応

native631のcomplete exportをArtifact Toolで読み取り、詳細6タブの先頭/追加端11画像を視認。値/見出し/手修正G:Mの青/出典リンク/収録範囲/原本r14を確認。固定150pxのID・JSON・長文列は参照のCLIPを維持し、全文値は別の全値照合で確認済み。描画は読み込みに約17分かかったが正常終了し、原本/公開/取得入力を書き換えていない。画像private/audits/native631-export-preview-20261010、証拠native631-format-and-links-20261010.json。Google実画面はCUAを1回再確認してもwindows sandbox helper_unknown_errorで起動不可、native APIとXLSX表示を代替確認した。

後続frozen1874/622保存ページでは676候補とS2件の10(MAX)表記保留を検出した。docs/card-details-designの通りMAX明示と特訓☆を分ける修正・境界試験を追加しPython144 PASS、JS25のコードは変更なし。S【アイドルのたまご】甜花はLv10/4能力60、夏葉はLv10/Vo40 Da80 Vi60 Me60、特訓回数null。676既存候補の内容不変、678(P281/S397)候補・構造保留0へ補完。候補hash365e12b9101a57229b01d2bb7c705f7e2c76dcc0190bd1d58f14611cbccee920、private/audits/after631-latest-fixed-candidate-20261010.json。保存入力全件の追加再変換を実行中で、終了後に全JSON一致を照合する。取得済みページを再取得しない。公開631/原本r14はこの修正で変更しない。

private/details/after631-adoption678-20261010は631のfresh exportから作成した後続計画で、654旧計画を上限にしない。まだnativeコピー/書込/原本採用/公開は行っていない。631原本/公開を保護し、現在nativeのfresh export・入力hash照合を行ってから次の採用へ進む。全件取得は通常60秒以上/1ページで012が継続中。


## 最終保存時の照合（2026-10-10、取得は継続）

631原本/公開d1-c4c54f3692bd4473/UI v9・54匿名ファイル一致・3幅操作・native全値/書式/出典/11代替画像確認済み。後続678候補の最新コードによる全入力再変換が補完候補と全JSON一致（hash365e12b9101a57229b01d2bb7c705f7e2c76dcc0190bd1d58f14611cbccee920）。旧676候補不変。Python144/JS25 PASS。変更ファイルはsrc/card_details.py、tests/test_detail_html.py/test_support_detail_html.py/ui-v5-smoke.mjs、docs/card-details-design/integration/verification、README/operations/TASK/HANDOFF、公開index/details pointerと新不変バンドル。中断前後の編集を保持してGitHubへ保存済み。

最新の後続計画はprivate/details/after631-adoption678-20261010（678=P281/S397、11178項目、631から47カード/773項目追加、10405旧ID/手修正保持、入力意味hash72dfd5ef40cf814b919bcb21becfb7798603ce9786c5dffa8d9deb94cd5d7191、出力hash e89e866166ae3474729c9bbcae0cbb3b17ee2c06aa855b5b59da23813447cfb6）。書込要求private/details/after631-requests678-20261010は140小バッチ、まだ送信していない。654旧計画は履歴として保持。次回は現在native原本をfresh exportして入力hashと照合し、変化があれば手修正を保って再計画する。旧元原本や採用済み631へ直接未確認バッチを適用しない。

今回の検証用render/変換/更新/公開処理は完了し、未確認の書込応答はない。残って動くのは全件取得012だけ（launcher28492/worker29464）。記録時state1910・2026-10-09T16:35:42+00:00、保存634/1363（新規629+再利用5）、pending729、status=running、active_attempt=None、STOPなし、stderr0。60秒以上/1ページ、共有ゲート、実HTTP失敗/Retry-After停止を維持。保存済みを再取得せず、稼働中の012を二重起動しない。終了後の旧コード監査は新コードで保存入力を再変換してから採用判断する。取得は停止していない。

未完了条件と保留は検証表の通り。全件詳細の入力取得/採用/公開、効果/条件の全面構造化、独立した公式網羅確認、基礎新規実在カード本番追加/修正実証等を完成済みと扱わない。個別リンク47件はユーザー保留。Google実画面は環境起動障害で未確認だがAPI/エクスポート代替を確認済み。今回は再開と追加公開まで進めた状態で、プロジェクト完成・一時停止・ユーザー操作待ちではない。


## 2026-10-10 1,293件版の原本・公開接続

Googleのnative全コピーへ詳細6タブを359 bounded batchで登録し、全値/固定ID/手修正/基礎9タブ保持、全書込セル書式、出典実リンク、フィルターを確認。現在原本r15・1293カード/21868項目、公開d1-b89ba62ab2260b7d/UI v9、匿名56ファイル一致と公開3幅PASS。旧631原本/サイト/接続記録をbackupに保存し、private/sheets-connection.jsonの全現行参照をr15へ統一した。exact checkpointはprivate/details/expanded-after631-write-checkpoint-20261010.json。保存入力全再変換と旧UIデータ保持試験もPASS。全件原入力は通常60秒以上で012が継続し、後続の入力は別候補へ再変換中。全期間の詳細完成・公式独立網羅・効果/条件の全面構造化・基礎新規カード本番追加/修正実証などの残件を完成済みと扱わない。

## 2026-10-10 全個別ページ分の原本登録・公開確認

全1,363保存ページを現行コードで再変換し、1,419カード（P548/S871）・構造例外0、旧1,380カード全値不変。39カード/656項目追加で原本r18・24,025項目。native全コピーへ21batch、全15タブ値一致・基礎9タブ不変・旧23,369固定IDと手修正保持。17,402書込セルと周囲26,006セルの書式/validation/chips/formula、追加656出典URL/全1419リンク/47空欄、5フィルターを確認。実exportの11範囲を代替描画し変更6画像を確認。Google実画面の成功とは扱わない。

詳細d1-7a9722efb8a845e1・UI v10、公開a86c08367c44a4d4f4df776d617db991180a2644、tag ui-v10-details1419-20261010、Actions38026099293 success。匿名62/62ファイル一致、公開/ローカル/同1419データの旧UI v9切戻しがPC1280/390/320でPASS。公開2画像確認。Python157/JS29 PASS。新JSON13,813,547bytes、同内容整形版27,145,783bytesから49.1%減。旧不変版は書換えない。

取得runはcomplete4098・active_attemptなし、worker/workflow正常終了・ロックなし。古い稼働コードの最終監査22保留は現行コードの全再変換で解消済み、元ログを保持。collect_detail_catalog.py statusは取得状況の確認用。正式原本/公開記録は同runのlatest-verified-publication.jsonを読む。取得を二重起動しない。証拠はprivate/audits/detail1419-public-verification-20261010.json、full-linked-replay-comparison-20261010.json、full-linked-worker-finished-20261010.json、detail1419-content-coverage-20261010.json。

残件: 47ページなし保留、S90カード最大Lv360セルの原文空欄（SHA/原セル全件照合済み）、全効果/条件構造化、独立公式全件照合、本番の実在基礎カード新規追加実証、全面実機/スクリーンリーダー・Google実画面・本番障害全面復旧。Pステージ/適正、Sファイトは今回対象外。全リンク付きカードの取得・登録・公開確認と、全項目/全ゲームの完成を区別する。
