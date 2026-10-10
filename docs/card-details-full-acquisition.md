# 全件の詳細HTML取得とオフライン監査

更新: 2026-10-10 JST。対象1,363ページの保存と入力整合確認は完了（新規1,358/再利用5）。現行コードの全入力再変換で1,419カード（P548/S871）を例外なしで変換し、詳細原本r18へ登録済み。公開62ファイル一致とPC/390/320検索を確認済み。47ページなしは保留。**取得・原本登録の完了は、全ゲーム網羅や全効果・条件の構造化完成を意味しない**。

## 対象、期間、既知の不足

基礎索引 `v1-93a6a8b8d40e754a` の固定ID・P/S・URLを読み取り専用で使用する。1,466カード（P548/S918）中、個別URLあり1,419、URLなし47。URLを正規化・重複排除した取得対象は1,363ページ。47件はユーザーが保留したままとし、新しいURLを推測しない。

アイドルロードの28ページは、それぞれR基底・SRロード・SSRロードの3カードが同じURLを持つ。HTMLは一度だけ取得し、カード行は84件の別IDを維持する。節と派生の対応が確認できるまで、この84件の詳細変換は `needs_variant_mapping` とする。 現行の全入力再変換では28ページ・84カードすべての対応を確認済みで、派生対応の残件は0。

基礎索引の判明している初回実装日は2018-04-24～2026-10-02、初回日不明56件。これは全ゲームの収録期間やWikiの最終編集日を保証するものではない。取得日は `fetch.json` の `fetched_at` で別に記録する。再利用する5ページは2026-10-06～09の保存物であり、全ページが今回の最新取得と表示しない。

## 制御と保存

- `detail_catalog_enabled=true`、期待カード1,466・ページ1,363を別の明示設定とする。一覧用の旧 `full_collection_enabled=false` と `request_limit=20` は変更しない。詳細は凍結した全件カタログで限定し、任意URLや無制限巡回を許さない。
- P/S・固定ID・基礎索引のハッシュ・URL・件数が変わったら通信前に拒否する。1363より大きい実行予算も拒否する。
- 1ページずつ、前回の取得完了から60秒以上空ける。共通取得状態・排他ロックも使用する。robots.txtを各ページ取得前に確認するため、1ページにつき最大2リクエスト。画像や添付は取得しない。
- 429、503、403、確認画面、URL/本文の不整合、その他の取得失敗では後続を停止する。自動リトライ・自動再起動を行わない。新規失敗後24時間とサーバーRetry-Afterの長い期限を維持する。
- 取得済みの正常HTMLはURL・canonical・本文・SHA-256・取得日時を検証して再利用する。原入力を上書きせず、新規取得は一意な `attempt-...` ディレクトリへ保存する。
- 再開前と全ページ完了時にも保存済み入力の整合を検査する。ハッシュ不一致は確認待ちにし、黙って再取得・置換しない。
- runの `catalog.json` は不変。`state.json` は一時ファイルから置換し、ページごとの保存結果・再開位置・実行中の取得を記録する。`worker.lock` はPIDと開始時刻を持つ。`status` はプロセスの実在も確認する。
- 生HTML・効果原文・候補・監査・ログはすべて `private/` に保持し、Git/Pages/正式Sheetへ自動で送らない。PCの終了・スリープでは処理が止まる/休止する。常駐サービスや別端末での継続は設定していない。

## セットアップと通常の操作

READMEのPython仮想環境と `requirements.txt` を使用する。新規依存なし。インターネットからWikiへHTTPS接続できること、書込み可能な `private/raw/`、基礎索引の版付き `cards.json` が必要。別環境でも通常のPython CLIとして実行できる。停止中に原入力を安全にコピーすれば、同じ相対パスからオフライン変換を再現できる。Gitだけには非公開入力が含まれない。

```powershell
# 新規runだけ。すでにあるrunへinitを再実行しない
./.venv/Scripts/python.exe scripts/collect_detail_catalog.py init private/raw/detail-catalog-YYYYMMDD
./.venv/Scripts/python.exe scripts/collect_detail_catalog.py status private/raw/detail-catalog-YYYYMMDD
# 残りページ数以下の有限予算。試験なら1～2、今回の開始時は1358
./.venv/Scripts/python.exe scripts/collect_detail_catalog.py run private/raw/detail-catalog-YYYYMMDD --max-attempts 1358
```

今回のrunは `private/raw/detail-catalog-20261009`。60秒間隔だけで約22時間38分、応答・検証等を含め約23時間が目安。background実行でも同じCLIを使い、WindowsのStart-Processは `-WindowStyle Hidden` とする。stdout/stderrは再起動ごとに別名へ保存し、旧ログを保持する。ジョブを二重起動しない。トークンの消費・会話の終了は、このローカルプロセスの正常終了を意味しない。

```powershell
# 状況確認（追加のWiki通信なし）
./.venv/Scripts/python.exe scripts/collect_detail_catalog.py status private/raw/detail-catalog-20261009
# 安全な停止要求。通信中の応答保存を終える区切りで止める
./.venv/Scripts/python.exe scripts/collect_detail_catalog.py stop private/raw/detail-catalog-20261009
# statusでstopped、worker_is_alive=false、active_attempt=nullを確認した後に再開
./.venv/Scripts/python.exe scripts/collect_detail_catalog.py run private/raw/detail-catalog-20261009 --max-attempts 1363 --clear-stop
```

`max-attempts` はこの起動での新規試行の上限。既存の正常ページは予算を消費せずスキップし、残りが0なら新規通信をしない。47件は予算の対象外。`complete` は対象1,363ページの入力保存完了だけを意味し、詳細の検証・採用・公開や全ゲーム網羅の完成ではない。

## オフライン変換と欠損の監査

```powershell
./.venv/Scripts/python.exe scripts/transform_detail_catalog.py private/raw/detail-catalog-20261009 private/audits/detail-catalog-YYYYMMDD-checkpoint-01.json
./.venv/Scripts/python.exe -m unittest discover -s tests
```

取得中も、atomically保存された1つの状態スナップショットから変換する。出力先は未使用名とし、同じ内容の再実行のみ許可する。Wikiへの追加アクセス、入力更新、正式原本更新、公開を行わない。

`card_coverage` に全1,466件の固定ID、P/S、入力状態、URL、取得時刻・ハッシュ、変換結果を残す。候補には原セル位置を持つ技能データを保持する。状態は `input_pending` / `input_failed` / `input_needs_inspection` / `input_invalid` / `missing_page_on_hold` / `needs_variant_mapping` / `needs_structure_review` / `candidate_needs_review`。変換できないカードを抜いた件数だけで全件成功と表示しない。構造例外は保存HTMLだけで調査し、他の正常カードの変換を続ける。

全ページ取得後も、構造例外・派生対応・固定detail_idと手修正優先・原本コピーへの採用・公開用の効果構造化・Web検索・詳細バンドル版一致を別に検証する。Pステージ/適正、Sファイトは今回の候補に含めない。

## 失敗・強制終了後の復旧

1. `status`、stdout/stderr、該当attemptの `fetch.json` / `response.html`、共通 `collect_one.py status` を読む。新しい取得を先に起動しない。STOP要求中は終了を待ち、通信中のプロセスを無理に終了しない。
2. `worker_is_alive=false` なのにworker.lockがある場合は、記録PIDとプロセスを確認し、`release-stale-lock --expected-pid PID` を使う。生存PID/不一致PIDでは解除できない。PIDの再利用があれば、現存プロセスを終了して帳尻を合わせない。
3. `workflow.lock` が残った場合も、PIDが終了していることを確認し、同じ解除CLIへ `--lock-kind workflow` を指定する。この解除は共通取得ロックを変更しない。
4. 共通 `private/raw/acquisition-state.lock` が残る場合、このCLIは自動削除しない。WindowsではGet-CimInstance Win32_Processでcollect_one/all/detail_catalogを実行するPythonプロセスがないことを確認し、ロック・状態・ログを新しい監査ディレクトリへ退避してから、その明示したロックファイルだけをRemove-Item -LiteralPathで除く。状態JSON・失敗日時・Retry-After・原HTMLは削除しない。
5. 再開時、active_attemptの応答と成功報告が完全なら、ハッシュ等を検証して既取得として回復する。再送しない。欠落/部分保存で結果不明なら `needs_inspection` として停止する。
6. 結果不明のページを調査した後は `resolve-unknown RUN --page-id DC-... --reason '確認結果'` を使う。この操作は通信しない。完全な保存成功が確認できれば回復し、それ以外は履歴・部分保存を保持してfailedとし、確認時点から保守的に24時間停止する。ロックが残っていれば先に上記手順で確認する。
7. failedの原因を保存入力から確認し、共通ゲートが `can_fetch=true` になった後だけ `run RUN --max-attempts 1 --retry-page DC-...` と明示する。STOPがあれば `--clear-stop` も指定する。成功後に残りの予算で再開する。HTTP制限やrobots拒否を別URL・並列・待機削除で回避しない。

停止・復旧は元の原本Sheet、public site、既存入力を変更しない。ディスク不整合・ロックの所有者不明など、実行可否を確定できない状態は記録して止め、独立した正常入力の変換だけ続ける。


## 今回のbackground起動と最終監査

取得の後でオフライン監査まで行う `scripts/run_detail_workflow.py` を使用する。有限の取得予算を1回だけ実行し、完了・安全停止・失敗のいずれでも、保存済み状態から全1,466カードの監査を生成する。取得を自動再実行しない。構造例外は明記し、正式採用・公開は行わない。

```powershell
./.venv/Scripts/python.exe scripts/run_detail_workflow.py private/raw/detail-catalog-20261009 --max-attempts 1351 --clear-stop
```

上の1351は最終起動前の残数。再開時は実際のstatusから残数を確認する。wrapperの `workflow.lock` は最終監査まで保持し、`workflow-report.json` にphaseとPID、終了時の取得状態、監査の保存先・ハッシュ・不足を記録する。`phase=finished` は有限の取得・監査ジョブが終了した意味で、詳細データの全件完成を意味しない。取得失敗/確認待ちではCLIも終了コード1を返す。

最終出力は `private/audits/detail-catalog-<内容SHA256>.json`。取得状態がcompleteでも、全節の構造が未対応なら `all_details_validated=false` のまま。監査が失敗した場合はphase=audit_failedを残し、変換CLIだけを保存入力から再実行する。PC終了などでwrapperが強制終了した場合は、workflow.lockとworker.lockをそれぞれ所有PID確認後に解除してから再開する。


## 2026-10-09のHTTP200誤検知回復と後続

可視文字数990の正常S-Rを1000文字の基準で拒否したため、個別カードはcanonical・登録タイトル・スキル表で検証する方式へ変更した。後続P【♡AKQJ10】は観測URLに♡がないため停止したが、失敗時に保存したHTTP200本文を正しい登録タイトルと照合し、追加リクエストなしで別の正常入力ディレクトリへ回復した。失敗報告・時刻・応答SHA・以前のstateは保持している。実際のHTTP429等ではない。レビュー済みの同じ失敗日時・同じローカル理由だけを停止条件から除外し、実HTTPのバックオフ・Retry-Afterは維持する。

workflow-006は残り1279ページを有限予算で取得後、全カード監査を行う。PIDと現在の残数はHANDOFF.mdの最新記録と実stateで照合する。workflow-005の終了報告はworkflow-report-005-finished.jsonへ保存した。60カード865項目の原本/公開接続は別工程で実施し、現在は[詳細接続手順](card-details-integration.md)を使う。旧報告のdetails_adopted_or_published=falseはその取得ジョブが自動採用していない意味で、独立工程の段階採用・公開実績とは区別する。

## 登録済みページの取得順と凍結再変換

workflow007は登録済みロード28ページだけを優先し、取得頻度・共通ロック・HTTP停止を維持した。28ページは全件正常保存。通常順へ戻す008は残数1213の有限予算で、現行の派生変換器を読込み起動した。旧006/007の終了報告とログは保持。取得完了の監査も正式原本/公開へ自動採用しない。

優先指定は `run_detail_workflow.py RUN --max-attempts 残数 --clear-stop --priority-page DC-登録済ID`。複数指定できる。未知ID・重複は通信前に拒否する。成功済みを再送しない。429/Retry-Afterを回避する指定には使えない。

```powershell
./.venv/Scripts/python.exe scripts/transform_detail_catalog.py private/raw/detail-catalog-20261009 private/audits/new-candidate-a.json --save-state-snapshot private/audits/new-frozen-state.json
./.venv/Scripts/python.exe scripts/transform_detail_catalog.py private/raw/detail-catalog-20261009 private/audits/new-candidate-b.json --state-snapshot private/audits/new-frozen-state.json
```

初回は同じ原子的stateをprivateへ保存し、次回はそのstateと不変catalog/原HTMLを使う。取得が進行してlive stateが変わっても同じ内容SHAになることを実156件と合成境界で確認した。古いstateの入力が改変・消失していれば拒否して不足を記録する。原本・公開・取得状態は更新しない。状態スナップショットを公開先へ保存することも拒否する。


## 2026-10-09 今回の256件版上限と停止

ユーザー指定により原本/公開採用は256件まで。取得010はSTOPで終了、最終監査終了07:18:33UTC、state677/stopped、224保存/残1139、active_attemptなし、worker/workflow/request lockなし、旧PID終了。STOPを保持する。保存済みの原入力・最終オフライン候補は残すが、自動採用しない。再開指示までrun/clear-stopや追加採用を実行しない。現在の原本/公開確認と具体的な再開地点はHANDOFF.md末尾を参照する。

## 2026-10-10 全個別ページ分の原本登録・公開確認

全1,363保存ページを現行コードで再変換し、1,419カード（P548/S871）・構造例外0、旧1,380カード全値不変。39カード/656項目追加で原本r18・24,025項目。native全コピーへ21batch、全15タブ値一致・基礎9タブ不変・旧23,369固定IDと手修正保持。17,402書込セルと周囲26,006セルの書式/validation/chips/formula、追加656出典URL/全1419リンク/47空欄、5フィルターを確認。実exportの11範囲を代替描画し変更6画像を確認。Google実画面の成功とは扱わない。

詳細d1-7a9722efb8a845e1・UI v10、公開a86c08367c44a4d4f4df776d617db991180a2644、tag ui-v10-details1419-20261010、Actions38026099293 success。匿名62/62ファイル一致、公開/ローカル/同1419データの旧UI v9切戻しがPC1280/390/320でPASS。公開2画像確認。Python157/JS29 PASS。新JSON13,813,547bytes、同内容整形版27,145,783bytesから49.1%減。旧不変版は書換えない。

取得runはcomplete4098・active_attemptなし、worker/workflow正常終了・ロックなし。古い稼働コードの最終監査22保留は現行コードの全再変換で解消済み、元ログを保持。collect_detail_catalog.py statusは取得状況の確認用。正式原本/公開記録は同runのlatest-verified-publication.jsonを読む。取得を二重起動しない。証拠はprivate/audits/detail1419-public-verification-20261010.json、full-linked-replay-comparison-20261010.json、full-linked-worker-finished-20261010.json、detail1419-content-coverage-20261010.json。

残件: 47ページなし保留、S90カード最大Lv360セルの原文空欄（SHA/原セル全件照合済み）、全効果/条件構造化、独立公式全件照合、本番の実在基礎カード新規追加実証、全面実機/スクリーンリーダー・Google実画面・本番障害全面復旧。Pステージ/適正、Sファイトは今回対象外。全リンク付きカードの取得・登録・公開確認と、全項目/全ゲームの完成を区別する。
